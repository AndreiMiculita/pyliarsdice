import os
import random
import time
from io import StringIO
from multiprocessing import Queue
import copy

import numpy as np
from scipy.stats import binom

from ui.invoker import *
from bid import Bid
from dmchunk import Chunk
from model import Model
from player import Player
from communication_interface import CommunicationInterface

##############################################################
######                    GLOBALS                       ######
##############################################################


N_PLAYERS = 4
N_STARTING_DICE = 5
DIFFICULTY = 1

states = {
    'end': 0,
    'start': 1,
    'first_turn': 2,
    'bidding_phase': 3,
    'doubting_phase': 4,
    'resolve_doubt': 5
}
rev_states = {
    0: 'end',
    1: 'start',
    2: 'first_turn',
    3: 'bidding_phase',
    4: 'doubting_phase',
    5: 'resolve_doubt'
}

playercolors = ['none',
                '#CC3363',
                '#6A80C8',
                '#5ED71D',
                '#F0976A'
                ]


##############################################################
######                HELPER FUNCTIONS (GENERAL)        ######
##############################################################


def most_common(lst):
    return max(set(lst), key=lst.count)


def store_settings(n_players, n_starting_dice, difficulty):
    global N_PLAYERS
    global N_STARTING_DICE
    global DIFFICULTY
    N_PLAYERS = n_players
    N_STARTING_DICE = n_starting_dice
    DIFFICULTY = difficulty


def determine_probability(difference, n_unknown_dice, roll_prob):
    # determines the probability of at least n times a diceValue in m unknown dice

    p = 0
    for k in range(difference, n_unknown_dice + 1):
        p += binom.pmf(k, n_unknown_dice, roll_prob)

    return p


