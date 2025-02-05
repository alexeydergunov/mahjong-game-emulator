import copy
import logging
import os

import mortal.mortal_helpers as mortal_helpers
from emulator.wall import Wall
from mortal.mortal_bot import MortalBot
from mortal.mortal_helpers import MortalEvent


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
        return "ESWN"[(self.dealer_id + player_id) % 4]

    def process(self):
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
        logging.info("Round started")
        logging.debug("East: %s", start_hands[self.dealer_id])
        logging.debug("South: %s", start_hands[(self.dealer_id + 1) % 4])
        logging.debug("West: %s", start_hands[(self.dealer_id + 2) % 4])
        logging.debug("North: %s", start_hands[(self.dealer_id + 3) % 4])

        if len(self.players) == 0:
            self.init_players()

        turn = 0
        while True:
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
                logging.info("Round (possibly) ended with a draw, the wall supported by Mortal has ended, "
                             "but probably duplicate wall has some more tiles")
                break

            win_actions = []
            for action in actions:
                if action["type"] == "hora":
                    win_actions.append(action)

            if len(win_actions) > 0:
                for action in win_actions:
                    player_id = int(action["actor"])
                    logging.info("Round ended on turn %.2f, player %d (%s) declared win: %s",
                                 turn / 4.0, player_id, self.get_seat(player_id), action)
                break

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
                    assert self.wall.can_declare_kan(player_id=kan_player_id)
                    tile = self.wall.draw_kan_tile(player_id=kan_player_id)
                    logging.debug("Player %d (%s) drew kan replacement tile %s",
                                  kan_player_id, self.get_seat(kan_player_id), tile)
                    self.events.append(mortal_helpers.draw_tile(player_id=kan_player_id, tile=tile))
                    turn += 1
                    if kan_type == "ankan":
                        dora_marker = self.wall.get_dora_markers()[-1]
                        logging.debug("New dora marker: %s", dora_marker)
                        self.events.append(mortal_helpers.add_dora_marker(tile=dora_marker))
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
                        logging.info("Round ended by draw: player %d (%s) can't draw tile",
                                     current_player_id, self.get_seat(current_player_id))
                        break

                    if len(self.events) >= 2 and self.events[-2]["type"] == "reach":
                        riichi_player_id = self.events[-2]["actor"]
                        assert self.events[-1]["type"] == "dahai"
                        assert self.events[-1]["actor"] == riichi_player_id
                        self.events.append(mortal_helpers.successful_riichi(player_id=riichi_player_id))

                    tile = self.wall.draw_tile(player_id=current_player_id)
                    logging.debug("Player %d (%s) drew tile %s",
                                  current_player_id, self.get_seat(current_player_id), tile)
                    self.events.append(mortal_helpers.draw_tile(player_id=current_player_id, tile=tile))
                    turn += 1
                continue

            redeal_actions = []
            for action in actions:
                if action["type"] == "ryukyoku":
                    redeal_actions.append(action)
            assert len(redeal_actions) <= 1
            if len(redeal_actions) == 1:
                logging.info("Round ended with an abortive draw")
                break

            kan_and_pon_actions = []
            for action in actions:
                if action["type"] in {"ankan", "kakan", "daiminkan", "pon"}:
                    kan_and_pon_actions.append(action)
            assert len(kan_and_pon_actions) <= 1
            if len(kan_and_pon_actions) == 1:
                player_id = int(kan_and_pon_actions[0]["actor"])
                logging.debug("Called %s by player %d (%s)", kan_and_pon_actions[0]["type"],
                              player_id, self.get_seat(player_id))
                self.events.append(kan_and_pon_actions[0])
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
                if len(self.events) > 3 and self.events[-3]["type"] in {"daiminkan", "kakan"}:
                    assert self.events[-3]["actor"] == player_id
                    assert self.events[-2]["type"] == "tsumo"
                    assert self.events[-2]["actor"] == player_id
                    dora_marker = self.wall.get_dora_markers()[-1]
                    logging.info("New dora marker: %s", dora_marker)
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
