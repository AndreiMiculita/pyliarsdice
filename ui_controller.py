class UIController:
    """
    This is a base class which must be inherited by the main widget.
    Basically an interface to avoid cyclical imports.
    """

    def display_dice(self, player_nr: int, dice: [int], highlight: int):
        return NotImplemented

    def display_rolling_dice(self, player_nr: int, dice_count: int):
        return NotImplemented

    def display_anonymous_dice(self, player_nr: int, dice_count: int):
        return NotImplemented

    def display_action_enemy(self, enemy_nr: int, action: int, target: int):
        return NotImplemented

    def display_bet_enemy(self, enemy_nr: int, number: int, dice: int):
        return NotImplemented

    def set_bet_limits(self, number_min: int, number_max: int, dice_min: int, dice_max: int):
        return NotImplemented

    def set_bluff_controls_enabled(self, enabled: bool, target: int):
        return NotImplemented

    def set_bet_controls_enabled(self, enabled: bool, previous_bet: str):
        return NotImplemented

    def indicate_turn(self, player: int):
        return NotImplemented

    def display_winner_and_close(self, player: int):
        return NotImplemented
