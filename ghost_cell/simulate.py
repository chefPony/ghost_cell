from time import time
from subprocess import Popen, PIPE
import argparse
import multiprocessing as mp
import psutil
import sys

import pandas as pd
import numpy as np

from scenario_generator import ScenarioGenerator
from constants import MIN_FACTORY_COUNT, MAX_FACTORY_COUNT

PARALLEL = False
NUM_CPU = psutil.cpu_count(logical=False)

parser = argparse.ArgumentParser(description='Simulate ghost in the cell game')
parser.add_argument('--n_sim', metavar='N', type=int, help='number of simulations', required=True)
parser.add_argument('--player_1', type=str, help='bot to use as player 1', required=True)
parser.add_argument('--player_2', type=str, help='bot to use as player 2', required=True)

class Simulator:

    def __init__(self, player_1, player_2):
        self.player_1 = player_1
        self.player_2 = player_2
        self.count = 0

    # TODO: better be static?
    def simulate(self, factory_count):
        if self.player_1.endswith(".py"):
            p0 = Popen(["python", self.player_1], stdout=PIPE, stdin=PIPE, stderr=sys.stderr, shell=False, text=True,
                       bufsize=-1)
        else:
            p0 = Popen(["./"+self.player_1], stdout=PIPE, stdin=PIPE, stderr=sys.stderr, shell=False, text=True, bufsize=-1)
        if self.player_2.endswith(".py"):
            p1 = Popen(['python', self.player_2], stdout=PIPE, stdin=PIPE, stderr=sys.stderr, shell=False, text=True, bufsize=-1)
        else:
            p1 = Popen(["./" + self.player_2], stdout=PIPE, stdin=PIPE, stderr=sys.stderr, shell=False, text=True, bufsize=-1)

        self.scenario = ScenarioGenerator.generate(factory_count=factory_count)
        if int(time()*1e4) % 2 == 0:
            self.scenario.players = {1: p0, -1: p1}
            bot_player = {1: self.player_1, -1: self.player_2}
        else:
            self.scenario.players = {-1: p0, 1: p1}
            bot_player = {-1: self.player_1, 1: self.player_2}
        start_game = time()
        self.scenario.match()
        print(f"{self.count} Winner is {bot_player.get(self.scenario.winner, 'draw')} by {self.scenario.win_condition} in "
              f"{np.around(time()-start_game, 2)}s", file=sys.stderr)
        result = {"win": bot_player.get(self.scenario.winner, 'draw'), "win_condition": self.scenario.win_condition,
                  "turn": self.scenario.turn, "factory_count": factory_count, "as_player": self.scenario.winner,
                  "final_score": " ".join([f"{player}|{score} " for player, score in self.scenario.score.items()]),
                  "playing_time": time() - start_game}
        self.count += 1

        p0.kill(), p1.kill()
        p0.wait(), p1.wait()

        return result

def main():
    args = parser.parse_args()
    factory_counts = np.random.randint(MIN_FACTORY_COUNT, MAX_FACTORY_COUNT, args.n_sim)
    simulator = Simulator(player_1=args.player_1, player_2=args.player_2)

    start = time()
    pool = mp.Pool(NUM_CPU)

    records = list()
    if PARALLEL:
        print(f"Parallelize simulation on {NUM_CPU} cores")
        # TODO: better to instantiate the class inside the map to avoid processes step over each other
        records = pool.map(simulator.simulate, list(factory_counts))
    else:
        for n_factory in factory_counts:
            r = simulator.simulate(factory_count=n_factory)
            #if r["win_condition"] == "invalid action":
            #    print(simulator.scenario.input[-simulator.scenario.winner], file=sys.stderr)
            #    break
            records.append(r)

    stat = pd.DataFrame.from_records(records)
    stat.to_csv(f"simulations/simulation_{args.player_1.split('.')[0]}_vs_{args.player_2.split('.')[0]}.csv",
                index=False)

    n_games = stat.shape[0]
    player_1_wins = sum(stat.win == args.player_1)
    player_2_wins = sum(stat.win == args.player_2)
    p_1, p_2 = player_1_wins/n_games, player_2_wins/n_games
    b = np.round(1.96 * np.sqrt(p_1 * p_2 / n_games), 3)
    print(f"Simulation over in {time() - start}")
    print(f"Games played {n_games}")
    print(f"{args.player_1} total wons: {player_1_wins}")
    print(f"{args.player_2} total wons: {player_2_wins}")
    print(f"{args.player_1} win probability 95% confidence {p_1 - b} {p_1} {p_1 + b}")
    print(f"{args.player_2} win probability 95% confidence {p_2 - b} {p_2} {p_2 + b}")


if __name__ == "__main__":
    main()