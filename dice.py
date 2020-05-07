import random


class Dice:

    def __init__(self):
        self.faceValue = random.randint(1, 6)

    def roll(self):
        self.faceValue = random.randint(1, 6)
        return self.faceValue
