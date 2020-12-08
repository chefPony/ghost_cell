import numpy as np
import sys
import math
from copy import copy
from collections import defaultdict
from time import time

ID, PLAYER, TROOPS, PROD, FROM, TO, SIZE, DIST, BLOCKED = 0, 1, 2, 3, 2, 3, 4, 5, 5
PLAYER_MAP = {-1: 1, 1: 0}


class Game:
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
        self.factories = np.zeros((self.factory_count, 6))
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
        self.update_stats()

    def clone(self):
        game_proj = Game()
        game_proj.factory_count = self.factory_count
        game_proj.max_distance = self.max_distance
        game_proj.factories = self.factories.copy()
        game_proj.troops = self.troops.copy()
        game_proj.distance_matrix = self.distance_matrix
        game_proj.bombs = self.bombs.copy()
        game_proj.player_production = self.player_production.copy()
        game_proj.player_troops = self.player_troops.copy()
        return game_proj

    def produce_new_cyborgs(self):
        prod_factories = (self.factories[:, PLAYER] == 1) | (self.factories[:, PLAYER] == -1)
        self.factories[prod_factories, TROOPS] += np.where(self.factories[prod_factories, BLOCKED] == 0,
                                                           self.factories[prod_factories, PROD], 0)

    def move_cyborgs(self):
        self.troops = np.roll(self.troops, shift=-1, axis=1)

    def solve_battles(self):
        troop_balance = self.troops[:, :, PLAYER_MAP[1]] - self.troops[:, :, PLAYER_MAP[-1]]
        incoming, factory_troops = abs(troop_balance[:, 0]), self.factories[:, TROOPS]
        attack_player, factory_player = np.sign(troop_balance[:, 0]), self.factories[:, PLAYER]
        outcome_troops = np.where(factory_player == attack_player, factory_troops + incoming, factory_troops - incoming)
        outcome_player = np.where(outcome_troops >= 0, factory_player, attack_player)
        outcome_troops = np.abs(outcome_troops)
        self.factories[:, TROOPS], self.factories[:, PLAYER] = outcome_troops, outcome_player
        self.troops[:, 0] = 0

    def update_stats(self):
        for player in [-1, 1]:
            f_player = self.factories[:, PLAYER] == player
            self.player_production[player] = np.sum(self.factories[f_player, PROD])
            self.player_troops[player] = np.sum(self.factories[f_player, TROOPS]) + \
                                         np.sum(self.troops[:, :, PLAYER_MAP[player]])

    def next_state(self, action):
        # print(f"In NEXT STATE", file=sys.stderr, flush=True)
        # Move Cyborgs
        self.move_cyborgs()
        # Increase troops for production
        action.apply(self)
        self.produce_new_cyborgs()
        # Battle
        self.solve_battles()
        self.update_stats()
        # for d in range(1, game_proj.max_distance):
        #    if d not in game_proj.bombs.keys():
        #        continue
        #    elif d > 1:
        #        incoming_bombs = game_proj.bombs.pop(d)
        #        game_proj.bombs[d - 1] = incoming_bombs
        #    else:
        #        bomb = game_proj.bombs.pop(d)
        #        destroyed = max(int(game_proj[bomb["destination"], TROOPS] / 2), 10)
        #        game_proj[bomb["destination"], TROOPS] -= destroyed
        #        game_proj[bomb["destination"], PROD] = 0


class Action:
    def apply(self, game):
        pass

    def is_valid(self, game):
        raise NotImplementedError

    @property
    def str(self):
        raise NotImplementedError


class Wait(Action):
    def __init__(self):
        self.prefix = "WAIT"

    def is_valid(self, game):
        return True

    def apply(self, game):
        pass

    @property
    def str(self):
        return f"{self.prefix}"


class Message(Action):
    def __init__(self, message):
        self.prefix = "MSG"
        self.message = message

    def is_valid(self, game):
        return True

    @property
    def str(self):
        return f"{self.prefix} {self.message}"


class Move(Action):
    def __init__(self, source, destination, cyborg_count):
        self.source = int(source)
        self.destination = int(destination)
        self.cyborg_count = int(cyborg_count)
        self.prefix = "MOVE"

    @property
    def str(self):
        return f"{self.prefix} {self.source} {self.destination} {self.cyborg_count}"

    def apply(self, game):
        game.factories[self.source, TROOPS] = game.factories[self.source, TROOPS] - self.cyborg_count
        distance = game.distance_matrix[self.source, self.destination]
        factory_update = time()
        game.update_troop(entity_id=-1, player=1, source=self.source, destination=self.destination,
                          troops=self.cyborg_count, distance=distance)

    def is_valid(self, game):
        if game.factories[self.source, PLAYER] != 1:
            return False
        elif self.source == self.destination:
            return False
        elif self.cyborg_count <= 0:
            return False
        else:
            return True


