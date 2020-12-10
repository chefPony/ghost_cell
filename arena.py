import sys
import numpy as np
from time import time
from entities import Factory, MovingTroop, Bomb
from collections import defaultdict
from exception import InvalidAction
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired
from threading  import Thread


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

    def __init__(self, factories, links, bot_1, bot_2):
        self.factory_count = len(factories)
        self.link_count = len(links)
        self.links = links
        self.distance_matrix = np.zeros((self.factory_count, self.factory_count), dtype=int)
        for factory_1, factory_2, distance in links:
            self.distance_matrix[factory_1, factory_2], self.distance_matrix[factory_2, factory_1] = distance, distance
        self.factories = [Factory(*factory) for factory in factories]
        self.troops = list()
        self.bombs = list()
        self.battles = [Battle(factory) for factory in self.factories]
        self.players = {1: bot_1, -1:bot_2}
        self.bomb_counter = {1: 2, -1: 2}
        self.troop_id = 0
        self.bomb_id = 0
        self.winner = 0
        self.turn = 1

    @property
    def timeout(self):
        if self.turn == 1:
            return 100
        else:
            return 50

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

        input_str = self.input
        for player, bot in self.players.items():
            try:
                print(f"{self.turn} {player}")
                bot.stdin.write(input_str[player]+"\n")
                stdout_data = bot.stdout.readline().replace("\n", "")
                bot.stdin.flush()
                #bot.stdout.flush()
                #bot.stdin.flush()
                #bot.stdout.flush()
            except TimeoutExpired:
                bot.kill()
                bot.communicate()
                self.winner = -1 * player
                raise TimeoutExpired
            print(f"{player}| {stdout_data}")
            for action_str in stdout_data.split(";"):
                try:
                    self.apply_action(action_str, player)
                except InvalidAction:
                    bot.kill()
                    bot.communicate()
                    self.winner = -1 * player
                    raise InvalidAction

        for factory in self.factories:
            factory.produce()

        for battle in self.battles:
            battle.resolve()

        for bomb in self.bombs:
            bomb.explode()

        self.check_win_condition()
        self.turn += 1

    @property
    def input(self):
        input_str = dict()
        if self.turn == 1:
            input_common = [str(self.factory_count), str(self.link_count)] +\
                           [f"{s} {d} {l}" for s,d,l in self.links] + [str(self.entity_count)]
        else:
            input_common = [str(self.entity_count)]

        for player in self.players.keys():
            input_factory = [" ".join(map(str, [e.entity_id, e.entity_type, e.player * player, e.troops, e.prod,
                                                e.blocked, "0"])) for e in self.factories]
            input_troops = [" ".join(map(str, [e.entity_id, e.entity_type, e.player * player, e.source.entity_id,
                                               e.destination.entity_id, e.troops, e.distance])) for e in self.troops]
            input_bombs = [" ".join(map(str, [e.entity_id, e.entity_type, e.player * player, e.source.entity_id,
                                              e.destination.entity_id, e.distance, "0"])) for e in self.bombs]
            input_str[player] = "\n".join(input_common + input_factory + input_troops + input_bombs)
        return input_str

    def match(self):
        while self.winner == 0:
            self.play()

        return self.winner

def apply_message(scenario):
    pass


def apply_wait(scenario):
    pass


def apply_move(scenario, source, destination, n_cyborgs, player):
    if source == destination:
        raise InvalidAction(f"Player {player}: move actions source must be different from destination")
    elif scenario.factories[source].player != player:
        raise InvalidAction(f"Player {player}: does not own factory {source}")
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
        raise InvalidAction(f"Player {player}: bomb source must be different from destination")
    elif scenario.factories[source].player != player:
        raise InvalidAction(f"Player {player}: does not own factory {source}")
    elif scenario.bomb_counter[player] == 0:
        raise InvalidAction(f"Player {player}: does not have bombs")
    else:
        scenario.bombs.append(Bomb(entity_id=scenario.bomb_id, source=scenario.factories[int(source)],
                                   destination=scenario.factories[int(destination)], player=player,
                                   distance=scenario.distance_matrix[int(source), int(destination)]))
        scenario.bomb_counter[player.player_id] -= 1
        scenario.bomb_id += 1


def apply_inc(scenario, factory, player):
    if scenario.factories[factory].player != player:
        raise InvalidAction(f"Player {player}: does not own factory {factory}")
    else:
        scenario.factories[factory].increment_prod()


if __name__ == "__main__":

    p0 = Popen(['python', 'main.py'], stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=False, text=True, bufsize=1)
    p1 = Popen(['python', 'main2.py'], stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=False, text=True, bufsize=1)
    scenario = Scenario(factories=[(0, 1, 10, 0, 0), (1, -1, 9, 0, 0)],
                        links=[(0, 1, 5)], bot_1=p0, bot_2=p1)

    scenario.match()

    p0.terminate(), p1.terminate()

    print(f"Game endend at turn{scenario.turn}")
    print(f"Final score {scenario.score}")
    print(f"Winner is : {scenario.winner}")
