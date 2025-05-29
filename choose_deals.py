import logging
import os
import shutil
import time
from collections import defaultdict
from random import Random


def choose_random_deals_1(deal_map: dict[str, list[str]], count: int, r: Random) -> list[str]:
    chosen_filenames = []
    for filename, outcomes_list in deal_map.items():
        if len(outcomes_list) >= 5:
            chosen_filenames.append(filename)
    assert len(chosen_filenames) >= count
    r.shuffle(chosen_filenames)
    chosen_filenames = chosen_filenames[:count]
    return chosen_filenames


def choose_random_deals_2(deal_map: dict[str, list[str]], count: int, r: Random) -> list[str]:
    arr = []
    for filename, outcomes_list in deal_map.items():
        if len(outcomes_list) >= 3:
            for _ in range(len(outcomes_list)):
                arr.append(filename)
    assert len(arr) >= count
    chosen_filenames = []
    while len(chosen_filenames) < count:
        filename = r.choice(arr)
        chosen_filenames.append(filename)
        arr = [x for x in arr if x != filename]
    return chosen_filenames


def main():
    logging.basicConfig(level=logging.INFO, format="")

    deal_map: dict[str, list[str]] = defaultdict(list)  # filename -> list of unique outcomes
    with open("_infinite_log.txt", "r") as f:
        filename = None
        for line in f:
            line = line.strip()
            if "Duplicate wall picture path" in line:
                filename = line[line.rindex("/") + 1:]
            elif "->" in line:
                assert filename is not None
                deal_map[filename].append(line[line.index("("):])

    logging.info("Parsed %d deals", len(deal_map))
    for i, (filename, outcomes_list) in enumerate(sorted(deal_map.items(), key=lambda t: (-len(t[1]), t[0]))):
        logging.info("%d. Filename %s -> %d unique outcomes", i, filename, len(outcomes_list))

    seed = str(time.time())  # 1748532061.7101543
    logging.info("Random seed: '%s'", seed)
    r = Random(seed)
    chosen_filenames = choose_random_deals_2(deal_map=deal_map, count=12, r=r)

    logging.info("================================================================================")
    for i, filename in enumerate(chosen_filenames):
        game = i // 12 + 1
        deal = i % 12 + 1
        logging.info("Game %d, deal %d -> %s, %d outcomes:",
                     game, deal, filename, len(deal_map[filename]))
        for outcome in deal_map[filename]:
            logging.info("  %s", outcome)

    archive_directory = "_chosen_deals"
    if os.path.exists(archive_directory):
        shutil.rmtree(archive_directory)
    os.mkdir(archive_directory)
    for i, filename in enumerate(chosen_filenames):
        game = i // 12 + 1
        deal = i % 12 + 1
        src_file = os.path.join("wall_pictures", filename)
        dst_file = os.path.join(archive_directory, f"{game}_{deal:02d}_{filename}")
        shutil.copy(src_file, dst_file)

    archive_name = "_chosen_deals_archive.zip"
    logging.info("Creating archive...")
    if os.path.exists(archive_name):
        os.remove(archive_name)
    shutil.make_archive(archive_name.split(".")[0], "zip", archive_directory)
    logging.info("Archive created: %s bytes", os.path.getsize(archive_name))


if __name__ == "__main__":
    main()
