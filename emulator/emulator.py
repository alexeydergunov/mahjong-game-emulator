import copy
import logging
import os
from typing import Any

import mortal.mortal_helpers as mortal_helpers
from emulator import win_calc
from emulator.wall import Wall
from mortal.mortal_bot import MortalBot
from mortal.mortal_helpers import MortalEvent
from mortal.mortal_helpers import TILES


class SingleRoundEmulator:
    def __init__(self, round_wind: str, round_id: int, honba: int, riichi_sticks: int,
                 dealer_id: int, scores: list[int], wall: Wall, player_pth_files: list[str]):
        assert round_wind in {"E", "S", "W"}
        assert 1 <= round_id <= 4
        assert honba >= 0
        assert riichi_sticks >= 0
        assert 0 <= dealer_id <= 3
        assert len(scores) == 4
        self.round_wind = round_wind
        self.round_id = round_id
        self.honba = honba
        self.riichi_sticks = riichi_sticks
        self.dealer_id = dealer_id
        self.scores = scores

        assert len(player_pth_files) == 4
        self.player_pth_files = player_pth_files
        self.players: list[MortalBot] = []
        self.wall = wall
        self.events: list[MortalEvent] = []
        self.player_events: list[list[MortalEvent]] = [[], [], [], []]

        self.player_closed_hands: list[list[str]] = [[], [], [], []]
        self.player_open_sets: list[list[list[str]]] = [[], [], [], []]
        self.player_closed_kans: list[list[list[str]]] = [[], [], [], []]
        self.successful_riichi_players: set[int] = set()

    def init_players(self):
        for player_id, pth_file in enumerate(self.player_pth_files):
            logging.debug("Initializing player %d with file %s", player_id, os.path.basename(pth_file))
            self.players.append(MortalBot(player_id=player_id, pth_file=pth_file))

    def get_public_events(self, player_id: int) -> list[MortalEvent]:
        # add missing events since last caching
        events_to_react = []
        for ei in range(len(self.player_events[player_id]), len(self.events)):
            event = copy.deepcopy(self.events[ei])
            if event["type"] == "start_kyoku":
                for i in range(4):
                    if i != player_id:
                        event["tehais"][i] = ["?"] * 13
            elif event["type"] == "tsumo":
                if event["actor"] != player_id:
                    event["pai"] = "?"
            events_to_react.append(event)
        self.player_events[player_id].extend(events_to_react)
        return events_to_react

    def get_seat(self, player_id: int) -> str:
        return "ESWN"[(player_id - self.dealer_id + 4) % 4]

    def get_win_tile(self, is_tsumo: bool) -> str:
        for event in reversed(self.events):
            if is_tsumo:
                if event["type"] == "tsumo":
                    return event["pai"]
            else:
                if event["type"] in {"dahai", "kakan"}:
                    return event["pai"]
        raise Exception("Can't find win tile")

    def process(self) -> dict[str, Any]:
        start_hands = self.wall.deal_start_hands()
        dora_marker = self.wall.get_dora_markers()[-1]
        self.events.append(mortal_helpers.start_hand(
            round_wind=self.round_wind,
            dora_marker=dora_marker,
            round_id=self.round_id,
            honba=self.honba,
            riichi_sticks=self.riichi_sticks,
            dealer_id=self.dealer_id,
            scores=self.scores,
            start_hands=start_hands
        ))
        for player_id in range(4):
            self.player_closed_hands[player_id].extend(start_hands[player_id])
        logging.debug("Round started, dora marker %s", dora_marker)
        logging.debug("East: %s", sorted(start_hands[self.dealer_id], key=lambda x: TILES.index(x)))
        logging.debug("South: %s", sorted(start_hands[(self.dealer_id + 1) % 4], key=lambda x: TILES.index(x)))
        logging.debug("West: %s", sorted(start_hands[(self.dealer_id + 2) % 4], key=lambda x: TILES.index(x)))
        logging.debug("North: %s", sorted(start_hands[(self.dealer_id + 3) % 4], key=lambda x: TILES.index(x)))
        if len(self.players) == 0:
            self.init_players()

        turn = 0
        while True:
            logging.debug("Current hands:")
            for player_id in range(4):
                logging.debug("Hand of player %d (%s): closed hands %s, open sets %s, closed kans %s",
                              player_id, self.get_seat(player_id),
                              sorted(self.player_closed_hands[player_id], key=lambda x: TILES.index(x)),
                              self.player_open_sets[player_id],
                              self.player_closed_kans[player_id],
                              )

            actions = []
            wall_ended = False
            for player_id in range(4):
                try:
                    action = self.players[player_id].react_one(self.get_public_events(player_id=player_id),
                                                               with_meta=False,
                                                               with_nulls=True)
                    actions.append(action)
                except RuntimeError as e:
                    if "rule violation: attempt to tsumo from exhausted yama" in str(e):
                        wall_ended = True

            if wall_ended:
                logging.info("Round (possibly) ended with a draw on turn %.2f, the wall supported by Mortal has ended, "
                             "but probably duplicate wall has some more tiles", turn / 4.0)
                return {"result": "draw"}

            win_actions = []
            for action in actions:
                if action["type"] == "hora":
                    win_actions.append(action)

            if len(win_actions) > 0:
                result = {"result": "win", "wins": []}
                for action in win_actions:
                    player_id = int(action["actor"])
                    target = int(action["target"])
                    is_tsumo: bool = player_id == target
                    is_riichi: bool = player_id in self.successful_riichi_players
                    dora_markers = self.wall.get_dora_markers()
                    ura_dora_markers = self.wall.get_ura_dora_markers() if is_riichi else []
                    han, fu, cost = win_calc.calculate_win(
                        closed_hand=sorted(self.player_closed_hands[player_id], key=lambda x: TILES.index(x)),
                        open_sets=self.player_open_sets[player_id],
                        closed_kans=self.player_closed_kans[player_id],
                        win_tile=self.get_win_tile(is_tsumo=is_tsumo),
                        dora_markers=dora_markers,
                        ura_dora_markers=ura_dora_markers,
                        player_wind=self.get_seat(player_id),
                        round_wind=self.round_wind,
                        is_riichi=is_riichi,
                        is_tsumo=is_tsumo,
                        riichi_sticks=self.riichi_sticks + len(self.successful_riichi_players - {player_id}),
                        honba=self.honba,
                    )
                    logging.info("Round ended on turn %.2f, player %d (%s) "
                                 "declared win with %d han, %d fu: %s",
                                 turn / 4.0, player_id, self.get_seat(player_id), han, fu, action)
                    win_desc = {
                        "win_type": "tsumo" if is_tsumo else "ron",
                        "winner": self.get_seat(player_id),
                        "han": han,
                        "fu": fu,
                    }
                    if not is_tsumo:
                        win_desc["loser"] = self.get_seat(target)
                    result["wins"].append(win_desc)
                return result

            valid_actions_count = 0
            for player_id in range(4):
                if actions[player_id] == self.events[-1]:
                    actions[player_id] = {"type": "none"}
                if actions[player_id] != {"type": "none"}:
                    valid_actions_count += 1

            if valid_actions_count == 0:
                # time to take tile
                kan_player_id = None
                kan_type = None
                riichi_player_id = None
                last_discard_player_id = None
                for event in reversed(self.events):
                    if event["type"] in {"ankan", "kakan", "daiminkan"}:
                        kan_player_id = event["actor"]
                        kan_type = event["type"]
                        break
                    if event["type"] == "reach":
                        riichi_player_id = event["actor"]
                        break
                    if event["type"] == "dahai":
                        last_discard_player_id = event["actor"]
                        break

                if kan_player_id is not None:
                    if not self.wall.can_declare_kan(player_id=kan_player_id):
                        logging.info("Round (possibly) ended with a draw on turn %.2f, "
                                     "duplicate wall of a player has ended, but Mortal wants kan", turn / 4.0)
                        return {"result": "draw"}
                    tile = self.wall.draw_kan_tile(player_id=kan_player_id)
                    logging.debug("Player %d (%s) drew kan replacement tile %s",
                                  kan_player_id, self.get_seat(kan_player_id), tile)
                    if kan_type == "ankan":
                        dora_marker = self.wall.get_dora_markers()[-1]
                        logging.debug("New dora marker: %s", dora_marker)
                        self.events.append(mortal_helpers.add_dora_marker(tile=dora_marker))
                    self.events.append(mortal_helpers.draw_tile(player_id=kan_player_id, tile=tile))
                    self.player_closed_hands[kan_player_id].append(tile)
                    turn += 1
                else:
                    if riichi_player_id is not None:
                        logging.debug("Successful riichi by player %d (%s)",
                                      riichi_player_id, self.get_seat(riichi_player_id))
                        current_player_id = (riichi_player_id + 1) % 4
                    elif last_discard_player_id is not None:
                        current_player_id = (last_discard_player_id + 1) % 4
                    else:
                        current_player_id = self.dealer_id  # first turn only

                    if not self.wall.can_draw_tile(player_id=current_player_id):
                        logging.info("Round ended by draw on turn %.2f: player %d (%s) can't draw tile",
                                     turn / 4.0, current_player_id, self.get_seat(current_player_id))
                        return {"result": "draw"}

                    if len(self.events) >= 2 and self.events[-2]["type"] == "reach":
                        riichi_player_id = self.events[-2]["actor"]
                        assert self.events[-1]["type"] == "dahai"
                        assert self.events[-1]["actor"] == riichi_player_id
                        self.events.append(mortal_helpers.successful_riichi(player_id=riichi_player_id))
                        self.successful_riichi_players.add(riichi_player_id)

                    tile = self.wall.draw_tile(player_id=current_player_id)
                    logging.debug("Player %d (%s) drew tile %s",
                                  current_player_id, self.get_seat(current_player_id), tile)
                    self.events.append(mortal_helpers.draw_tile(player_id=current_player_id, tile=tile))
                    self.player_closed_hands[current_player_id].append(tile)
                    turn += 1
                continue

            redeal_actions = []
            for action in actions:
                if action["type"] == "ryukyoku":
                    redeal_actions.append(action)
            assert len(redeal_actions) <= 1
            if len(redeal_actions) == 1:
                logging.info("Round ended with an abortive draw")
                return {"result": "draw"}

            kan_and_pon_actions = []
            for action in actions:
                if action["type"] in {"ankan", "kakan", "daiminkan", "pon"}:
                    kan_and_pon_actions.append(action)
            assert len(kan_and_pon_actions) <= 1
            if len(kan_and_pon_actions) == 1:
                call_action = kan_and_pon_actions[0]
                player_id = int(call_action["actor"])
                logging.debug("Called %s by player %d (%s)", call_action["type"],
                              player_id, self.get_seat(player_id))
                self.events.append(call_action)
                if call_action["type"] == "pon":
                    # noinspection PyTypeChecker
                    kan_tiles: list[str] = call_action["consumed"]
                    for tile in kan_tiles:
                        self.player_closed_hands[player_id].remove(tile)
                    self.player_open_sets[player_id].append([call_action["pai"]] + kan_tiles)
                elif call_action["type"] == "daiminkan":
                    # noinspection PyTypeChecker
                    kan_tiles: list[str] = call_action["consumed"]
                    for tile in kan_tiles:
                        self.player_closed_hands[player_id].remove(tile)
                    self.player_open_sets[player_id].append([call_action["pai"]] + kan_tiles)
                elif call_action["type"] == "ankan":
                    # noinspection PyTypeChecker
                    kan_tiles: list[str] = call_action["consumed"]
                    for tile in kan_tiles:
                        self.player_closed_hands[player_id].remove(tile)
                    self.player_closed_kans[player_id].append(kan_tiles)
                elif call_action["type"] == "kakan":
                    # noinspection PyTypeChecker
                    kan_tiles: list[str] = call_action["consumed"]
                    self.player_closed_hands[player_id].remove(call_action["pai"])
                    for i in range(len(self.player_open_sets[player_id])):
                        if sorted(self.player_open_sets[player_id][i]) == sorted(kan_tiles):
                            self.player_open_sets[player_id][i].insert(0, call_action["pai"])
                continue

            chi_actions = []
            for action in actions:
                if action["type"] == "chi":
                    chi_actions.append(action)
            assert len(chi_actions) <= 1
            if len(chi_actions) == 1:
                player_id = int(chi_actions[0]["actor"])
                logging.debug("Called chi by player %d (%s)",
                              player_id, self.get_seat(player_id))
                self.events.append(chi_actions[0])
                # noinspection PyTypeChecker
                chi_tiles: list[str] = chi_actions[0]["consumed"]
                for tile in chi_tiles:
                    self.player_closed_hands[player_id].remove(tile)
                self.player_open_sets[player_id].append([chi_actions[0]["pai"]] + chi_tiles)
                continue

            discard_actions = []
            for action in actions:
                if action["type"] == "dahai":
                    discard_actions.append(action)
            assert len(discard_actions) <= 1
            if len(discard_actions) == 1:
                player_id = int(discard_actions[0]["actor"])
                logging.debug("Discarded tile %s by player %d (%s)", discard_actions[0]["pai"],
                              player_id, self.get_seat(player_id))
                self.events.append(discard_actions[0])
                self.player_closed_hands[player_id].remove(discard_actions[0]["pai"])
                if len(self.events) > 3 and self.events[-3]["type"] in {"daiminkan", "kakan"}:
                    assert self.events[-3]["actor"] == player_id
                    assert self.events[-2]["type"] == "tsumo"
                    assert self.events[-2]["actor"] == player_id
                    dora_marker = self.wall.get_dora_markers()[-1]
                    logging.debug("New dora marker: %s", dora_marker)
                    self.events.append(mortal_helpers.add_dora_marker(tile=dora_marker))
                continue

            riichi_actions = []
            for action in actions:
                if action["type"] == "reach":
                    riichi_actions.append(action)
            assert len(riichi_actions) <= 1
            if len(riichi_actions) == 1:
                player_id = int(riichi_actions[0]["actor"])
                logging.debug("Declared riichi by player %d (%s)",
                              player_id, self.get_seat(player_id))
                self.events.append(riichi_actions[0])
                continue

            raise Exception("Can't find a valid action")

        raise Exception("Process cycle didn't end correctly")
