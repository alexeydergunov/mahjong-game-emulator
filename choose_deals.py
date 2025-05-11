import logging
import os
import shutil
from collections import defaultdict
from random import Random


def main():
    logging.basicConfig(level=logging.INFO, format="")

    deal_map: dict[str, int] = defaultdict(int)  # filename -> number of unique outcomes
    with open("_infinite_log.txt", "r") as f:
        filename = None
        for line in f:
            line = line.strip()
            if "Duplicate wall picture path" in line:
                filename = line[line.rindex("/") + 1:]
            elif "->" in line:
                assert filename is not None
                deal_map[filename] += 1

    logging.info("Parsed %d deals", len(deal_map))
    for i, (filename, count) in enumerate(sorted(deal_map.items(), key=lambda t: (-t[1], t[0]))):
        logging.info("%d. Filename %s -> %d unique outcomes", i, filename, count)

    chosen_filenames = []
    for filename, count in deal_map.items():
        if count >= 5:
            chosen_filenames.append(filename)
    assert len(chosen_filenames) >= 96
    r = Random("2025-05-11 15:30")  # fixed seed
    r.shuffle(chosen_filenames)
    chosen_filenames = chosen_filenames[:96]

    logging.info("================================================================================")
    archive_directory = "_chosen_deals"
    if os.path.exists(archive_directory):
        shutil.rmtree(archive_directory)
    os.mkdir(archive_directory)
    for i, filename in enumerate(chosen_filenames):
        game = i // 12 + 1
        deal = i % 12 + 1
        logging.info("Game %d, deal %d -> %s, %d outcomes",
                     game, deal, filename, deal_map[filename])
        src_file = os.path.join("wall_pictures", filename)
        dst_file = os.path.join(archive_directory, f"{game}_{deal:02d}_{filename}")
        shutil.copy(src_file, dst_file)
    logging.info("Creating archive...")
    shutil.make_archive("_chosen_deals_archive", "zip", archive_directory)


if __name__ == "__main__":
    main()
