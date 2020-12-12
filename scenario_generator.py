from arena import Scenario
from entities import Factory
import numpy as np
from constants import WIDTH, HEIGHT, EXTRA_SPACE_BETWEEN_FACTORIES, MIN_PRODUCTION_RATE, MAX_PRODUCTION_RATE,\
    PLAYER_INIT_UNITS_MIN, PLAYER_INIT_UNITS_MAX, MIN_TOTAL_PRODUCTION_RATE


class ScenarioGenerator:

    def __init__(self):
        pass


    #distances.put(factory.id, (int)
    #Math.round((position.distance(factory.position) - getRadius() - factory.getRadius()) / 800.));
    def generate(self, factory_count, initial_unit_count):
        factories = list()
        factory_count = factory_count if factory_count % 2 == 1 else factory_count + 1
        factory_radius = 600 if factory_count > 10 else 700
        min_space_between_factories = 2 * (factory_radius + EXTRA_SPACE_BETWEEN_FACTORIES)

        center = Factory(0, 0, 0, 0, 0)
        center.point = (WIDTH / 2, HEIGHT / 2)
        factories.append(center)

        total_production_rate = 0
        i = 1
        while i < (factory_count - 1) :
            x_i = np.random.randint(0, WIDTH / 2 - 2 * factory_radius, 1) + factory_radius + EXTRA_SPACE_BETWEEN_FACTORIES
            y_i = np.random.randint(0, HEIGHT - 2 * factory_radius, 1) + factory_radius + EXTRA_SPACE_BETWEEN_FACTORIES
            valid = True
            for j in range(i):
                x_j, y_j = factories[j].point
                distance = int((np.sqrt((x_i - x_j)**2 + (y_i - y_j)**2) - factory_radius * 2) / 800)
                if distance < min_space_between_factories:
                    valid = False
                    break

            if valid:
                prod = np.random.randint(MIN_PRODUCTION_RATE, MAX_PRODUCTION_RATE, 1)
                total_production_rate += prod * 2
                if i == 1:
                    player_troops = np.random.randint(PLAYER_INIT_UNITS_MIN, PLAYER_INIT_UNITS_MAX, 1)
                    factories.append(Factory(entity_id=i, player=1, troops=player_troops, prod=prod, blocked=0))
                    factories[i].point = (x_i, y_i)
                    i += 1
                    factories.append(Factory(entity_id=i, player=-1, troops=player_troops, prod=prod, blocked=0))
                    factories[i].point = (WIDTH - x_i, HEIGHT - y_i)
                    i += 1
                else:
                    troops = np.random.randint(0, 5 * prod + 1, 1)
                    factories.append(Factory(entity_id=i, player=0, troops=troops, prod=prod, blocked=0))
                    factories[i].point = (x_i, y_i)
                    i += 1
                    factories.append(Factory(entity_id=i, player=0, troops=troops, prod=prod, blocked=0))
                    factories[i].point = (WIDTH - x_i, HEIGHT - y_i)
                    i += 1

            while total_production_rate < MIN_TOTAL_PRODUCTION_RATE:
                for factory in factories[1:]:
                    if (factory.prod < MAX_PRODUCTION_RATE) & (total_production_rate < MIN_TOTAL_PRODUCTION_RATE):
                        factory.prod += 1
                        total_production_rate += 1

            get_distance = lambda factory_1, factory_2: int(
                (np.sqrt((factory_1.point[0] - factory_2.point[0]) ** 2 + (factory_1.point[1] - factory_2.point[1]) ** 2)
                 - factory_radius * 2) / 800)

            links = list()
            for i in range(factory_count):
                for j in range(i+1, factory_count):
                    links.append((i, j, get_distance(factories[i], factories[j])))

            scenario = Scenario(factories=factories, links=links)
            return scenario


