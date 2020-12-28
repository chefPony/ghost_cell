import unittest

import numpy as np

from lightweight_bot import Player, GameState, ID, PLAYER, TROOPS, PROD, BLOCKED, DIST, FROM, TO


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

    def create_hard_choice(self):
        square_state = GameState()
        square_state.factory_count = 4
        square_state.factories = np.zeros((square_state.factory_count, 6), dtype=int)
        square_state.factories[:, ID] = [0, 1, 2, 3]
        square_state.factories[:, PLAYER] = [1, 0 ,0, 0]
        square_state.factories[:, TROOPS] = [22, 12, 3, 12]
        square_state.factories[:, PROD] = [0, 3, 2, 3]
        square_state.factories[:, BLOCKED] = [0, 0, 0, 0]
        square_state.distance_matrix = np.array([[0, 1, 2, 5],
                                                 [1, 0, 1, 2],
                                                 [2, 1, 0, 2],
                                                 [5, 2, 2, 0]])
        square_state.max_distance = 5
        square_state.troops = np.zeros((square_state.factory_count, square_state.max_distance + 1, 2), dtype=int)
        return square_state

    def test_square_scenario(self):
        state = self.create_square_state(d=6, player=[1, 0, 0, -1], troops=[10, 5, 5, 10], prod=[1, 0, 0, 1], blocked=0)
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.7)
        player.get_state(game_state=state)
        player.select_plan()
        self.assertSequenceEqual(player.action_list, ["WAIT"])
        #print(player.required_troops, "\n")
        #print(player.move_value_matrix)

    def test_double_attack(self):
        state = self.create_square_state(d=3, player=[1, 1, 1, -1], troops=[1, 16, 16, 10], prod=[1, 0, 0, 1], blocked=0)
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.7)
        player.get_state(game_state=state)
        player.select_plan()
        print(player.action_list)

    def test_hard_choice(self):
        state = self.create_hard_choice()
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.7)
        player.get_state(game_state=state)
        player.select_plan()
        print(player.action_list)

    def test_duel(self):
        state = self.create_duel(d=2, player=[1, -1], troops=[10, 10], prod=[1, 1], blocked=0)
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.7)
        player.get_state(game_state=state)
        player.select_plan()
        self.assertSequenceEqual(player.action_list, ["WAIT"])

        state = self.create_duel(d=2, player=[1, -1], troops=[15, 10], prod=[1, 1], blocked=0)
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.8)
        player.get_state(game_state=state)
        player.select_plan()
        self.assertSequenceEqual(player.action_list, ["WAIT"])


if __name__ == '__main__':
    unittest.main()
