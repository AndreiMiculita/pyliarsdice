import time
import threading
import time
from multiprocessing import Queue

from PySide2 import QtCore
from PySide2.QtCore import QSize
from PySide2.QtGui import QMovie, QPixmap
from PySide2.QtWidgets import QWidget, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QSpinBox, QPushButton, \
    QMessageBox

from game import Game
from ui_controller import UIController

dice_images = ["assets/images/dice-blank.png",
               "assets/images/dice-1-star.png",
               "assets/images/dice-2.png",
               "assets/images/dice-3.png",
               "assets/images/dice-4.png",
               "assets/images/dice-5.png",
               "assets/images/dice-6.png"]

dice_image_unknown = "assets/images/dice-q.png"


class MainWidget(QWidget, UIController):

    def __init__(self, difficulty: int, n_opponents: int):
        """
        This widget is everything in the window, except for the menu bar and status bar.
        :param difficulty: an integer value for the difficulty (0: random, 1: model)
        :param n_opponents: integer representing how many opponents there are
        """
        super(MainWidget, self).__init__()
        self.turn_label = QLabel(text="")
        self.actions_group = QGroupBox('Your Action', objectName="ActionsGroup")  # objectName required for CSS
        self.call_bluff_button = QPushButton('CALL BLUFF (C)')
        self.trust_button = QPushButton('BELIEVE BID (T)')
        self.bet_button = QPushButton('BET (B)')
        self.all_enemies_group = QGroupBox("Enemies")  # Use findChild to address individual components for each enemy
        self.select_dice_spin_box = QSpinBox()
        self.select_number_spin_box = QSpinBox()
        self.player_cup_group = QGroupBox("Your Cup")
        self.n_opponents = n_opponents
        self.set_bluff_controls_enabled(False)
        self.set_bet_controls_enabled(False)
        self.init_ui()

        for enemy_nr in range(1, n_opponents + 1):
            self.display_bet_enemy(enemy_nr=enemy_nr, number=0, dice=0)

        self.q = Queue()

        # Difficulty is 0, 1 in UI but 1, 2 in Game object, so add 1
        self.game = Game(ui_controller=self, n_players=n_opponents + 1, n_starting_dice=5, difficulty=difficulty + 1,
                         input_queue=self.q)

        self.game_thread = threading.Thread(target=self.game.play)

        self.game_thread.start()

    def init_ui(self) -> None:
        """
        Initialize UI layout. There shouldn't be any functionality here
        """
        vertical_main_layout = QGridLayout()
        vertical_main_layout.setSpacing(10)

        # Enemy half of the screen -------------------------

        # Display all enemies in a group with a horizontal layout
        all_enemies_layout = QHBoxLayout()

        for i in range(0, self.n_opponents):
            enemy_group = QGroupBox(f"Player {i + 1}")  # Player 0 is human user
            enemy_layout = QGridLayout()

            # Enemy cup
            # Before the cup is lifted, this should only show dice with question marks, or the number of dice under it,
            # but not the types
            # Note that enemies are indexed from 1, player is 0
            enemy_cup_group = QGroupBox("Enemy Cup", objectName=f"enemy_cup{i + 1}")
            enemy_cup_group.setProperty("cssClass", "cup")

            enemy_bet_group = QGroupBox("Enemy Bet")
            enemy_bet_layout = QHBoxLayout()

            # Here we display the amount of dice the enemy has bet
            enemy_number_label = QLabel("", objectName=f"enemy_number{i + 1}")
            enemy_number_label.resize(enemy_number_label.sizeHint())

            enemy_times_label = QLabel("×")
            enemy_times_label.resize(enemy_times_label.sizeHint())

            # Here we display the type of dice the enemy has bet
            enemy_dice_label = QLabel("", objectName=f"enemy_dice{i + 1}")
            enemy_dice_label.resize(enemy_dice_label.sizeHint())

            enemy_bet_layout.addWidget(enemy_number_label)
            enemy_bet_layout.addWidget(enemy_times_label)
            enemy_bet_layout.addWidget(enemy_dice_label)

            enemy_bet_group.setLayout(enemy_bet_layout)

            # Here we'll show if the enemy is thinking, or if they call your bluff
            enemy_action_group = QGroupBox("Enemy Action", objectName=f"enemy_action_group{i + 1}")
            # print(f"init i = {i}")

            enemy_layout.addWidget(enemy_cup_group, 0, 0, 1, 2)
            enemy_layout.addWidget(enemy_bet_group, 1, 0, 1, 1)
            enemy_layout.addWidget(enemy_action_group, 1, 1, 1, 1)

            enemy_group.setLayout(enemy_layout)

            all_enemies_layout.addWidget(enemy_group)

        self.all_enemies_group.setLayout(all_enemies_layout)

        # Player half of the screen -------------------------

        self.player_cup_group.setProperty("cssClass", "cup")

        player_bet_group = QGroupBox("Your Bet")
        player_bet_layout = QHBoxLayout()

        # Here the player can select the number of dice to bet
        select_number_layout = QVBoxLayout()
        select_number_label = QLabel("Number")
        self.select_number_spin_box.setRange(1, 6)
        select_number_layout.addWidget(select_number_label)
        select_number_layout.addWidget(self.select_number_spin_box)

        player_times_label = QLabel("×")
        player_times_label.resize(player_times_label.sizeHint())

        # Here the player can select the type of dice to bet
        select_dice_layout = QVBoxLayout()
        select_dice_label = QLabel("Dice")
        self.select_dice_spin_box.setRange(1, 6)
        select_dice_layout.addWidget(select_dice_label)
        select_dice_layout.addWidget(self.select_dice_spin_box)

        player_bet_layout.addLayout(select_number_layout)
        player_bet_layout.addWidget(player_times_label)
        player_bet_layout.addLayout(select_dice_layout)

        player_bet_group.setLayout(player_bet_layout)

        # This is a group that contains the buttons for betting and calling a bluff
        # The buttons are linked to the functions below this function
        actions_layout = QVBoxLayout()

        self.bet_button.setShortcut("B")
        self.bet_button.setStatusTip('Bet the selected amount and dice.')
        self.bet_button.clicked.connect(self.bet)

        self.call_bluff_button.setShortcut("C")
        self.call_bluff_button.setStatusTip("Call the opponent's bluff.")
        self.call_bluff_button.clicked.connect(self.call_bluff)

        self.trust_button.setShortcut("T")
        self.trust_button.setStatusTip("Trust the opponent.")
        self.trust_button.clicked.connect(self.trust)

        actions_layout.addWidget(self.bet_button)
        actions_layout.addWidget(self.call_bluff_button)
        actions_layout.addWidget(self.trust_button)

        self.actions_group.setLayout(actions_layout)

        # Put all the groups into a vertical layout
        vertical_main_layout.addWidget(self.turn_label, 0, 0, 1, 2)
        vertical_main_layout.addWidget(self.all_enemies_group, 1, 0, 2, 2)
        vertical_main_layout.addWidget(self.player_cup_group, 3, 0, 1, 2)
        vertical_main_layout.addWidget(player_bet_group, 4, 0, 1, 1)
        vertical_main_layout.addWidget(self.actions_group, 4, 1, 1, 1)
        self.setLayout(vertical_main_layout)

    def bet(self):
        """
        Action to be done when the "bet" button is pressed (i.e. get values from spinboxes and send them to the game)
        Prints bet to stdout, and also sends it into the input queue
        :return:
        """
        print(int(self.select_number_spin_box.value()))
        self.q.put(int(self.select_number_spin_box.value()))
        time.sleep(0.1)  # Wait for 2nd question
        print(int(self.select_dice_spin_box.value()))
        self.q.put(int(self.select_dice_spin_box.value()))

    def call_bluff(self):
        """
        Action to be done when the "call bluff" button is pressed (send signal to the game)
        Prints action to stdout, and also sends it into the input queue
        :return:
        """
        print("1")
        self.q.put("1")

    def trust(self):
        """
        Action to be done when the "trust" button is pressed (send signal to the game)
        Prints action to stdout, and also sends it into the input queue
        :return:
        """
        print("0")
        self.q.put("0")

    def display_dice_player(self, dice: [int]):
        """
        Display the dice under the player's cup
        :param dice: list of dice numbers that the player is holding
        :return:
        """
        player_cup_layout = QHBoxLayout()
        for die in dice:
            # print(die, dice_images[die - 1])
            die_image = QPixmap(dice_images[die])
            die_image = die_image.scaled(50, 50, QtCore.Qt.KeepAspectRatio)
            die_img_label = QLabel()
            die_img_label.setPixmap(die_image)
            die_img_label.setScaledContents(False)
            player_cup_layout.addWidget(die_img_label)
        self.player_cup_group.setLayout(player_cup_layout)

    def display_anonymous_dice_enemy(self, enemy_nr: int, dice_count: int):
        """
        Display how many dice the enemy has, without showing what they are
        :param enemy_nr: which enemy to display the dice for
        :param dice_count: how many anonymous dice to display
        :return:
        """
        enemy_cup_layout = QHBoxLayout()
        for die in range(dice_count):
            die_image = QPixmap(dice_image_unknown)
            die_image = die_image.scaled(50, 50, QtCore.Qt.KeepAspectRatio)
            die_img_label = QLabel()
            die_img_label.setPixmap(die_image)
            die_img_label.resize(50, 50)
            die_img_label.setScaledContents(False)
            enemy_cup_layout.addWidget(die_img_label)
        enemy_cup_group = self.all_enemies_group.findChild(QGroupBox, f"enemy_cup{enemy_nr}")
        if enemy_cup_group is not None:
            enemy_cup_group.setLayout(enemy_cup_layout)
        else:
            print(f"enemy {enemy_nr} cup group not found")

    def display_dice_enemy(self, enemy_nr: int, dice: [int]):
        """
        Displays what dice the enemy has
        :param enemy_nr: which enemy to display the dice for
        :param dice: list of dice numbers that the enemy is holding
        :return:
        """
        enemy_cup_layout = QHBoxLayout()
        for die in dice:
            # print(die, dice_images[die - 1])
            die_image = QPixmap(dice_images[die])
            die_image = die_image.scaled(50, 50, aspectMode=QtCore.Qt.KeepAspectRatio,
                                         mode=QtCore.Qt.SmoothTransformation)
            die_img_label = QLabel()
            die_img_label.setPixmap(die_image)
            die_img_label.resize(50, 50)
            die_img_label.setScaledContents(False)
            enemy_cup_layout.addWidget(die_img_label)
        enemy_cup_group = self.all_enemies_group.findChild(QGroupBox, f"enemy_cup{enemy_nr}")
        if enemy_cup_group is not None:
            enemy_cup_group.setLayout(enemy_cup_layout)
        else:
            print(f"enemy {enemy_nr} cup group not found")

    def display_action_enemy(self, enemy_nr: int, action: int, target: int = 0):
        """
        Display which action an enemy is currently executing
        :param enemy_nr: which enemy to display the action for
        :param action: id of the action: 0 - thinking, 1 - doubting, 2 - waiting
        :param target: (optional)  who the action is directed towards (e.g. who they are doubting)
        :return:
        """
        # TODO: implement this
        enemy_action_layout = QVBoxLayout()
        enemy_action_image_label = QLabel()

        if action == 0:
            enemy_action_label = QLabel("Thinking", objectName=f"enemy_action_label{enemy_nr}")
            # use https://loading.io/
            enemy_loading_movie = QMovie("assets/images/loader.gif")
        elif action == 1:
            enemy_action_label = QLabel(f"Doubting player{target}!", objectName=f"enemy_action_label{enemy_nr}")
            enemy_loading_movie = QMovie("assets/images/exclamation.gif")
        elif action == 2:
            enemy_action_label = QLabel("Waiting", objectName=f"enemy_action_label{enemy_nr}")
            enemy_loading_movie = QMovie("assets/images/waiting.gif")
        else:
            pass

        enemy_loading_movie.setScaledSize(QSize(50, 50))
        enemy_action_image_label.setMovie(enemy_loading_movie)
        enemy_loading_movie.start()
        enemy_action_layout.addWidget(enemy_action_label)
        enemy_action_layout.addWidget(enemy_action_image_label)
        enemy_action_group = self.all_enemies_group.findChild(QGroupBox, f"enemy_action_group{enemy_nr}")
        if enemy_action_group is not None:
            enemy_action_group.setLayout(enemy_action_layout)
        else:
            print(f"Enemy {enemy_nr} action group not found")

    def display_bet_enemy(self, enemy_nr: int, number: int, dice: int):
        """
        Displays what the enemy has bet
        :param enemy_nr: which enemy has bet
        :param number: how many dice the enemy has bet
        :param dice: what dice (1-6) the enemy has bet
        :return:
        """
        number_label = self.all_enemies_group.findChild(QLabel, f"enemy_number{enemy_nr}")
        if number_label is not None:
            number_label.setText(str(number))
        else:
            print(f"Number label for enemy{enemy_nr} not found")
        dice_label: QLabel = self.all_enemies_group.findChild(QLabel, f"enemy_dice{enemy_nr}")
        if dice_label is not None:
            die_image = QPixmap(dice_images[dice])
            die_image = die_image.scaled(50, 50, aspectMode=QtCore.Qt.KeepAspectRatio,
                                         mode=QtCore.Qt.SmoothTransformation)
            dice_label.setPixmap(die_image)
            dice_label.resize(50, 50)
            dice_label.setScaledContents(False)
        else:
            print(f"Dice label for enemy{enemy_nr} not found")

    def set_bet_limits(self, number_min: int, number_max: int, dice_min: int, dice_max: int):
        """
        Set the limits for the spinboxes
        :param number_min: min limit for number of dice
        :param number_max: max limit for type of dice
        :param dice_min: min limit for type of dice
        :param dice_max: max limit for type of dice
        :return:
        """
        self.select_number_spin_box.setRange(number_min, number_max)
        self.select_dice_spin_box.setRange(dice_min, dice_max)

    def set_bluff_controls_enabled(self, enabled: bool):
        """
        Enables or disables the call bluff/trust buttons
        :param enabled: whether the controls are enabled or not
        :return:
        """
        self.call_bluff_button.setEnabled(enabled)
        self.trust_button.setEnabled(enabled)

    def set_bet_controls_enabled(self, enabled: bool):
        """
        Enables or disables the bet button and spinboxes
        :param enabled: whether the controls are enabled or not
        :return:
        """
        self.select_number_spin_box.setEnabled(enabled)
        self.select_dice_spin_box.setEnabled(enabled)
        self.bet_button.setEnabled(enabled)

    def indicate_turn(self, player: int):
        """
        This indicates whose turn it is, in the label at the top of the window.
        :param player: int  with value 0 for human player, >0 for opponents
        :return:
        """
        if player == 0:
            self.turn_label.setText("Your turn")
        else:
            self.turn_label.setText(f"Opponent {player}'s turn")

    def display_winner_and_close(self, player: int):
        reply = QMessageBox.question(self, 'End of game',
                                     f"Player {player} won! Close the game?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.close()
        else:
            self.close()

    def __delete__(self, instance):
        self.game.over = True
        super(MainWidget, self).__delete__()