class IncreaseProd(Action):
    def __init__(self, factory):
        self.factory = int(factory)
        self.prefix = "INC"

    def apply(self, game):
        game.factories[self.factory, PROD] += 1
        game.factories[self.factory, TROOPS] += -10

    def is_valid(self, game):
        if game.factories[self.factory, PLAYER] != 1:
            return False
        elif game.factories[self.factory, TROOPS] < 10:
            return False
        elif game.factories[self.factory, PROD] > 2:
            return False
        else:
            return True

    @property
    def str(self):
        return f"{self.prefix} {self.factory}"


class SendBomb(Action):
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
        self.prefix = "BOMB"

    def is_valid(self, game):
        source_attr = game.factories.loc[self.source]
        if source_attr.player != 1:
            return False
        else:
            return True

    def apply(self, game):
        init_clone = time()
        game_proj = game.clone()
        end_clone = time()
        distance = game.distance_matrix[self.source, self.destination]
        factory_update = time()
        game_proj.update_bomb(entity_id=-1, player=1, source=self.source, destination=self.destination)
        troop_update = time()

    @property
    def str(self):
        return f"{self.prefix} {self.source} {self.destination}"


class ActionEvaluator:

    def __init__(self, criterion, optimizer):
        self.criterion = criterion
        self.optimizer = optimizer

    def evaluate(self, action, game):
        return self.criterion(action, game)

    def optimize(self, action, game):
        return self.optimizer(action, game, self.criterion)


def move_optimizer(action, game, criterion):
    # print(f"MOVE OPTIMIZER", file=sys.stderr, flush=True)
    init_opt = time()
    if isinstance(action, Wait):
        return criterion(action, game)
    best_value = -10000
    best_action = action
    source_troops = game.factories[int(action.source), TROOPS]
    for p in [0.3, 0.9]:
        action.cyborg_count = int(source_troops * p)
        if int(source_troops * p) == 0:
            continue
        else:
            init_eval = time()
            value = criterion(action, game)
            # print(f"Move evaluated in {(time() - init_eval) * 1e3}ms", file=sys.stderr, flush=True)
            if value > best_value:
                best_value = value
                best_action = action.cyborg_count

    action.cyborg_count = best_action
    # print(f"Move optimized in {(time() - init_opt) * 1e3}ms", file=sys.stderr, flush=True)
    return best_value


def do_not_optimize(action, game, criterion):
    if isinstance(action, Move):
        source_troops = game.factories[action.source, TROOPS]
        action.cyborg_count = int(source_troops * 0.3)
        if action.cyborg_count == 0:
            return -1000
    value = criterion(action, game)
    return value


def evaluate_with_states(action, game, n_steps=4, penalty=0.9):
    # print(f"{action.str}", file=sys.stderr, flush=True)
    delta_prod, delta_troops = np.zeros((n_steps + 1,)), np.zeros((n_steps + 1,))
    penalty_vec = np.array([penalty ** i for i in range(n_steps)])
    game_proj = game.clone()
    delta_prod[0] = game_proj.player_production[1] - game_proj.player_production[-1]
    delta_prod[0] = game_proj.player_troops[1] - game_proj.player_troops[-1]
    game_proj.next_state(action)
    delta_prod[1] = game_proj.player_production[1] - game_proj.player_production[-1]
    delta_prod[1] = game_proj.player_troops[1] - game_proj.player_troops[-1]
    for i in range(2, n_steps + 1):
        game_proj.next_state(Wait())
        delta_prod[i] = game_proj.player_production[1] - game_proj.player_production[-1]
        delta_troops[i] = game_proj.player_troops[1] - game_proj.player_troops[-1]
    score = (delta_prod[1:] - delta_prod[:-1]) * 10 + (delta_troops[1:] - delta_troops[:-1])

    # print(f"{game.distance_matrix[action.source, action.destination]}", file=sys.stderr, flush=True)
    # print(f"{delta_prod} {delta_prod[1:] - delta_prod[:-1]}", file=sys.stderr, flush=True)
    # print(f"{delta_troops}", file=sys.stderr, flush=True)
    # print(f"{score}", file=sys.stderr, flush=True)
    score = sum(score * penalty_vec)

    # print(f"Action apply takes      {(end_eval - init_eval) * 1e3}ms", file=sys.stderr, flush=True)
    # print(f"Game proj takes      {proj_time * 1e3}ms", file=sys.stderr, flush=True)
    # print(f"Metric compute takes {metric_time * 1e3}ms", file=sys.stderr, flush=True)
    # print(f"Actio  evaluation takes {(time() - init_eval) * 1e3}ms", file=sys.stderr, flush=True)
    return score


