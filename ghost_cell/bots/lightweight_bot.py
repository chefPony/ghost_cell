import sys
import numpy as np
from collections import deque
from heapq import heappush, heappop
from time import time

ID, PLAYER, TROOPS, PROD, FROM, TO, SIZE, DIST, BLOCKED = 0, 1, 2, 3, 2, 3, 4, 5, 5
PLAYER_MAP = {-1: 1, 1: 0}


def dijkstra(distance_matrix, source, min_distance_matrix, step_matrix, path_tree):
    n_node = distance_matrix.shape[0]
    dist_dict = {source: 0}
    node_set = list()
    heappush(node_set, (0, source))
    explored = list()
    prev = dict()
    while len(node_set) > 0:
        current_d, current_n = heappop(node_set)
        if current_d > dist_dict[current_n]:
            continue
        to_explore = [n for n in range(n_node) if (n != current_n) and (n not in explored)]
        for neigh in to_explore:
            d_neigh = current_d + distance_matrix[current_n, neigh]
            if d_neigh < dist_dict.get(neigh, 1000):
                dist_dict[neigh] = d_neigh
                prev[neigh] = current_n
                heappush(node_set, (d_neigh, neigh))

    for n in [n for n in range(n_node) if n != source]:
        min_distance_matrix[source, n] = dist_dict[n]
        path_tree[(source, n)] = deque()
        current = n
        while current != source:
            path_tree[(source, n)].appendleft((prev[current], current))
            current = prev[current]
        step_matrix[source, n] = len(path_tree[(source, n)])


class GameState:
    def __init__(self):
        self.player_production = {0: 0, 1: 0, -1: 0}
        self.player_troops = {0: 0, 1: 0, -1: 0}

    def initialize(self, input):
        self.factory_count = int(input())  # the number of factories
        self.link_count = int(input())  # the number of links between factories
        self.distance_matrix = np.zeros((self.factory_count, self.factory_count), dtype=int)
        for i in range(self.link_count):
            factory_1, factory_2, distance = [int(j) for j in input().split()]
            self.distance_matrix[factory_1, factory_2], self.distance_matrix[factory_2, factory_1] = distance, distance
        self.max_distance = np.max(self.distance_matrix)
        self.factories = np.zeros((self.factory_count, 6), dtype=int)
        self.troops = np.zeros((self.factory_count, self.max_distance + 1, 2), dtype=int)
        self.bombs = dict()

        self.path_tree = dict()
        self.min_distance_matrix = np.zeros((self.factory_count, self.factory_count), dtype=int)
        self.step_matrix = np.zeros((self.factory_count, self.factory_count), dtype=int)
        for source in range(self.factory_count):
            dijkstra(self.distance_matrix, source, self.min_distance_matrix, self.step_matrix, self.path_tree)

    def update_factory(self, entity_id, player, troops, prod, blocked):
        self.factories[entity_id, ID] = entity_id
        self.factories[entity_id, PLAYER] = player
        self.factories[entity_id, TROOPS] = troops
        self.factories[entity_id, PROD] = prod
        self.factories[entity_id, BLOCKED] = blocked

    def update_troop(self, entity_id, player, source, destination, troops, distance):
        self.troops[destination, distance, PLAYER_MAP[player]] += troops

    def update_bomb(self, entity_id, player, source, destination, countdown):
        self.bombs[entity_id] = {"id": entity_id, "player": player, "source": source, "destination": destination,
                                 "countdown": countdown}

    def current_status(self, input):
        self.troops[:, :, :] = 0
        self.entity_count = int(input())  # the number of entities (e.g. factories and troops)
        for i in range(self.entity_count):
            inputs = input().split()
            entity_id, entity_type = int(inputs[0]), inputs[1]
            arg_1, arg_2, arg_3, arg_4, arg_5 = int(inputs[2]), int(inputs[3]), int(inputs[4]), int(inputs[5]), int(
                inputs[6])
            if entity_type == "FACTORY":
                self.update_factory(entity_id, player=arg_1, troops=arg_2, prod=arg_3, blocked=arg_4)
            elif entity_type == "TROOP":
                self.update_troop(entity_id, player=arg_1, source=arg_2, destination=arg_3, troops=arg_4,
                                  distance=arg_5)
            elif entity_type == "BOMB":
                self.update_bomb(entity_id, player=arg_1, source=arg_2, destination=arg_3, countdown=arg_4)

    def reset(self):
        self.troops[:, :, :] = 0
        self.bombs = dict()


