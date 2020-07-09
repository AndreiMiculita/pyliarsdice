from game import Game
from model import Model
from dmchunk import Chunk
from scipy.stats import binom



def determine_probability(difference, n_unknown_dice, roll_prob):
    # determines the probability of at least n times a diceValue in m unknown dice

    p = 0
    for k in range(difference, n_unknown_dice + 1):
        p += binom.pmf(k, n_unknown_dice, roll_prob)

    return p


def test():

    # p = determine_probability(5,10,1/3)
    # print(p)
    # m = Model()
    # print(m)
    #
    # g = Chunk(name="goal-chunk", slots={"goal": "count",



    game = Game(n_players=3, n_starting_dice=5)
    game.play()



if __name__ == '__main__':
    test()
