import numpy as np
from model import Model
from dmchunk import Chunk
import matplotlib.pyplot as plt

def test():
    m = Model()
    print(m)

    g = Chunk(name="goal-chunk", slots={"goal": "count", "current": "two"})
    m.goal = g

    print(m)

    c1 = Chunk(name="c1", slots={"type": "numbers", "val1": 1, "val2": 2, "word": "two"})
    c2 = Chunk(name="c2", slots={"type": "numbers", "val1": 2, "val2": 3, "word": "three"})

    m.add_encounter(c1)
    m.add_encounter(c2)

    m.time += 15  # Advance the model time by 15 seconds
    m.add_encounter(c2)

    m.time += 20
    m.add_encounter(c1)

    m.time += 5
    m.add_encounter(c2)

    print(m)

if __name__ == '__main__':
    test()




