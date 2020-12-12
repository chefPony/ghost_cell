from scenario_generator import ScenarioGenerator
from arena import Scenario, enqueue_output
from time import time
import threading
from subprocess import Popen, PIPE
from queue import Queue

if __name__ == "__main__":
    start = time()
    scenario = ScenarioGenerator.generate(factory_count=7)
    print(f"Scenario generated in {time() - start} s")
    p0 = Popen(['python', 'main.py'], stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=False, text=True, bufsize=1)
    p1 = Popen(['python', 'main2.py'], stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=False, text=True, bufsize=1)

    p0_queue, p1_queue = Queue(), Queue()
    thread0 = threading.Thread(target=enqueue_output, args=(p0.stdout, p0_queue))
    thread1 = threading.Thread(target=enqueue_output, args=(p1.stdout, p1_queue))
    thread0.daemon, thread1.daemon = True, True
    thread0.start(), thread1.start()

    scenario.players = {1: (p0, p0_queue), -1: (p1, p1_queue)}
    scenario.match()

    p0.terminate(), p1.terminate()

    print(f"Game endend at turn {scenario.turn}")
    print(f"Final score {scenario.score}")
    print(f"Winner is : {scenario.winner}")