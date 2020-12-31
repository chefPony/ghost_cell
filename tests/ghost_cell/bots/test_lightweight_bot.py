import unittest

import numpy as np

from ghost_cell.bots.lightweight_bot import Player, GameState, ID, PLAYER, TROOPS, PROD, BLOCKED, dijkstra
#from ghost_cell.scenario_generator import ScenarioGenerator

class MyTestCase(unittest.TestCase):

    def create_square_state(self, d, player, troops, prod, blocked):
        square_state = GameState()
        square_state.factory_count = 4
        square_state.factories = np.zeros((square_state.factory_count, 6), dtype=int)
        square_state.factories[:, ID] = [0, 1, 2, 3]
        square_state.factories[:, PLAYER] = player
        square_state.factories[:, TROOPS] = troops
        square_state.factories[:, PROD] = prod
        square_state.factories[:, BLOCKED] = blocked
        square_state.distance_matrix = np.array([[0, d, d, int(d * np.sqrt(2))],
                                                 [d, 0, int(d * np.sqrt(2)), d],
                                                 [d, int(d * np.sqrt(2)), 0, d],
                                                 [int(d * np.sqrt(2)), d, d, 0]])
        square_state.max_distance = int(d * np.sqrt(2))
        square_state.troops = np.zeros((square_state.factory_count, square_state.max_distance + 1, 2), dtype=int)
        square_state.bombs = {0: {"id": 0, "player":-1, "source": 3, "destination": -1, "countdown": -1}}
        return square_state

    def create_duel(self, d, player, troops, prod, blocked):
        square_state = GameState()
        square_state.factory_count = 2
        square_state.factories = np.zeros((square_state.factory_count, 6), dtype=int)
        square_state.factories[:, ID] = [0, 1]
        square_state.factories[:, PLAYER] = player
        square_state.factories[:, TROOPS] = troops
        square_state.factories[:, PROD] = prod
        square_state.factories[:, BLOCKED] = blocked
        square_state.distance_matrix = np.array([[0, d],
                                                 [d, 0]])
        square_state.max_distance = int(d)
        square_state.troops = np.zeros((square_state.factory_count, square_state.max_distance + 1, 2), dtype=int)
        return square_state

    def create_hard_choice_1(self):
        state = GameState()
        state.factory_count = 4
        state.factories = np.zeros((state.factory_count, 6), dtype=int)
        state.factories[:, ID] = [0, 1, 2, 3]
        state.factories[:, PLAYER] = [1, 0 ,0, 0]
        state.factories[:, TROOPS] = [22, 12, 3, 12]
        state.factories[:, PROD] = [0, 3, 2, 3]
        state.factories[:, BLOCKED] = [0, 0, 0, 0]
        state.distance_matrix = np.array([[0, 1, 2, 5],
                                                 [1, 0, 1, 2],
                                                 [2, 1, 0, 2],
                                                 [5, 2, 2, 0]])
        state.max_distance = 5
        state.troops = np.zeros((state.factory_count, state.max_distance + 1, 2), dtype=int)
        return state

    def create_hard_choice_2(self):
        state = GameState()
        state.factory_count = 6
        state.factories = np.zeros((state.factory_count, 6), dtype=int)
        state.factories[:, ID] = [0, 1, 2, 3, 4, 5]
        state.factories[:, PLAYER] = [1, 0, 0, 0, 0, 0]
        state.factories[:, TROOPS] = [16, 0, 8, 0, 10, 2]
        state.factories[:, PROD] = [0, 0, 2, 0, 2, 1]
        state.factories[:, BLOCKED] = [0, 0, 0, 0, 0, 0]
        state.distance_matrix = np.array([[0, 2, 3, 2, 4, 1],
                                          [2, 0, 1, 3, 6, 4],
                                          [3, 1, 0, 1, 4, 4],
                                          [2, 3, 1, 0, 2, 2],
                                          [4, 6, 4, 2, 0, 2],
                                          [1, 4, 4, 2, 2, 0]])
        state.max_distance = 6
        state.troops = np.zeros((state.factory_count, state.max_distance + 1, 2), dtype=int)
        return state

    def create_complex_scenario(self):
        state = GameState()
        state.factory_count = 15
        state.factories = np.zeros((state.factory_count, 6), dtype=int)
        state.factories = np.array([[ 0,  0,  0,  0,  0,  0],
                                    [ 1,  1,  1,  0,  0,  0],
                                    [ 2, -1,  0,  0,  0,  0],
                                    [ 3,  1,  1,  0,  0,  0],
                                    [ 4,  0,  0,  0,  0,  0],
                                    [ 5,  1,  7,  1,  0,  0],
                                    [ 6, -1,  2,  1,  0,  0],
                                    [ 7,  0, 10,  2,  0,  0],
                                    [ 8,  0, 10,  2,  0,  0],
                                    [ 9,  1,  1,  0,  0,  0],
                                    [10,  0,  0,  0,  0,  0],
                                    [11,  1,  4,  2,  0,  0],
                                    [12, -1,  2,  2,  0,  0],
                                    [13,  1,  1,  0,  0,  0],
                                    [14,  0,  0,  0,  0,  0]])
        state.distance_matrix = np.array([[ 0,  6,  6,  7,  7,  5,  5,  2,  2,  3,  3,  4,  4,  3,  3],
                                          [ 6,  0, 14,  2, 14,  1, 13,  4,  9,  5,  9,  3, 12,  2, 11],
                                          [ 6, 14,  0, 14,  2, 13,  1,  9,  4,  9,  5, 12,  3, 11,  2],
                                          [ 7,  2, 14,  0, 15,  4, 12,  6,  9,  4, 10,  1, 12,  3, 11],
                                          [ 7, 14,  2, 15,  0, 12,  4,  9,  6, 10,  4, 12,  1, 11,  3],
                                          [ 5,  1, 13,  4, 12,  0, 12,  2,  8,  5,  7,  4, 10,  2, 10],
                                          [ 5, 13,  1, 12,  4, 12,  0,  8,  2,  7,  5, 10,  4, 10,  2],
                                          [ 2,  4,  9,  6,  9,  2,  8,  0,  5,  4,  3,  4,  6,  2,  6],
                                          [ 2,  9,  4,  9,  6,  8,  2,  5,  0,  3,  4,  6,  4,  6,  2],
                                          [ 3,  5,  9,  4, 10,  5,  7,  4,  3,  0,  7,  1,  8,  2,  6],
                                          [ 3,  9,  5, 10,  4,  7,  5,  3,  4,  7,  0,  8,  1,  6,  2],
                                          [ 4,  3, 12,  1, 12,  4, 10,  4,  6,  1,  8,  0, 10,  1,  9],
                                          [ 4, 12,  3, 12,  1, 10,  4,  6,  4,  8,  1, 10,  0,  9,  1],
                                          [ 3,  2, 11,  3, 11,  2, 10,  2,  6,  2,  6,  1,  9,  0,  8],
                                          [ 3, 11,  2, 11,  3, 10,  2,  6,  2,  6,  2,  9,  1,  8,  0]])
        state.max_distance = np.max(state.distance_matrix)
        state.troops = np.zeros((state.factory_count, state.max_distance + 1, 2), dtype=int)
        state.troops[:, :, 0] = np.array([[0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])
        state.troops[:, :, 1] = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 1, 8, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 4, 2, 2, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])
        return state

    def test_square_scenario(self):
        state = self.create_square_state(d=6, player=[1, 0, 0, -1], troops=[10, 5, 5, 10], prod=[1, 0, 0, 1], blocked=0)
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.7)
        player._update_from_state(game_state=state)
        player.select_plan()
        self.assertSequenceEqual(player.action_list, ["WAIT"])
        #print(player.troops_required, "\n")
        #print(player.move_value_matrix)

    def test_double_attack(self):
        state = self.create_square_state(d=3, player=[1, 1, 1, -1], troops=[1, 16, 16, 10], prod=[1, 0, 0, 1], blocked=0)
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.7)
        player._update_from_state(game_state=state)
        player.select_plan()
        print(player.action_list)

    def test_hard_choice(self):
        state = self.create_hard_choice_1()
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.7)
        player._update_from_state(game_state=state)
        player.select_plan()
        print(player.action_list)
        #self.assertSequenceEqual(["MOVE 0 2 4", "MOVE 0 1 13"], player.action_list)

    def test_hard_choice_2(self):
        state = self.create_hard_choice_2()
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.7)
        player._update_from_state(game_state=state)
        player.select_plan()
        print(state.factories[:,[ID, TROOPS, PROD]])
        print(player.action_list)
        #self.assertSequenceEqual(["MOVE 0 2 4", "MOVE 0 1 13"], player.action_list)

    def test_complex_scenario(self):
        state = self.create_complex_scenario()
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.95, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.7)
        player._update_from_state(game_state=state)
        player.select_plan()
        print(state.factories[:,[ID, PLAYER, TROOPS, PROD]])
        print(player.action_list)

    def test_duel(self):
        state = self.create_duel(d=2, player=[1, -1], troops=[10, 10], prod=[1, 1], blocked=0)
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.7)
        player._update_from_state(game_state=state)
        player.select_plan()
        self.assertSequenceEqual(player.action_list, ["WAIT"])

        state = self.create_duel(d=2, player=[1, -1], troops=[15, 10], prod=[1, 1], blocked=0)
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.8)
        player._update_from_state(game_state=state)
        player.select_plan()
        self.assertSequenceEqual(player.action_list, ["WAIT"])

    def test_dijkstra(self):
        scenario = ScenarioGenerator().generate(factory_count=7)
        min_dist_matrix = np.zeros((scenario.factory_count, scenario.factory_count), dtype=int)
        path_tree = dict()
        for source in range(scenario.factory_count):
            dijkstra(scenario.distance_matrix, source, min_dist_matrix, path_tree)

if __name__ == '__main__':
    unittest.main()
