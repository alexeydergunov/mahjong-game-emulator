import copy
import logging
import os

import mortal.mortal_helpers as mortal_helpers
from emulator.wall import Wall
from mortal.mortal_bot import MortalBot
from mortal.mortal_helpers import MortalEvent


class SingleRoundEmulator:
    def __init__(self, round_wind: str, round_id: int, honba: int, riichi_sticks: int,
                 dealer_id: int, scores: list[int], wall: Wall):
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

        self.players: list[MortalBot] = []
        self.wall = wall
        self.events: list[MortalEvent] = []

    def init_players(self):
        pth_file = os.path.join(os.path.dirname(__file__), "../mortal/mortal_lib/mortal.pth")
        for i in range(4):
            self.players.append(MortalBot(player_id=i, pth_file=pth_file))

    def get_public_events(self, player_id: int) -> list[MortalEvent]:
        events = copy.deepcopy(self.events)
        for event in events:
            if event["type"] == "start_kyoku":
                for i in range(4):
                    if i != player_id:
                        event["tehais"][i] = ["?"] * 13
            elif event["type"] == "tsumo":
                if event["actor"] != player_id:
                    event["pai"] = "?"
        return events

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
        logging.info("East: %s", start_hands[self.dealer_id])
        logging.info("South: %s", start_hands[(self.dealer_id + 1) % 4])
        logging.info("West: %s", start_hands[(self.dealer_id + 2) % 4])
        logging.info("North: %s", start_hands[(self.dealer_id + 3) % 4])

        if len(self.players) == 0:
            self.init_players()

        while True:
            actions = []
            for player_id in range(4):
                action = self.players[player_id].react_one(self.get_public_events(player_id=player_id), with_meta=False, with_nulls=True)
                actions.append(action)

            win_actions = []
            for action in actions:
                if action["type"] == "hora":
                    win_actions.append(action)

            if len(win_actions) > 0:
                for action in win_actions:
                    player_id = action["actor"]
                    logging.info("Player %d (%s) declared win: %s", player_id, self.get_seat(player_id), action)
                logging.info("Round ended by win")
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
                riichi_player_id = None
                last_discard_player_id = None
                for event in reversed(self.events):
                    if event["type"] in {"ankan", "kakan", "daiminkan"}:
                        kan_player_id = event["actor"]
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
                    dora_marker = self.wall.get_dora_markers()[-1]
                    logging.info("Player %d (%s) drew kan replacement tile %s, new dora marker %s",
                                 kan_player_id, self.get_seat(kan_player_id), tile, dora_marker)
                    self.events.append(mortal_helpers.draw_tile(player_id=kan_player_id, tile=tile))
                    self.events.append(mortal_helpers.add_dora_marker(tile=dora_marker))
                else:
                    if riichi_player_id is not None:
                        logging.info("Successful riichi by player %d (%s)",
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
                    logging.info("Player %d (%s) drew tile %s",
                                 current_player_id, self.get_seat(current_player_id), tile)
                    self.events.append(mortal_helpers.draw_tile(player_id=current_player_id, tile=tile))
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
                logging.info("Called %s by player %d (%s)", kan_and_pon_actions[0]["type"],
                             kan_and_pon_actions[0]["actor"], self.get_seat(kan_and_pon_actions[0]["actor"]))
                self.events.append(kan_and_pon_actions[0])
                continue

            chi_actions = []
            for action in actions:
                if action["type"] == "chi":
                    chi_actions.append(action)
            assert len(chi_actions) <= 1
            if len(chi_actions) == 1:
                logging.info("Called chi by player %d (%s)",
                             chi_actions[0]["actor"], self.get_seat(chi_actions[0]["actor"]))
                self.events.append(chi_actions[0])
                continue

            discard_actions = []
            for action in actions:
                if action["type"] == "dahai":
                    discard_actions.append(action)
            assert len(discard_actions) <= 1
            if len(discard_actions) == 1:
                logging.info("Discarded tile %s by player %d (%s)", discard_actions[0]["pai"],
                             discard_actions[0]["actor"], self.get_seat(discard_actions[0]["actor"]))
                self.events.append(discard_actions[0])
                continue

            riichi_actions = []
            for action in actions:
                if action["type"] == "reach":
                    riichi_actions.append(action)
            assert len(riichi_actions) <= 1
            if len(riichi_actions) == 1:
                logging.info("Declared riichi by player %d (%s)",
                             riichi_actions[0]["actor"], self.get_seat(riichi_actions[0]["actor"]))
                self.events.append(riichi_actions[0])
                continue

            raise Exception("Can't find a valid action")
