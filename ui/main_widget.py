import random
import threading
import time
from io import StringIO
from multiprocessing import Queue
from typing import Union

from PySide2 import QtCore
from PySide2.QtCore import QSize
from PySide2.QtGui import QMovie, QPixmap, Qt, QIcon
from PySide2.QtWidgets import QWidget, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QSpinBox, \
    QPushButton, QMessageBox, QStackedWidget, QFrame, QProgressBar


from game import Game
from ui_controller import UIController

preferred_format = "webp" if "webp" in [s.data().decode() for s in QMovie.supportedFormats()] else "gif"
print("preferred_format", preferred_format)

dice_image_paths = ["assets/images/dice-none.png",
                    "assets/images/dice-1.png",
                    "assets/images/dice-2.png",
                    "assets/images/dice-3.png",
                    "assets/images/dice-4.png",
                    "assets/images/dice-5.png",
                    "assets/images/dice-6.png"]

playercolors = ['none',
    '#ff0000',
    '#0080ff',
    '#e6e600',
    '#6600cc'
]


dice_images_highlighted_paths = ["assets/images/dice-none.png",
                                 f"assets/images/dice-1-hl-anim.{preferred_format}",
                                 f"assets/images/dice-2-hl-anim.{preferred_format}",
                                 f"assets/images/dice-3-hl-anim.{preferred_format}",
                                 f"assets/images/dice-4-hl-anim.{preferred_format}",
                                 f"assets/images/dice-5-hl-anim.{preferred_format}",
                                 f"assets/images/dice-6-hl-anim.{preferred_format}"]

dice_image_unknown_path = "assets/images/dice-q.png"
dice_image_blank_path = "assets/images/dice-blank.png"
dice_images_rolling_paths = [f"assets/images/dice-rolling-1.{preferred_format}",
                             f"assets/images/dice-rolling-2.{preferred_format}",
                             f"assets/images/dice-rolling-3.{preferred_format}"]

check_icon_path = "assets/images/checkmark.png"
excl_icon_path = "assets/images/exclamation_image.png"


