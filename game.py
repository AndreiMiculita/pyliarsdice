from player import Player
from bid import Bid
import random

N_PLAYERS = 4
N_STARTING_DICE = 6
DIFFICULTY = 1


def store_settings(n_players, n_starting_dice, difficulty):
    N_PLAYERS = n_players
    N_STARTING_DICE = n_starting_dice
    DIFFICULTY = difficulty


states = {
    'end': 0,
    'start': 1,
    'first_turn': 2,
    'bidding_phase': 3,
    'doubting_phase': 4,
}
rev_states = {
    0: 'end',
    1: 'start',
    2: 'first_turn',
    3: 'bidding_phase',
    4: 'doubting_phase'
}


class Game:
    def __init__(self, n_players=4, n_starting_dice=6, difficulty=1):
        self.difficulty = difficulty
        self.players = [Player(n_starting_dice) for i in range(n_players)]
        self.n_players = n_players
        self.n_dice = n_players * n_starting_dice
        self.current_bid = Bid(0, 0)
        self.turn = 0
        self.current_player = 0
        self.previous_player = 0
        self.state = states['start']
        # First player is chosen at random
        # Turns happen by iterating circularly the players list
        self.player_ID = random.randint(0, n_players - 1)

        store_settings(n_players, n_starting_dice, difficulty)

    def reset(self):
        self.__init__(N_PLAYERS, N_STARTING_DICE, DIFFICULTY)

    def all_roll(self):
        for p in self.players:
            p.roll_hand()

    def update_turn(self, reset=False):
        if reset:
            self.turn = 0
        else:
            self.turn += 1
            self.previous_player = self.current_player
            self.current_player += 1
            if self.current_player > self.n_players - 1:
                self.current_player = 0

    def doubting(self):
        """
        Asks the current player if he doubts the bid of the previous player.
        Redirection to model for opponents and GUI for human player.
        :return: Boolean
        """
        if self.current_player == self.player_ID:
            doubt = self.ui_doubt()
        else:
            doubt = self.model_doubt()
        return doubt

    def model_doubt(self):
        """
        TODO: Needs to be connected to model
        Calls for the model, observe the bid and based on observations and memory decide if it should call a bluff
        :return: Boolean whether the model decides it should call a bluff.
        """
        model_id = self.current_player
        doubt = False   # Placeholder
        return doubt

    def ui_doubt(self):
        """
        TODO: Needs to be connected to GUI
        Calls for the ui and ask the player if it should call a bluff
        :return: Boolean whether the player decides it should call a bluff.
        """
        doubt = bool(input("Do you want to doubt? 1=yes, 0=no: "))   # Placeholder
        return doubt

    def resolve_doubt(self):
        """
        """
        bid_roll = self.current_bid.roll
        bid_count = self.current_bid.count
        count = 0
        for idx in range(self.n_players):
            count += self.players[idx].get_roll_count(bid_roll)

        if count <= bid_count:
            # Player doubts but it's wrong - previous player loses a die
            self.players[self.previous_player].remove_die()
        else:
            # Player doubts and it's right - player loses a die
            self.players[self.current_player].remove_die()

    def bidding(self):
        """
        Asks the current player for a new bid.
        Redirection to model for opponents and GUI for human player.
        """
        if self.current_player == self.player_ID:
            count, roll = self.ui_bid()
        else:
            count, roll = self.model_bid()
        self.current_bid = Bid(count, roll)

    def ui_bid(self):
        """
        TODO: Needs to be connected to the GUI
        Ask the human player for a new bid.
        :return: count: The number of dice with the same value in the bid.\n
        roll: The dice value to bid.
        """
        count = int(input("Bid count: "))   # Placeholder
        roll = int(input("Roll count: "))   # Placeholder
        return count, roll

    def model_bid(self):
        """
        TODO: Needs to be connected to model
        Ask the model for a new bid.
        :return: count: The number of dice with the same value in the bid.\n
        roll: The dice value to bid.
        """
        count = random.randint(0, 9)  # Placeholder
        roll = random.randint(0, 9)   # Placeholder
        return count, roll

    # Runs the state machine
    def play(self):
        over = False
        print(f"Player ID is: {self.player_ID}")
        while not over:
            self.n_dice = 0
            for p_idx in range(self.n_players):
                n_dice_pl = self.players[p_idx].get_hand_size()
                if n_dice_pl == 0:
                    winner = p_idx
                    self.state = states['end']
                self.n_dice += n_dice_pl
            print(f"[DEBUG] Current Player: {self.current_player} - Current Bid: {self.current_bid} - Current State: {rev_states[self.state]} - Dice in game: {self.n_dice}")
            # Games starts and everybody rolls.
            # Nobody should doubt on the first turn.
            if self.state == states['start']:
                self.update_turn(reset=True)
                self.all_roll()
                self.state = states['bidding_phase']
                continue

            # Check whether the current player wants to doubt before asking the bid.
            if self.state == states['doubting_phase']:
                doubt = self.doubting()
                if doubt:
                    self.resolve_doubt()
                    self.state = states['start']
                    # resolve_doubt sends state into 'end' if a player's hand is empty.
                else:
                    self.state = states['bidding_phase']
                continue

            # Ask the current player for a bid and pass to next player.
            if self.state == states['bidding_phase']:
                self.bidding()
                self.update_turn()
                self.state = states['doubting_phase']
                continue

            if self.state == states['end']:
                over = True
                print(f"Player ID: {winner} won the game.")
                continue
