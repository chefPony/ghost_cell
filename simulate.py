from scenario_generator import ScenarioGenerator
from arena import enqueue_output
from constants import MIN_FACTORY_COUNT, MAX_FACTORY_COUNT
import pandas as pd
import numpy as np
from time import time
import threading
from subprocess import Popen, PIPE
from queue import Queue
import argparse
import multiprocessing as mp
import psutil
PARALLEL = False
NUM_CPU = psutil.cpu_count(logical = False)

parser = argparse.ArgumentParser(description='Simulate ghost in the cell game')
parser.add_argument('--n_sim', metavar='N', type=int, help='number of simulations', required=True)
parser.add_argument('--player_1', type=str, help='bot to use as player 1', required=True)
parser.add_argument('--player_2', type=str, help='bot to use as player 2', required=True)

class Simulator:

    def __init__(self, player_1, player_2):
        self.player_1 = player_1
        self.player_2 = player_2


    def simulate(self, factory_count):
        p0 = Popen(["./"+self.player_1], stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=False, text=True, bufsize=-1)
        p1 = Popen(['python', self.player_2], stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=False, text=True, bufsize=-1)

        p0_queue, p1_queue, p0_err, p1_err = Queue(), Queue(), Queue(), Queue()
        thread0 = threading.Thread(target=enqueue_output, args=(p0.stdout, p0.stderr, p0_queue, p0_err))
        thread1 = threading.Thread(target=enqueue_output, args=(p1.stdout, p1.stderr, p1_queue, p1_err))
        thread0.daemon, thread1.daemon = True, True
        thread0.start(), thread1.start()

        scenario = ScenarioGenerator.generate(factory_count=factory_count)
        if int(time()*1e4) % 2 == 0:
            scenario.players = {1: (p0, p0_queue, p0_err), -1: (p1, p1_queue, p1_err)}
            bot_player = {1: self.player_1, -1: self.player_2}
        else:
            scenario.players = {-1: (p0, p0_queue, p0_err), 1: (p1, p1_queue, p1_err)}
            bot_player = {-1: self.player_1, 1: self.player_2}
        start_game = time()
        scenario.match()
        result = {"win": bot_player[scenario.winner], "win_condition": scenario.win_condition,
                  "turn": scenario.turn, "factory_count": factory_count, "as_player": scenario.winner,
                  "final_score": " ".join([f"{player}|{score} " for player, score in scenario.score.items()]),
                  "playing_time": time() - start_game}

        p0.terminate(), p1.terminate()
        p0.wait(), p1.wait()

        return result

def main():
    args = parser.parse_args()
    factory_counts = np.random.randint(MIN_FACTORY_COUNT, MAX_FACTORY_COUNT, args.n_sim)
    simulator = Simulator(player_1=args.player_1, player_2=args.player_2)

    start = time()
    pool = mp.Pool(NUM_CPU)
    print(f"Parallelize simulation on {NUM_CPU} cores")
    records = list()
    if PARALLEL:
        records = pool.map(simulator.simulate, list(factory_counts))
    else:
        for n_factory in factory_counts:
            r = simulator.simulate(factory_count=n_factory)
            records.append(r)
    stat = pd.DataFrame.from_records(records)
    stat.to_csv(f"simulation_{args.player_1.split('.')[0]}_vs_{args.player_2.split('.')[0]}.csv", index=False)

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