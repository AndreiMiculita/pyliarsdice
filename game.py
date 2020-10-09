import random
import time
from multiprocessing import Queue

import numpy as np
from scipy.stats import binom

import ui.invoker as invoker
from bid import Bid
from dmchunk import Chunk
from model import Model
from player import Player
from ui_controller import UIController

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


##############################################################
######                HELPER FUNCTIONS                  ######
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
    def __init__(self, ui_controller: UIController, input_queue: Queue, n_players=4, n_starting_dice=5, difficulty=2):
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
        self.state = states['start']

        # First player is chosen at random
        # Turns happen by iterating circularly the players list
        self.player_ID = 0
        self.players[0].strategy = 'human'

        self.chunk_retrieval_count = 0
        self.chunk_retrieval_failure_count = 0

        self.model_bluff_chance = 33

        store_settings(n_players, n_starting_dice, difficulty)

    def reset_models(self):
        for idx in range(self.n_players):
            if self.players[idx].strategy == 'model':
                self.players[idx].model = Model()

    def reset(self):
        self.__init__(self.ui_controller, self.input_queue, N_PLAYERS, N_STARTING_DICE, DIFFICULTY)

    def all_roll(self):
        for p in self.players:
            p.roll_hand()
        for idx, p in enumerate(self.players):
            if idx != self.player_ID:
                invoker.invoke_in_main_thread(self.ui_controller.display_action_enemy, enemy_nr=idx,
                                              action=3)

                invoker.invoke_in_main_thread(self.ui_controller.display_rolling_dice_enemy,
                                              enemy_nr=idx,
                                              dice_count=p.get_hand_size())


            else:
                invoker.invoke_in_main_thread(self.ui_controller.display_rolling_dice_player,
                                              dice_count=p.get_hand_size())

        # Sleep for 2 seconds, animation will play
        time.sleep(random.uniform(2.5, 3.5))  # agent 'rolling dice'

        for idx, p in enumerate(self.players):
            if idx != self.player_ID:
                invoker.invoke_in_main_thread(self.ui_controller.display_action_enemy, enemy_nr=idx,
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

    #################################################################
    ########                DOUBTING PHASE                    #######
    #################################################################

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

    def determine_model_doubt(self, player_index):
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
                # TODO: think about how to set the threshold
                # print(f'[DEBUG] Probability of bid is {round(probability_of_bid,
                # 3)}, believe threshold is {round(believe_threshold[0], 3)}')
                self.players[player_index].reasoning_string += f'Determining probability of {self.current_bid.count} x {self.current_bid.roll} and comparing to believe threshold:\n'
                self.players[player_index].reasoning_string += f'Probability of bid is {round(probability_of_bid, 3)}, believe threshold is {round(believe_threshold[0], 3)}\n'
                if probability_of_bid >= believe_threshold[0]:
                    doubt = False
                else:
                    doubt = True

        else:  # bid is on joker dice
            dice_count = self.players[player_index].hand.count(
                self.current_bid.roll)  # counts instances of the value of the dice in the bid (only joker dice)

            if dice_count >= self.current_bid.count:  # the number of dice is already in the model's cup
                # print('[DEBUG] Bid count present in Models cup')
                doubt = False
            else:
                difference = self.current_bid.count - dice_count
                probability_of_bid = determine_probability(difference, n_unknown_dice,
                                                           1 / 6)  # probability that at least the difference of
                # joker dice is in the unknown dice, prob = 1/6
                believe_threshold = np.random.normal(1 / 4, 1 / 12,
                                                     1)  # compare probability to non-static threshold,
                # TODO: think about how to set the threshold
                self.players[player_index].reasoning_string += f'Determining probability of {self.current_bid.count} x {self.current_bid.roll} and comparing to believe threshold:\n'
                self.players[player_index].reasoning_string += f'Probability of bid is {round(probability_of_bid, 3)}, believe threshold is {round(believe_threshold[0], 3)}\n'
                # print(f'[DEBUG] Probability of bid is {round(probability_of_bid,
                # 3)}, believe threshold is {round( believe_threshold[0], 3)}')
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

        if self.players[self.current_player].strategy == 'random':
            believe_percentage = 0.8
            if random.randint(1, 1000) <= 1000 * believe_percentage:
                doubt = False  # Placeholder
            else:
                doubt = True

        elif self.players[self.current_player].strategy == 'model':
            doubt = self.determine_model_doubt(self.current_player)
            if doubt:
                self.players[self.current_player].reasoning_string += f'I do not believe {self.current_bid.count} x {self.current_bid.roll} is on the table\n'
            else:
                self.players[self.current_player].reasoning_string += f'I believe {self.current_bid.count} x {self.current_bid.roll} is on the table\n'
        return doubt

    def ui_doubt(self):
        """
        Calls for the ui and ask the player if it should call a bluff
        :return: Boolean whether the player decides it should call a bluff.
        """
        invoker.invoke_in_main_thread(fn=self.ui_controller.set_bluff_controls_enabled, enabled=True,
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
        invoker.invoke_in_main_thread(fn=self.ui_controller.set_bluff_controls_enabled, enabled=False)

        return doubt

    def resolve_doubt(self):
        """
        """
        bid_roll = self.current_bid.roll
        bid_count = self.current_bid.count
        count = 0
        lose_dice_players = []  # save such that players dice are gone after hands are shown

        print('[RESOLVING DOUBT] Every remaining player has to state whether they believe the bid or not')
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
                    invoker.invoke_in_main_thread(self.ui_controller.indicate_turn, player=idx)
                    # time.sleep(random.uniform(1.5, 4))  # agent 'thinking'
                    x = len(self.players[idx].model.dm)  # counts number of chunks in memory
                    y = random.uniform(1, 1.5)
                    if x != 0:
                        y += np.log(x * 2)
                    if y < 2.5:
                        y = 2.5


                    print(f'Number of chunks in memory = {x}, Waiting time = {round(y, 2)}s ')
                    time.sleep(y)  # agent 'thinking'

                believe = ""
                if self.players[idx].strategy == 'human':
                    invoker.invoke_in_main_thread(self.ui_controller.set_bluff_controls_enabled, enabled=True,
                                                  target=self.previous_player)
                    invoker.invoke_in_main_thread(self.ui_controller.display_dice_player, dice=self.players[0].hand)
                    print(f"Your hand is {self.players[idx].hand}. Do you believe {bid_count} x {bid_roll} is on the "
                          f"table? 1=yes, 0=no: ")
                    believe_ui = int(self.input_queue.get(block=True))
                    if believe_ui == 0:  # these were swapped, this circumvents the problem
                        believe = True
                    else:
                        believe = False
                    print(f'believe ui response = {believe}')
                    if believe == -1:
                        quit(0)
                    while believe != 0 and believe != 1:
                        print(
                            f'(Try again) Your hand is {self.players[idx].hand}. Do you believe {bid_count} x {bid_roll}'
                            f' is on the table? 1=yes, 0=no: ')
                        believe = int(self.input_queue.get(block=True))
                        if believe == -1:
                            quit(0)
                    invoker.invoke_in_main_thread(self.ui_controller.set_bluff_controls_enabled, enabled=False)

                elif self.players[idx].strategy == 'random':
                    if random.randint(1, 100) >= 50:
                        believe = True
                    else:
                        believe = False


                elif self.players[idx].strategy == 'model':
                    if self.determine_model_doubt(idx):
                        believe = False  # if doubt is true -> believe = False (and vice versa)
                    else:
                        believe = True

                if believe:
                    invoker.invoke_in_main_thread(fn=self.ui_controller.display_action_enemy,
                                                  enemy_nr=idx,
                                                  action=4,
                                                  target=self.previous_player)
                    print(f'Player {idx} believes the bid is on the table')
                    if count >= bid_count:  # lose a die when the bid is believed and true, or not believe and false
                        lose_dice_players.append(idx)
                        # self.players[idx].remove_die()

                else:
                    invoker.invoke_in_main_thread(fn=self.ui_controller.display_action_enemy,
                                                  enemy_nr=idx,
                                                  action=1,
                                                  target=self.previous_player)
                    print(f'Player {idx} does not believe the bid is on the table')
                    if count < bid_count:
                        lose_dice_players.append(idx)
                        # self.players[idx].remove_die()

        print('Players hands are opened: ', end='')
        print(handstring)

        # Reveal all dice in ui and wait for a bit
        for idx, player in enumerate(self.players):
            if idx > 0:
                invoker.invoke_in_main_thread(self.ui_controller.display_dice_enemy, enemy_nr=idx, dice=player.hand,
                                              highlight=bid_roll)
            else:
                # TODO: Add such that human players dice are highlighted as well.
                pass
            time.sleep(0.1 * len(player.hand))  # Wait for 2nd question
        time.sleep(0.2 * self.n_total_dice)  # Wait for 2nd question

        print(f'The bid was {bid_count} x {bid_roll}. On the table in total, there was {count} x {bid_roll}')

        if count >= bid_count:  #
            # Player doubts but the number of dice in the bid is actually there - previous player loses a die
            self.players[self.previous_player].remove_die()
        else:
            # Player doubts and it's right - player loses a die
            self.players[self.current_player].remove_die()
            self.current_player = (self.current_player + self.n_players - 1) % self.n_players  # previous
            # player can start again

        for i in lose_dice_players:
            self.players[i].remove_die()


        print('[INFO] Number of dice remaining per player: ', end='')
        for idx in range(self.n_players):
            print(f' Player {idx}: {self.players[idx].get_hand_size()}  ||  ', end='')
            if idx > 0:
                invoker.invoke_in_main_thread(self.ui_controller.display_anonymous_dice_enemy, enemy_nr=idx,
                                              dice_count=self.players[idx].get_hand_size())

        print()

        for idx in range(self.n_players):
            if idx > 0:
                print(f'Player {idx} has {len(self.players[idx].model.dm)} chunks stored')

    ###############################################################
    ######                    BIDDING PHASE                  ######
    ###############################################################

    def models_remember_bid(self):
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

                        time_to_add = + round(random.uniform(1, 4),
                                              2)  # add time according to length of a turn, might need adjustment
                        self.players[i].model.time += round(time_to_add, 2)

                        added = True
                    except ValueError:
                        number += 1

                self.players[i].reasoning_string += f'Storing chunk to remember that Player {self.current_player} has made a bet on dice value {self.current_bid.roll}\n'
                print(self.players[i].model.dm[0])
                # print(self.players[i].model.dm[1])

    def bidding(self):
        """
        Asks the current player for a new bid.
        Redirection to model for opponents and GUI for human player.
        """
        if self.current_player == self.player_ID:
            count, roll = self.ui_bid()
        else:
            invoker.invoke_in_main_thread(self.ui_controller.display_action_enemy, enemy_nr=self.current_player,
                                          action=0)
            count, roll = self.model_bid()
            self.players[self.current_player].reasoning_string += f'I am bidding: {count} x {roll} is on the table\n'
        self.current_bid = Bid(count, roll)

    def is_higher_bid(self, count, roll):

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
        invoker.invoke_in_main_thread(self.ui_controller.set_bet_controls_enabled, enabled=True,
                                      previous_bet=f"{self.current_bid.count} × {self.current_bid.roll}")

        count, roll = 0, 0
        invoker.invoke_in_main_thread(self.ui_controller.set_bet_limits, number_min=0, number_max=10, dice_min=1,
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
        invoker.invoke_in_main_thread(self.ui_controller.set_bet_controls_enabled, enabled=False,
                                      previous_bet=f"{self.current_bid.count} × {self.current_bid.roll}")

        return count, roll

    def model_bid(self):
        """
        Ask the model for a new bid.
        :return: count: The number of dice with the same value in the bid.\n
        roll: The dice value to bid.
        """

        count, roll = 0, 0

        if self.players[self.current_player].strategy == 'random':

            if self.current_bid.roll == 1:
                if random.randint(1, 100) <= 25:  # random chance to bid on 1's
                    roll = 1
                    count = self.current_bid.count + 1
                else:
                    count = self.current_bid.count * 2  # first non-joker bid over a joker bid must be double the count
                    roll = random.randint(1, 6)

            else:  # current bid is not on joker dice

                if random.randint(1, 100) <= 25:  # random chance to bid on 1's
                    if self.current_bid.count % 2 == 1:
                        count = int((self.current_bid.count + 1) / 2)  # joker bid must be double the count
                    else:
                        count = int((self.current_bid.count / 2) + 1)
                    roll = 1
                else:

                    higher = False
                    while not higher:  # Random bid, on a higher count with random dice value
                        count = self.current_bid.count
                        roll = random.randint(1, 6)

                        if count > self.current_bid.count or (
                                count == self.current_bid.count and roll > self.current_bid.roll):
                            higher = True
                        else:
                            count = self.current_bid.count + 1
                            roll = random.randint(1, 6)
                            higher = True

        elif self.players[self.current_player].strategy == 'model':
            if random.randint(1, 100) <= self.model_bluff_chance:  # chance to bluff
                if random.randint(1,
                                  100) >= 66:  # determine which player the model will bluff on, next player has a
                    # higher chance, since he has to assess the bid.
                    bluff_player = self.previous_player
                    # print('[DEBUG] bluffing on prev player')
                    self.players[self.current_player].reasoning_string += 'Aiming to bluff on one of the dice values bet on by previous player\n'
                else:
                    bluff_player = (self.current_player + 1) % self.n_players
                    # print('[DEBUG] bluffing on next player')
                    self.players[self.current_player].reasoning_string += 'Aiming to bluff on one of the dice values bet on by next player\n'

                retrieve_chunk = Chunk(name="partial-test", slots={"type": "bid_memory", "player": bluff_player})
                chunk, latency = self.players[self.current_player].model.retrieve(
                    retrieve_chunk)  # retrieve a chunk from declarative memory

                self.players[self.current_player].reasoning_string += f'Trying to memorize a chunk containing a value Player {bluff_player} has bid on\n'

                if chunk is not None:  # a chunk was retrieved
                    self.chunk_retrieval_count += 1
                    # print(chunk)
                    roll = chunk.slots['dice_value']  #
                    # print(f'[MODEL] Player {self.current_player} will bluff on {roll}, since Player {bluff_player}
                    # has bid on {roll} before')
                    self.players[self.current_player].reasoning_string += f'Retrieved a chunk containing that {bluff_player} has bet on {roll} this round\n'
                    self.players[self.current_player].reasoning_string += f'Bluffing on {roll}, since Player {bluff_player} has bet on {roll} before\n'
                else:  # no chunk was retrieved / retrieval failure
                    self.chunk_retrieval_failure_count += 1
                    self.players[self.current_player].reasoning_string += f'No chunk was retrieved\n'
                    self.players[self.current_player].reasoning_string += f'Can not remember a value Player {bluff_player} has bet on before, bluffing on random value\n'
                    # print('[DEBUG] no chunk was retrieved / retrieval failure')
                    roll = random.randint(1, 6)  # bluffing happens on a random die value

                if roll == 1:  # bluff will be on joker dice
                    self.players[
                        self.current_player].reasoning_string += f'Bluffing on joker dice\n'
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

                # print(f'num in hand:{self.players[self.current_player].hand.count(self.players[
                # self.current_player].hand[0])}')

                highest_value = [self.players[self.current_player].hand[m] for m in
                                 range(len(self.players[self.current_player].hand))
                                 if self.players[self.current_player].hand.count(
                        self.players[self.current_player].hand[m]) == n_of_most]

                bid_value = highest_value[random.randint(0, len(
                    highest_value) - 1)]  # determine most common value in hand and choose one of those values from
                # hand (if multiple, chooses randomly)

                roll = bid_value
                self.players[
                    self.current_player].reasoning_string += f'My hand is {self.players[self.current_player].hand}, betting on one of the most common dice values in hand, which is {roll}\n'

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

                self.players[
                    self.current_player].reasoning_string += f'Determined bid is {count} x {roll}\n'
        return count, roll

    def clear_ui_bets(self):
        for idx, player in enumerate(self.players):  # Counts dice, which also determines winner
            if idx != self.player_ID:
                invoker.invoke_in_main_thread(self.ui_controller.display_bet_enemy, enemy_nr=idx,
                                              number="", dice=0)

    ########################################################################
    ######           MAIN LOOP THAT RUNS STATE MACHINE                ######
    ########################################################################

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


            # print(f"[DEBUG] Current Player: {self.current_player} - Current Bid: {self.current_bid} - Current
            # State: {rev_states[self.state]} - Dice in game: {self.n_total_dice}")

            # Games starts and everybody rolls.
            # Nobody should doubt on the first turn.

            if self.state == states['start']:
                self.reset_models()
                self.clear_ui_bets()
                self.current_bid = Bid(1, 0)
                self.update_turn(reset=True)
                print('----------------- NEW ROUND ----------------------')
                print(f'[FIRST TURN]: Player {self.current_player}')
                invoker.invoke_in_main_thread(self.ui_controller.indicate_turn, player=self.current_player)
                self.all_roll()

                print(f'All players rolled the dice! My hand is {self.players[0].hand} \n'
                      f'Total number of dice remaining = {self.n_total_dice} \n')

                for idx, player in enumerate(self.players):  # Counts dice, which also determines winner
                    if idx != self.player_ID:
                        self.players[idx].reasoning_string += f'----------[Model Reasoning]  NEW ROUND ---------------\n'
                        self.players[idx].reasoning_string += f'This text shows the reasoning by Player {idx}\n'
                        self.players[idx].reasoning_string += f'My hand is {self.players[idx].hand}\n'

                invoker.invoke_in_main_thread(self.ui_controller.display_dice_player, dice=self.players[0].hand)

                for idx, player in enumerate(self.players):  # Counts dice, which also determines winner
                    if idx > 0:
                        invoker.invoke_in_main_thread(self.ui_controller.display_anonymous_dice_enemy,
                                                      enemy_nr=idx, dice_count=player.get_hand_size())


                if self.current_player != self.player_ID:
                    invoker.invoke_in_main_thread(self.ui_controller.display_action_enemy,
                                                  enemy_nr=self.current_player,
                                                  action=0)

                    # time.sleep(random.uniform(1.5, 4))  # agent 'thinking'
                    x = len(self.players[self.current_player].model.dm)  # counts number of chunks in memory
                    y = random.uniform(1, 1.5)
                    if x != 0:
                        y += np.log(x * 2)
                    if y < 2.5:
                        y = 2.5
                    print(f'Number of chunks in memory = {x}, Waiting time = {round(y, 2)}s ')
                    time.sleep(y)  # agent 'thinking'

                self.state = states['bidding_phase']
                continue

            # Check whether the current player wants to doubt before asking the bid.
            if self.state == states['doubting_phase']:
                if self.current_player == self.player_ID:
                    print(
                        f'My hand is {self.players[self.player_ID].hand} \nTotal number of dice remaining = {self.n_total_dice}')
                    invoker.invoke_in_main_thread(self.ui_controller.display_dice_player,
                                                  dice=self.players[self.player_ID].hand)

                print(f'[TURN]: Player {self.current_player}')
                invoker.invoke_in_main_thread(self.ui_controller.indicate_turn(player=self.current_player))

                # if self.players[self.current_player].strategy == 'model':
                #     print(f'Number of chunks in dm: {len(self.players[self.current_player].model.dm)}')
                if self.current_player != self.player_ID:
                    invoker.invoke_in_main_thread(self.ui_controller.display_action_enemy,
                                                  enemy_nr=self.current_player,
                                                  action=0)
                    # time.sleep(random.uniform(1.5, 4))  # agent 'thinking'
                    x = len(self.players[self.current_player].model.dm)  # counts number of chunks in memory
                    y = random.uniform(1, 1.5)
                    if x != 0:
                        y += np.log(x * 2)
                    if y < 2.5:
                        y = 2.5
                    print(f'Number of chunks in memory = {x}, Waiting time = {round(y, 2)}s ')
                    time.sleep(y)  # agent 'thinking'
                doubt = self.doubting()

                if doubt:
                    print(f'Player {self.current_player} does not believe the bid of Player {self.previous_player}')
                    if self.current_player != self.player_ID:
                        invoker.invoke_in_main_thread(fn=self.ui_controller.display_action_enemy,
                                                      enemy_nr=self.current_player,
                                                      action=1,
                                                      target=self.previous_player)

                    self.resolve_doubt()
                    print(f'-------Player 1 reasoning ---- \n {self.players[1].reasoning_string} -----------------')
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
                if self.current_player != self.player_ID:
                    invoker.invoke_in_main_thread(self.ui_controller.display_bet_enemy, enemy_nr=self.current_player,
                                                  number=self.current_bid.count, dice=self.current_bid.roll)

                if self.previous_player != self.player_ID and self.previous_player != self.current_player:
                    invoker.invoke_in_main_thread(self.ui_controller.display_bet_enemy, enemy_nr=self.previous_player,
                                                  number="", dice=0)

                if self.current_player != self.player_ID:
                    invoker.invoke_in_main_thread(self.ui_controller.display_action_enemy, enemy_nr=self.current_player,
                                                  action=2)

                self.models_remember_bid()

                self.update_turn()
                self.state = states['doubting_phase']
                continue

            if self.state == states['end']:
                over = True
                if len(winner) <= 1:
                    print(f"Player {winner[0]} has played away all its dice and won the game!.")
                    invoker.invoke_in_main_thread(self.ui_controller.display_winner_and_close, player=winner[0])
                else:
                    winners = str(winner)[1:-1]
                    print(f"Players {winners} have played away all their dice and won the game!.")
                    invoker.invoke_in_main_thread(self.ui_controller.display_winner_and_close, player=winners)
                continue

        print(f'Chunks retrieved during game: {self.chunk_retrieval_count}')
        print(f'Chunk retrieve failures during game: {self.chunk_retrieval_failure_count}')
        print('Game Finished!')
        quit(0)


"""
#TODO: 
- Create Reasoning text file for every ACT-R agent (concatenate strings of text). Make available as option to show
- Highlight dice correctly in final dice count (now todo: add for human player). Also add button or click to continue for user after game is finished, such that it has time to count
- Enemy bet not always shown (fixed I think)
"""
