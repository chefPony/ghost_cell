import numpy as np
from time import time
from entities import Factory, MovingTroop, Bomb
from collections import defaultdict
from exception import InvalidAction


class Battle:

    def __init__(self, factory: Factory):
        self.factory = factory
        self.incoming = 0

    def add_to_battle(self, troop: MovingTroop):
        if (troop.distance == 0) and (troop.destination == self.factory):
            self.incoming += troop.troops * np.sign(troop.player)
            del troop
        else:
            pass

    def resolve(self):
        incoming_player = np.sign(self.incoming)
        if self.factory.player != incoming_player:
            self.factory.troops -= abs(self.incoming)
            self.factory.player = incoming_player
        else:
            self.factory.troops += abs(self.incoming)
        self.incoming = 0


class Scenario:

    def __init__(self, factories, links, player_1, player_2):
        self.factory_count = len(factories)
        self.link_count = len(links)
        self.links = " ".join(links)
        self.distance_matrix = np.zeros((self.factory_count, self.factory_count), dtype=int)
        for factory_1, factory_2, distance in links:
            self.distance_matrix[factory_1, factory_2], self.distance_matrix[factory_2, factory_1] = distance, distance
        self.factories = [Factory(*factory) for factory in factories]
        self.troops = list()
        self.bombs = list()
        self.battles = [Battle(factory) for factory in self.factories]
        self.players = [player_1, player_2]
        self.bomb_counter = {1: 2, -1: 2}
        self.troop_id = 0
        self.bomb_id = 0
        self.winner = 0
        self.turn = 1

    @property
    def score(self):
        score = defaultdict(int)
        for factory in self.factories:
            score[factory.player] += factory.troops
        for troop in self.troops:
            score[troop.player] += troop.troops
        return score

    @property
    def entity_count(self):
        return len(self.factories) + len(self.troops) + len(self.bombs)

    def check_win_condition(self):
        score = self.score
        if score[1] == 0:
           self.winner = -1
        elif score[-1] == 0:
            self.winner = 1
        elif self.turn >= 200:
            self.winner = 1 * (score[1] > score[-1]) - 1 * (score[1] < score[-1])
        else:
            pass

    def apply_action(self, action_str, player):
        action_data = action_str.split(" ")
        if action_data[0] == "WAIT":
            apply_wait(self)
        elif action_data[0] == "MSG":
            apply_message(self)
        elif action_data[0] == "MOVE":
            apply_move(self, source=int(action_data[1]), destination=int(action_data[2]), n_cyborgs=int(action_data[3]),
                       player=player)
        elif action_data[0] == "BOMB":
            apply_bomb(self, source=int(action_data[1]), destination=int(action_data[2]), player=player)
        elif action_data[0] == "INC":
            apply_inc(self, factory=int(action_data[1]), player=player)
        else:
            raise InvalidAction(f"Unrecognized action string: {action_str}")

    def play(self):

        # Move troops and bombs
        for troop in self.troops:
            troop.move()
            if troop.distance == 0:
                self.battles[troop.destination.entity_id].add_to_battle(troop)

        for bomb in self.bombs:
            bomb.move()

        for player in self.players:
            plan = player.get_plan()
            for action_str in plan.split(";"):
                try:
                    self.apply_action(action_str, player)
                except InvalidAction:
                    self.winner = -1 * player.player_id
                    break

        for factory in self.factories:
            factory.produce()

        for battle in self.battles:
            battle.resolve()

        for bomb in self.bombs:
            bomb.explode()

        self.check_win_condition()

    @property
    def input(self):
        input_list = [str(self.factory_count), str(self.link_count)] + self.links + [str(self.entity_count)] + \
                     [e.str for e in self.factories + self.troops + self.bombs]

        class Input:
            def __init__(self):
                self.ind = 0

            def __call__(self):
                out = input_list[self.ind]
                self.ind += 1
                return out

        return Input()


def apply_message(scenario):
    pass


def apply_wait(scenario):
    pass


def apply_move(scenario, source, destination, n_cyborgs, player):
    if source == destination:
        raise InvalidAction(f"Player {player.player_id}: move actions source must be different from destination")
    elif scenario.factories[source].player != player.player_id:
        raise InvalidAction(f"Player {player.player_id}: does not own factory {source}")
    else:
        n_cyborgs = min(int(n_cyborgs), scenario.factories[int(source)].troops)
        scenario.factories[int(source)].troops -= n_cyborgs
        scenario.troops.append(MovingTroop(entity_id=scenario.troop_id, source=scenario.factories[int(source)],
                                           destination=scenario.factories[int(destination)], troops=n_cyborgs,
                                           distance=scenario.distance_matrix[int(source), int(destination)],
                                           player=player))
        scenario.troop_id += 1


def apply_bomb(scenario, source, destination, player):
    if source == destination:
        raise InvalidAction(f"Player {player.player_id}: bomb source must be different from destination")
    elif scenario.factories[source].player != player.player_id:
        raise InvalidAction(f"Player {player.player_id}: does not own factory {source}")
    elif scenario.bomb_counter[player.player_id] == 0:
        raise InvalidAction(f"Player {player.player_id}: does not have bombs")
    else:
        scenario.bombs.append(Bomb(entity_id=scenario.bomb_id, source=scenario.factories[int(source)],
                                   destination=scenario.factories[int(destination)], player=player,
                                   distance=scenario.distance_matrix[int(source), int(destination)]))
        scenario.bomb_counter[player.player_id] -= 1
        scenario.bomb_id += 1


def apply_inc(scenario, factory, player):
    if scenario.factories[factory].player != player.player_id:
        raise InvalidAction(f"Player {player.player_id}: does not own factory {factory}")
    else:
        scenario.factories[factory].increment_prod()