import random


class Die:
    def __init__(self):
        """
        Initialize an Die object with a random value in the [1,6] range.
        """
        self.value = random.randint(1, 6)

    def roll(self):
        """
        Randomly changes the value of the die.\n
        :return: The new roll integer value.
        """
        self.value = random.randint(1, 6)
        return self.value
