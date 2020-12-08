import sys
import math
from copy import copy
from collections import defaultdict
from time import time
import numpy as np

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

ID, PLAYER, TROOPS, PROD, FROM, TO, SIZE, DIST = 0, 1, 2, 3, 2, 3, 4, 5


class Game:
    def __init__(self):
        pass

    def initialize(self, input):
        self.factory_count = int(input())  # the number of factories
        self.link_count = int(input())  # the number of links between factories
        self.distance_matrix = np.zeros((self.factory_count, self.factory_count), dtype=int)
        for i in range(self.link_count):
            factory_1, factory_2, distance = [int(j) for j in input().split()]
            self.distance_matrix[factory_1, factory_2], self.distance_matrix[factory_2, factory_1] = distance, distance
        self.max_distance = np.max(self.distance_matrix)

    def current_status(self, input):
        self.factories = np.zeros((self.factory_count, 6))
        self.entity_count = int(input())  # the number of entities (e.g. factories and troops)
        self.troops = defaultdict(list)
        self.bombs = defaultdict(list)
        for i in range(self.entity_count):
            inputs = input().split()
            entity_id, entity_type = int(inputs[0]), inputs[1]
            arg_1, arg_2, arg_3, arg_4, arg_5 = int(inputs[2]), int(inputs[3]), int(inputs[4]), int(inputs[5]), int(
                inputs[6])
            if entity_type == "FACTORY":
                self.factories[entity_id, ID] = entity_id
                self.factories[entity_id, PLAYER] = arg_1
                self.factories[entity_id, TROOPS] = arg_2
                self.factories[entity_id, PROD] = arg_3
            elif entity_type == "TROOP":
                self.troops[arg_5].append({"id": entity_id, "player": arg_1, "source": arg_2,
                                           "destination": arg_3, "troops": arg_4})
            elif entity_type == "BOMB":
                self.bombs[arg_4].append({"id": entity_id, "player": arg_1, "source": arg_2, "destination": arg_3,
                                          "distance": arg_4})

    def clone(self):
        game_proj = Game()
        game_proj.factory_count = game.factory_count
        game_proj.max_distance = game.max_distance
        game_proj.factories = self.factories.copy()
        game_proj.troops = self.troops.copy()
        game_proj.distance_matrix = self.distance_matrix
        game_proj.bombs = self.bombs.copy()
        return game_proj

    def next_state(self):
        # print(f"In NEXT STATE", file=sys.stderr, flush=True)
        init_clone = time()
        game_proj = self.clone()
        end_clone = time()
        prod_factories = (game_proj.factories[:, PLAYER] == 1) | (game_proj.factories[:, PLAYER] == -1)
        # Increase troops for production
        game_proj.factories[prod_factories, TROOPS] += game_proj.factories[prod_factories, PROD]
        factory_update = time()
        # If no troops are moving return
        # print(f"Game cloned in   {(end_clone - init_clone) * 1e3}ms", file=sys.stderr, flush=True)
        # print(f"Factories update {(factory_update - end_clone) * 1e3}ms", file=sys.stderr, flush=True)

        # Move troops and bombs
        init_troop = time()
        battle_mat = np.zeros((game_proj.factory_count, 3), dtype=int)
        for d in range(1, game_proj.max_distance):
            if d not in game_proj.troops.keys():
                continue
            elif d > 1:
                incoming_troops = game_proj.troops.pop(d)
                game_proj.troops[d - 1] = incoming_troops
            else:
                incoming_troops = game_proj.troops.pop(d)
                for troop in incoming_troops:
                    destination, player = troop["destination"], troop["player"]
                    battle_mat[destination, player] += troop["troops"]
                balance = battle_mat[:, 1] - battle_mat[:, -1]
                attack_player = np.where(balance < 0, -1, 1)
                balance = np.abs(balance)
                factory_troops, factory_player = game_proj.factories[:, TROOPS], game_proj.factories[:, PLAYER]
                outcome_troops = np.where(factory_player == attack_player, factory_troops + balance,
                                          factory_troops - balance)
                outcome_player = np.where(outcome_troops >= 0, factory_player, attack_player)
                outcome_troops = np.abs(outcome_troops)
                game_proj.factories[:, TROOPS], game_proj.factories[:, PLAYER] = outcome_troops, outcome_player

        for d in range(1, game_proj.max_distance):
            if d not in game_proj.bombs.keys():
                continue
            elif d > 1:
                incoming_bombs = game_proj.bombs.pop(d)
                game_proj.bombs[d - 1] = incoming_bombs
            else:
                bomb = game_proj.bombs.pop(d)
                destroyed = max(int(game_proj[bomb["destination"], TROOPS] / 2), 10)
                game_proj[bomb["destination"], TROOPS] -= destroyed
                game_proj[bomb["destination"], PROD] = 0

        troop_update = time()
        # print(f"Troop update     {(troop_update - init_troop) * 1e3}ms", file=sys.stderr, flush=True)
        return game_proj

    def count_player_prod(self, player):
        return sum(self.factories[self.factories[:, PLAYER] == player, PROD])

    def count_player_troops(self, player):
        in_factory = sum(self.factories[self.factories[:, PLAYER] == player, TROOPS])
        moving = 0
        for _, troop_list in self.troops.items():
            for troop in troop_list:
                moving += troop["troops"] * (troop["player"] == player)
        return in_factory + moving


