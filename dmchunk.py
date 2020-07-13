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
        return f'Chunk {str(self.name)}\nSlots: {str(self.slots)}\nEncounters: {str(self.encounters)}\nFan: {str(self.fan)}\n '
