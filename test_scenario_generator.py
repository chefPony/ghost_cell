import unittest
from scenario_generator import ScenarioGenerator

class ScenarioGeneratorTest(unittest.TestCase):

    def test_distance(self):
        for n_factory in range(6, 16):
            scenario = ScenarioGenerator().generate(n_factory)
            for f1, f2, d in scenario.links:
                self.assertGreater(d, 0)
            #print(scenario.distance_matrix)


if __name__ == '__main__':
    unittest.main()
