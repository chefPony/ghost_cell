class Entity:

    def __init__(self, entity_id, player):
        self.entity_id = entity_id
        self.player = player


class MovingEntity(Entity):

    def __init__(self, entity_id, player, source, destination, distance):
        super().__init__(entity_id, player)
        self.source = source
        self.destination = destination
        self.distance = distance


class Factory(Entity):

    def __init__(self, entity_id, player, troops, prod):
        super().__init__(entity_id, player)
        self.troops = troops
        self.prod = prod
        self.blocked = 0
        self._point = None

    @property
    def point(self):
        return self._point

    @point.setter
    def point(self, x, y):
        self._point = (x, y)

    @property
    def entity_type(self):
        return "FACTORY"

    @property
    def str(self):
        return " ".join(map(str, [self.entity_id, self.entity_type, self.player, self.troops, self.prod,
                                  self.blocked, "0"]))

    def produce(self):
        if (self.player != 0) & (self.blocked == 0):
            self.troops += self.prod
        else:
            pass

    def increment_prod(self):
        if self.prod == 3:
            raise ValueError(f"Factory {self.entity_id} cannot increment production, already 3")
        elif self.troops < 10:
            raise ValueError(f"Factory {self.entity_id}  has not enough troop for upgrade: {self.troops}, required 10")
        else:
            self.prod += 1
            self.troops -= 10


class MovingTroop(MovingEntity):

    def __init__(self, entity_id: int, player: int, source: Factory, destination: Factory, troops: int, distance: int):
        super().__init__(entity_id, player, source, destination, distance)
        self.troops = troops

    @property
    def entity_type(self):
        return "TROOP"

    @property
    def str(self):
        return " ".join(map(str, [self.entity_id, self.entity_type, self.player, self.source, self.destination,
                                  self.troops, self.distance]))

    def move(self):
        if self.distance > 0:
            self.distance -= 1
        else:
            pass

class Bomb(MovingEntity):

    def __init__(self, entity_id: int, player: int, source: Factory, destination: Factory, distance: int):
        super().__init__(entity_id, player, source, destination, distance)

    @property
    def entity_type(self):
        return "BOMB"

    @property
    def str(self):
        return " ".join(map(str, [self.entity_id, self.entity_type, self.player, self.source, self.destination,
                                  self.distance, "0"]))

    def move(self):
        if self.distance > 0:
            self.distance -= 1
        else:
            pass

    def explode(self):
        destroyed = max(int(self.destination.troops / 2), 10)
        self.destination.troops -= destroyed
        self.destination.blocked = 5
        del self
