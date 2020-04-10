# Allow access to command-line arguments
import sys

# Import the core and GUI elements of Qt
from PySide2.QtGui import *
from PySide2.QtWidgets import *

# color scheme
background_color = "#004400"
background_color_2 = "#008800"
light_brown = "#99621E"
dark_brown = "#2F1000"

# TODO: add formatting (bold, italic, bullets)
how_to_string = "The game consists of multiple rounds. In every round, all players throw their dices under the cup, " \
                "such that the dices are only visible to themselves. Following, one of the players (in particular, " \
                "the player who has lost the previous round) starts with a bid. In a clock-wise fashion, we go to the " \
                "next players turn.\nExcept for the first turn in the round, every player has a choice between two " \
                "types of actions:\n* Overbid the previous player - overbidding means that either the number of dices " \
                "is higher than the bid of the previous player, or the value of the dice is higher with the same " \
                "number of dices as the previous player.\n* Overbidding with Joker dices - a joker dice counts as " \
                "double the number of dices when it's used as a bid. This is because every other value has a double " \
                "chance of appearing on the table (since a joker also counts towards their number), while the joker " \
                "itself is only based on the probability of appearing itself.\nA bid can be anything, independently " \
                "of the roll of dices under the cup. This means bluffing is a substantial part of this game and can " \
                "be strategically used to cause other players to lie.\n* Calling the previous player a liar - " \
                "whenever you believe that the bid of the previous player is a lie (i.e. the number of dices of the " \
                "bid is not on the table), you can call that player a liar. \nAt the point that someone has performed " \
                "the action of calling the previous player a liar, every player has to specify whether he or she " \
                "believes that the number of dices of the bid is on the table or not, in a clock-wise fashion. " \
                "Following, everyone opens their cup and the dices are counted and compared to the bid.\nIf the " \
                "number of the bid is equal or less than the number of dices on the table, the bid is correct. " \
                "However, if the number of the bid is greater than the number of the dices on the table, the bid is a " \
                "lie. All the players who are correct lose one die.\nAfter this the round has ended. A new round " \
                "starts with the remaining number of dices for each player, restarting the bidding with the player " \
                "who lost the last round. For multiple players, this will be the person who was either correctly " \
                "called a liar, or the player who incorrectly called another player a liar.\nAfter every round, " \
                "all the players who were correct lose a die. The goal is to be the first to lose all of the dices " \
                "from your cup. However, the game will be played until all players except one have no more dices " \
                "remaining their cups. "


