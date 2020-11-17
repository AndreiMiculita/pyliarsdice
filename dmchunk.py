class Chunk(object):

    def __init__(self, name, slots):
        self.name = name
        self.slots = slots
        self.encounters = []
        self.fan = 0  # How many other chunks refer to this chunk?

    def add_encounter(self, time):
        """
        Add an encounter of this chunk at the specified time.
        """
        if time not in self.encounters:
            self.encounters.append(time)

    def __str__(self):
        return f"Chunk {self.name}\n" \
               f"Slots: {self.slots}\n" \
               f"Encounters: {self.encounters}\n" \
               f"Fan: {self.fan}\n"

