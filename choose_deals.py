import logging
from collections import defaultdict


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


if __name__ == "__main__":
    main()
