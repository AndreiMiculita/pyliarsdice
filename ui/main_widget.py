import threading
import time

from PySide2 import QtCore, QtGui
from PySide2.QtCore import QSize
from PySide2.QtGui import QMovie, QPixmap
from PySide2.QtWidgets import QWidget, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QSpinBox, QPushButton
from game import Game

dice_images = ["assets/images/dice-1-star.png",
               "assets/images/dice-2.png",
               "assets/images/dice-3.png",
               "assets/images/dice-4.png",
               "assets/images/dice-5.png",
               "assets/images/dice-6.png"]

dice_image_unknown = "assets/images/dice-q.png"


class MainWidget(QWidget):

    def __init__(self, difficulty: int, opponents: int):
        """
        This widget is everything in the window, except for the menu bar and status bar.
        :param difficulty: an integer value for the difficulty (0: random, 1: model)
        :param opponents: integer representing how many opponents there are
        """
        super(MainWidget, self).__init__()
        self.all_enemies_group = QGroupBox("Enemies")
        self.select_dice_spin_box = QSpinBox()
        self.select_number_spin_box = QSpinBox()
        self.player_cup_group = QGroupBox("Your Cup")
        self.opponents = opponents
        self.init_ui()
        print(f"Difficulty: {difficulty}")
        # Difficulty is 0, 1 in UI but 1, 2 in Game object, so add 1
        self.game = Game(n_players=opponents + 1, n_starting_dice=5, difficulty=difficulty + 1)
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

        for i in range(0, self.opponents):
            enemy_group = QGroupBox(f"Player {i + 1}")  # Player 0 is human user
            enemy_layout = QGridLayout()

            # Enemy cup
            # Before the cup is lifted, this should only show dice with question marks, or the number of dice under it,
            # but not the types
            enemy_cup_group = QGroupBox("Enemy Cup", objectName=f"enemy_cup{i}")
            enemy_cup_group.setProperty("cssClass", "cup")

            enemy_bet_group = QGroupBox("Enemy Bet")
            enemy_bet_layout = QHBoxLayout()

            # Here we display the amount of dice the enemy has bet
            enemy_number_label = QLabel("1", objectName=f"enemy_number{i}")
            enemy_number_label.resize(enemy_number_label.sizeHint())

            enemy_times_label = QLabel("×")
            enemy_times_label.resize(enemy_times_label.sizeHint())

            # Here we display the type of dice the enemy has bet
            enemy_dice_label = QLabel("1", objectName=f"enemy_dice{i}")
            enemy_dice_label.resize(enemy_dice_label.sizeHint())

            enemy_bet_layout.addWidget(enemy_number_label)
            enemy_bet_layout.addWidget(enemy_times_label)
            enemy_bet_layout.addWidget(enemy_dice_label)

            enemy_bet_group.setLayout(enemy_bet_layout)

            # Here we'll show if the enemy is thinking, or if they call your bluff
            enemy_action_group = QGroupBox("Enemy Action")
            enemy_action_layout = QVBoxLayout()
            enemy_action_label = QLabel("Thinking", objectName=f"enemy_action{i}")

            # use https://loading.io/
            enemy_loading_label = QLabel()
            enemy_loading_movie = QMovie("assets/images/loader.gif")
            enemy_loading_movie.setScaledSize(QSize(50, 50))
            enemy_loading_label.setMovie(enemy_loading_movie)
            enemy_loading_movie.start()
            enemy_action_layout.addWidget(enemy_action_label)
            enemy_action_layout.addWidget(enemy_loading_label)
            enemy_action_group.setLayout(enemy_action_layout)

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
        actions_group = QGroupBox('Your Action')
        actions_layout = QVBoxLayout()

        bet_btn = QPushButton('BET (B)')
        bet_btn.setShortcut("B")
        bet_btn.setStatusTip('Bet the selected amount and dice.')
        bet_btn.clicked.connect(self.bet)

        call_bluff_btn = QPushButton('CALL BLUFF (C)')
        call_bluff_btn.setShortcut("C")
        call_bluff_btn.setStatusTip("Call the opponent's bluff.")
        bet_btn.clicked.connect(lambda: self.display_anonymous_dice_enemy(1, 2))

        actions_layout.addWidget(bet_btn)
        actions_layout.addWidget(call_bluff_btn)

        actions_group.setLayout(actions_layout)

        # Put all the groups into a vertical layout
        vertical_main_layout.addWidget(self.all_enemies_group, 0, 0, 2, 2)
        vertical_main_layout.addWidget(self.player_cup_group, 2, 0, 1, 2)
        vertical_main_layout.addWidget(player_bet_group, 3, 0, 1, 1)
        vertical_main_layout.addWidget(actions_group, 3, 1, 1, 1)
        self.setLayout(vertical_main_layout)

    def bet(self):
        """
        Action to be done when the "bet" button is pressed (i.e. get values from spinboxes and send them to the game)
        :return:
        """
        print(int(self.select_number_spin_box.value()))
        time.sleep(0.1)  # Wait for 2nd question
        print(int(self.select_dice_spin_box.value()))
        return NotImplemented

    def call_bluff(self):
        """
        Action to be done when the "call bluff" button is pressed (send signal to the game)
        :return:
        """
        print("1")
        return NotImplemented

    def display_dice_player(self, dice: [int]):
        """
        Display the dice under the player's cup
        :param dice: list of dice numbers that the player is holding
        :return:
        """
        player_cup_layout = QHBoxLayout()
        for die in dice:
            print(die, dice_images[die - 1])
            die_image = QPixmap(dice_images[die - 1])  # dice images are indexed from 0
            die_image = die_image.scaled(50, 50, QtCore.Qt.KeepAspectRatio)
            die_img_label = QLabel()
            die_img_label.setPixmap(die_image)
            die_img_label.setScaledContents(False)
            player_cup_layout.addWidget(die_img_label)
        self.player_cup_group.setLayout(player_cup_layout)
        return NotImplemented

    def display_anonymous_dice_enemy(self, enemy_nr: int, dice_count: int):
        """

        :param enemy_nr: which enemy to display the dice for
        :param dice_count: how many anonymous dice to display
        :return:
        """
        enemy_cup_layout = QHBoxLayout()
        for die in range(dice_count):
            die_image = QPixmap(dice_image_unknown)  # dice images are indexed from 0
            die_image = die_image.scaled(50, 50, QtCore.Qt.KeepAspectRatio)
            die_img_label = QLabel()
            die_img_label.setPixmap(die_image)
            die_img_label.resize(50, 50)
            die_img_label.setScaledContents(False)
            enemy_cup_layout.addWidget(die_img_label)
        self.all_enemies_group.findChild(QGroupBox, f"enemy_cup{enemy_nr}").setLayout(enemy_cup_layout)

    def display_dice_enemy(self, enemy_nr: int, dice: [int]):
        """

        :param enemy_nr: which enemy to display the dice for
        :param dice: list of dice numbers that the enemy is holding
        :return:
        """
        enemy_cup_layout = QHBoxLayout()
        for die in dice:
            print(die, dice_images[die - 1])
            die_image = QPixmap(dice_images[die - 1])  # dice images are indexed from 0
            die_image = die_image.scaled(50, 50, QtCore.Qt.KeepAspectRatio)
            die_img_label = QLabel()
            die_img_label.setPixmap(die_image)
            die_img_label.resize(50, 50)
            die_img_label.setScaledContents(False)
            enemy_cup_layout.addWidget(die_img_label)
        self.all_enemies_group.findChild(QGroupBox, f"enemy_cup{enemy_nr}").setLayout(enemy_cup_layout)

    def __delete__(self, instance):
        self.game.over = True
        super(MainWidget, self).__delete__()