class Player:

    def __init__(self, player_id: int, moving_troop_dist_th: int, moving_troop_discount: float,
                 stationing_troop_dist_th: int, stationing_troop_discount: float, factory_value_penalty=0.9):
        self.moving_troop_dist_th = moving_troop_dist_th
        self.moving_troop_discount = moving_troop_discount
        self.stationing_troop_dist_th = stationing_troop_dist_th
        self.stationing_troop_discount = stationing_troop_discount
        self.factory_value_penalty = factory_value_penalty
        self.action_list = list()
        self.player_id = player_id

        self.state = None
        self.my_factories, self.enemy_factories, self.total_prod = None, None, 0
        self.prod_penalty_matrix = None
        self.bomb_state = dict()

        self.bomb_reserve = 2

    def _moving_troops_cost(self, factory_id: int):
        troop_discount = np.array([self.moving_troop_discount ** i for i in range(self.moving_troop_dist_th + 1)])
        incoming_enemy = self.state.troops[factory_id, :self.moving_troop_dist_th + 1, PLAYER_MAP[-self.player_id]]
        incoming_ally = self.state.troops[factory_id, :self.moving_troop_dist_th + 1, PLAYER_MAP[self.player_id]]
        return sum((incoming_enemy - incoming_ally) * troop_discount)

    def _stationing_troops_cost(self, factory_id: int):
        enemy_factories_nearby = (self.state.factories[:, PLAYER] == -self.player_id) & \
                                 (self.state.factories[:, ID] != factory_id) & \
                                 (self.state.distance_matrix[factory_id, :] <= self.stationing_troop_dist_th)
        factory_discount = [self.stationing_troop_discount ** max(d, 0)
                            for d in self.state.distance_matrix[factory_id, enemy_factories_nearby]]

        nearby_enemy = self.state.factories[enemy_factories_nearby, TROOPS]
        return sum(nearby_enemy * factory_discount)

    def _available_troops_factory(self, factory_id: int):
        if self.state.factories[factory_id, PLAYER] != self.player_id:
            return 0.
        else:
            factory_cost, troop_cost = self._stationing_troops_cost(factory_id), self._moving_troops_cost(factory_id)
            troops = self.state.factories[factory_id, TROOPS]
            prod = self.state.factories[factory_id, PROD]
            # blocked = self.state.factories[factory_id, BLOCKED]
            available_troops = troops - factory_cost - max(troop_cost, 0)
            return available_troops * (available_troops > 0)

    def _compute_distance_penalty_matrix(self):
        self.distance_penalty_matrix = np.power(np.array(self.moving_troop_discount),
                                                np.maximum(self.state.distance_matrix - 1, 0))

    def _compute_prod_penalty_matrix(self):
        prod_vec = self.state.factories[:, PROD] * (self.state.factories[:, BLOCKED] == 0) * self.enemy_factories
        self.prod_penalty_matrix = (self.state.min_distance_matrix + self.state.step_matrix - 1) * prod_vec[None, :]

    def _compute_troops_required(self):

        troops_required = np.array([
            [self._required_troops_factory(factory_id) for factory_id in self.state.factories[:, ID]]]).T
        troops_required = np.ceil(troops_required)

        self.total_troops_required = sum(troops_required)

        self.troops_required_matrix = np.dot(troops_required, self.matrix_converter).T
        self.troops_required_matrix = self.prod_penalty_matrix + self.troops_required_matrix

    def _compute_troops_reserve(self):

        troops_reserve = np.array([
            [self._available_troops_factory(factory_id) for factory_id in self.state.factories[:, ID]]]).T
        troops_reserve = np.floor(abs(troops_reserve) * (troops_reserve > 0))

        # self.total_capacity = sum(troops_reserve)
        self.troops_reserve_vector = troops_reserve
        # self.troops_reserve_matrix = np.dot(troops_reserve, self.matrix_converter)

    def _required_troops_factory(self, factory_id):
        player = self.state.factories[factory_id, PLAYER]
        troops = self.state.factories[factory_id, TROOPS]
        prod = self.state.factories[factory_id, PROD]
        block = self.state.factories[factory_id, BLOCKED]
        troop_cost, factory_cost = self._moving_troops_cost(factory_id), self._stationing_troops_cost(factory_id)
        if player == self.player_id:
            required_to_take = troop_cost + factory_cost - troops - prod * (block == 0)
        elif player == -self.player_id:
            required_to_take = troop_cost + factory_cost + troops + 1 + prod * (block == 0)
        else:
            required_to_take = troop_cost + factory_cost + troops + 1

        return abs(required_to_take) * (required_to_take > 0)

    def _factory_value(self, factory_id, k=3):
        prod = self.state.factories[factory_id, PROD]
        k_neighbors = min(k, sum(self.my_factories), sum(self.enemy_factories))
        k_ally, k_enemy = 0, 0
        sum_distance_ally, sum_distance_enemy = 0, 0
        for fid in np.argsort(self.state.distance_matrix[factory_id, :]):
            if fid == factory_id:
                continue
            elif (k_ally == k_neighbors) & (k_enemy == k_neighbors):
                break
            elif self.my_factories[fid] & (k_ally < k_neighbors):
                sum_distance_ally += self.state.distance_matrix[factory_id, fid]
                k_ally += 1
            elif self.enemy_factories[fid] & (k_enemy < k_neighbors):
                sum_distance_enemy += self.state.distance_matrix[factory_id, fid]
                k_enemy += 1
        if (sum_distance_ally > 0) & (sum_distance_enemy > 0):
            ratio = (sum_distance_enemy / sum_distance_ally)
        else:
            ratio = 1
        return (prod + 0.1) * ratio

    def _compute_value(self):
        value = np.array([self._factory_value(fid, 3) for fid in self.state.factories[:, ID]])
        # print(value, file=sys.stderr)
        return value

    def predict_bomb(self):
        fids = self.state.factories[self.my_factories, ID]
        troops = self.state.factories[self.my_factories, TROOPS]
        prod = self.state.factories[self.my_factories, PROD]
        targets = [(fid, tr, pr) for fid, tr, pr in zip(fids, troops, prod)]
        targets = list(sorted(targets, key=lambda x: (-x[1], -x[2])))

        bomb_keys = list(self.bomb_state.keys())
        for bid in bomb_keys:
            if bid not in self.state.bombs.keys():
                self.bomb_state.pop(bid)

        for bomb_id, bomb in self.state.bombs.items():
            source, destination, countdown = bomb["source"], bomb["destination"], bomb["countdown"]

            if bomb_id not in self.bomb_state.keys():
                self.bomb_state[bomb_id] = bomb
                self.bomb_state[bomb_id]["turn_active"] = 1
            else:
                self.bomb_state[bomb_id]["turn_active"] += 1
                self.bomb_state[bomb_id]["countdown"] -= 1

            turn_active = self.bomb_state[bomb_id]["turn_active"]
            destination = self.bomb_state[bomb_id]["destination"]
            distance_from_target = self.state.distance_matrix[source, destination] if destination != -1 else -1
            if (bomb['player'] == -self.player_id) & (turn_active > distance_from_target):
                for fid, _, _ in targets:
                    distance_from_target = self.state.distance_matrix[source, fid]
                    if turn_active <= distance_from_target:
                        self.bomb_state[bomb_id]["destination"] = fid
                        self.bomb_state[bomb_id]["countdown"] = distance_from_target - turn_active
                        break

            # EVACUATE FACTORY
            destination = self.bomb_state[bomb_id]["destination"]
            if (self.my_factories[destination]) & (self.bomb_state[bomb_id]["countdown"] == 1):
                evacuate = self.bomb_state[bomb_id]["destination"]
                already_inc = f"INC {evacuate}" in self.action_list
                troops = self.troops_vector[evacuate]
                prod = max(self.state.factories[evacuate, PROD] + already_inc, 3)
                increments = round(min(troops / 10, 3 - prod))
                # print(f"{increments} {troops} {prod}", file=sys.stderr)
                while increments > 0:
                    self.action_list.append(f"INC {evacuate}")
                    troops -= 10
                    increments -= 1
                refugee = np.argsort(self.state.distance_matrix[evacuate, :])
                for fid in refugee:
                    if self.my_factories[fid] & (fid != evacuate):
                        self.action_list.append(f"MOVE {evacuate} {fid} {troops + prod}")
                        break

    def _prioritize_target(self):
        target_value = self._compute_value()
        total_troops_ratio = self.total_enemy_troops / self.total_ally_troops
        max_required_target = np.max(self.troops_required_matrix, axis=0)
        ordered_targets = np.argsort(-target_value)
        ordered_targets = ordered_targets[(target_value[ordered_targets] > total_troops_ratio) &
                                          (max_required_target[ordered_targets] >= 1)]
        return ordered_targets, max_required_target

    def select_move(self):
        #print(self.troops_required_matrix, file=sys.stderr)
        ordered_targets, max_required_target = self._prioritize_target()

        for target_id in ordered_targets:
            max_troops_required = max_required_target[target_id]
            if max_troops_required <= sum(self.troops_reserve_vector):
                ordered_sources = np.argsort(self.state.min_distance_matrix[:, target_id])
                to_consider = (self.my_factories[ordered_sources]) & (ordered_sources != target_id) & \
                              (self.troops_reserve_vector[ordered_sources].reshape((-1,)) >= 1)
                ordered_sources = ordered_sources[to_consider]
                committed = 0
                #print(f"Target: {target_id} {max_troops_required}", file=sys.stderr)
                #print(f"Sources: {ordered_sources}", file=sys.stderr)

                for source_id in ordered_sources:
                    #print(f"Committed: {committed}", file=sys.stderr)
                    move_list = self.state.path_tree[(source_id, target_id)]
                    first_target = move_list[0][1]
                    required_from_source = 0
                    #print(f"Source {source_id}, path {move_list}", file=sys.stderr)
                    for isource, itarget in move_list:
                        #print(f"{isource} {itarget} {self.troops_required_matrix[isource, itarget]}", file=sys.stderr)
                        required_from_source += self.troops_required_matrix[source_id, itarget]
                    n_cyborgs = int(min(required_from_source, self.troops_reserve_vector[source_id]))
                    #print(f"Required {required_from_source}, n_cyborgs {n_cyborgs}", file=sys.stderr)
                    self.action_list.append(f"MOVE {source_id} {first_target} {n_cyborgs}")
                    committed += n_cyborgs
                    self._update_from_move(source_id, first_target, n_cyborgs)
                    max_troops_required = np.max(self.troops_required_matrix[:, target_id], axis=0)
                    if (committed >= required_from_source) | (committed > max_troops_required):
                        break

    def select_increments(self):
        if sum(self.troops_reserve_vector) < 10:
            return
        for source_id, available in enumerate(self.troops_reserve_vector):
            if (available > 10) & (self.state.factories[source_id, PROD] < 3):
                # print(f" FACTORY {self.state.factories}", file=sys.stderr)
                # print(f" AVAILABLE {self.troops_reserve_matrix}", file=sys.stderr)
                # print(f" INC FACTORY {source_id} {available} {self.state.factories[source_id, TROOPS]}", file=sys.stderr)
                self.action_list.append(f"INC {source_id}")
                self._update_after_increment(source_id)

    def select_bomb_target(self):
        bomb_value_matrix = np.zeros((self.state.factory_count, self.state.factory_count))
        stationed_troops = -np.dot((self.state.factories[:, TROOPS] * self.state.factories[:, PLAYER]).reshape(-1, 1),
                                  self.matrix_converter).T
        prod_block = -np.dot((self.state.factories[:, PROD] * 5 * self.state.factories[:, PLAYER]).reshape(-1, 1),
                            self.matrix_converter).T
        distance_penalty = np.power(np.array(0.9), self.state.distance_matrix)
        bomb_value_matrix = stationed_troops * distance_penalty
        #TODO: fix this
        sign = np.sign(bomb_value_matrix)
        bomb_value_matrix = np.floor(np.abs(bomb_value_matrix/2))
        bomb_value_matrix[(bomb_value_matrix >= 5) & (bomb_value_matrix < 10)] = 10
        bomb_value_matrix *= sign
        for source_id in range(self.state.factory_count):
            for target_id in range(self.state.factory_count):
                if source_id == target_id:
                    bomb_value_matrix[source_id, target_id] = 0
                else:
                    distance = self.state.distance_matrix[source_id, target_id]
                    discount_vector = np.power(np.array(0.9), np.arange(distance, 0, -1))
                    incoming_enemy = sum(self.state.troops[target_id, 1:(distance + 1),
                                         PLAYER_MAP[-self.player_id]] * discount_vector)
                    incoming_ally = sum(self.state.troops[target_id, 1:(distance + 1),
                                        PLAYER_MAP[self.player_id]] * discount_vector)
                    bomb_value_matrix[source_id, target_id] += (incoming_enemy - incoming_ally)

        legal_sources = np.dot(self.my_factories.reshape(-1, 1),  self.matrix_converter)
        bomb_value_matrix = (bomb_value_matrix + prod_block) * legal_sources

        sources, targets = np.unravel_index(np.argsort(-bomb_value_matrix, axis=None), bomb_value_matrix.shape)

        if len(self.state.bombs) > 0:
            my_bomb_targets = [v["destination"] for k, v in self.state.bombs.items() if v["player"] == self.player_id]
        else:
            my_bomb_targets = list()

        for source, target in zip(sources, targets):
            if (bomb_value_matrix[source, target] > 20) & (target not in my_bomb_targets) & (self.bomb_reserve > 0):
                #print(f"BOMB {source} {target}", file=sys.stderr)
                #print(f"{self.my_factories[source]}", file=sys.stderr)
                self.action_list.append(f"BOMB {source} {target}")
                self._update_after_bomb(source, target)
            else:
                break


    def _update_from_state(self, game_state: GameState):
        self.state = game_state
        self.matrix_converter = np.ones((1, self.state.factory_count))
        self.my_factories = self.state.factories[:, PLAYER] == self.player_id
        self.enemy_factories = self.state.factories[:, PLAYER] == -self.player_id
        self.moving_troop_dist_th = min(self.moving_troop_dist_th, self.state.max_distance)
        self.stationing_troop_dist_th = min(self.stationing_troop_dist_th, self.state.max_distance)
        self.total_prod = sum(game_state.factories[self.my_factories, PROD])

        self.troops_vector = self.state.factories[:, TROOPS]
        self.total_ally_troops = sum(self.state.factories[self.my_factories, TROOPS])
        self.total_ally_troops += np.sum(self.state.troops[:, :, PLAYER_MAP[self.player_id]])
        self.total_enemy_troops = sum(self.state.factories[self.enemy_factories, TROOPS])
        self.total_enemy_troops += np.sum(self.state.troops[:, :, PLAYER_MAP[-self.player_id]])

        self._compute_distance_penalty_matrix()
        self._compute_prod_penalty_matrix()
        self._compute_troops_required()
        self._compute_troops_reserve()

    def _update_from_move(self, source_id: int, target_id: int, n_cyborgs: int):
        self.troops_reserve_vector[source_id] -= n_cyborgs
        self.troops_vector[source_id] -= n_cyborgs
        self.troops_required_matrix[:, target_id] -= n_cyborgs
        self.troops_required_matrix = np.floor(self.troops_required_matrix) * (self.troops_required_matrix > 0)

    def _update_after_increment(self, factory_id):
        self.troops_reserve_vector[factory_id] -= 10
        self.troops_vector[factory_id] -= 10

    def _update_after_bomb(self, source_id: int, target_id: int):
        self.troops_reserve_vector[source_id] = 0
        self.bomb_reserve -= 1

    def select_plan(self):
        self.select_increments()
        if self.bomb_reserve > 0:
            self.select_bomb_target()
        self.select_move()
        self.predict_bomb()
        if len(self.action_list) == 0:
            self.action_list.append("WAIT")

    def execute_plan(self):
        print(";".join(self.action_list))

    def reset(self):
        self.action_list = list()


if __name__ == "__main__":
    game = GameState()
    game.initialize(input)
    agent = Player(player_id=1, moving_troop_dist_th=5, moving_troop_discount=1., stationing_troop_dist_th=3,
                   stationing_troop_discount=0.7)
    # game loop
    while True:
        start = time()
        game.current_status(input)
        agent._update_from_state(game)
        # Write an action using print
        # To debug: print("Debug messages...", file=sys.stderr, flush=True)
        # Any valid action, such as "WAIT" or "MOVE source destination cyborgs"
        start_plan = time()
        agent.select_plan()
        agent.execute_plan()
        agent.reset()
        game.reset()
