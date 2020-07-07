import random
from die import Die
from model import Model
from dmchunk import Chunk


class Player:
    def __init__(self, n_starting_dice, difficulty):
        """
        Defines an object Player in a game of Liar's Dice.\n
        :param n_dice: Number of dice the player is initialized with.
        """
        self.n_dice = n_starting_dice
        self.hand = []

        # for _ in range(n_starting_dice):
        #     self.hand.append(Die())
        for _ in range(n_starting_dice): # die object redundant, using ints is probably easier
            self.hand.append(random.randint(1, 6))
        self.hand.sort()

        if difficulty == 1:
            self.strategy = 'random'
        elif difficulty == 2:
            self.strategy = 'model'
            self.model = Model()


    def get_hand_size(self):
        return len(self.hand)

    def remove_die(self):
        """
        Removes a single die from the hand of the player.\n
        :return: The removed die.
        """
        self.n_dice -= 1
        return self.hand.pop()


    def add_die(self):
        """
        Adds a single die to the hand of the player.\n
        :return:
        """

        # self.hand.append(Die())

        self.n_dice += 1
        random.randint(1, 6)

        self.hand.sort()

    def roll_hand(self):
        """
        Randomly changes the values of the dice in the player's hand.\n
        :return: The new hand.
        """


        # for die in self.hand:
        #     die.roll()
        #
        #
        #
        # return self.hand

        self.hand = []
        for _ in range(self.n_dice):  # die object redundant, using ints is probably easier
            self.hand.append(random.randint(1, 6))
        self.hand.sort()

    def get_roll_count(self, roll):
        """
        Counts the number of dice in the hand with the determined value.\n
        :param roll: The value of the dice to be counted.\n
        :return: The number of dice with the determined value.
        """

        return self.hand.count(roll)

        # count = 0
        #
        # for die in self.hand:
        #     if die == roll:
        #         count += 1
        #
        # return count

    def renew_model(self):
        self.model = Model()