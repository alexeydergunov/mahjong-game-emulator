import itertools
import logging
import os
from collections import defaultdict
from random import SystemRandom, Random
from typing import Optional

from drawing import drawing
from emulator.emulator import SingleRoundEmulator
# noinspection PyUnresolvedReferences
from emulator.wall import StandardWall, DuplicateWall, get_all_tiles


def main():
    logging.basicConfig(level=logging.INFO)

    pth_files_dir = os.path.join(os.path.dirname(__file__), "mortal/mortal_lib/pth")
    pth_files = [
        os.path.join(pth_files_dir, "bot_20240110_best_94dd_64e8.pth"),
        os.path.join(pth_files_dir, "bot_20240110_mortal_1280_872a.pth"),
        os.path.join(pth_files_dir, "bot_20240308_best_0a88_6563.pth"),
        os.path.join(pth_files_dir, "bot_20240308_mortal_baad_d6a2.pth"),
    ]
    logging.info("Pth files:")
    for pth_file in pth_files:
        logging.info("%s", pth_file)

    seed = None
    logging.info("Seed: %s", seed)
    if seed is None:
        r = SystemRandom()
    else:
        r = Random(seed)
    shuffled_tiles = get_all_tiles()
    r.shuffle(shuffled_tiles)
    logging.info("Shuffled tiles: %s", shuffled_tiles)

    result_counts: dict[tuple[str, Optional[str], Optional[str]], int] = defaultdict(int)
    for i, p in enumerate(itertools.permutations(range(4))):
        wall = DuplicateWall(shuffled_tiles=shuffled_tiles)
        if i == 0:
            logging.info("Wall: %s", wall.get_wall_info())
            if isinstance(wall, DuplicateWall):
                drawing.draw_duplicate_wall(wall=wall, dead_wall_in_one_line=True, overwrite_file=True)
        logging.info("Testing model permutation %d / 24", i + 1)
        emulator = SingleRoundEmulator(
            round_wind="E",
            round_id=1,
            honba=0,
            riichi_sticks=0,
            dealer_id=0,
            scores=[25000] * 4,
            wall=wall,
            player_pth_files=[pth_files[p[0]], pth_files[p[1]], pth_files[p[2]], pth_files[p[3]]],
        )
        emulation_result = emulator.process()
        if emulation_result["result"] == "draw":
            result_counts[("draw", None, None)] += 1
        else:
            assert emulation_result["result"] == "win"
            for win_desc in emulation_result["wins"]:
                result_counts[(win_desc["win_type"], win_desc["winner"], win_desc.get("loser"))] += 1

    logging.info("Round result counts:")
    for result, count in sorted(result_counts.items(), key=lambda t: (t[1], t[0]), reverse=True):
        logging.info("%s -> %d", result, count)


if __name__ == "__main__":
    main()