def heuristic_evaluate(action, game):
    if isinstance(action, Move):
        distance = game.distance_matrix[action.source, action.destination]
        target_player, target_prod = game.factories[action.destination, PLAYER], game.factories[
            action.destination, PROD]
        target_troops, target_incoming = game.factories[action.destination, TROOPS], game.factories[
            action.destination, PROD]
        prize = target_prod * (target_player != 1)
        troops_matrix = game.troops.copy()
        enemy_troops = troops_matrix[action.destination, :, PLAYER_MAP[-1]]
        ally_troops = troops_matrix[action.destination, :, PLAYER_MAP[1]]
        incidence = np.triu(np.ones((game.max_distance + 1, game.max_distance + 1), dtype=int))
        incidence_prod = np.triu(-np.ones((game.max_distance + 1, game.max_distance + 1), dtype=int), k=1)
        cumul_ally, cumul_enemy = ally_troops.dot(incidence), enemy_troops.dot(incidence)
        player = np.sign(cumul_enemy - cumul_ally + target_troops * (target_player != 1))
        prod_cost = target_prod * (target_player == -1) * player.dot(incidence_prod)
        final = target_troops * (target_player == -1) + cumul_enemy - (cumul_ally + prod_cost) - target_troops * (
                    target_player == 1)
    return final


class Player:

    def __init__(self, player_id, move_action_eval, prod_action_eval, bomb_action_eval):
        self.player_id = player_id
        self.move_action_eval = move_action_eval
        self.prod_action_eval = prod_action_eval
        self.bomb_action_eval = bomb_action_eval

    def get_actions(self, game):
        init_get_actions = time()

        sources = game.factories[game.factories[:, PLAYER] == 1, ID]
        move_list = [Move(source=source_id, destination=dest_id, cyborg_count=1) for source_id in sources
                     for dest_id in game.factories[:, ID] if source_id != dest_id]
        inc_list = [IncreaseProd(factory=source_id) for source_id in sources]
        # wait_list.append(Wait())
        action_list = move_list + inc_list
        print(f"Got available actions in {(time() - init_get_actions) * 1e3}ms", file=sys.stderr, flush=True)
        return action_list

    def get_plan(self, game: Game, time_limit=45):
        init_plan = time()
        plan = list()
        # print(f"N actions {len(action_list)}", file=sys.stderr, flush=True)
        # print(f"N valid actions {len([a for a in action_list if a.is_valid(game)])}", file=sys.stderr, flush=True)
        # if len(action_list) == 0:
        #    return plan.append(Wait().str)
        t = (time() - init_plan) * 1e3
        opt_time = 0
        n = 0
        game_copy = game.clone()
        while t < time_limit:
            print(f"Cycles {n}", file=sys.stderr, flush=True)
            opt_start = time()
            action_list = [a for a in self.get_actions(game_copy) if a.is_valid(game_copy)]
            action_sample = np.random.choice(action_list, size=(min(20, len(action_list)),), replace=False)
            action_sample = list(action_sample)
            action_sample.append(Wait())
            # print(f"{action_sample}", file=sys.stderr, flush=True)
            optimized_values = list(map(lambda x: self.move_action_eval.optimize(x, game_copy), action_sample))
            a_list = {a.str: v for a, v in zip(action_sample, optimized_values)}
            print(f"Action values : {a_list}", file=sys.stderr, flush=True)
            opt_time = opt_time + time() - opt_start
            print(f"Opt time : {(time() - opt_start) * 1e3}", file=sys.stderr, flush=True)
            action = action_sample[np.argmax(optimized_values)]
            # print(f"Best : {np.argmax(optimized_values)}", file=sys.stderr, flush=True)
            # print(f"Action: {action.to_str()}", file=sys.stderr, flush=True)
            if action.is_valid(game):
                plan.append(action.str)
                action.apply(game_copy)
            if isinstance(action, Wait):
                break
            t = (time() - init_plan) * 1e3
            print(f"Time elapsed {t}", file=sys.stderr, flush=True)
            n = n + 1
        print(f"Action optimization takes {opt_time * 1e3}ms", file=sys.stderr, flush=True)
        return plan

    def execute_plan(self, plan):
        print(f"{plan}", file=sys.stderr, flush=True)
        print(";".join(plan))


game = Game()
game.initialize(input)
move_action_evaluator = ActionEvaluator(criterion=evaluate_with_states, optimizer=do_not_optimize)
prod_action_evaluator = ActionEvaluator(criterion=lambda x: -10000, optimizer=lambda x: -10000)
bomb_action_evaluator = ActionEvaluator(criterion=lambda x: -10000, optimizer=lambda x: -10000)
agent = Player(player_id=1, move_action_eval=move_action_evaluator, bomb_action_eval=bomb_action_evaluator,
               prod_action_eval=prod_action_evaluator)
# game loop
print(f"{game.distance_matrix}", file=sys.stderr, flush=True)
while True:
    start = time()
    #print(f"{type(input)} {input}", file=sys.stderr, flush=True)
    game.current_status(input)
    print(f"Got game status in {(time() - start) * 1e3}ms", file=sys.stderr, flush=True)
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr, flush=True)
    # _delta_move(game, player_priority={0:10, 1:2, -1:20})
    # Any valid action, such as "WAIT" or "MOVE source destination cyborgs"
    start_plan = time()
    action_plan = agent.get_plan(game, time_limit=45)
    print(f"Action plan in {(time() - start_plan) * 1e3}ms", file=sys.stderr, flush=True)
    # print(f"{action_plan}", file=sys.stderr, flush=True)
    if len(action_plan) == 0:
        print("WAIT")
    else:
        agent.execute_plan(action_plan)
