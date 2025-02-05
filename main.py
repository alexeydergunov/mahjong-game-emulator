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

    wall = StandardWall(seed=329)
    emulator = SingleRoundEmulator(
        round_wind="E",
        round_id=1,
        honba=0,
        riichi_sticks=0,
        dealer_id=0,
        scores=[25000] * 4,
        wall=wall,
        player_pth_files=pth_files,
    )
    emulator.process()


if __name__ == "__main__":
    main()
