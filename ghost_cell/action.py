from ghost_cell.entities import Factory


class Action:
    def apply(self, arena):
        pass

    def is_valid(self, arena):
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
        pass

    @property
    def str(self):
        return f"{self.prefix}"


class Message(Action):
    def __init__(self, message):
        self.message = message

    @property
    def prefix(self):
        return "MSG"

    @property
    def str(self):
        return f"{self.prefix} {self.message}"


class Move(Action):

    def __init__(self, source: Factory, destination: Factory, cyborg_count: int):
        if source == destination:
            raise ValueError(f"Source and destination have to differ")
        self.source = source
        self.destination = destination
        self.cyborg_count = cyborg_count

    @property
    def prefix(self):
        return "MOVE"

    @property
    def str(self):
        return f"{self.prefix} {self.source} {self.destination} {self.cyborg_count}"

    def apply(self, game):
        game.factories[self.source, TROOPS] = game.factories[self.source, TROOPS] - self.cyborg_count
        distance = game.distance_matrix[self.source, self.destination]
        factory_update = time()
        game.update_troop(entity_id=-1, player=1, source=self.source, destination=self.destination,
                          troops=self.cyborg_count, distance=distance)

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
        self.factory = int(factory)
        self.prefix = "INC"

    def apply(self, game):
        game.factories[self.factory, PROD] += 1
        game.factories[self.factory, TROOPS] += -10

    def is_valid(self, game):
        if game.factories[self.factory, PLAYER] != 1:
            return False
        elif game.factories[self.factory, TROOPS] < 10:
            return False
        elif game.factories[self.factory, PROD] > 2:
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
        game_proj.update_bomb(entity_id=-1, player=1, source=self.source, destination=self.destination)
        troop_update = time()

    @property
    def str(self):
        return f"{self.prefix} {self.source} {self.destination}"