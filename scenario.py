import sys
import numpy as np
from time import time
from entities import Factory, MovingTroop, Bomb
from collections import defaultdict
from exception import InvalidAction
from subprocess import Popen, PIPE
import threading
from queue import Queue, Empty
from constants import TIMEOUT_MOVE
import select


class Battle:

    def __init__(self, factory: Factory):
        self.factory = factory
        self.incoming = 0
        self.id_incoming = list()

    def add_to_battle(self, troop):
        if (troop.distance == 0) and (troop.destination == self.factory):
            self.incoming += troop.troops * np.sign(troop.player)
            self.id_incoming.append(troop.entity_id)
        else:
            pass

    def resolve(self):
        incoming_player = np.sign(self.incoming)
        if self.factory.player != incoming_player:
            self.factory.player = incoming_player if self.factory.troops < abs(self.incoming) else self.factory.player
            self.factory.troops = abs(self.factory.troops - abs(self.incoming))
        else:
            self.factory.troops += abs(self.incoming)
        self.incoming = 0

    def clean_scenario(self, scenario):
        for i in self.id_incoming:
            scenario.troops.pop(i)
        self.id_incoming = list()


class Scenario:

    def __init__(self, factories, links):
        self.factory_count = len(factories)
        self.link_count = len(links)
        self.links = links
        self.distance_matrix = np.zeros((self.factory_count, self.factory_count), dtype=int)
        for factory_1, factory_2, distance in links:
            self.distance_matrix[factory_1, factory_2], self.distance_matrix[factory_2, factory_1] = distance, distance
        self.factories = factories
        self.troops = dict()
        self.bombs = dict()
        self.battles = [Battle(factory) for factory in self.factories]
        self.players = dict()
        self.bomb_counter = {1: 2, -1: 2}
        self.troop_id = 0
        self.bomb_id = 0
        self.winner = -2
        self.win_condition = None
        self.turn = 1

    @property
    def players(self):
        return self._players

    @players.setter
    def players(self, player_dict):
        self._players = player_dict

    @property
    def timeout(self):
        if self.turn == 1:
            return 1
        else:
            return TIMEOUT_MOVE

    @property
    def score(self):
        score = defaultdict(int)
        for factory in self.factories:
            score[factory.player] += factory.troops
        for _,troop in self.troops.items():
            score[troop.player] += troop.troops
        return score

    @property
    def entity_count(self):
        return len(self.factories) + len(self.troops) + len(self.bombs)

    def check_win_condition(self):
        score = self.score
        if (score[1] == 0) and (score[-1] > 0):
            self.winner = -1
            self.win_condition = "conquest"
        elif (score[1] > 0) and (score[-1] == 0):
            self.winner = 1
            self.win_condition = "conquest"
        elif self.turn >= 200:
            self.winner = 1 * (score[1] > score[-1]) - 1 * (score[1] < score[-1])
            self.win_condition = "score"
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
        for _, troop in self.troops.items():
            troop.move()

        about_to_explode = list()
        for _, bomb in self.bombs.items():
            bomb.move()
            if bomb.distance == 0:
                about_to_explode.append(bomb.entity_id)

        input_str = self.input
        #print(f"Turn {self.turn}", file=sys.stderr)
        #print(f"{len(self.troops)}")
        for player, bot in self.players.items():
            bot.stdin.write(input_str[player]+"\n")
            bot.stdin.flush()
            try:
                start = time()
                action_plan = read_from_stdout(bot, TIMEOUT_MOVE)
            except TimeoutError:
                print(f"Player {player} did not answer in time |{(time() - start) * 1e3}ms", file=sys.stderr)
                self.winner = -1 * player
                self.win_condition = "timeout"
                return
            else:
                for action_str in action_plan.replace("\n", "").split(";"):
                    try:
                        self.apply_action(action_str, player)
                    except InvalidAction:
                        print(f"Player {player} invalid action input {action_str}")
                        self.winner = -1 * player
                        self.win_condition = "invalid action"
                        return

        for factory in self.factories:
            factory.produce()

        for _, troop in self.troops.items():
            self.battles[troop.destination.entity_id].add_to_battle(troop)

        for battle in self.battles:
            battle.resolve()
            battle.clean_scenario(self)

        for bomb_id in about_to_explode:
            bomb = self.bombs.pop(bomb_id)
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
                                               e.destination.entity_id, e.troops, e.distance]))
                            for _, e in self.troops.items()]
            input_bombs = [" ".join(map(str, [e.entity_id, e.entity_type, e.player * player, e.source.entity_id,
                                              e.destination.entity_id, e.distance, "0"])) for _, e in self.bombs.items()]
            input_str[player] = "\n".join(input_common + input_factory + input_troops + input_bombs)
        return input_str

    def match(self):
        while self.winner == -2:
            self.play()
        #print(f"Winner is {self.winner} by {self.win_condition}")
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
        scenario.troops[scenario.troop_id] = MovingTroop(
            entity_id=scenario.troop_id, source=scenario.factories[int(source)],
            destination=scenario.factories[int(destination)], troops=n_cyborgs,
            distance=scenario.distance_matrix[int(source), int(destination)], player=player)
        scenario.troop_id += 1

def apply_bomb(scenario, source, destination, player):
    if source == destination:
        raise InvalidAction(f"Player {player}: bomb source must be different from destination")
    elif scenario.factories[source].player != player:
        raise InvalidAction(f"Player {player}: does not own factory {source}")
    elif scenario.bomb_counter[player] == 0:
        raise InvalidAction(f"Player {player}: does not have bombs")
    else:
        scenario.bombs[scenario.bomb_id] = Bomb(entity_id=scenario.bomb_id, source=scenario.factories[int(source)],
                                                destination=scenario.factories[int(destination)], player=player,
                                                distance=scenario.distance_matrix[int(source), int(destination)])
        scenario.bomb_counter[player] -= 1
        scenario.bomb_id += 1


def apply_inc(scenario, factory, player):
    if scenario.factories[factory].player != player:
        raise InvalidAction(f"Player {player}: does not own factory {factory}")
    else:
        scenario.factories[factory].increment_prod()


def read_from_stdout(process, timeout):
    plan = None
    while not plan:
        buff = select.select([process.stdout], [], [], timeout)[0]
        if not buff:
            raise TimeoutError
        plan = buff[0].readline()
    return plan



if __name__ == "__main__":

    p0 = Popen(['python', 'heuristic_bot.py'], stdout=PIPE, stdin=PIPE,  shell=False, text=True, bufsize=1)
    p1 = Popen(['python', 'wait_player.py'], stdout=PIPE, stdin=PIPE,  shell=False, text=True, bufsize=1)

    #p0_queue, p1_queue = Queue(), Queue()
    #p0_err, p1_err = Queue(), Queue()
    #thread0 = threading.Thread(target=enqueue_output, args=(p0.stdout, p0_queue))
    #thread1 = threading.Thread(target=enqueue_output, args=(p1.stdout, p1_queue))
    #thread0.daemon, thread1.daemon = True, True
    #thread0.start(), thread1.start()

    scenario = Scenario(factories=[Factory(0, 1, 30, 0), Factory(1, -1, 15, 0)], links=[(0, 1, 3)])
    scenario.players = {1: p0, -1: p1}
    scenario.match()

    p0.terminate(), p1.terminate()

    print(f"Game endend at turn {scenario.turn}")
    print(f"Final score {scenario.score}")
    print(f"Winner is : {scenario.winner}")
    print(f"Win by : {scenario.win_condition}")