class MainWidget(QWidget, UIController):

    def __init__(self, difficulty: int, n_opponents: int, reasoning_file: StringIO):
        """
        This widget is everything in the window, except for the menu bar and status bar.

        :param difficulty: an integer value for the difficulty (0: random, 1: model)
        :param n_opponents: integer representing how many opponents there are
        """
        super(MainWidget, self).__init__()
        self.player_action_group = QStackedWidget()
        self.info_label = QLabel(text="")
        self.info_label.setTextFormat(Qt.RichText)
        self.difficulty_label = QLabel(
            text="Playing against cognitive model(s).<br>" if difficulty == 1 else "Playing against random model(s).<br>")
        self.doubt_or_believe_group = QGroupBox(title='Your Action',
                                                objectName="ActionsGroup")  # objectName required for CSS
        self.call_bluff_button = QPushButton('CALL BLUFF (C)')
        self.trust_button = QPushButton('BELIEVE BID (V)')
        self.bet_button = QPushButton('BET (B)')
        self.continue_timeout_progress = QProgressBar()
        self.continue_button = QPushButton('CONTINUE')
        self.all_enemies_group = QFrame()  # Use findChild to address individual components for each enemy
        self.select_dice_spin_box = QSpinBox()
        self.select_number_spin_box = QSpinBox()
        self.player_cup_group = QGroupBox("Your Cup")
        self.n_opponents = n_opponents
        self.set_bluff_controls_enabled(False)
        self.set_bet_controls_enabled(False)

        self.check_icon = QIcon(check_icon_path)
        self.excl_icon = QIcon(excl_icon_path)

        self.dice_images = [QPixmap(d) for d in dice_image_paths]
        self.dice_images_highlighted = [QMovie(d) for d in dice_images_highlighted_paths]
        self.dice_images_rolling = [QMovie(d) for d in dice_images_rolling_paths]
        self.dice_image_unknown = QPixmap(dice_image_unknown_path)
        self.dice_image_blank = QPixmap(dice_image_blank_path)
        # use https://loading.io/
        self.thinking_image = QMovie(f"assets/images/loader.{preferred_format}")
        self.doubting_image = QMovie(f"assets/images/exclamation.{preferred_format}")
        self.waiting_image = QMovie(f"assets/images/waiting.{preferred_format}")
        self.rolling_image = QMovie(f"assets/images/rolling_dice.{preferred_format}")
        self.believing_image = QMovie(f"assets/images/checkmark.{preferred_format}")

        self.init_ui()

        for enemy_nr in range(1, n_opponents + 1):
            self.display_bet_enemy(enemy_nr=enemy_nr, number="", dice=0)
            self.display_action_enemy(enemy_nr=enemy_nr, action=2)

        self.q = Queue()

        # Difficulty is 0, 1 in UI but 1, 2 in Game object, so add 1
        self.game = Game(ui_controller=self, n_players=n_opponents + 1, n_starting_dice=5, difficulty=difficulty + 1,
                         input_queue=self.q, reasoning_file=reasoning_file)

        self.game_thread = threading.Thread(target=self.game.play)

        self.game_thread.start()

    def init_ui(self) -> None:
        """
        Initialize UI layout. There shouldn't be any functionality here
        """
        vertical_main_layout = QGridLayout()
        vertical_main_layout.setSpacing(10)

        top_group = QFrame()

        top_group_layout = QHBoxLayout()
        top_group_layout.addWidget(self.info_label, alignment=Qt.AlignLeft)
        top_group_layout.addWidget(self.difficulty_label, alignment=Qt.AlignRight)

        top_group.setLayout(top_group_layout)

        # Enemy half of the screen -------------------------

        # Display all enemies in a group with a horizontal layout
        all_enemies_layout = QHBoxLayout()

        for i in range(0, self.n_opponents):
            enemy_group = QGroupBox(f" Player {i + 1} ")  # Player 0 is human user
            color_title = "QGroupBox { border: 3px solid" + playercolors[i+1] +";}"

            enemy_group.setStyleSheet(color_title)
            enemy_layout = QGridLayout()

            # Enemy cup
            # Before the cup is lifted, this should only show dice with question marks, or the number of dice under it,
            # but not the types
            # Note that enemies are indexed from 1, player is 0
            enemy_cup_group = QGroupBox(title="Cup", objectName=f"enemy_cup{i + 1}")
            enemy_cup_group.setProperty("cssClass", "cup")

            enemy_bet_group = QGroupBox("Bet")
            enemy_bet_layout = QHBoxLayout()

            # Here we display the amount of dice the enemy has bet
            enemy_number_label = QLabel(text="", objectName=f"enemy_number{i + 1}")
            enemy_number_label.resize(enemy_number_label.sizeHint())

            enemy_times_label = QLabel(text="", objectName=f"enemy_x{i + 1}")
            enemy_times_label.resize(enemy_times_label.sizeHint())

            # Here we display the type of dice the enemy has bet
            enemy_dice_label = QLabel(text="", objectName=f"enemy_dice{i + 1}")
            enemy_dice_label.resize(enemy_dice_label.sizeHint())

            enemy_bet_layout.addWidget(enemy_number_label)
            enemy_bet_layout.addWidget(enemy_times_label)
            enemy_bet_layout.addWidget(enemy_dice_label)

            enemy_bet_group.setLayout(enemy_bet_layout)

            # Here we'll show if the enemy is thinking, or if they call your bluff
            enemy_action_group = QGroupBox(title="Action", objectName=f"enemy_action_group{i + 1}")
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
        player_bet_layout = QVBoxLayout()
        player_bet_selection_layout = QHBoxLayout()

        # Here the player can select the number of dice to bet
        select_number_layout = QVBoxLayout()
        select_number_label = QLabel("Number")
        self.select_number_spin_box.setRange(1, 6)
        self.select_number_spin_box.setFixedHeight(30)
        self.select_number_spin_box.setFixedWidth(70)
        select_number_layout.addWidget(select_number_label)
        select_number_layout.addWidget(self.select_number_spin_box)

        player_times_label = QLabel("×")
        player_times_label.resize(player_times_label.sizeHint())

        # Here the player can select the type of dice to bet
        select_dice_layout = QVBoxLayout()
        select_dice_label = QLabel("Dice")
        self.select_dice_spin_box.setRange(1, 6)
        self.select_dice_spin_box.setFixedHeight(30)
        self.select_dice_spin_box.setFixedWidth(70)
        select_dice_layout.addWidget(select_dice_label)
        select_dice_layout.addWidget(self.select_dice_spin_box)

        player_bet_selection_layout.addLayout(select_number_layout)
        player_bet_selection_layout.addWidget(player_times_label)
        player_bet_selection_layout.addLayout(select_dice_layout)

        self.bet_button.setShortcut("B")
        self.bet_button.setStatusTip('Bet the selected value and dice.')
        self.bet_button.clicked.connect(self.bet)

        player_bet_layout.addLayout(player_bet_selection_layout)
        player_bet_layout.addWidget(self.bet_button)

        player_bet_group.setLayout(player_bet_layout)

        # This is a group that contains the buttons for betting and calling a bluff
        # The buttons are linked to the functions below this function
        doubt_or_believe_layout = QVBoxLayout()

        self.call_bluff_button.setShortcut("C")
        self.call_bluff_button.setStatusTip("Call the opponent's bluff.")
        self.call_bluff_button.setIcon(self.excl_icon)
        self.call_bluff_button.clicked.connect(self.call_bluff)

        self.trust_button.setShortcut("V")
        self.trust_button.setStatusTip("Believe the opponent.")
        self.trust_button.setIcon(self.check_icon)
        self.trust_button.clicked.connect(self.trust)

        doubt_or_believe_layout.addWidget(self.trust_button)
        doubt_or_believe_layout.addWidget(self.call_bluff_button)

        self.doubt_or_believe_group.setLayout(doubt_or_believe_layout)

        continue_group = QGroupBox("Click or wait to continue")
        continue_layout = QVBoxLayout()

        self.continue_timeout_progress.setValue(0)
        self.continue_timeout_progress.setTextVisible(False)

        self.continue_button.setStatusTip("Click to continue.")
        # self.call_bluff_button.setIcon(self.excl_icon)
        self.continue_button.clicked.connect(self.continue_game)

        continue_layout.addWidget(self.continue_timeout_progress)
        continue_layout.addWidget(self.continue_button)

        continue_group.setLayout(continue_layout)

        self.player_action_group.addWidget(player_bet_group)
        self.player_action_group.addWidget(self.doubt_or_believe_group)
        self.player_action_group.addWidget(continue_group)

        # Put all the groups into a vertical layout
        vertical_main_layout.addWidget(self.all_enemies_group, 0, 0, 2,
                                       2 * self.n_opponents)
        vertical_main_layout.addWidget(top_group, 2, 0, 1,
                                       2 * self.n_opponents)
        vertical_main_layout.addWidget(self.player_cup_group, 3, self.n_opponents - 1, 1, 2)
        vertical_main_layout.addWidget(self.player_action_group, 4, self.n_opponents - 1, 1, 2)
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

    def continue_game(self):
        """
        Action to be done when the "continue" button is pressed (send signal to the game)
        Prints action to stdout, and also sends it into the input queue
        :return:
        """
        print("continue")
        self.q.put("continue")

    def put_layout_in_cup(self, player_nr, layout: QHBoxLayout):
        if player_nr == 0:
            # First remove the old layout
            if self.player_cup_group.layout() is not None:
                # Set new parent for layout, which will be garbage collected
                QWidget().setLayout(self.player_cup_group.layout())
            self.player_cup_group.setLayout(layout)
        else:
            enemy_cup_group = self.all_enemies_group.findChild(QGroupBox, f"enemy_cup{player_nr}")
            if enemy_cup_group is not None:
                # First remove the old layout
                if enemy_cup_group.layout() is not None:
                    # Set new parent for layout, which will be garbage collected
                    QWidget().setLayout(enemy_cup_group.layout())
                enemy_cup_group.setLayout(layout)
            else:
                print(f"enemy {player_nr} cup group not found")

    def get_label_with_img(self, image: Union[QMovie, QPixmap], size: (int, int) = (50, 50)):
        """
        Utility function that uses QPixmap for non-animated and QMovie for animated
        
        :param image: the image to display (as QMovie or QPixmap)
        :param size: size of the image to display
        :return: 
        """
        img_label = QLabel()
        if isinstance(image, QMovie):
            image.setScaledSize(QSize(*size))
            img_label.setMovie(image)
            image.start()
        elif isinstance(image, QPixmap):
            image = image.scaled(*size, aspectMode=QtCore.Qt.KeepAspectRatio,
                                 mode=QtCore.Qt.SmoothTransformation)
            img_label.setPixmap(image)
            img_label.setScaledContents(False)

        return img_label

    def display_dice(self, player_nr: int, dice: [int], state: int = 0, highlight: int = 0):
        """
        Displays what dice a player has

        :param player_nr: which player to display the dice for
        :param dice: list of dice numbers that the player is holding; can also be an integer, if the dice are anonymous or rolling
        :param state: only needed if dice is an int, this tells whether the dice are anonymous (0) or rolling (1)
        :param highlight: only needed if dice is a list, this tells which dice type (1-6) to highlight; 0 for no highlight
        :return:
        """
        player_cup_layout = QHBoxLayout()
        if isinstance(dice, list):
            dice_list = dice
        elif isinstance(dice, int):
            dice_list = range(0, dice)
        else:
            dice_list = []
            print(f"Unknown parameter dice={dice} passed to display_dice")
        for die in dice_list:
            if state == 1:  # rolling
                die_img_label = self.get_label_with_img(random.choice(self.dice_images_rolling))
            else:
                if isinstance(dice, list):  # dice visible, maybe with highlights
                    die_img_label = self.get_label_with_img(
                        self.dice_images_highlighted[die] if (die == highlight or die == 1) and highlight != 0 else
                        self.dice_images[die])
                elif state == 0:  # anonymous
                    die_img_label = self.get_label_with_img(self.dice_image_unknown)
                else:
                    die_img_label = self.get_label_with_img(self.dice_image_blank)
                    print(f"Wrong arguments given to display_dice: {dice}")

            player_cup_layout.addWidget(die_img_label)

        self.put_layout_in_cup(player_nr=player_nr, layout=player_cup_layout)

    def display_action_enemy(self, enemy_nr: int, action: int, target: int = 0):
        """
        Display which action an enemy is currently executing

        :param enemy_nr: which enemy to display the action for
        :param action: id of the action: 0 - thinking, 1 - doubting, 2 - waiting
        :param target: (optional)  who the action is directed towards (e.g. who they are doubting)
        :return:
        """
        enemy_action_layout = QVBoxLayout()

        if action == 0:
            enemy_action_label = QLabel(text="Thinking", objectName=f"enemy_action_label{enemy_nr}")
            enemy_action_image = self.thinking_image
        elif action == 1:
            enemy_action_label = QLabel(text=f"Doubting Player {target}!", objectName=f"enemy_action_label{enemy_nr}")
            enemy_action_image = self.doubting_image
        elif action == 2 or action == 7:
            enemy_action_label = QLabel(text="...", objectName=f"enemy_action_label{enemy_nr}")
            enemy_action_image = self.waiting_image
        elif action == 3:
            enemy_action_label = QLabel(text="Rolling Dice", objectName=f"enemy_action_label{enemy_nr}")
            enemy_action_image = self.rolling_image
        elif action == 4:
            enemy_action_label = QLabel(text=f"Believing Player {target}", objectName=f"enemy_action_label{enemy_nr}")
            enemy_action_image = self.believing_image
        else:
            pass

        enemy_action_image_label = self.get_label_with_img(enemy_action_image, (70, 70))
        enemy_action_layout.addWidget(enemy_action_label)
        enemy_action_layout.addWidget(enemy_action_image_label)
        enemy_action_group = self.all_enemies_group.findChild(QGroupBox, f"enemy_action_group{enemy_nr}")
        if enemy_action_group is not None:
            # First remove the old layout
            if enemy_action_group.layout() is not None:
                # Set new parent for layout, which will be garbage collected
                QWidget().setLayout(enemy_action_group.layout())
            enemy_action_group.setLayout(enemy_action_layout)
        else:
            print(f"Enemy {enemy_nr} action group not found, to display action {action}")

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
            print(f"Number label for enemy{enemy_nr} not found, to display {number}")
        x_label = self.all_enemies_group.findChild(QLabel, f"enemy_x{enemy_nr}")
        if x_label is not None:
            x_label.setText("×" if dice != 0 else "")
        else:
            print(f"X label for enemy{enemy_nr} not found")
        dice_label = self.all_enemies_group.findChild(QLabel, f"enemy_dice{enemy_nr}")
        if dice_label is not None:
            die_image = self.dice_images[dice]
            die_image = die_image.scaled(50, 50, aspectMode=QtCore.Qt.KeepAspectRatio,
                                         mode=QtCore.Qt.SmoothTransformation)
            dice_label.setPixmap(die_image)
            dice_label.resize(50, 50)
            dice_label.setScaledContents(False)
        else:
            print(f"Dice label for enemy{enemy_nr} not found, to display {dice}")

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

    def set_bet_controls_enabled(self, enabled: bool, previous_bet: str = ""):
        """
        Enables or disables the bet button and spinboxes

        :param enabled: whether the controls are enabled or not
        :param previous_bet: bet which must be beaten
        :return:
        """
        self.select_number_spin_box.setEnabled(enabled)
        self.select_dice_spin_box.setEnabled(enabled)
        self.bet_button.setEnabled(enabled)
        self.bet_button.setStatusTip(
            f"Bet the selected value and dice. You must overbid {previous_bet}!" if enabled else f"Cannot bet at the moment.")
        self.player_action_group.setCurrentIndex(0)

    def set_bluff_controls_enabled(self, enabled: bool, target: int = 0):
        """
        Enables or disables the call bluff/trust buttons

        :param enabled: whether the controls are enabled or not
        :param target: who to doubt/trust
        :return:
        """
        self.call_bluff_button.setText(f"CALL PLAYER {target}'S BLUFF (C)" if enabled else f"CALL BLUFF (C)")
        self.trust_button.setText(f"BELIEVE PLAYER {target} (V)" if enabled else f"BELIEVE (V)")

        self.call_bluff_button.setEnabled(enabled)
        self.trust_button.setEnabled(enabled)

        self.player_action_group.setCurrentIndex(1)

    def set_continue_controls_enabled(self, enabled: bool):
        """
        Enables or disables the continue button

        :param enabled: whether the controls are enabled or not
        :return:
        """

        self.continue_timeout_progress.setEnabled(enabled)
        self.continue_button.setEnabled(enabled)
        self.player_action_group.setCurrentIndex(2)

    def set_continue_timeout_progress(self, value: int):
        self.continue_timeout_progress.setValue(value)

    def show_info(self, string: str):
        """
        This indicates whose turn it is, in the label at the top of the window.

        :param string: int  with value 0 for human player, >0 for opponents
        :return:
        """
        self.info_label.setText(string if "<br>" in string else string + "<br>")  # Quick hack to always have 2 lines

    def display_winner_and_close(self, players: list):
        if len(players) <= 1:
            winner = str(players[0])
            end_string = f"Player {winner} has played away all its dice!"
        else:
            winners = str(players)[1:-1]
            end_string = f"Players {winners} have played away all their dice!"

        if 0 in players:
            end_string = end_string + '\nYou won! Close the game?'
        else:
            end_string = end_string + '\nYou lost! Close the game?'

        reply = QMessageBox.question(self, 'End of the game',
                                     end_string, QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.close()
            self.parentWidget().slideInIdx(0)
        else:
            self.close()
            self.parentWidget().slideInIdx(0)
