class UIController:
    """
    This is a base class which must be inherited by the main widget.
    Basically an interface to avoid cyclical imports
    """

    def display_dice_player(self, dice: [int]):
        return NotImplemented

    def display_anonymous_dice_enemy(self, enemy_nr: int, dice_count: int):
        return NotImplemented

    def display_dice_enemy(self, enemy_nr: int, dice: [int]):
        return NotImplemented

    def display_action_enemy(self, enemy_nr: int, action: int):
        return NotImplemented

    def display_bet_enemy(self, enemy_nr: int, number: int, dice: int):
        return NotImplemented

    def set_bet_limits(self, number_min: int, number_max: int, dice_min: int, dice_max: int):
        return NotImplemented