class Action:
    def apply(self, game):
        pass

    def is_valid(self, game):
        raise NotImplementedError

    @property
    def str(self):
        raise NotImplementedError


class Wait(Action):
    def __init__(self):
        self.prefix = "WAIT"

    def is_valid(self, game):
        return True

    def apply(self, game):
        return game.clone()

    @property
    def str(self):
        return f"{self.prefix}"


class Message(Action):
    def __init__(self, message):
        self.prefix = "MSG"
        self.message = message

    def is_valid(self, game):
        return True

    @property
    def str(self):
        return f"{self.prefix} {self.message}"


class Move(Action):
    def __init__(self, source, destination, cyborg_count):
        self.source = int(source)
        self.destination = int(destination)
        self.cyborg_count = int(cyborg_count)
        self.prefix = "MOVE"

    @property
    def str(self):
        return f"{self.prefix} {self.source} {self.destination} {self.cyborg_count}"

    def apply(self, game):
        init_clone = time()
        game_proj = game.clone()
        end_clone = time()
        game_proj.factories[self.source, TROOPS] = game_proj.factories[self.source, TROOPS] - self.cyborg_count
        distance = game.distance_matrix[self.source, self.destination]
        factory_update = time()
        game_proj.troops[distance].append({"id": -1, "player": 1, "source": self.source,
                                           "destination": self.destination, "troops": self.cyborg_count})
        troop_update = time()
        # print(f"In APPLY", file=sys.stderr, flush=True)
        # print(f"Game cloned in   {(end_clone - init_clone)*1e3}ms", file=sys.stderr, flush=True)
        # print(f"Factories update {(factory_update - end_clone)*1e3}ms", file=sys.stderr, flush=True)
        # print(f"Troop update     {(troop_update - factory_update)*1e3}ms", file=sys.stderr, flush=True)
        return game_proj

    def is_valid(self, game):
        if game.factories[self.source, PLAYER] != 1:
            return False
        elif self.source == self.destination:
            return False
        elif self.cyborg_count <= 0:
            return False
        else:
            return True


class IncreaseProd(Action):
    def __init__(self, factory):
        self.factory = factory
        self.prefix = "INC"

    def apply(self, game):
        game_proj = game.clone()
        game_proj.factories[self.factory, PROD] += 1
        game_proj.factories[self.factory, TROOPS] += -10
        return game_proj

    def is_valid(self, game):
        factory_attr = game.factories.loc[self.factory]
        if factory_attr.player != 1:
            return False
        elif factory_attr.troops < 10:
            return False
        elif factory_attr.prod > 2:
            return False
        else:
            return True

    @property
    def str(self):
        return f"{self.prefix} {self.factory}"


