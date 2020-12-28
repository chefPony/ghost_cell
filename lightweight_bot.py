import numpy as np
import sys
import math
from copy import copy
from collections import defaultdict
from time import time

ID, PLAYER, TROOPS, PROD, FROM, TO, SIZE, DIST, BLOCKED = 0, 1, 2, 3, 2, 3, 4, 5, 5
PLAYER_MAP = {-1: 1, 1: 0}

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

    def __init__(self, player_id: int, distance_threshold: int, distance_discount: float):
        self.player_id = player_id
        self.distance_threshold = distance_threshold
        self.distance_discount = distance_discount
        self.state = None

    def get_state(self, game_state: GameState):
        self.state = game_state
        self.my_factories = self.state.factories[:, PLAYER] == self.player_id

    def _compute_required_troops_ally(self, factory_id: int):

        troop_discount = np.array([self.distance_discount ** i for i in range(self.distance_threshold + 1)])
        incoming_enemy = self.state.troops[factory_id, :self.distance_threshold + 1, PLAYER_MAP[-self.player_id]]
        incoming_ally = self.state.troops[factory_id, :self.distance_threshold + 1, PLAYER_MAP[self.player_id]]

        enemy_factories = self.state.factories[:, PLAYER] == -self.player_id
        factory_discount = [self.distance_discount ** (d - 1) for d in self.state.distance_matrix[factory_id, enemy_factories]]
        nearby_enemy = self.state.factories[enemy_factories, TROOPS]

        required_defense = (incoming_enemy - incoming_ally) * troop_discount + sum(nearby_enemy * factory_discount)
        return required_defense

    def _compute_required_troops_enemy(self, factory_id: int):
        troops = self.state.factories[factory_id, TROOPS]

        troop_discount = np.array([self.distance_discount ** i for i in range(self.distance_threshold + 1)])
        incoming_enemy = self.state.troops[factory_id, :self.distance_threshold + 1, PLAYER_MAP[-self.player_id]]
        incoming_ally = self.state.troops[factory_id, :self.distance_threshold + 1, PLAYER_MAP[self.player_id]]

        enemy_factories = self.state.factories[:, PLAYER] == -self.player_id
        factory_discount = [self.distance_discount ** (d - 1) for d in
                            self.state.distance_matrix[factory_id, enemy_factories]]
        nearby_enemy = self.state.factories[enemy_factories, TROOPS]

        required_to_take = troops + (incoming_enemy - incoming_ally) * troop_discount + sum(nearby_enemy * factory_discount)
        return required_to_take

    def _compute_required_troops_neutral(self, factory_id: int):
        troops = self.state.factories[factory_id, TROOPS]

        troop_discount = np.array([self.distance_discount ** i for i in range(self.distance_threshold + 1)])
        incoming_enemy = self.state.troops[factory_id, :self.distance_threshold + 1, PLAYER_MAP[-self.player_id]]
        incoming_ally = self.state.troops[factory_id, :self.distance_threshold + 1, PLAYER_MAP[self.player_id]]

        enemy_factories = self.state.factories[:, PLAYER] == -self.player_id
        factory_discount = [self.distance_discount ** (d - 1) for d in
                            self.state.distance_matrix[factory_id, enemy_factories]]
        nearby_enemy = self.state.factories[enemy_factories, TROOPS]

        required_to_take = troops + (incoming_enemy - incoming_ally) * troop_discount + sum(
            nearby_enemy * factory_discount)
        return required_to_take

    def _required_troops(self, factory_id):
        player = self.state.factories[factory_id, PLAYER]

        if player == self.player_id:
            required_to_take = self._compute_required_troops_ally(factory_id)
        elif player == -self.player_id:
            required_to_take = self._compute_required_troops_enemy(factory_id)
        else:
            required_to_take = self._compute_required_troops_neutral(factory_id)

        return required_to_take

    def _move_value_matrix(self):
        self.required_troops = np.array([self._required_troops(factory_id) for factory_id in self.state.factories[:, ID]])
        self.available_troops = np.where(self.my_factories, max(self.state.factories[:, TROOPS] - self.required_troops, 0), 0)
        self.total_capacity = sum(self.available_troops)
        self.required_troops[self.my_factories] = max(self.required_troops[self.my_factories] -
                                                      self.state.factories[self.my_factories, TROOPS], 0)
        self.troops_ratio_matr = np.tensordot(self.available_troops, self.required_troops)
        self.gain_matr = np.tensordot(self.state.factories[:, PROD], np.ones((self.state.factory_count,))).T
        self.distance_discount_matr = np.power(np.array(self.distance_discount), self.state.distance_matrix-1)
        self.move_value_matrix = self.gain_matr * self.distance_discount_matr * self.troops_ratio_matr

    def execute_plan(self, plan):
        print(f"{plan}", file=sys.stderr, flush=True)
        print(";".join(plan))


game = GameState()
game.initialize(input)
agent = Player(player_id=1, distance_threshold=5, distance_discount=0.9)
# game loop
while True:
    start = time()
    game.current_status(input)
    agent.get_state(game)
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr, flush=True)
    # Any valid action, such as "WAIT" or "MOVE source destination cyborgs"
    start_plan = time()
    action_plan = agent.get_plan(game, time_limit=35)
    if len(action_plan) == 0:
        print("WAIT")
    else:
        agent.execute_plan(action_plan)
    game.troops[:, :, :] = 0

