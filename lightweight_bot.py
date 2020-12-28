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

class Player:

    def __init__(self, player_id: int, moving_troop_dist_th: int, moving_troop_discount: float,
                 stationing_troop_dist_th: int, stationing_troop_discount: float):
        self.player_id = player_id
        self.moving_troop_dist_th = moving_troop_dist_th
        self.moving_troop_discount = moving_troop_discount
        self.stationing_troop_dist_th = stationing_troop_dist_th
        self.stationing_troop_discount = stationing_troop_discount
        self.state = None

    def get_state(self, game_state: GameState):
        self.state = game_state
        self.my_factories = self.state.factories[:, PLAYER] == self.player_id
        self.moving_troop_dist_th = min(self.moving_troop_dist_th, self.state.max_distance)
        self.stationing_troop_dist_th = min(self.stationing_troop_dist_th, self.state.max_distance)

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


    def _compute_factories_value(self):
        prod = self.state.factories[:, PROD]
        return prod + 0.1

    def _required_troops(self, factory_id):
        player = self.state.factories[factory_id, PLAYER]
        troops = self.state.factories[factory_id, TROOPS]
        troop_cost, factory_cost = self._moving_troops_cost(factory_id), self._stationing_troops_cost(factory_id)
        if player == self.player_id:
            required_to_take = troop_cost + factory_cost
        elif player == -self.player_id:
            required_to_take = troop_cost + factory_cost + troops
        else:
            required_to_take = troop_cost + factory_cost + troops + 1

        return required_to_take

    def _move_value_matrix(self):
        self.required_troops = np.array([self._required_troops(factory_id)
                                         for factory_id in self.state.factories[:, ID]])
        self.available_troops = np.where(self.my_factories,
                                         np.max(self.state.factories[:, TROOPS] - self.required_troops, 0), 0)
        self.total_capacity = sum(self.available_troops)
        self.required_troops[self.my_factories] =\
            abs(self.required_troops[self.my_factories] - self.state.factories[self.my_factories, TROOPS]) * \
               (self.required_troops[self.my_factories] > self.state.factories[self.my_factories, TROOPS])

        self.troops_ratio_matr = np.dot(self.available_troops.reshape(-1, 1),
                                        1./(self.required_troops.reshape(1, -1) + 1e-6))
        self.troops_ratio_matr[self.my_factories, self.my_factories] *= self.required_troops[self.my_factories] > 0

        self.factory_value_matr = np.dot(self._compute_factories_value().reshape(-1, 1),
                                         np.ones((1, self.state.factory_count))).T
        self.distance_discount_matr = np.power(np.array(self.moving_troop_discount),
                                               np.maximum(self.state.distance_matrix-1, 0))
        self.move_value_matrix = self.factory_value_matr * self.distance_discount_matr * self.troops_ratio_matr

    def execute_plan(self, plan):
        print(f"{plan}", file=sys.stderr, flush=True)
        print(";".join(plan))


if __name__ == "__main__":
    game = GameState()
    game.initialize(input)
    agent = Player(player_id=1, moving_troop_dist_th=20, moving_troop_discount=0.9, stationing_troop_dist_th=3,
                   stationing_troop_discount=0.7)
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