class SendBomb(Action):
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
        self.prefix = "BOMB"

    def is_valid(self, game):
        source_attr = game.factories.loc[self.source]
        if source_attr.player != 1:
            return False
        else:
            return True

    def apply(self, game):
        init_clone = time()
        game_proj = game.clone()
        end_clone = time()
        distance = game.distance_matrix[self.source, self.destination]
        factory_update = time()
        game_proj.bombs[distance].append({"id": -1, "player": 1, "source": self.source,
                                          "destination": self.destination})
        troop_update = time()

    @property
    def str(self):
        return f"{self.prefix} {self.source} {self.destination}"


class ActionEvaluator:

    def __init__(self, criterion, optimizer):
        self.criterion = criterion
        self.optimizer = optimizer

    def evaluate(self, action, game):
        return self.criterion(action, game)

    def optimize(self, action, game):
        return self.optimizer(action, game, self.criterion)


def move_optimizer(action, game, criterion):
    if isinstance(action, Wait):
        return criterion(action, game)
    best_value = -10000
    best_action = action
    source_troops = game.factories[int(action.source), TROOPS]
    for p in [0.3, 0.9]:
        action.cyborg_count = int(source_troops * p)
        init_eval = time()
        value = criterion(action, game)
        # print(f"Move evaluated in {(time() - init_eval) * 1e3}ms", file=sys.stderr, flush=True)
        if value > best_value:
            best_value = value
            best_action = action.cyborg_count

    action.cyborg_count = best_action
    # print(f"{action.prefix} {action.source.id} {action.destination.id} {action.cyborg_count} {best_value}",
    #      file=sys.stderr, flush=True)
    return best_value


def do_not_optimize(action, game, criterion):
    if isinstance(action, Move):
        source_troops = game.factories[int(action.source), TROOPS]
        action.cyborg_count = int(source_troops * 0.8)
    value = criterion(action, game)
    return value


def evaluate_with_states(action, game, n_steps=4):
    init_eval = time()
    game_new = action.apply(game)
    end_eval = time()
    prod_bonus, troop_bonus = 0, 0
    delta_prod_baseline = game.count_player_prod(player=1) - game.count_player_prod(player=-1)
    delta_troops_baseline = game.count_player_troops(player=1) - game.count_player_troops(player=-1)
    for i in range(n_steps):
        game_new = game_new.next_state()
        delta_prod = game_new.count_player_prod(player=1) - game_new.count_player_prod(player=-1)
        delta_troops = game_new.count_player_troops(player=1) - game_new.count_player_troops(player=-1)
        prod_bonus += (delta_prod - delta_prod_baseline) * 0.9 ** i
        troop_bonus += (delta_troops - delta_troops_baseline) * 0.9 ** i
        delta_prod_baseline, delta_troops_baseline = delta_prod, delta_troops
    end_proj = time()

    # print(f"{action.str}", file=sys.stderr, flush=True)
    # print(f"{game_new.factories}", file=sys.stderr, flush=True)
    # print(f"{game_new.count_player_prod(player=1)} {game_new.count_player_prod(player=-1)}", file=sys.stderr, flush=True)
    # print(f"{delta_prod_new} {delta_prod_old} {delta_troops_new} {delta_troops_old}", file=sys.stderr, flush=True)
    # print(f"Game proj takes      {(end_proj - end_eval) * 1e3}ms", file=sys.stderr, flush=True)
    # print(f"Metric compute takes {(end_metric - end_proj) * 1e3}ms", file=sys.stderr, flush=True)
    return prod_bonus * 10 + troop_bonus


