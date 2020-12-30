import sys
import numpy as np
from collections import defaultdict
from time import time

ID, PLAYER, TROOPS, PROD, FROM, TO, SIZE, DIST, BLOCKED = 0, 1, 2, 3, 2, 3, 4, 5, 5
PLAYER_MAP = {-1: 1, 1: 0}

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
        self.bombs = defaultdict(list)

    def update_factory(self, entity_id, player, troops, prod, blocked):
        self.factories[entity_id, ID] = entity_id
        self.factories[entity_id, PLAYER] = player
        self.factories[entity_id, TROOPS] = troops
        self.factories[entity_id, PROD] = prod
        self.factories[entity_id, BLOCKED] = blocked

    def update_troop(self, entity_id, player, source, destination, troops, distance):
        self.troops[destination, distance, PLAYER_MAP[player]] += troops

    def update_bomb(self, entity_id, player, source, destination, distance):
        self.bombs[distance].append({"id": entity_id, "player": player, "source": source, "destination": destination,
                                     "distance": distance})

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
                self.update_bomb(entity_id, player=arg_1, source=arg_2, destination=arg_3, distance=arg_4)


class Player:

    def __init__(self, player_id: int,  moving_troop_dist_th: int, moving_troop_discount: float,
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

    def _update_from_state(self, game_state: GameState):
        self.state = game_state
        self.matrix_converter = np.ones((1, self.state.factory_count))
        self.my_factories = self.state.factories[:, PLAYER] == self.player_id
        self.enemy_factories = self.state.factories[:, PLAYER] == -self.player_id
        self.moving_troop_dist_th = min(self.moving_troop_dist_th, self.state.max_distance)
        self.stationing_troop_dist_th = min(self.stationing_troop_dist_th, self.state.max_distance)
        self.total_prod = sum(game_state.factories[self.my_factories, PROD])

        self._compute_distance_penalty_matrix()
        self._compute_prod_penalty_matrix()
        self._compute_troops_required()
        self._compute_troops_reserve()

    def _update_from_move(self, source_id: int, target_id: int, n_cyborgs: int):
        self.troops_reserve_vector[source_id] -= n_cyborgs
        self.troops_required_matrix[:, target_id] -= n_cyborgs
        self.troops_required_matrix = np.floor(self.troops_required_matrix) * (self.troops_required_matrix > 0)

    def _moving_troops_cost(self, factory_id: int):
        troop_discount = np.array([self.moving_troop_discount ** i for i in range(self.moving_troop_dist_th + 1)])
        incoming_enemy = self.state.troops[factory_id, :self.moving_troop_dist_th + 1, PLAYER_MAP[-self.player_id]]
        incoming_ally = self.state.troops[factory_id, :self.moving_troop_dist_th + 1, PLAYER_MAP[self.player_id]]
        return sum((incoming_enemy - incoming_ally) * troop_discount)

    def _stationing_troops_cost(self, factory_id: int):
        enemy_factories_nearby = (self.state.factories[:, PLAYER] == -self.player_id) & \
                                 (self.state.factories[:, ID] != factory_id) &\
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
            blocked = self.state.factories[factory_id, BLOCKED]
            available_troops = troops + prod * (blocked == 0) - factory_cost - max(troop_cost, 0)
            return available_troops * (available_troops > 0)

    def _compute_distance_penalty_matrix(self):
        self.distance_penalty_matrix = np.power(np.array(self.moving_troop_discount),
                                                np.maximum(self.state.distance_matrix-1, 0))

    def _compute_prod_penalty_matrix(self):
        prod_vec = self.state.factories[:, PROD] * self.enemy_factories
        self.prod_penalty_matrix = self.state.distance_matrix * prod_vec[None, :]

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

        #self.total_capacity = sum(troops_reserve)
        self.troops_reserve_vector = troops_reserve
        #self.troops_reserve_matrix = np.dot(troops_reserve, self.matrix_converter)

    def _required_troops_factory(self, factory_id):
        player = self.state.factories[factory_id, PLAYER]
        troops = self.state.factories[factory_id, TROOPS]
        troop_cost, factory_cost = self._moving_troops_cost(factory_id), self._stationing_troops_cost(factory_id)
        if player == self.player_id:
            required_to_take = troop_cost + factory_cost - troops
        elif player == -self.player_id:
            required_to_take = troop_cost + factory_cost + troops + 1
        else:
            required_to_take = troop_cost + factory_cost + troops + 1

        return abs(required_to_take) * (required_to_take > 0)

    def _compute_factories_value(self):
        prod = self.state.factories[:, PROD]
        to_consider_ally = (self.state.factories[:, ID] != self.state.factories[:, ID, None]) & self.my_factories
        to_consider_enemy = (self.state.factories[:, ID] != self.state.factories[:, ID, None]) & self.enemy_factories
        n_vec_ally = np.sum(to_consider_ally, axis=1, dtype=int)
        mean_distance_ally = np.sum(self.state.distance_matrix * to_consider_ally, axis=1)/(n_vec_ally + 1e-5)
        mean_distance_ally = mean_distance_ally + (n_vec_ally < 1)
        n_vec_enemy = np.sum(to_consider_enemy, axis=1, dtype=int)
        mean_distance_enemy = np.sum(self.state.distance_matrix * to_consider_enemy, axis=1)/(n_vec_enemy + 1e-5)
        mean_distance_enemy = mean_distance_enemy + (n_vec_enemy < 1)
        return (prod * 10 + 1) * mean_distance_enemy/mean_distance_ally

    def select_move(self):
        target_value = self._compute_factories_value()
        max_required_target = np.max(self.troops_required_matrix, axis=0)
        ordered_targets = np.array(list(reversed(np.argsort(target_value))))
        ordered_targets = ordered_targets[(target_value[ordered_targets] > 1) &
                                          (max_required_target[ordered_targets] > 0)]
        for target_id in ordered_targets:
            max_troops_required = max_required_target[target_id]
            if max_troops_required <= sum(self.troops_reserve_vector):
                ordered_sources = np.array(list(reversed(np.argsort(self.state.distance_matrix[:, target_id]))))
                to_consider = (self.my_factories[ordered_sources]) & (ordered_sources != target_id) & \
                              (self.troops_reserve_vector[ordered_sources].reshape((-1,)) > 0)
                ordered_sources = ordered_sources[to_consider]
                committed = 0
                k = 0
                for source_id in ordered_sources:
                    required_from_source = self.troops_required_matrix[source_id, target_id]
                    n_cyborgs = int(min(required_from_source, self.troops_reserve_vector[source_id]))
                    self.action_list.append(f"MOVE {source_id} {target_id} {n_cyborgs}")
                    committed += n_cyborgs
                    self._update_from_move(source_id, target_id, n_cyborgs)
                    if (committed >= required_from_source) | (committed > max_troops_required):
                        break

    def select_increments(self):
        if sum(self.troops_reserve_vector) < 10:
            return
        for source_id, available in enumerate(self.troops_reserve_vector):
            if (available > 10) & (self.state.factories[source_id, PROD] < 3):
                #print(f" FACTORY {self.state.factories}", file=sys.stderr)
                #print(f" AVAILABLE {self.troops_reserve_matrix}", file=sys.stderr)
                #print(f" INC FACTORY {source_id} {available} {self.state.factories[source_id, TROOPS]}", file=sys.stderr)
                self.action_list.append(f"INC {source_id}")

    def select_plan(self):
        self.select_move()
        self.select_increments()
        if len(self.action_list) == 0:
            self.action_list.append("WAIT")

    def execute_plan(self):
        print(";".join(self.action_list))

    def reset(self):
        self.action_list = list()


if __name__ == "__main__":
    game = GameState()
    game.initialize(input)
    agent = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.99, stationing_troop_dist_th=100,
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
        game.troops[:, :, :] = 0

