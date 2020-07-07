from player import Player
from bid import Bid
import random
from model import Model
from dmchunk import Chunk
import time as time

N_PLAYERS = 4
N_STARTING_DICE = 5
DIFFICULTY = 1


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


####################################################################################################################################################
################################################                HELPER FUNCTIONS                  ##################################################
####################################################################################################################################################


def most_common(lst):
    return max(set(lst), key=lst.count)

def store_settings(n_players, n_starting_dice, difficulty):
    N_PLAYERS = n_players
    N_STARTING_DICE = n_starting_dice
    DIFFICULTY = difficulty


class Game:
    def __init__(self, n_players=4, n_starting_dice=5, difficulty=2):
        self.difficulty = difficulty   # difficulty 1 -> random strategy, difficulty 2 -> ACT-R model
        self.players = [Player(n_starting_dice, self.difficulty) for i in range(n_players)]
        self.n_players = n_players
        self.n_total_dice = n_players * n_starting_dice
        self.current_bid = Bid(1, 0)
        self.turn = random.randint(0, n_players - 1)
        self.current_player = self.turn
        self.previous_player = 0
        self.state = states['start']
        # First player is chosen at random
        # Turns happen by iterating circularly the players list
        self.player_ID = 0
        self.players[0].strategy = 'human'


        self.t0 = time.time()

        store_settings(n_players, n_starting_dice, difficulty)

    def reset(self):
        self.__init__(N_PLAYERS, N_STARTING_DICE, DIFFICULTY)

    def all_roll(self):
        for p in self.players:
            p.roll_hand()

    def update_turn_generic(self):  # sets turn to the next player
        self.turn = (self.turn + 1) % self.n_players

    def update_turn(self, reset=False):
        if reset:
            self.turn = 0
        else:
            self.turn += 1
            self.previous_player = self.current_player
            self.current_player += 1
            if self.current_player > self.n_players - 1:
                self.current_player = 0


    ####################################################################################################################################################
    ################################################                DOUBTING PHASE                    ##################################################
    ####################################################################################################################################################


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

        if self.players[self.current_player].strategy == 'random':
            believe_percentage = 0.8
            model_id = self.current_player
            if random.randint(1,1000) <= 1000*believe_percentage:
                doubt = False  # Placeholder
            else:
                doubt = True

        elif self.players[self.current_player].strategy == 'model': # TODO implement ACT-R reasoning
            n_unknown_dice = self.n_total_dice - len(self.players[self.current_player].hand) # determine number of unknown dice

            if self.current_bid.roll != 1:
                dice_count = self.players[self.current_player].hand.count(self.current_bid.roll)  # counts instances of the value of the dice in the bid
                dice_count += self.players[self.current_player].hand.count(1)  # add joker dice to count

                if dice_count >= self.current_bid.count:
                    doubt = True
                else:
                    difference = self.current_bid.count - dice_count
                    # TODO: determine the probability of having the difference in the dice of current bid among n unknown dice

            else:
                pass
            # TODO: implement for joker dice


            believe_percentage = 0.8
            model_id = self.current_player
            if random.randint(1, 1000) <= 1000 * believe_percentage:
                doubt = False  # Placeholder
            else:
                doubt = True

        return doubt

    def ui_doubt(self):
        """
        TODO: Needs to be connected to GUI
        Calls for the ui and ask the player if it should call a bluff
        :return: Boolean whether the player decides it should call a bluff.
        """
        doubt = int(input(f"Do you want to doubt and call {self.current_bid.count} x {self.current_bid.roll} a lie? 1=yes, 0=no: "))  # Placeholder
        while doubt != 0 and doubt != 1:
            doubt = int(input(f"(Try again) Do you want to doubt and call {self.current_bid.count} x {self.current_bid.roll} a lie? 1=yes, 0=no: "))  # Placeholder
        return doubt

    def resolve_doubt(self):
        """
        """
        bid_roll = self.current_bid.roll
        bid_count = self.current_bid.count
        count = 0

        print('[RESOLVING DOUBT] Every remaining player has to state whether they believe the bid or not')
        handstring = ''
        for idx in range(self.n_players):
            count += self.players[idx].get_roll_count(bid_roll)

            if bid_roll != 1:   # joker dice addition, given that this wasn't the value bid on.
                count += self.players[idx].get_roll_count(1)

            handstring += f'Player {idx}: {self.players[idx].hand} '

        # Ask all players whether they believe the bid, remove their dice accordingly
        for idx in range(self.n_players):

            if idx != self.current_player and idx != self.previous_player:  # only apply to other players than current and previous turn

                if self.players[idx].strategy == 'human':
                    believe = int(input(
                        f"Do you believe {bid_count} x {bid_roll} is on the table? 1=yes, 0=no: "))  # Placeholder
                    while believe != 0 and believe != 1:
                        believe = int(input(f'(Try again) Do you believe {bid_count} x {bid_roll} is on the table? 1=yes, 0=no: '))  # Placeholder


                elif self.players[idx].strategy == 'random':
                    if random.randint(1,100) >= 50:
                        believe = True
                    else:
                        believe = False


                elif self.players[idx].strategy == 'model':  # TODO, implement more strategic play
                    if random.randint(1, 100) >= 50:
                        believe = True
                    else:
                        believe = False

                if believe:
                    print(f'Player {idx} believes the bid is on the table')
                    if count >= bid_count:  # lose a die when the bid is believed and true, or not believe and false
                        self.players[idx].remove_die()
                else:
                    print(f'Player {idx} does not believe the bid is on the table')
                    if count < bid_count:
                        self.players[idx].remove_die()



        print('Players hands are opened: ', end='')
        print(handstring)
        print(f'The bid was {bid_count} x {bid_roll}. On the table in total, there was {count} x {bid_roll}')

        if count >= bid_count:  #
            # Player doubts but the number of dice in the bid is actually there - previous player loses a die
            self.players[self.previous_player].remove_die()
        else:
            # Player doubts and it's right - player loses a die
            self.players[self.current_player].remove_die()
            self.current_player = (self.current_player + self.n_players - 1) % self.n_players  # previous player can start again





        print('[INFO] Number of dice remaining per player: ', end='')
        for idx in range(self.n_players):
            print(f' Player {idx}: {self.players[idx].get_hand_size()}  ||  ', end='')
        print()


    ####################################################################################################################################################
    ################################################                    BIDDING PHASE                  #################################################
    ####################################################################################################################################################

    def models_remember_bid(self):

        for i in range(self.n_players):
            if self.players[i].strategy == 'model':
                time_to_add = + round(random.uniform(5, 15), 2)   # add time according to length of a turn, might need adjustment
                self.players[i].model.time += time_to_add

                added = False
                number = 0

                while not added:  # This loop handles potential chunk naming problems
                    try:
                        ch = Chunk(name="bid_memory" + str(number),
                                   slots={"type": "bid_memory",
                                          "player": self.current_player,
                                          "dice_value": self.current_bid.roll})  # remember the value a player has bid on
                        self.players[i].model.add_encounter(ch)  # remember the bid of a player


                        added = True
                    except ValueError:
                        number += 1



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

        self.models_remember_bid()

    def ui_bid(self):
        """
        TODO: Needs to be connected to the GUI
        Ask the human player for a new bid.
        :return: count: The number of dice with the same value in the bid.\n
        roll: The dice value to bid.
        """
        count = int(input("[BID] Number of dice: "))  # Placeholder
        roll = int(input("[BID] Value of those dice: "))  # Placeholder
        return count, roll

    def model_bid(self):
        """
        TODO: Needs to be connected to model
        Ask the model for a new bid.
        :return: count: The number of dice with the same value in the bid.\n
        roll: The dice value to bid.
        """
        if self.players[self.current_player].strategy == 'random':
            higher = False
            while not higher: # Random bid, on a higher count with random dice value
                count = self.current_bid.count
                roll = random.randint(1, 6)

                if count > self.current_bid.count or (count == self.current_bid.count and roll > self.current_bid.roll):
                    higher = True
                else:
                    count = self.current_bid.count + 1
                    roll = random.randint(1, 6)
                    higher = True

        elif self.players[self.current_player].strategy == 'model':  # TODO implement ACT-R reasoning

            count = self.players[self.current_player].hand.count(most_common(self.players[self.current_player].hand))

            higher = False
            while not higher:  # Random bid, on a higher count with random dice value
                count = self.current_bid.count
                roll = random.randint(1, 6)

                if count > self.current_bid.count or (count == self.current_bid.count and roll > self.current_bid.roll):
                    higher = True
                else:
                    count = self.current_bid.count + 1
                    roll = random.randint(1, 6)
                    higher = True


        return count, roll

    ####################################################################################################################################################
    ################################################           MAIN LOOP THAT RUNS STATE MACHINE                ########################################
    ####################################################################################################################################################

    # Run the state machine
    def play(self):
        over = False
        print(f"Total players = {self.n_players} - Human Player ID is: {self.player_ID}")
        print(f'Strategies: {[self.players[i].strategy for i in range(self.n_players)]} \n')
        while not over:

            self.n_total_dice = 0
            winner = []
            for p_idx in range(self.n_players):  # Counts dice, which also determines winner
                n_dice_pl = self.players[p_idx].get_hand_size()
                if n_dice_pl == 0:  # A player with 0 dice is the winner
                    winner += [p_idx]
                    self.state = states['end']
                self.n_total_dice += n_dice_pl


            # print(f"[DEBUG] Current Player: {self.current_player} - Current Bid: {self.current_bid} - Current State: {rev_states[self.state]} - Dice in game: {self.n_total_dice}")

            # Games starts and everybody rolls.
            # Nobody should doubt on the first turn.

            if self.state == states['start']:
                self.current_bid = Bid(1, 0)
                self.update_turn(reset=True)
                print(f'[FIRST TURN]: Player {self.current_player}')
                self.all_roll()
                print(f'Rolled the dice! My hand is {self.players[0].hand} \nTotal number of dice remaining = {self.n_total_dice} \n')
                self.state = states['bidding_phase']
                continue

            # Check whether the current player wants to doubt before asking the bid.
            if self.state == states['doubting_phase']:
                if self.current_player == 0: print(f'My hand is {self.players[0].hand} \nTotal number of dice remaining = {self.n_total_dice}')
                # input("Press [Enter] to continue...\n")
                print(f'[TURN]: Player {self.current_player}')

                # if self.players[self.current_player].strategy == 'model':
                #     print(self.players[self.current_player].model)

                doubt = self.doubting()

                if doubt:
                    print(f'Player {self.current_player} does not believe the bid of Player {self.previous_player}')
                    self.resolve_doubt()
                    self.state = states['start']
                    # resolve_doubt sends state into 'end' if a player's hand is empty.
                else:
                    self.state = states['bidding_phase']
                    print(f'Player {self.current_player} believes the bid -> ', end='')
                continue


            # Ask the current player for a bid and pass to next player.
            if self.state == states['bidding_phase']:
                self.bidding()
                print(f'Player {self.current_player} has bid {self.current_bid.count} x {self.current_bid.roll}')
                self.update_turn()
                self.state = states['doubting_phase']
                continue

            if self.state == states['end']:
                over = True
                if len(winner) <= 1:
                    print(f"Player {winner[0]} has played away all its dice and won the game!.")
                else:
                    winners = str(winner)[1:-1]
                    print(f"Players {winners} have played away all their dice and won the game!.")
                continue

        print('Game Finished!')