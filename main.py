import itertools
import logging
import os

from emulator.emulator import SingleRoundEmulator
# noinspection PyUnresolvedReferences
from emulator.wall import StandardWall, DuplicateWall


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

    seed = 330
    logging.info("Seed: %s", seed)

    for i, p in enumerate(itertools.permutations(range(4))):
        wall = DuplicateWall(seed=seed)
        if i == 0:
            logging.info("Wall: %s", wall.get_wall_info())
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
        emulator.process()


if __name__ == "__main__":
    main()
