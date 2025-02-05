import random

from mortal.mortal_helpers import TILES


def get_all_tiles(shuffle: bool) -> list[str]:
    all_tiles: list[str] = []
    for tile in TILES:
        count = 4
        if tile.startswith("5"):
            count = 3
            if tile.endswith("r"):
                count = 1
        for i in range(count):
            all_tiles.append(tile)
    assert len(all_tiles) == 136
    if shuffle:
        random.shuffle(all_tiles)
    return all_tiles


class Wall:
    def deal_start_hands(self) -> list[list[str]]:
        raise NotImplemented()

    def get_dora_markers(self) -> list[str]:
        raise NotImplemented()

    def get_ura_dora_markers(self) -> list[str]:
        raise NotImplemented()

    def can_draw_tile(self, player_id: int) -> bool:
        raise NotImplemented()

    def can_declare_kan(self, player_id: int) -> bool:
        raise NotImplemented()

    def draw_tile(self, player_id: int) -> str:
        raise NotImplemented()

    def draw_kan_tile(self, player_id: int) -> str:
        raise NotImplemented()


class StandardWall(Wall):
    def __init__(self):
        self.wall = get_all_tiles(shuffle=True)

        self.kan_count: int = 0
        self.pointer: int = 0

    def deal_start_hands(self) -> list[list[str]]:
        result: list[list[str]] = []
        for player_id in range(4):
            result.append([])
        for deal_count in [4, 4, 4, 1]:
            for _ in range(deal_count):
                for player_id in range(4):
                    result[player_id].append(self.draw_tile(player_id=player_id))
        for player_id in range(4):
            assert len(result[player_id]) == 13
        return result

    def get_dora_markers(self):
        result = []
        for i in range(self.kan_count + 1):
            result.append(self.wall[len(self.wall) - 5 - 2 * i])
        return result

    def get_ura_dora_markers(self):
        result = []
        for i in range(self.kan_count + 1):
            result.append(self.wall[len(self.wall) - 6 - 2 * i])
        return result

    def can_draw_tile(self, player_id: int) -> bool:
        return self.pointer + 14 + self.kan_count < len(self.wall)

    def can_declare_kan(self, player_id: int) -> bool:
        return self.kan_count < 4 and self.can_draw_tile(player_id=player_id)

    def draw_tile(self, player_id: int) -> str:
        result = self.wall[self.pointer]
        self.pointer += 1
        return result

    def draw_kan_tile(self, player_id: int) -> str:
        self.kan_count += 1
        return self.wall[len(self.wall) - self.kan_count]


class DuplicateWall(Wall):
    def __init__(self):
        self.start_hands: list[list[str]] = []
        self.walls: list[list[str]] = []
        self.dead_wall: list[str] = []
        self.pointers: list[int] = [0] * 4
        self.kan_count: int = 0

        all_tiles = get_all_tiles(shuffle=True)

        for player_id in range(4):
            self.start_hands.append([])
            for i in range(13):
                self.start_hands[player_id].append(all_tiles.pop())

        for player_id in range(4):
            self.start_hands.append([])
            for i in range(18):
                self.walls[player_id].append(all_tiles.pop())

        for i in range(12):
            self.dead_wall.append(all_tiles.pop())

        assert len(all_tiles) == 0

    def deal_start_hands(self) -> list[list[str]]:
        return self.start_hands

    def get_dora_markers(self) -> list[str]:
        result = []
        for i in range(self.kan_count + 1):
            result.append(self.dead_wall[len(self.dead_wall) - 3 - 2 * i])
        return result

    def get_ura_dora_markers(self) -> list[str]:
        result = []
        for i in range(self.kan_count + 1):
            result.append(self.dead_wall[len(self.dead_wall) - 4 - 2 * i])
        return result

    def can_draw_tile(self, player_id: int) -> bool:
        return self.pointers[player_id] < len(self.walls[player_id])

    def can_declare_kan(self, player_id: int) -> bool:
        return self.kan_count < 4 and self.can_draw_tile(player_id=player_id)

    def draw_tile(self, player_id: int) -> str:
        result = self.walls[player_id][self.pointers[player_id]]
        self.pointers[player_id] += 1
        return result

    def draw_kan_tile(self, player_id: int) -> str:
        self.kan_count += 1
        return self.draw_tile(player_id=player_id)
