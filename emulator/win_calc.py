from collections import defaultdict
from typing import Optional

from mahjong.constants import EAST, SOUTH, WEST, NORTH
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig, OptionalRules
from mahjong.hand_calculating.hand_response import HandResponse
from mahjong.meld import Meld

import mortal.mortal_helpers as mortal_helpers


# TODO: add ippatsu, chankan, rinshan, houtei, haitei, daburu riichi, etc.
def calculate_win(closed_hand: list[str],
                  open_sets: list[list[str]],
                  closed_kans: list[list[str]],
                  win_tile: str,
                  dora_markers: list[str],
                  ura_dora_markers: list[str],
                  player_wind: str,
                  round_wind: str,
                  is_riichi: bool,
                  is_tsumo: bool,
                  riichi_sticks: int,
                  honba: int,
                  ) -> tuple[int, int, Optional[int]]:
    hand_config = HandConfig(
        is_riichi=is_riichi,
        player_wind=[EAST, SOUTH, WEST, NORTH]["ESWN".index(player_wind)],
        round_wind=[EAST, SOUTH, WEST, NORTH]["ESWN".index(round_wind)],
        is_tsumo=is_tsumo,
        options=OptionalRules(
            has_aka_dora=True,
            has_open_tanyao=True,
            has_double_yakuman=False,
        ),
        tsumi_number=honba,
        kyoutaku_number=riichi_sticks,
    )

    tile_map: dict[str, list[int]] = defaultdict(list)
    for tile_136 in range(136):
        tile_map[mortal_helpers.convert_tile_to_mortal(tile_136=tile_136)].append(tile_136)

    tiles_136 = []
    for tile in closed_hand:
        tiles_136.append(tile_map[tile].pop())
    if is_tsumo:
        assert len(tiles_136) % 3 == 2
        win_tile_136 = tiles_136[-1]
    else:
        assert len(tiles_136) % 3 == 1
        win_tile_136 = tile_map[win_tile].pop()
        tiles_136.append(win_tile_136)
    dora_markers_136 = []
    for tile in dora_markers + ura_dora_markers:
        dora_markers_136.append(tile_map[tile].pop())

    melds = []
    for closed_kan in closed_kans:
        meld_tiles_136 = []
        for tile in closed_kan:
            meld_tiles_136.append(tile_map[tile].pop())
        melds.append(Meld(meld_type=Meld.KAN, tiles=meld_tiles_136, opened=False, called_tile=meld_tiles_136[0]))
    for open_set in open_sets:
        if len(open_set) == 3:
            if len(set(open_set)) < 3:
                meld_type = Meld.PON
            else:
                meld_type = Meld.CHI
        else:
            meld_type = Meld.KAN
        meld_tiles_136 = []
        for tile in open_set:
            meld_tiles_136.append(tile_map[tile].pop())
        melds.append(Meld(meld_type=meld_type, tiles=meld_tiles_136, opened=True, called_tile=meld_tiles_136[0]))

    for meld in melds:
        for tile_136 in meld.tiles:
            tiles_136.append(tile_136)

    hand_calculator = HandCalculator()
    hand_response: HandResponse = hand_calculator.estimate_hand_value(
        tiles=tiles_136,
        win_tile=win_tile_136,
        melds=melds,
        dora_indicators=dora_markers_136,
        config=hand_config,
    )
    return hand_response.han, hand_response.fu, (hand_response.cost or {}).get("total")
