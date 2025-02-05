from typing import Any

FIVE_RED_MAN = 16
FIVE_RED_PIN = 52
FIVE_RED_SOU = 88

TILES = [
    "1m", "2m", "3m", "4m", "5m", "5mr", "6m", "7m", "8m", "9m",  # "5[m,p,s]r" is a red five
    "1p", "2p", "3p", "4p", "5p", "5pr", "6p", "7p", "8p", "9p",
    "1s", "2s", "3s", "4s", "5s", "5sr", "6s", "7s", "8s", "9s",
    "E", "S", "W", "N",
    "P", "F", "C",  # white, green, red
]

MortalEvent = dict[str, Any]


def convert_tile_to_mortal(tile_136: int) -> str:
    if tile_136 == FIVE_RED_MAN:
        return "5mr"
    if tile_136 == FIVE_RED_PIN:
        return "5pr"
    if tile_136 == FIVE_RED_SOU:
        return "5sr"
    if tile_136 < 36:
        return str(tile_136 // 4 + 1) + "m"
    if tile_136 < 72:
        return str((tile_136 - 36) // 4 + 1) + "p"
    if tile_136 < 108:
        return str((tile_136 - 72) // 4 + 1) + "s"
    return "ESWNPFC"[(tile_136 - 108) // 4]


def start_game() -> MortalEvent:
    return {"type": "start_game"}


def start_hand(round_wind: str, dora_marker: str, round_id: int, honba: int, riichi_sticks: int,
               dealer_id: int, scores: list[int], start_hands: list[list[str]]) -> MortalEvent:
    assert round_wind in {"E", "S", "W"}
    assert 1 <= round_id <= 4
    assert honba >= 0
    assert riichi_sticks >= 0
    assert 0 <= dealer_id <= 3
    assert len(scores) == 4
    assert len(start_hands) == 4
    for hand in start_hands:
        assert len(hand) == 13
        for tile in hand:
            assert tile == "?" or tile in TILES

    return {
        "type": "start_kyoku",
        "bakaze": round_wind,
        "dora_marker": dora_marker,
        "kyoku": round_id,
        "honba": honba,
        "kyotaku": riichi_sticks,
        "oya": dealer_id,
        "scores": scores,
        "tehais": start_hands,
    }


def draw_tile(player_id: int, tile: str) -> MortalEvent:
    assert 0 <= player_id <= 3
    assert tile in TILES
    return {"type": "tsumo", "actor": player_id, "pai": tile}


def draw_unknown_tile(player_id: int) -> MortalEvent:
    assert 0 <= player_id <= 3
    return {"type": "tsumo", "actor": player_id, "pai": "?"}


def discard_tile(player_id: int, tile: str, tsumogiri: bool) -> MortalEvent:
    assert 0 <= player_id <= 3
    assert tile in TILES
    return {"type": "dahai", "actor": player_id, "pai": tile, "tsumogiri": tsumogiri}


def pon(player_id: int, from_whom: int, tile: str, pon_tiles: list[str]) -> MortalEvent:
    assert 0 <= player_id <= 3
    assert 0 <= from_whom <= 3
    assert from_whom != player_id
    assert tile in TILES
    assert len(pon_tiles) == 2
    assert all(t in TILES for t in pon_tiles)
    assert len(set(pon_tiles) | {tile}) <= 2  # can be red five
    return {"type": "pon", "actor": player_id, "target": from_whom, "pai": tile, "consumed": pon_tiles}


def chi(player_id: int, tile: str, chi_tiles: list[str]) -> MortalEvent:
    assert 0 <= player_id <= 3
    assert tile in TILES
    assert len(chi_tiles) == 2
    assert all(t in TILES for t in chi_tiles)
    from_whom = player_id - 1
    if from_whom < 0:
        from_whom += 4
    return {"type": "chi", "actor": player_id, "target": from_whom, "pai": tile, "consumed": chi_tiles}


def declare_riichi(player_id: int) -> MortalEvent:
    assert 0 <= player_id <= 3
    return {"type": "reach", "actor": player_id}


def successful_riichi(player_id: int) -> MortalEvent:
    assert 0 <= player_id <= 3
    return {"type": "reach_accepted", "actor": player_id}


def tsumo(player_id: int) -> MortalEvent:
    assert 0 <= player_id <= 3
    return {"type": "hora", "actor": player_id, "target": player_id}


def ron(winner_id: int, loser_id: int) -> MortalEvent:
    assert 0 <= winner_id <= 3
    assert 0 <= loser_id <= 3
    assert winner_id != loser_id
    return {"type": "hora", "actor": winner_id, "target": loser_id}


def redeal() -> MortalEvent:
    return {"type": "ryukyoku"}


def skip() -> MortalEvent:
    return {"type": "none"}


def closed_kan(player_id: int, tile: str) -> MortalEvent:
    assert 0 <= player_id <= 3
    assert tile in TILES
    consumed = [tile, tile, tile, tile]
    if tile.startswith("5"):
        if tile.endswith("r"):
            consumed = [tile[:-1], tile[:-1], tile[:-1], tile]
        else:
            consumed = [tile, tile, tile, tile + "r"]
    assert all(t in TILES for t in consumed)
    return {"type": "ankan", "actor": player_id, "consumed": consumed}


def added_kan(player_id: int, tile: str) -> MortalEvent:
    assert 0 <= player_id <= 3
    assert tile in TILES
    if tile.startswith("5"):
        if tile.endswith("r"):
            consumed = [tile[:-1], tile[:-1], tile[:-1]]
        else:
            consumed = [tile, tile, tile + "r"]
    else:
        consumed = [tile, tile, tile]
    assert all(t in TILES for t in consumed)
    return {"type": "kakan", "actor": player_id, "pai": tile, "consumed": consumed}


def open_kan(player_id: int, from_whom: int, tile: str) -> MortalEvent:
    assert 0 <= player_id <= 3
    assert 0 <= from_whom <= 3
    assert player_id != from_whom
    assert tile in TILES
    if tile.startswith("5"):
        if tile.endswith("r"):
            consumed = [tile[:-1], tile[:-1], tile[:-1]]
        else:
            consumed = [tile, tile, tile + "r"]
    else:
        consumed = [tile, tile, tile]
    assert all(t in TILES for t in consumed)
    return {"type": "daiminkan", "actor": player_id, "target": from_whom, "pai": tile, "consumed": consumed}


def add_dora_marker(tile: str) -> MortalEvent:
    assert tile in TILES
    return {"type": "dora", "dora_marker": tile}
