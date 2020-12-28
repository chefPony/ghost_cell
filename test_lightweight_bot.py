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

    def test_square_scenario(self):
        state = self.create_square_state(d=6, player=[1, 0, 0, -1], troops=[10, 5, 5, 10], prod=[1, 0, 0, 1], blocked=0)
        player = Player(player_id=1, moving_troop_dist_th=100, moving_troop_discount=0.9, stationing_troop_dist_th=100,
                        stationing_troop_discount=0.7)
        player.get_state(game_state=state)
        player._move_value_matrix()
        print(player.move_value_matrix)


if __name__ == '__main__':
    unittest.main()