class Player:

    def __init__(self, player_id, move_action_eval, prod_action_eval, bomb_action_eval):
        self.player_id = player_id
        self.action_eval = move_action_eval
        self.prod_action_eval = prod_action_eval
        self.bomb_action_eval = bomb_action_eval

    def get_actions(self, game):
        init_get_actions = time()
        wait_action = Wait()
        action_list = [(wait_action, self.action_eval(wait_action, game))]
        sources = game.factories[game.factories[:, PLAYER] == self.player_id, ID]

        for source_id in sources:
            increment_action = IncreaseProd(factory=source_id)
            if increment_action.is_valid(game):
                action_list.append((increment_action, self.action_eval(increment_action, game)))
            for dest_id in game.factories[:, ID]:
                move_action = Move(source=source_id, destination=dest_id, cyborg_count=1)
                bomb_action = SendBomb(source=source_id, destination=dest_id)
                if move_action.is_valid(game):
                    action_list.append((move_action, self.action_eval(increment_action, game)))
                if bomb_action.is_valid(game):
                    action_list.append((bomb_action, self.action_eval(increment_action, game)))

        self.action_list = sorted(action_list, key=lambda x: x[1], reverse=True)
        print(f"Got available actions in {(time() - init_get_actions) * 1e3}ms", file=sys.stderr, flush=True)


    def get_plan(self, game: Game, time_limit=45):
        init_plan = time()
        plan = list()
        if len(self.action_list) == 0:
            return plan.append(Wait().str)
        t = (time() - init_plan) * 1e3
        opt_time = 0
        n = 0
        game_copy = game.clone()
        while t < time_limit:
            # print(f"Cycles {n}", file=sys.stderr, flush=True)
            opt_start = time()
            optimized_values = list(map(lambda x: self.move_action_eval.optimize(x, game_copy), action_list))
            a_list = {a.str: v for a, v in zip(action_list, optimized_values)}
            print(f"Action values : {a_list}", file=sys.stderr, flush=True)
            opt_time = opt_time + time() - opt_start
            # print(f"Opt time : {(time() - opt_start) * 1e3}", file=sys.stderr, flush=True)
            action = action_list[np.argmax(optimized_values)]
            # print(f"Best : {np.argmax(optimized_values)}", file=sys.stderr, flush=True)
            # print(f"Action: {action.to_str()}", file=sys.stderr, flush=True)
            if action.is_valid(game_copy):
                plan.append(action.str)
                game_copy = action.apply(game_copy)
            if isinstance(action, Wait):
                break
            t = (time() - init_plan) * 1e3
            n = n + 1
        print(f"Action optimization takes {opt_time * 1e3}ms", file=sys.stderr, flush=True)
        return plan

    def execute_plan(self, plan):
        print(f"{plan}", file=sys.stderr, flush=True)
        print(";".join(plan))


game = Game()
game.initialize(input)
move_action_evaluator = ActionEvaluator(criterion=evaluate_with_states, optimizer=move_optimizer)
prod_action_evaluator = ActionEvaluator(criterion=lambda x: -10000, optimizer=lambda x: -10000)
bomb_action_evaluator = ActionEvaluator(criterion=lambda x: -10000, optimizer=lambda x: -10000)
agent = Planner(move_action_eval=move_action_evaluator, bomb_action_eval=bomb_action_evaluator,
                prod_action_eval=prod_action_evaluator)
# game loop
print(f"{game.distance_matrix}", file=sys.stderr, flush=True)
while True:
    start = time()
    game.current_status(input)
    print(f"Got game status in {(time() - start) * 1e3}ms", file=sys.stderr, flush=True)
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr, flush=True)
    # _delta_move(game, player_priority={0:10, 1:2, -1:20})
    # Any valid action, such as "WAIT" or "MOVE source destination cyborgs"
    start_plan = time()
    action_plan = agent.get_plan(game, time_limit=45)
    print(f"Action plan in {(time() - start_plan) * 1e3}ms", file=sys.stderr, flush=True)
    print(f"{action_plan}", file=sys.stderr, flush=True)
    if len(action_plan) == 0:
        print("WAIT")
    else:
        agent.execute_plan(action_plan)
