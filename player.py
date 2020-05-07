import random
from dice import Dice


class Player:

    def __init__(self):
        self.hand = []
        self.numberOfDiceInHand = 6
        for i in range(self.numberOfDiceInHand):
            self.hand.append(Dice())

    def loseDice(self):
        if self.numberOfDiceInHand < 1:
            print("Error: attempting to remove dice with 0 dice in hand.")
        else:
            self.hand = self.hand[:-1]
            self.numberOfDiceInHand -= 1

    def addDice(self):
        self.hand.append(Dice())
        self.numberOfDiceInHand += 1

    def rollHand(self):
        for index in range(self.numberOfDiceInHand):
            self.hand[index].roll()

    def getRollNumber(self, number):
        rollnumber = 0

        for die in self.hand:
            if die.faceValue == number:
                rollnumber += 1

        return rollnumber

    def getHand(self):
        playerhand = []
        for die in self.hand:
            playerhand.append(die.faceValue)
        return playerhand
    


