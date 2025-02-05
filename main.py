import logging

from emulator.emulator import SingleRoundEmulator
from emulator.wall import StandardWall


def main():
    logging.basicConfig(level=logging.INFO)
    wall = StandardWall(seed=322)
    emulator = SingleRoundEmulator(
        round_wind="E",
        round_id=1,
        honba=0,
        riichi_sticks=0,
        dealer_id=0,
        scores=[25000] * 4,
        wall=wall,
    )
    emulator.process()


if __name__ == "__main__":
    main()
