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
        self.troops[:, 0, :] = 0

    def update_stats(self):
        for player in [-1, 1]:
            f_player = self.factories[:, PLAYER] == player
            self.player_production[player] = np.sum(self.factories[f_player, PROD])
            self.player_troops[player] = np.sum(self.factories[f_player, TROOPS]) + \
                                         np.sum(self.troops[:, :, PLAYER_MAP[player]])

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


def evaluate_inc(source, game):
    discount = np.array([0.9 ** i for i in range(5)])
    source_player, source_prod = game.factories[source, PLAYER], game.factories[source, PROD]
    source_troops, source_incoming = game.factories[source, TROOPS], game.troops[source, :, :]
    enemy_source_incoming = source_incoming[:5, PLAYER_MAP[-1]]
    ally_source_incoming = source_incoming[:5, PLAYER_MAP[1]]

    available_troops = max(sum(source_prod * discount) + source_troops + sum(ally_source_incoming)
                           - sum(enemy_source_incoming), 0)
    available_troops = min(available_troops, source_troops)

    roi = (source_prod + 1) / 10. * (available_troops > 10.)
    return roi

def evaluate_move(source, destination, game):

    discount = np.array([0.9 ** i for i in range(5)])
    distance = game.distance_matrix[source, destination]

    source_player, source_prod = game.factories[source, PLAYER], game.factories[source, PROD]
    source_troops, source_incoming = game.factories[source, TROOPS], game.troops[source, :, :]
    enemy_source_incoming = source_incoming[:5, PLAYER_MAP[-1]]
    ally_source_incoming = source_incoming[:5, PLAYER_MAP[1]]

    target_player, target_prod = game.factories[destination, PLAYER], game.factories[destination, PROD]
    target_troops, target_incoming = game.factories[destination, TROOPS], game.troops[destination, :, :]
    enemy_target_incoming = target_incoming[:distance+1, PLAYER_MAP[-1]]
    ally_target_incoming = target_incoming[:distance+1, PLAYER_MAP[1]]

    available_troops = max(sum(source_prod * discount) + source_troops + sum(ally_source_incoming)
                           - sum(enemy_source_incoming), 0)
    available_troops = min(available_troops, source_troops)

    gain = target_prod + 0.1
    if target_player == 1:
        required_troops = max(sum(enemy_target_incoming) - sum(ally_target_incoming) - target_troops, 0)
        roi = gain/(required_troops + 1e-5) * (required_troops > 0) - distance * 1e-2
    elif target_player == 0:
        required_troops = max(target_troops + sum(enemy_target_incoming) - sum(ally_target_incoming) + 1
                              , 0)
        roi = gain/(required_troops + 1e-5) * (required_troops > 0) - distance * 5e-2
    elif target_player == -1:
        required_troops = max(target_troops + sum(enemy_target_incoming) + target_prod * distance
                              - sum(ally_target_incoming) + 1, 0)
        roi = gain/(required_troops + 1e-5) * (required_troops > 0) - distance * 5e-2
    return min(required_troops, available_troops), roi * (available_troops>required_troops)


class Player:

    def __init__(self, player_id):
        self.player_id = player_id

    def get_actions(self, game):
        init_get_actions = time()
        action_list = list()
        sources = game.factories[game.factories[:, PLAYER] == 1, ID]
        for source_id in sources:
            action_list.append((IncreaseProd(int(source_id)), evaluate_inc(int(source_id), game)))
            for dest_id in game.factories[:, ID]:
                if source_id != dest_id:
                    tr, roi = evaluate_move(int(source_id), int(dest_id), game)
                    if tr > 0:
                        action_list.append((Move(source_id, dest_id, tr), roi))
        # wait_list.append(Wait())
        action_list.append((Wait(), 0.00001))
        #print(f"Got available actions in {(time() - init_get_actions) * 1e3}ms", file=sys.stderr, flush=True)
        return action_list

    def get_plan(self, game: Game, time_limit=45):
        init_plan = time()
        plan = list()
        t = (time() - init_plan) * 1e3
        opt_time = 0
        n = 0
        while t < time_limit:
            opt_start = time()
            action_list = self.get_actions(game)
            action_list = [a for a in action_list if a[0].is_valid(game)]
            #print(f"{sorted([(a.str, _) for a,_ in action_list], key=lambda x: x[1], reverse=True)}", file=sys.stderr, flush=True)
            best_action, _ = max(action_list, key=lambda x : x[1])
            if best_action.is_valid(game):
                plan.append(best_action.str)
                best_action.apply(game)
            if isinstance(best_action, Wait):
                break
            t = (time() - init_plan) * 1e3
            #print(f"Time elapsed {t}", file=sys.stderr, flush=True)
            n = n + 1
        #print(f"Action optimization takes {opt_time * 1e3}ms", file=sys.stderr, flush=True)
        return plan

    def execute_plan(self, plan):
        #print(f"{plan}", file=sys.stderr, flush=True)
        print(";".join(plan))


game = Game()
game.initialize(input)
agent = Player(player_id=1)
# game loop
#print(f"{game.distance_matrix}", file=sys.stderr, flush=True)
while True:
    start = time()
    #print(f"{type(input)} {input}", file=sys.stderr, flush=True)
    game.current_status(input)
    #print(f"{game.troops[:, :, PLAYER_MAP[1]]}", file=sys.stderr, flush=True)
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr, flush=True)
    # _delta_move(game, player_priority={0:10, 1:2, -1:20})
    # Any valid action, such as "WAIT" or "MOVE source destination cyborgs"
    start_plan = time()
    action_plan = agent.get_plan(game, time_limit=35)
    #print(f"Action plan in {(time() - start_plan) * 1e3}ms", file=sys.stderr, flush=True)
    # print(f"{action_plan}", file=sys.stderr, flush=True)
    if len(action_plan) == 0:
        print("WAIT")
    else:
        agent.execute_plan(action_plan)
    game.troops[:, :, :] = 0
    #print(f"Turn took {(time() - start) * 1e3}ms", file=sys.stderr, flush=True)