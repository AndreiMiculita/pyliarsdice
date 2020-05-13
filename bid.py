class Bid:
    def __init__(self, count, roll):
        """
        Initialize a Bid object with the value and number of dice in game.\n
        :param count: The number of dice in game with 'roll' value.\n
        :param roll: The value to count.
        """
        self.count = count
        self.roll = roll

    def __str__(self):
        return f"[{self.count}, {self.roll}]"
