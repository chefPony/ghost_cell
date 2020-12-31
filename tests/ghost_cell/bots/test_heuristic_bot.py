from ghost_cell.bots import ghost_cell
from collections import defaultdict
import numpy as np
import unittest


class MyTestCase(unittest.TestCase):
    
    def build_dummy_game(self, game, n_factories, links):
        game.factory_count = int(n_factories)  # the number of factories
        game.link_count = len(links)  # the number of links between factories
        game.distance_matrix = np.zeros((game.factory_count, game.factory_count), dtype=int)
        for i in range(len(links)):
            factory_1, factory_2, distance = [int(j) for j in links[i]]
            game.distance_matrix[factory_1, factory_2], game.distance_matrix[factory_2, factory_1] = distance, distance
        game.max_distance = np.max(game.distance_matrix)
        game.factories = np.zeros((game.factory_count, 6))
        game.troops = np.zeros((game.factory_count, game.max_distance + 1, 2), dtype=int)
        game.bombs = defaultdict(list)
    
    def test_heuristic_evaluate(self):
        game = ghost_cell.Game()
        self.build_dummy_game(game, n_factories=2, links=[(0, 1, 3)])
        game.update_factory(entity_id=0, player=-1, troops=10, prod=1, blocked=0)
        game.update_factory(entity_id=1, player=1, troops=10, prod=1, blocked=0)
        for troops, distance in zip([12], [1]):
            game.update_troop(entity_id=-1, player=1, troops=troops, distance=distance, source=1, destination=0)
        #for troops, distance in zip([4], [2]):
        #    game.update_troop(entity_id=-1, player=-1, troops=troops, distance=distance, source=4, destination=0)
        cost = ghost_cell.heuristic_evaluate(ghost_cell.Move(source=1, destination=0, cyborg_count=1), game)
        self.assertEqual(cost, 0)

    def test_heuristic_evaluate_2(self):
        game = ghost_cell.Game()
        self.build_dummy_game(game, n_factories=2, links=[(0, 1, 3)])
        game.update_factory(entity_id=0, player=-1, troops=10, prod=1, blocked=0)
        game.update_factory(entity_id=1, player=1, troops=10, prod=1, blocked=0)
        for troops, distance in zip([12], [1]):
            game.update_troop(entity_id=-1, player=1, troops=troops, distance=distance, source=1, destination=0)
        for troops, distance in zip([3], [2]):
            game.update_troop(entity_id=-1, player=-1, troops=troops, distance=distance, source=4, destination=0)
        cost = ghost_cell.heuristic_evaluate(ghost_cell.Move(source=1, destination=0, cyborg_count=1), game)
        self.assertEqual(cost, 0)

if __name__ == '__main__':
    unittest.main()
