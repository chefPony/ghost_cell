import unittest
from ghost_cell.constants import MIN_TOTAL_PRODUCTION_RATE, PLAYER_INIT_UNITS_MIN,\
    PLAYER_INIT_UNITS_MAX
from ghost_cell.scenario_generator import ScenarioGenerator

class ScenarioGeneratorTest(unittest.TestCase):

    def test_distance(self):
        for n_factory in range(7, 15):
            scenario = ScenarioGenerator().generate(n_factory)
            for f1, f2, d in scenario.links:
                self.assertGreater(d, 0)
            #print(scenario.distance_matrix)

    def test_factory(self):
        for n_factory in range(6, 15):
            scenario = ScenarioGenerator().generate(n_factory)
            self.assertEqual(scenario.factories[1].player, 1)
            self.assertEqual(scenario.factories[2].player, -1)
            self.assertEqual(scenario.factories[1].troops, scenario.factories[2].troops)

            troops = scenario.factories[1].troops
            self.assertGreaterEqual(troops, PLAYER_INIT_UNITS_MIN)
            self.assertLessEqual(troops, PLAYER_INIT_UNITS_MAX)

            total_prod = sum([f.prod for f in scenario.factories])
            self.assertGreaterEqual(total_prod, MIN_TOTAL_PRODUCTION_RATE)


if __name__ == '__main__':
    unittest.main()
