# Allow access to command-line arguments
import sys

# Import the core and GUI elements of Qt
from PySide2.QtGui import *
from PySide2.QtWidgets import *

# color scheme
background_color = "#006600"
light_brown = "#99621E"
dark_brown = "#2F1000"


class MainWidget(QWidget):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.init_ui()

    def init_ui(self):
        grid = QGridLayout()
        grid.setSpacing(10)

        enemy_cup_group = QGroupBox("Enemy Cup")

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

        player_cup_group = QGroupBox("Your Cup")

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

        actions_layout = QVBoxLayout()

        bet_btn = QPushButton('BET')
        bet_btn.setStatusTip('Bet the selected amount and dice.')
        bet_btn.resize(bet_btn.sizeHint())

        call_bluff_btn = QPushButton('CALL BLUFF')
        call_bluff_btn.setStatusTip("Call the opponent's bluff.")
        call_bluff_btn.resize(call_bluff_btn.sizeHint())

        actions_layout.addWidget(bet_btn)
        actions_layout.addWidget(call_bluff_btn)

        grid.addWidget(enemy_cup_group, 0, 0, 1, 2)
        grid.addWidget(enemy_bet_group, 1, 0, 1, 1)
        grid.addWidget(player_cup_group, 2, 0, 1, 2)
        grid.addWidget(player_bet_group, 3, 0, 1, 1)
        grid.addLayout(actions_layout, 3, 1, 1, 1)
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
        self.setStyleSheet(f"#mainWindow {{background-color:{background_color}; color:white}} QStatusBar {{"
                           f"color:white;}} QLabel {{color:white; qproperty-alignment: AlignCenter;}} QGroupBox{{"
                           f"color:white;}}")

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
        return NotImplemented

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
