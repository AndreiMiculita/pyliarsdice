import random
from die import Die


class Player:
    def __init__(self, n_dice):
        """
        Defines an object Player in a game of Liar's Dice.\n
        :param n_dice: Number of dice the player is initialized with.
        """
        self.hand = []
        for _ in range(n_dice):
            self.hand.append(Die())

    def get_hand_size(self):
        return len(self.hand)

    def remove_die(self):
        """
        Removes a single die from the hand of the player.\n
        :return: The removed die.
        """
        return self.hand.pop()

    def add_die(self):
        """
        Adds a single die to the hand of the player.\n
        :return:
        """
        self.hand.append(Die())

    def roll_hand(self):
        """
        Randomly changes the values of the dice in the player's hand.\n
        :return: The new hand.
        """
        for die in self.hand:
            die.roll()
        return self.hand

    def get_roll_count(self, roll):
        """
        Counts the number of dice in the hand with the determined value.\n
        :param roll: The value of the dice to be counted.\n
        :return: The number of dice with the determined value.
        """
        count = 0
        for die in self.hand:
            if die.value == roll:
                count += 1

        return count
