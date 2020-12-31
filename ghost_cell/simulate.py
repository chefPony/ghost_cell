import sys
import os
from time import time
from subprocess import Popen, PIPE
import argparse
import multiprocessing as mp
import psutil
from functools import partial
from datetime import datetime

import pandas as pd
import numpy as np

from ghost_cell.scenario_generator import ScenarioGenerator
from ghost_cell.constants import MIN_FACTORY_COUNT, MAX_FACTORY_COUNT

BOT_PATH = os.path.abspath("ghost_cell/bots")
RESULT_PATH = os.path.abspath("simulations")
NUM_CPU = psutil.cpu_count(logical=False)

parser = argparse.ArgumentParser(description='Simulate ghost in the cell game')
parser.add_argument('--n_sim', metavar='N', type=int, help='number of simulations', required=True)
parser.add_argument('--player_1', type=str, help='bot to use as player 1', required=True)
parser.add_argument('--player_2', type=str, help='bot to use as player 2', required=True)
parser.add_argument('--parallel', type=bool, help='if simulation should run in parallel on cpus', required=True,
                    default=False)

class Simulator:

    def __init__(self):
        pass

    @staticmethod
    def simulate(factory_count, player_1, player_2):

        if player_1.endswith(".py"):
            p0 = Popen(["python", f"{BOT_PATH}/{player_1}"], stdout=PIPE, stdin=PIPE, stderr=sys.stderr, shell=False, text=True,
                       bufsize=-1)
        else:
            p0 = Popen([f"cd {BOT_PATH}/./{player_1}"], stdout=PIPE, stdin=PIPE, stderr=sys.stderr, shell=False, text=True, bufsize=-1)
        if player_2.endswith(".py"):
            p1 = Popen(['python', f"{BOT_PATH}/{player_2}"], stdout=PIPE, stdin=PIPE, stderr=sys.stderr, shell=False, text=True, bufsize=-1)
        else:
            p1 = Popen([f"{BOT_PATH}/./{player_2}"], stdout=PIPE, stdin=PIPE, stderr=sys.stderr, shell=False, text=True, bufsize=-1)

        scenario = ScenarioGenerator.generate(factory_count=factory_count)
        if int(time()*1e4) % 2 == 0:
            scenario.players = {1: p0, -1: p1}
            bot_player = {1: player_1, -1: player_2}
        else:
            scenario.players = {-1: p0, 1: p1}
            bot_player = {-1: player_1, 1: player_2}
        start_game = time()
        scenario.match()
        print(f"Winner is {bot_player.get(scenario.winner, 'draw')} by {scenario.win_condition} in "
              f"{np.around(time()-start_game, 2)}s", file=sys.stderr)
        result = {"win": bot_player.get(scenario.winner, 'draw'), "win_condition": scenario.win_condition,
                  "turn": scenario.turn, "factory_count": factory_count, "as_player": scenario.winner,
                  "final_score": " ".join([f"{player}|{score} " for player, score in scenario.score.items()]),
                  "playing_time": time() - start_game}
        #self.count += 1

        p0.kill(), p1.kill()
        p0.wait(), p1.wait()

        return result

def main():
    args = parser.parse_args()
    factory_counts = np.random.randint(MIN_FACTORY_COUNT, MAX_FACTORY_COUNT, args.n_sim)
    simulate_scenario = partial(Simulator.simulate, player_1=args.player_1, player_2=args.player_2)

    start = time()
    pool = mp.Pool(NUM_CPU)
    print(args.parallel)
    records = list()
    if args.parallel:
        print(f"Parallelize simulation on {NUM_CPU} cores")
        records = pool.map(simulate_scenario, list(factory_counts))
    else:
        for n_factory in factory_counts:
            r = simulate_scenario(factory_count=n_factory)
            records.append(r)

    datestamp = datetime.today().strftime('%Y-%m-%d-%H:%M:%S').replace('-', '').replace(':', '')
    stat = pd.DataFrame.from_records(records)
    stat.to_csv(f"simulations/simulation_{datestamp}_{args.player_1.split('.')[0]}_vs_{args.player_2.split('.')[0]}.csv",
                index=False)

    n_games = stat.shape[0]
    player_1_wins = sum(stat.win == args.player_1)
    player_2_wins = sum(stat.win == args.player_2)
    draws = sum(stat.win == "draw")
    p_1, p_2 = player_1_wins/(n_games-draws), player_2_wins/(n_games-draws)
    b = 1.96 * np.sqrt(p_1 * p_2 / (n_games - draws))
    print(f"Simulation over in {time() - start}")
    print(f"Games played {n_games}")
    print(f"{args.player_1} total wons: {player_1_wins}")
    print(f"{args.player_2} total wons: {player_2_wins}")
    print(f"Draws: {draws}")
    print(f"{args.player_1} win probability 95% confidence {p_1 - b:.3f} {p_1:.3f} {p_1 + b:.3f}")
    print(f"{args.player_2} win probability 95% confidence {p_2 - b:.3f} {p_2:.3f} {p_2 + b:.3f}")


if __name__ == "__main__":
    main()