class Game:
    def __init__(self, ui_controller: CommunicationInterface, input_queue: Queue, n_players=4, n_starting_dice=5,
                 difficulty=2,
                 reasoning_file: StringIO = os.devnull):
        self.reasoning_file = reasoning_file
        self.reasoning_file.truncate(0)
        self.reasoning_file.seek(0)
        self.ui_controller = ui_controller
        self.input_queue = input_queue
        self.difficulty = difficulty  # difficulty 1 -> random strategy, difficulty 2 -> ACT-R model
        self.players = [Player(n_starting_dice, self.difficulty) for _ in range(n_players)]
        self.n_players = n_players
        self.n_total_dice = n_players * n_starting_dice
        self.current_bid = Bid(1, 0)
        self.turn = random.randint(0, n_players - 1)
        self.current_player = self.turn
        self.previous_player = 0
        self.round = 1
        self.state = states['start']

        # First player is chosen at random
        # Turns happen by iterating circularly the players list
        self.player_ID = 0
        self.players[0].strategy = 'human'

        self.chunk_retrieval_count = 0
        self.chunk_retrieval_failure_count = 0

        self.model_bluff_chance = 33

        store_settings(n_players, n_starting_dice, difficulty)


    ####################################################################################################
    #############################             HELPER FUNCTIONS (CLASS)               ###################
    ####################################################################################################

    def reset_models(self):
        for idx in range(self.n_players):
            if self.players[idx].strategy == 'model':
                self.players[idx].model = Model()

    def increase_models_time(self, t):
        for idx in range(self.n_players):
            if self.players[idx].strategy == 'model':
                self.players[idx].model.time += t

    def reset(self):
        self.__init__(self.ui_controller, self.input_queue, N_PLAYERS, N_STARTING_DICE, DIFFICULTY)

    def all_roll(self):
        for p in self.players:
            p.roll_hand()
        for idx, p in enumerate(self.players):
            if idx != self.player_ID:
                invoke_in_main_thread(self.ui_controller.display_action_enemy, enemy_nr=idx,
                                      action=3)
            invoke_in_main_thread(self.ui_controller.display_dice, player_nr=idx,
                                  dice=p.get_hand_size(),
                                  state=1)
        invoke_in_main_thread(self.ui_controller.show_info, string="All players are rolling dice.")

        # Sleep for 2 seconds, animation will play
        time.sleep(random.uniform(2.5, 3.5))  # agent 'rolling dice'

        for idx, p in enumerate(self.players):
            if idx != self.player_ID:
                invoke_in_main_thread(self.ui_controller.display_action_enemy, enemy_nr=idx,
                                      action=2)

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

    ####################################################################################################
    #############################                DOUBTING PHASE                    #####################
    ####################################################################################################

    def doubting(self):
        """
        Asks the current player if he doubts the bid of the previous player.
        Redirection to model for opponents and GUI for human player.
        :return: Boolean
        """
        if self.current_player == self.player_ID:
            doubt = self.ui_doubt()
            if doubt:
                self.reasoning_file.write(f"<p>You do not believe the bid</p>")
            else:
                self.reasoning_file.write(f"<p>You believe the bid</p>")
        else:
            doubt = self.model_doubt()

        return doubt

    def determine_model_doubt(self, player_index):
        '''
        Determines whether the model believes a bid, on the basis of probability calculations and some randomness
        :param player_index:
        :return: doubt (true or false)
        '''
        n_unknown_dice = self.n_total_dice - len(
            self.players[player_index].hand)  # determine number of unknown dice
        if self.current_bid.roll != 1:  # bid is on a non-joker dice

            dice_count = self.players[player_index].hand.count(
                self.current_bid.roll)  # counts instances of the value of the dice in the bid
            dice_count += self.players[player_index].hand.count(1)  # add joker dice to count

            if dice_count >= self.current_bid.count:  # the number of dice is already in the models cup
                # print('[DEBUG] Bid count present in Models cup')
                doubt = False
            else:
                difference = self.current_bid.count - dice_count
                probability_of_bid = determine_probability(difference, n_unknown_dice,
                                                           1 / 3)  # probability that at least the difference of a
                # given value is in the unknown dice, 1/3 prob since joker dice also add to total
                believe_threshold = np.random.normal(1 / 4, 1 / 12,
                                                     1)  # compare probability to non-static threshold,
                # TODO: think about how to set the threshold, this could be another difficulty -> more random threshold

                self.reasoning_file.write(
                    f"<p class='t{player_index}'>Determining probability of {self.current_bid.count} x {self.current_bid.roll} and comparing to believe threshold:</p>")
                self.reasoning_file.write(
                    f"<p class='t{player_index}'>Probability of bid is {round(probability_of_bid, 3)}, believe threshold is {round(believe_threshold[0], 3)}</p>")

                if probability_of_bid >= believe_threshold[0]:
                    doubt = False
                else:
                    doubt = True

        else:  # bid is on joker dice
            dice_count = self.players[player_index].hand.count(
                self.current_bid.roll)  # counts instances of the value of the dice in the bid (only joker dice)

            if dice_count >= self.current_bid.count:  # the number of dice is already in the model's cup
                doubt = False
            else:
                difference = self.current_bid.count - dice_count
                probability_of_bid = determine_probability(difference, n_unknown_dice,
                                                           1 / 6)  # probability that at least the difference of
                # joker dice is in the unknown dice, prob = 1/6
                believe_threshold = np.random.normal(1 / 4, 1 / 12,
                                                     1)  # compare probability to non-static threshold,
                # TODO: think about how to set the threshold, this could be another difficulty -> more random threshold
                self.reasoning_file.write(
                    f"<p class='t{player_index}'>Determining probability of {self.current_bid.count} x {self.current_bid.roll} and comparing to believe threshold:</p>")
                self.reasoning_file.write(
                    f"<p class='t{player_index}'>Probability of bid is {round(probability_of_bid, 3)}, believe threshold is {round(believe_threshold[0], 3)}</p>")

                if probability_of_bid >= believe_threshold[0]:
                    doubt = False
                else:
                    doubt = True

        return doubt

    def model_doubt(self):
        """
        TODO: Needs to be connected to model
        Calls for the model, observe the bid and based on observations and memory decide if it should call a bluff
        :return: Boolean whether the model decides it should call a bluff.
        """
        doubt = False

        # ------------------------------------Determine random (not) believe--------------------------------------- #
        if self.players[self.current_player].strategy == 'random':
            y = random.uniform(2.5, 4)
            time.sleep(y)  # agent 'thinking'
            self.increase_models_time(y)  # increase the model time with thinking time

            believe_percentage = 0.8
            if random.randint(1, 1000) <= 1000 * believe_percentage:
                doubt = False  # Placeholder
                self.reasoning_file.write(f"<p class='t{self.current_player}'>I believe the bid (80% probability)</p>")
            else:
                doubt = True
                self.reasoning_file.write(
                    f"<p class='t{self.current_player}'>I do not believe the bid (20% probability)</p>")

        # ------------------------------------Determine model (not) believe--------------------------------------- #
        elif self.players[self.current_player].strategy == 'model':

            x = len(self.players[self.current_player].model.dm)  # counts number of chunks in memory
            y = random.uniform(1, 1.5)
            if x != 0:
                y += np.log(x * 2)
            if y < 2.5:
                y = 2.5
            print(f'Number of chunks in memory = {x}, Waiting time = {round(y, 2)}s ')
            time.sleep(y)  # agent 'thinking'
            self.increase_models_time(y)  # increase the model time with thinking time

            doubt = self.determine_model_doubt(self.current_player)
            if doubt:
                self.reasoning_file.write(
                    f"<p class='t{self.current_player}'>I do not believe {self.current_bid.count} x {self.current_bid.roll} is on the table</p>")

            else:
                self.reasoning_file.write(
                    f"<p class='t{self.current_player}'>I believe {self.current_bid.count} x {self.current_bid.roll} is on the table</p>")
        return doubt

    def ui_doubt(self):
        """
        Calls for the ui and ask the player if it should call a bluff
        :return: Boolean whether the player decides it should call a bluff.
        """
        y = random.uniform(2.5, 4)
        self.increase_models_time(y)  # increase model time with approx human 'thinking' time

        invoke_in_main_thread(fn=self.ui_controller.set_bluff_controls_enabled, enabled=True,
                              target=self.previous_player)

        print(f"Do you want to doubt and call {self.current_bid.count} x {self.current_bid.roll} a lie? 1=yes, 0=no: ")
        doubt = int(self.input_queue.get(block=True))
        if doubt == -1:
            quit(0)

        while doubt != 0 and doubt != 1:
            print(
                f"(Try again) Do you want to doubt and call {self.current_bid.count} x {self.current_bid.roll} a lie? "
                f"1=yes, 0=no: ")
            doubt = int(self.input_queue.get(block=True))
            if doubt == -1:
                quit(0)
        invoke_in_main_thread(fn=self.ui_controller.set_bluff_controls_enabled, enabled=False)

        return doubt

    #########################################################################################################
    ###########################                 RESOLVING DOUBT                   ###########################
    #########################################################################################################

    def resolve_doubt(self):
        """
        Here each of the players is asked whether they believe the bid or not, which determines who loses a die
        """
        bid_roll = self.current_bid.roll
        bid_count = self.current_bid.count
        count = 0
        lose_dice_players = []  # save such that players dice are gone after hands are shown

        print('[RESOLVING DOUBT] Every remaining player has to state whether they believe the bid or not')
        invoke_in_main_thread(self.ui_controller.show_info, string=f"Resolving doubt.")
        handstring = ''
        for idx in range(self.n_players):
            count += self.players[idx].get_roll_count(bid_roll)

            if bid_roll != 1:  # joker dice addition, given that this wasn't the value bid on.
                count += self.players[idx].get_roll_count(1)

            handstring += f'Player {idx}: {self.players[idx].hand} '

        # Ask all players whether they believe the bid, remove their dice accordingly
        for player in range(self.n_players):

            idx = (self.current_player + self.n_players + player) % self.n_players
            # this makes sure the players are asked in the correct order (starting from the first player after the doubting)

            if idx != self.current_player and idx != self.previous_player:  # only apply to other players than
                # current and previous turn
                if idx != self.player_ID:
                    invoke_in_main_thread(self.ui_controller.show_info, string=f"Resolving doubt: Player {idx}'s turn.")
                else:
                    invoke_in_main_thread(self.ui_controller.show_info, string=f"Resolving doubt: Your turn.")

                believe = ""

                # ------------------------------------Human resolve doubt--------------------------------------- #
                if self.players[idx].strategy == 'human':
                    y = random.uniform(2.5, 4)
                    self.increase_models_time(y)  # increase model time with approx human 'thinking' time

                    invoke_in_main_thread(self.ui_controller.set_bluff_controls_enabled, enabled=True,
                                          target=self.previous_player)
                    invoke_in_main_thread(self.ui_controller.display_dice, player_nr=self.player_ID,
                                          dice=self.players[0].hand)
                    print(f"Your hand is {self.players[idx].hand}. Do you believe {bid_count} x {bid_roll} is on the "
                          f"table? 1=yes, 0=no: ")
                    believe_ui = int(self.input_queue.get(block=True))
                    believe = believe_ui == 0

                    if believe == -1:
                        quit(0)
                    while believe != 0 and believe != 1:
                        print(
                            f'(Try again) Your hand is {self.players[idx].hand}. Do you believe {bid_count} x {bid_roll}'
                            f' is on the table? 1=yes, 0=no: ')
                        believe = int(self.input_queue.get(block=True))
                        if believe == -1:
                            quit(0)
                    invoke_in_main_thread(self.ui_controller.set_bluff_controls_enabled, enabled=False)
                    if believe == 1:
                        self.reasoning_file.write(f"<p'>You believe the bid</p>")
                    else:
                        self.reasoning_file.write(f"<p'>You do not believe the bid</p>")


                # ------------------------------------Random resolve doubt--------------------------------------- #
                elif self.players[idx].strategy == 'random':
                    y = random.uniform(2.5, 4)
                    time.sleep(y)  # agent 'thinking'
                    self.increase_models_time(y)  # increase the model time with thinking time

                    if random.randint(1, 100) >= 50:
                        believe = True
                        self.reasoning_file.write(
                            f"<p class='t{idx}'>I believe the bid (50% probability in resolve)</p>")
                    else:
                        believe = False
                        self.reasoning_file.write(
                            f"<p class='t{idx}'>I do not believe the bid (50% probability in resolve)</p>")


                # ------------------------------------Model resolve doubt--------------------------------------- #
                elif self.players[idx].strategy == 'model':
                    x = len(self.players[idx].model.dm)  # counts number of chunks in memory
                    y = random.uniform(1, 1.5)
                    if x != 0:
                        y += np.log(x * 2)
                    if y < 2.5:
                        y = 2.5
                    print(f'Number of chunks in memory = {x}, Waiting time = {round(y, 2)}s ')
                    time.sleep(y)  # agent 'thinking'
                    self.increase_models_time(y)  # increase the model time with thinking time

                    if self.determine_model_doubt(idx):
                        believe = False  # if doubt is true -> believe = False (and vice versa)
                        self.reasoning_file.write(
                            f"<p class='t{idx}'>I do not believe the bid</p>")
                    else:
                        believe = True
                        self.reasoning_file.write(
                            f"<p class='t{idx}'>I believe the bid</p>")

                if believe:
                    invoke_in_main_thread(fn=self.ui_controller.display_action_enemy,
                                          enemy_nr=idx,
                                          action=4,
                                          target=self.previous_player)
                    print(f'Player {idx} believes the bid is on the table')
                    if count >= bid_count:  # lose a die when the bid is believed and true, or not believe and false
                        lose_dice_players.append(idx)
                        # self.players[idx].remove_die()

                else:
                    invoke_in_main_thread(fn=self.ui_controller.display_action_enemy,
                                          enemy_nr=idx,
                                          action=1,
                                          target=self.previous_player)
                    print(f'Player {idx} does not believe the bid is on the table')
                    if count < bid_count:
                        lose_dice_players.append(idx)
                        # self.players[idx].remove_die()

        print('Players hands are opened: ', end='')
        print(handstring)

        # -------------------------------Reveal all dice, determine who is correct---------------------------------- #
        # Reveal all dice in ui and wait for a bit

        for idx, player in enumerate(self.players):
            invoke_in_main_thread(self.ui_controller.display_dice, player_nr=idx, dice=player.hand,
                                  highlight=bid_roll)
            time.sleep(0.1 * len(player.hand))

        print(f'The bid was {bid_count} x {bid_roll}. On the table in total, there was {count} x {bid_roll}')
        invoke_in_main_thread(self.ui_controller.show_info,
                              string=f"The bid was: {bid_count} x {bid_roll}.<br>"
                                     f"On the table: {count} x {bid_roll}.")

        timeout_time = 0.2 * self.n_total_dice  # Lower this to make it faster
        time.sleep(timeout_time)
        # self.wait_for_continue(timeout_time)

        if count >= bid_count:  #
            # Player doubts but the number of dice in the bid is actually there - previous player loses a die
            lose_dice_players.append(self.previous_player)
        else:
            # Player doubts and it's right - player loses a die
            lose_dice_players.append(self.current_player)
            self.current_player = (self.current_player + self.n_players - 1) % self.n_players  # previous
            # player can start again

        # -----------------------------------------Players losing a die-------------------------------------------- #
        # This part handles which players lose a die and what is printed / shown in the UI
        if len(lose_dice_players) <= 1:
            if lose_dice_players[0] == 0:
                invoke_in_main_thread(self.ui_controller.show_info,
                                      string=f"You were correct.<br>"
                                             f"You lose a die.")
            else:
                invoke_in_main_thread(self.ui_controller.show_info,
                                      string=f"Player {', '.join(map(str, lose_dice_players))} was correct.<br>"
                                             f"Player {', '.join(map(str, lose_dice_players))} will lose a die.")
        else:
            lose_dice_players.sort()
            if 0 in lose_dice_players:
                temp_lose_dice_players = copy.deepcopy(lose_dice_players)
                temp_lose_dice_players.pop(0)

                invoke_in_main_thread(self.ui_controller.show_info,
                                      string=f"{'Player' if len(temp_lose_dice_players) == 1 else 'Players'} {', '.join(map(str, temp_lose_dice_players))} and you were correct. <br>"
                                             f"{'Player' if len(temp_lose_dice_players) == 1 else 'Players'} {', '.join(map(str, temp_lose_dice_players))} and you will lose a die.")
            else:
                invoke_in_main_thread(self.ui_controller.show_info,
                                      string=f"Players {', '.join(map(str, lose_dice_players))} were correct.<br>"
                                             f" They will lose a die.")

        for idx in range(self.n_players):
            invoke_in_main_thread(self.ui_controller.display_dice, player_nr=idx,
                                  dice=self.players[idx].get_hand_size(),
                                  state=2 if idx in lose_dice_players else 0)

        for i in lose_dice_players:
            self.players[i].remove_die()

        time.sleep(4)

        # print('[INFO] Number of dice remaining per player: ', end='')
        # for idx in range(self.n_players):
        #     print(f' Player {idx}: {self.players[idx].get_hand_size()}  ||  ', end='')
        #     if idx != self.player_ID:
        #         invoke_in_main_thread(self.ui_controller.display_dice, player_nr=idx,
        #                               dice=self.players[idx].get_hand_size(),
        #                               state=0)

        print()

    #########################################################################################################
    ###########################                    BIDDING PHASE                  ###########################
    #########################################################################################################

    def models_remember_bid(self):
        # Making and storing chunks of bids for ACT-R models
        for i in range(self.n_players):
            if i != self.current_player and self.players[i].strategy == 'model':

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

                self.reasoning_file.write(
                    f"<p class='t{i}'>Storing chunk to remember that Player {self.current_player} has made a bid on dice value {self.current_bid.roll}</p>")

    def bidding(self):
        """
        Asks the current player for a new bid.
        Redirection to model for opponents and GUI for human player.
        """
        if self.current_player == self.player_ID:
            self.increase_models_time(random.uniform(2.5,
                                                     4))  # increasing model times with a random, since human players might take very long or short to affect models
            count, roll = self.ui_bid()
            self.reasoning_file.write(f"<p>You have bid {count} x {roll}</p>")
        else:
            invoke_in_main_thread(self.ui_controller.display_action_enemy, enemy_nr=self.current_player,
                                  action=0)
            count, roll = self.model_bid()
            if self.players[self.current_player].strategy == 'model' or self.players[
                self.current_player].strategy == 'random':
                self.reasoning_file.write(
                    f"<p class='t{self.current_player}'>I am bidding: {count} x {roll} is on the table</p>")

        self.current_bid = Bid(count, roll)

    def is_higher_bid(self, count, roll):
        # Determines whether the bid is sufficient to overbid the previous bid

        if self.current_bid.roll == 1:  # overbidding a bid on joker dice
            if roll == 1:  # case of bidding joker dice yourself
                if count > self.current_bid.count:  # simply higher bid on joker dice if possible
                    return True
                else:
                    return False
            else:
                if count >= self.current_bid.count * 2:  # must bid double over joker dice, with non-joker dice
                    return True
                else:
                    return False

        else:  # overbidding a bid on non-joker dice
            if roll == 1:  # case of bidding joker dice yourself
                if self.current_bid.count % 2 == 1:  # bet was on uneven
                    if count >= (self.current_bid.count + self.current_bid.count % 2) / 2:
                        return True
                    else:
                        return False
                else:  # bet had even dice
                    if count > self.current_bid.count / 2:
                        return True
                    else:
                        return False
            else:
                if count > self.current_bid.count:  # higher count than previous bid
                    return True
                elif count == self.current_bid.count and roll > self.current_bid.roll:  # same count with higher
                    # value than previous bid
                    return True
                else:
                    return False  # bid not high enough

    def ui_bid(self):
        """
        Ask the human player for a new bid.
        :return: count: The number of dice with the same value in the bid.\n
        roll: The dice value to bid.
        """

        higher = False
        invoke_in_main_thread(self.ui_controller.set_bet_controls_enabled, enabled=True,
                              previous_bet=f"{self.current_bid.count} × {self.current_bid.roll}")

        count, roll = 0, 0
        invoke_in_main_thread(self.ui_controller.set_bet_limits, number_min=0, number_max=self.n_total_dice, dice_min=1,
                              dice_max=6)

        while not higher:  # Random bid, on a higher count with random dice value
            print("[BID] Number of dice: ")  # Placeholder
            count = int(self.input_queue.get(block=True))
            if count == -1:
                quit(0)
            print("[BID] Value of those dice: ")  # Placeholder
            roll = int(self.input_queue.get(block=True))
            if roll == -1:
                quit(0)
            if count > 0 and 1 <= roll <= 6 and self.is_higher_bid(count, roll):
                higher = True
            else:
                print('Bid impossible or not high enough, try again!')
                invoke_in_main_thread(self.ui_controller.show_info, string=
                f"<b style='color:#FF0000'>You need to overbid {self.current_bid.count} × {self.current_bid.roll}!</b><br>"
                f"See Help > How to Play for rules.")
        invoke_in_main_thread(self.ui_controller.set_bet_controls_enabled, enabled=False,
                              previous_bet=f"{self.current_bid.count} × {self.current_bid.roll}")

        return count, roll

    def model_bid(self):
        """
        Ask the model for a new bid.
        :return: count: The number of dice with the same value in the bid.\n
        roll: The dice value to bid.
        """

        count, roll = 0, 0

        # -----------------------------------------Random bidding-------------------------------------------- #
        if self.players[self.current_player].strategy == 'random':

            if self.current_bid.roll == 1:
                if random.randint(1, 1000) <= 167:  # random chance to bid on 1's
                    roll = 1
                    count = self.current_bid.count + 1
                else:
                    count = self.current_bid.count * 2  # first non-joker bid over a joker bid must be double the count
                    roll = random.randint(2, 6)

            else:  # current bid is not on joker dice

                if random.randint(1, 1000) <= 167:  # random chance to bid on 1's
                    if self.current_bid.count % 2 == 1:
                        count = int((self.current_bid.count + 1) / 2)  # joker bid must be double the count
                    else:
                        count = int((self.current_bid.count / 2) + 1)
                    roll = 1
                else:

                    higher = False
                    while not higher:  # Random bid, on a higher count with random dice value
                        count = self.current_bid.count
                        roll = random.randint(2, 6)

                        if count > self.current_bid.count or (
                                count == self.current_bid.count and roll > self.current_bid.roll):
                            higher = True
                        else:
                            count = self.current_bid.count + 1
                            roll = random.randint(2, 6)
                            higher = True

        # -----------------------------------------Model bidding-------------------------------------------- #
        elif self.players[self.current_player].strategy == 'model':
            if random.randint(1, 100) <= self.model_bluff_chance:  # chance to bluff
                if random.randint(1, 100) >= 66:  # determine which player the model will bluff on, next player has a
                    # higher chance, since he has to assess the bid.
                    bluff_player = self.previous_player
                    self.reasoning_file.write(
                        f"<p class='t{self.current_player}'>Aiming to bluff on one of the dice values bid on by previous player</p>")
                else:
                    bluff_player = (self.current_player + 1) % self.n_players
                    self.reasoning_file.write(
                        f"<p class='t{self.current_player}'>Aiming to bluff on one of the dice values bid on by next player</p>")

                chunk = None
                tries = 0
                while chunk is None and tries < self.n_players - 1:  # model has a number of tries to remember the bet of a player according to the number of players, otherwise models remember too little with the increased time
                    retrieve_chunk = Chunk(name="memorize_bid_value",
                                           slots={"type": "bid_memory", "player": bluff_player})
                    chunk, latency = self.players[self.current_player].model.retrieve(
                        retrieve_chunk)  # retrieve a chunk from declarative memory
                    tries += 1
                self.reasoning_file.write(
                    f"<p class='t{self.current_player}'>Trying to memorize a chunk containing a value Player {bluff_player} has bid on</p>")

                if chunk is not None:  # a chunk was retrieved
                    self.chunk_retrieval_count += 1
                    roll = chunk.slots['dice_value']  #

                    self.reasoning_file.write(
                        f"<p class='t{self.current_player}'>Retrieved a chunk containing that Player {bluff_player} has bid on {roll} this round</p>")
                    self.reasoning_file.write(
                        f"<p class='t{self.current_player}'>Bluffing on {roll}, since Player {bluff_player} has bid on {roll} before</p>")

                else:  # no chunk was retrieved / retrieval failure
                    # print('\nChunk retrieval failed')
                    self.chunk_retrieval_failure_count += 1

                    self.reasoning_file.write(
                        f"<p class='t{self.current_player}'>No chunk was retrieved</p>")
                    self.reasoning_file.write(
                        f"<p class='t{self.current_player}'>Can not remember a value Player {bluff_player} has bid on before, bluffing on random value</p>")

                    # print('[DEBUG] no chunk was retrieved / retrieval failure')
                    roll = random.randint(1, 6)  # bluffing happens on a random die value

                if roll == 1:  # bluff will be on joker dice

                    self.reasoning_file.write(
                        f"<p class='t{self.current_player}'>Bluffing on joker dice</p>")

                    if self.current_bid.roll == 1:  # current bid is on joker dice, so + 1 suffices
                        count = self.current_bid.count + 1
                    else:  # current bid is not on joker dice, calculate first possible bid on joker dice
                        if self.current_bid.count % 2 == 1:
                            count = int((self.current_bid.count + 1) / 2)  # joker bid must be double the count
                        else:
                            count = int((self.current_bid.count / 2) + 1)

                else:  # roll is not a joker dice, determine first possible bid with this value

                    if self.current_bid.roll == 1:  # current bid is on joker dice, must be at least double this value
                        count = self.current_bid.count * 2  # first non-joker bid over a joker bid must be double the
                        # count

                    else:  # bid is not on a joker dice
                        if roll > self.current_bid.roll:  # just the higher value suffices
                            count = self.current_bid.count
                        else:
                            count = self.current_bid.count + 1  # else: increment count, and bid on the value

            else:  # model will not bluff -> determine a bid from hand
                most_com_value = most_common(self.players[self.current_player].hand)
                n_of_most = self.players[self.current_player].hand.count(most_com_value)

                highest_value = [self.players[self.current_player].hand[m] for m in
                                 range(len(self.players[self.current_player].hand))
                                 if self.players[self.current_player].hand.count(
                        self.players[self.current_player].hand[m]) == n_of_most]

                bid_value = highest_value[random.randint(0, len(
                    highest_value) - 1)]  # determine most common value in hand and choose one of those values from
                # hand (if multiple, chooses randomly)

                roll = bid_value

                self.reasoning_file.write(
                    f"<p class='t{self.current_player}'>My hand is {self.players[self.current_player].hand}, bidding on one of the most common dice values in hand, which is {roll}</p>")

                if roll == 1:  # bidding on the joker dice
                    if self.current_bid.roll == 1:  # current bid is on joker dice, so + 1 suffices
                        count = self.current_bid.count + 1
                    else:  # current bid is not on joker dice, calculate first possible bid on joker dice
                        if self.current_bid.count % 2 == 1:
                            count = int((self.current_bid.count + 1) / 2)  # joker bid must be double the count
                        else:
                            count = int((self.current_bid.count / 2) + 1)

                else:  # roll is not a joker dice, determine first possible bid with this value

                    if self.current_bid.roll == 1:  # current bid is on joker dice, must be at least double this value
                        count = self.current_bid.count * 2  # first non-joker bid over a joker bid must be double the
                        # count

                    else:  # bid is not on a joker dice
                        if roll > self.current_bid.roll:  # just the higher value suffices
                            count = self.current_bid.count
                        else:
                            count = self.current_bid.count + 1  # else: increment count, and bid on the value

                self.reasoning_file.write(
                    f"<p class='t{self.current_player}'>Determined bid is {count} x {roll}</p>")

        return count, roll

    def clear_ui_bets(self):
        for idx, player in enumerate(self.players):  # Counts dice, which also determines winner
            if idx != self.player_ID:
                invoke_in_main_thread(self.ui_controller.display_bet_enemy, enemy_nr=idx,
                                      number="", dice=0)

    def wait_for_continue(self, timeout_time: float):
        """
        Wait for the player to continue, after a doubt has been resolved
        :return: once the player has given some input, or a timeout expires
        """
        invoke_in_main_thread(self.ui_controller.set_continue_controls_enabled, enabled=True)
        loader_step = 5  # How much% the loader should move each tick
        # Wait for the player to click to continue
        import queue  # to recognize the exception
        for i in range(0, 101, loader_step):  # Start and stop must be 0 and 101
            try:
                continue_ = self.input_queue.get(block=True,
                                                 timeout=float(timeout_time) * float(loader_step) / float(100))
                if continue_ == -1:
                    quit(0)
                break
            except queue.Empty:
                invoke_in_main_thread(self.ui_controller.set_continue_timeout_progress, i)

        invoke_in_main_thread(self.ui_controller.set_continue_controls_enabled, enabled=False)

    #######################################################################################################
    #########################           MAIN LOOP THAT RUNS STATE MACHINE                ##################
    #######################################################################################################

    # Run the state machine
    def play(self):
        over = False
        # Print game information
        print(f"Total players = {self.n_players} - Human Player ID is: {self.player_ID}")
        print(f'Strategies: {[self.players[i].strategy for i in range(self.n_players)]} \n')
        self.reasoning_file.write(f"<div class='topbox'>")
        for i in range(1, self.n_players):
            self.reasoning_file.write(f"<div class='playerbox' style='background-color:{playercolors[i]};'>"
                                      f"Player {i}</div>")
        self.reasoning_file.write(f"</div>")

        while not over:  # main while loop
            self.n_total_dice = 0
            winner = []
            for p_idx in range(self.n_players):  # Counts dice, which also determines winner
                n_dice_pl = self.players[p_idx].get_hand_size()
                if n_dice_pl == 0:  # A player with 0 dice is the winner
                    winner += [p_idx]
                    self.state = states['end']
                self.n_total_dice += n_dice_pl



            # -----------------------------------------Start-------------------------------------------- #
            # Games starts and everybody rolls.
            # Nobody should doubt on the first turn.
            if self.state == states['start']:
                self.reset_models()
                self.clear_ui_bets()
                self.current_bid = Bid(1, 0)
                self.update_turn(reset=True)
                print('----------------- NEW ROUND ----------------------')
                if self.n_total_dice == self.n_players * 5:
                    self.round = 1
                else:
                    self.round += 1
                    self.reasoning_file.write(f"</div>")

                self.reasoning_file.write(
                    f"<div class='roundbox' style='margin-top:50px;'><div class='roundtitle'>Round {self.round}</div>")
                self.all_roll()

                print(f'All players rolled the dice! My hand is {self.players[0].hand} \n'
                      f'Total number of dice remaining = {self.n_total_dice} \n')

                invoke_in_main_thread(self.ui_controller.display_dice, player_nr=self.player_ID,
                                      dice=self.players[self.player_ID].hand,
                                      highlight=0)

                for idx, player in enumerate(self.players):  # Counts dice, which also determines winner
                    if idx > 0:
                        invoke_in_main_thread(self.ui_controller.display_dice, player_nr=idx,
                                              dice=player.get_hand_size(),
                                              state=0)

                for idx, player in enumerate(self.players):  # Counts dice, which also determines winner
                    if idx != self.player_ID and (
                            self.players[idx].strategy == 'model' or self.players[idx].strategy == 'random'):
                        self.reasoning_file.write(
                            f"<p class='t{idx}'> My hand is {self.players[idx].hand}</p>")

                print(f'[FIRST TURN]: Player {self.current_player}')
                if self.current_player != self.player_ID:
                    self.reasoning_file.write(
                        f"<p class='turntitle tn{self.current_player}'>Player {self.current_player}'s turn (first):</p>")
                    invoke_in_main_thread(self.ui_controller.show_info, string=f"Player {self.current_player}'s turn.")
                else:
                    self.reasoning_file.write(
                        f"<p class='turntitle tn{self.current_player}'>Your turn (first):</p>")
                    invoke_in_main_thread(self.ui_controller.show_info, string=f"Your turn.")

                if self.current_player != self.player_ID:
                    self.reasoning_file.write(
                        f"<p class='t{self.current_player}'>Player {self.current_player} can bid first:</p>")
                    invoke_in_main_thread(self.ui_controller.display_action_enemy,
                                          enemy_nr=self.current_player,
                                          action=0)

                    y = random.uniform(2.5, 4)
                    time.sleep(
                        y)  # agent 'thinking'  (First turn means never any chunks stored, so random time addition can be both for models and random opponents)

                self.state = states['bidding_phase']
                continue

            # ----------------------------------------Doubting Phase--------------------------------------------- #
            # Check whether the current player wants to doubt before asking the bid.
            if self.state == states['doubting_phase']:
                if self.current_player == self.player_ID:
                    print(
                        f'My hand is {self.players[self.player_ID].hand} \nTotal number of dice remaining = {self.n_total_dice}')
                    invoke_in_main_thread(self.ui_controller.display_dice, player_nr=self.player_ID,
                                          dice=self.players[self.player_ID].hand)

                if self.current_player != self.player_ID:
                    self.reasoning_file.write(
                        f"<p class='turntitle tn{self.current_player}'>Player {self.current_player}'s turn:</p>")
                else:
                    self.reasoning_file.write(
                        f"<p class='turntitle tn{self.current_player}'>Your turn:</p>")

                print(f'[TURN]: Player {self.current_player}')

                if self.current_player != self.player_ID:
                    invoke_in_main_thread(self.ui_controller.show_info, string=f"Player {self.current_player}'s turn.")
                else:
                    invoke_in_main_thread(self.ui_controller.show_info, string=f"Your turn.")

                if self.current_player != self.player_ID:
                    invoke_in_main_thread(self.ui_controller.display_action_enemy,
                                          enemy_nr=self.current_player,
                                          action=0)
                    # time.sleep(random.uniform(1.5, 4))  # agent 'thinking'

                doubt = self.doubting()

                if doubt:
                    print(f'Player {self.current_player} does not believe the bid of Player {self.previous_player}')
                    if self.current_player != self.player_ID:
                        invoke_in_main_thread(fn=self.ui_controller.display_action_enemy,
                                              enemy_nr=self.current_player,
                                              action=1,
                                              target=self.previous_player)

                    self.state = states['resolve_doubt']

                else:
                    self.state = states['bidding_phase']
                    print(f'Player {self.current_player} believes the bid -> ', end='')
                continue

            # -----------------------------------------Resolve doubt-------------------------------------------- #
            if self.state == states[
                'resolve_doubt']:  # resolve_doubt sends state into 'end' if a player's hand is empty.
                self.reasoning_file.write(f"<p><i>Resolving Doubt</i></p>")
                self.resolve_doubt()
                self.state = states['start']


            # ------------------------------------------Bidding Phase------------------------------------------- #
            # Ask the current player for a bid and pass to next player.
            if self.state == states['bidding_phase']:

                self.bidding()
                print(f'Player {self.current_player} has bid {self.current_bid.count} x {self.current_bid.roll}')
                if self.current_player != self.player_ID:
                    invoke_in_main_thread(self.ui_controller.display_bet_enemy, enemy_nr=self.current_player,
                                          number=self.current_bid.count, dice=self.current_bid.roll)

                if self.previous_player != self.player_ID and self.previous_player != self.current_player:
                    invoke_in_main_thread(self.ui_controller.display_bet_enemy, enemy_nr=self.previous_player,
                                          number="", dice=0)

                if self.current_player != self.player_ID:
                    invoke_in_main_thread(self.ui_controller.display_action_enemy, enemy_nr=self.current_player,
                                          action=2)

                self.models_remember_bid()

                self.update_turn()
                self.state = states['doubting_phase']
                continue

            # -------------------------------------------End Phase------------------------------------------ #
            if self.state == states['end']:
                over = True
                if len(winner) <= 1:
                    print(f"Player {winner[0]} has played away all its dice and won the game!.")
                    invoke_in_main_thread(self.ui_controller.display_winner_and_close, players=winner)
                else:
                    winners = str(winner)[1:-1]
                    print(f"Players {winners} have played away all their dice and won the game!.")
                    invoke_in_main_thread(self.ui_controller.display_winner_and_close, players=winner)
                continue

        # print(f'Chunks retrieved during game: {self.chunk_retrieval_count}')
        # print(f'Chunk retrieve failures during game: {self.chunk_retrieval_failure_count}')
        print('Game Finished!')
        quit(0)
