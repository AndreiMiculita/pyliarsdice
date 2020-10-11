import random

from dmchunk import Chunk
from game import Game
from model import Model
from scipy.stats import binom
import numpy as np
import random


def determine_probability(difference, n_unknown_dice, roll_prob):
    # determines the probability of at least n times a diceValue in m unknown dice

    p = 0
    for k in range(difference, n_unknown_dice + 1):
        p += binom.pmf(k, n_unknown_dice, roll_prob)

    return p


def most_common(lst):
    return max(set(lst), key=lst.count)


def test():
    # p = determine_probability(5,10,1/3)
    # print(p)

    # print(m)

    # This loops tests the number of chunks used / encountered wrt time
    rem_chunk = 0
    not_rem_chunk = 0

    for _ in range(1000):
        m = Model()

        ch = Chunk(name="bid_memory" + str(1),
                   slots={"type": "bid_memory",
                          "player": 1,
                          "dice_value": 5})  # remember the value a player has bid on

        m.add_encounter(ch)  # remember the bid of a player
        m.time += round(random.uniform(2.5, 4),
                        2)  # add time according to length of a turn, might need adjustment
        # m.add_encounter(ch)

        ch = Chunk(name="bid_memory" + str(2),
                   slots={"type": "bid_memory",
                          "player": 2,
                          "dice_value": 6})  # remember the value a player has bid on

        m.add_encounter(ch)  # remember the bid of a player
        m.time += round(random.uniform(2.5, 4),
                        2)  # add time according to length of a turn, might need adjustment

        ch = Chunk(name="bid_memory" + str(3),
                   slots={"type": "bid_memory",
                          "player": 3,
                          "dice_value": 4})  # remember the value a player has bid on

        m.add_encounter(ch)  # remember the bid of a player
        m.time += round(random.uniform(2.5, 4),
                        2)  # add time according to length of a turn, might need adjustment
        # print(len(m.dm))
        retrieve_chunk = Chunk(name="partial-test", slots={"type": "bid_memory", "player": 3})
        chunk, latency = m.retrieve(retrieve_chunk)
        if chunk is not None:
            rem_chunk += 1

        else:
            chunk, latency = m.retrieve(retrieve_chunk)
            if chunk is not None:
                rem_chunk += 1
            else:
                # chunk, latency = m.retrieve(retrieve_chunk)
                # if chunk is not None:
                #     rem_chunk += 1
                #
                # else:
                    not_rem_chunk += 1
                    # print('ja')


    print(f'remembered chunks: {rem_chunk}')
    print(f'not remembered chunks: {not_rem_chunk}')

    #
    # hand = [2,2,4,4,6,6]
    # m = most_common(hand)
    # n_of_most = hand.count(m)
    # print(range(len(hand)))
    # print(hand.count(6))
    # highest_value = [hand[m] for m in range(len(hand)) if hand.count(hand[m]) == n_of_most]
    #
    # print(highest_value)
    #
    # bid_value = highest_value[random.randint(0, len(highest_value) - 1)]
    # print(bid_value)

    # chunk, latency = m.retrieve_partial(retrieve_chunk, trace=True)

    # print(chunk.player)
    #
    # game = Game(n_players=4, n_starting_dice=5)
    # game.play()


def test2():
    for x in range(1, 10):
        y = np.log(x * 2) + random.uniform(2, 2.5)
        print(f'Number of chunks in memory = {x}, Waiting time = {round(y, 2)}s ')

    print(np.sort([2,3,1]))

if __name__ == '__main__':
    test2()
