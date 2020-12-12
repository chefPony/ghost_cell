from scenario_generator import ScenarioGenerator
from arena import Scenario, enqueue_output
from constants import MIN_FACTORY_COUNT, MAX_FACTORY_COUNT
import pandas as pd
import numpy as np
from time import time
import threading
from subprocess import Popen, PIPE
from queue import Queue
import argparse

parser = argparse.ArgumentParser(description='Simulate ghost in the cell game')
parser.add_argument('--n_sim', metavar='N', type=int, help='number of simulations', required=True)
parser.add_argument('--player_1', type=str, help='bot to use as player 1', required=True)
parser.add_argument('--player_2', type=str, help='bot to use as player 2', required=True)

if __name__ == "__main__":
    args = parser.parse_args()
    factory_counts = np.random.randint(MIN_FACTORY_COUNT, MAX_FACTORY_COUNT, args.n_sim)
    records = list()
    start = time()
    for k, n_factory in enumerate(factory_counts):
        p0 = Popen(['python', args.player_1], stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=False, text=True, bufsize=1)
        p1 = Popen(['python', args.player_2], stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=False, text=True, bufsize=1)

        p0_queue, p1_queue = Queue(), Queue()
        thread0 = threading.Thread(target=enqueue_output, args=(p0.stdout, p0_queue))
        thread1 = threading.Thread(target=enqueue_output, args=(p1.stdout, p1_queue))
        thread0.daemon, thread1.daemon = True, True
        thread0.start(), thread1.start()


        scenario = ScenarioGenerator.generate(factory_count=n_factory)
        if k % 2 == 0:
            scenario.players = {1: (p0, p0_queue), -1: (p1, p1_queue)}
            bot_player = {1: args.player_1, -1: args.player_2}
        else:
            scenario.players = {-1: (p0, p0_queue), 1: (p1, p1_queue)}
            bot_player = {-1: args.player_1, 1: args.player_2}
        start_game = time()
        scenario.match()
        records.append({"win": bot_player[scenario.winner], "win_condition": scenario.win_condition,
                        "turn": scenario.turn, "factory_count": n_factory, "as_player": scenario.winner,
                        "final_score": " ".join([f"{player}|{score} " for player, score in scenario.score.items()]),
                        "playing_time": time()-start_game})

        p0.terminate(), p1.terminate()
        print(f"game {k} finished")

    stat = pd.DataFrame.from_records(records)
    stat.to_csv(f"simulation_{args.player_1.split('.')[0]}_vs_{args.player_2.split('.')[0]}.csv")

    n_games = stat.shape[0]
    player_1_wins = sum(stat.win == args.player_1)
    player_2_wins = sum(stat.win == args.player_2)
    p_1, p_2 = player_1_wins/n_games, player_2_wins/n_games
    b = 1.96 * np.sqrt(p_1 * p_2 / n_games)
    print(f"Simulation over in {time() - start}")
    print(f"Games played {n_games}")
    print(f"{args.player_1} total wons: {player_1_wins}")
    print(f"{args.player_2} total wons: {player_2_wins}")
    print(f"{args.player_1} win probability 95% confidence {p_1 - b} {p_1} {p_1 + b}")
    print(f"{args.player_2} win probability 95% confidence {p_2 - b} {p_2} {p_2 + b}")