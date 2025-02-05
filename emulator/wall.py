import random
from typing import Any

from mortal.mortal_helpers import TILES


def get_all_tiles(seed: Any) -> list[str]:
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
    random.seed(seed)
    random.shuffle(all_tiles)
    return all_tiles


class Wall:
    def get_wall_info(self) -> str:
        raise NotImplemented()

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
    def __init__(self, seed: Any):
        self.wall = get_all_tiles(seed=seed)

        self.kan_count: int = 0
        self.pointer: int = 0

    def get_wall_info(self) -> str:
        result = ""
        for tile in self.wall:
            if tile[0].isdigit():
                if tile.endswith("r"):
                    result += "0" + tile[1]
                else:
                    result += tile
            else:
                index = "ESWNPFC".index(tile)
                result += str(index) + "z"
        return result

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
    def __init__(self, seed: Any):
        self.start_hands: list[list[str]] = []
        self.walls: list[list[str]] = []
        self.dead_wall: list[str] = []
        self.pointers: list[int] = [0] * 4
        self.kan_count: int = 0

        all_tiles = get_all_tiles(seed=seed)

        for player_id in range(4):
            self.start_hands.append([])
            for i in range(13):
                self.start_hands[player_id].append(all_tiles.pop())

        for player_id in range(4):
            self.walls.append([])
            for i in range(18):
                self.walls[player_id].append(all_tiles.pop())

        for i in range(12):
            self.dead_wall.append(all_tiles.pop())

        assert len(all_tiles) == 0

    def get_wall_info(self) -> str:
        result = "\n"
        result += "East start hand: " + str(sorted(self.start_hands[0], key=lambda x: TILES.index(x))) + "\n"
        result += "South start hand: " + str(sorted(self.start_hands[1], key=lambda x: TILES.index(x))) + "\n"
        result += "West start hand: " + str(sorted(self.start_hands[2], key=lambda x: TILES.index(x))) + "\n"
        result += "North start hand: " + str(sorted(self.start_hands[3], key=lambda x: TILES.index(x))) + "\n"
        result += "East wall: " + str(self.walls[0]) + "\n"
        result += "South wall: " + str(self.walls[1]) + "\n"
        result += "West wall: " + str(self.walls[2]) + "\n"
        result += "North wall: " + str(self.walls[3]) + "\n"
        result += "Dora indicators: " + str(self.dead_wall[-3::-2]) + "\n"
        result += "Kan dora indicators: " + str(self.dead_wall[-4::-2]) + "\n"
        result += "Not used tiles:" + str(self.dead_wall[11:9:-1]) + "\n"
        return result

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
