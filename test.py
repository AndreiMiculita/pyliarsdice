from game import Game
from model import Model
from dmchunk import Chunk


def most_common(lst):
    return max(set(lst), key=lst.count)

def test():


    # m = Model()
    # print(m)
    #
    # g = Chunk(name="goal-chunk", slots={"goal": "count", "current": "two"})
    # m.goal = g
    #
    # print(m)
    #
    # c1 = Chunk(name="c1", slots={"type": "numbers", "val1": 1, "val2": 2, "word": "two"})
    # c2 = Chunk(name="c2", slots={"type": "numbers", "val1": 2, "val2": 3, "word": "three"})
    #
    # m.add_encounter(c1)
    # m.add_encounter(c2)
    #
    # m.time += 15  # Advance the model time by 15 seconds
    # m.add_encounter(c2)
    #
    # m.time += 20
    # m.add_encounter(c1)
    #
    # m.time += 5
    # m.add_encounter(c2)
    #
    # print(m)
    #
    # list = [5,4,3,5]
    # print(list.count(5))



    game = Game(n_players=3, n_starting_dice=5)
    game.play()

    #
    # d = Dice()
    # print(d.faceValue)

    # p = Player()
    # print(p.getHand())
    # print(p.getRollNumber(2))
    # p.addDice()
    # print(p.getHand())
    # p.rollHand()
    # print(p.getHand())
    # p.loseDice()
    # print(p.getHand())


if __name__ == '__main__':
    test()