class MainWidget(QWidget):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.init_ui()

    def init_ui(self):
        grid = QGridLayout()
        grid.setSpacing(10)

        enemy_cup_group = QGroupBox("Enemy Cup")
        enemy_cup_group.setProperty("cssClass", "cup")

        enemy_bet_group = QGroupBox("Enemy Bet")
        enemy_bet_layout = QHBoxLayout()

        enemy_number_label = QLabel("1")
        enemy_number_label.resize(enemy_number_label.sizeHint())

        enemy_times_label = QLabel("×")
        enemy_times_label.resize(enemy_times_label.sizeHint())

        enemy_dice_label = QLabel("1")
        enemy_dice_label.resize(enemy_dice_label.sizeHint())

        enemy_bet_layout.addWidget(enemy_number_label)
        enemy_bet_layout.addWidget(enemy_times_label)
        enemy_bet_layout.addWidget(enemy_dice_label)

        enemy_bet_group.setLayout(enemy_bet_layout)

        # Here we'll show if the enemy is thinking, or if they call your bluff
        enemy_action_group = QGroupBox("Enemy Action")
        enemy_action_layout = QVBoxLayout()
        enemy_action_label = QLabel("Thinking...")
        enemy_action_layout.addWidget(enemy_action_label)
        enemy_action_group.setLayout(enemy_action_layout)

        player_cup_group = QGroupBox("Your Cup")
        player_cup_group.setProperty("cssClass", "cup")

        player_bet_group = QGroupBox("Your Bet")
        player_bet_layout = QHBoxLayout()

        select_number_layout = QVBoxLayout()
        select_number_label = QLabel("Number")
        select_number_spin_box = QSpinBox()
        select_number_spin_box.setRange(1, 6)
        select_number_layout.addWidget(select_number_label)
        select_number_layout.addWidget(select_number_spin_box)

        player_times_label = QLabel("×")
        player_times_label.resize(player_times_label.sizeHint())

        select_dice_layout = QVBoxLayout()
        select_dice_label = QLabel("Dice")
        select_dice_spin_box = QSpinBox()
        select_dice_spin_box.setRange(1, 6)
        select_dice_layout.addWidget(select_dice_label)
        select_dice_layout.addWidget(select_dice_spin_box)

        player_bet_layout.addLayout(select_number_layout)
        player_bet_layout.addWidget(player_times_label)
        player_bet_layout.addLayout(select_dice_layout)

        player_bet_group.setLayout(player_bet_layout)

        actions_group = QGroupBox('Your Action')
        actions_layout = QVBoxLayout()

        bet_btn = QPushButton('BET')
        bet_btn.setStatusTip('Bet the selected amount and dice.')

        call_bluff_btn = QPushButton('CALL BLUFF')
        call_bluff_btn.setStatusTip("Call the opponent's bluff.")

        actions_layout.addWidget(bet_btn)
        actions_layout.addWidget(call_bluff_btn)

        actions_group.setLayout(actions_layout)

        grid.addWidget(enemy_cup_group, 0, 0, 1, 2)
        grid.addWidget(enemy_bet_group, 1, 0, 1, 1)
        grid.addWidget(enemy_action_group, 1, 1, 1, 1)
        grid.addWidget(player_cup_group, 2, 0, 1, 2)
        grid.addWidget(player_bet_group, 3, 0, 1, 1)
        grid.addWidget(actions_group, 3, 1, 1, 1)
        self.setLayout(grid)


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.init_ui()

    def init_ui(self):
        main_widget = MainWidget()
        self.setCentralWidget(main_widget)

        new_game_action = QAction('New Game', self)
        new_game_action.setShortcut(QKeySequence.New)
        new_game_action.setStatusTip('Start a new game.')
        new_game_action.triggered.connect(self.restart)

        exit_action = QAction('Exit', self)
        exit_action.setShortcut(QKeySequence.Close)
        exit_action.setStatusTip('Exit application.')
        exit_action.triggered.connect(self.close)

        how_to_play_action = QAction('How to play', self)
        how_to_play_action.setStatusTip('View game instructions.')
        how_to_play_action.setShortcut(QKeySequence.HelpContents)
        how_to_play_action.triggered.connect(self.show_how_to_play)

        about_action = QAction('About', self)
        about_action.setStatusTip("About Liar's Dice.")
        about_action.triggered.connect(self.show_about)

        self.statusBar()

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(new_game_action)
        file_menu.addAction(exit_action)
        help_menu = menubar.addMenu('&Help')
        help_menu.addAction(how_to_play_action)
        help_menu.addAction(about_action)

        self.resize(350, 550)
        self.center()
        self.setWindowTitle("Liar's Dice")
        self.setWindowIcon(QIcon('dice_icon.png'))
        self.setObjectName("mainWindow")
        self.setStyleSheet(
            f"#mainWindow {{background: qlineargradient( x1:0 y1:0, x2:0 y2:1, stop:0 {background_color}, stop:1 {background_color_2}); color:white}} QStatusBar {{ "
            f"color:white;}} QLabel {{color:white; qproperty-alignment: AlignCenter;}} QGroupBox{{"
            f"color:white;}} *[cssClass='cup'] {{ background-color: transparent;}}")

        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def bet(self):
        return NotImplemented

    def call_bluff(self):
        return NotImplemented

    def restart(self):
        return NotImplemented

    # def closeEvent(self, event):
    #     reply = QMessageBox.question(self, 'Confirmation',
    #                                  "Are you sure you want to quit?", QMessageBox.Yes |
    #                                  QMessageBox.No, QMessageBox.No)
    #
    #     if reply == QMessageBox.Yes:
    #         event.accept()
    #     else:
    #         event.ignore()

    def show_how_to_play(self):
        how_to_play_box = QMessageBox()
        how_to_play_box.setWindowTitle("Playing Liar's Dice")
        how_to_play_box.setText(how_to_string)
        how_to_play_box.exec_()

    def show_about(self):
        about_box = QMessageBox()
        about_box.setWindowTitle("About")
        about_box.setText("Liar's Dice implemented in python. Add licenses and other info here.")
        about_box.exec_()


def main():
    # Every Qt application must have one and only one QApplication object;
    # it receives the command line arguments passed to the script, as they
    # can be used to customize the application's appearance and behavior
    sys.argv.extend(["--platformtheme", "qt5ct"])
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
