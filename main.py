# Allow access to command-line arguments
import sys

# Import the core and GUI elements of Qt
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from main_widget import MainWidget

howto_text = "assets/howto.txt"
stylesheet = "assets/style.qss"


class Communicate(QObject):
    # This is a class attribute, so it gets reassigned every time it's changed in an instance
    # Couldn't fix it by making an instance attribute
    start_new_game = Signal()


class GoBack(QObject):
    # This is a class attribute, so it gets reassigned every time it's changed in an instance
    # Couldn't fix it by making an instance attribute
    back = Signal()


class StartScreenWidget(QWidget):

    def __init__(self, show_logo=True):
        """
        Widget for selecting difficulty
        """
        super(StartScreenWidget, self).__init__()
        self.difficulties = ["Easy", "Medium", "Hard"]
        self.start_game_signals = [Communicate(), Communicate(), Communicate()]
        self.show_logo = show_logo
        self.init_ui()

    def init_ui(self):
        vertical_main_layout = QGridLayout()
        vertical_main_layout.setSpacing(10)

        logo_pixmap = QPixmap("assets/images/dice_icon.png")
        logo = QLabel()
        logo.setPixmap(logo_pixmap)

        if self.show_logo:
            title = QLabel("Liar's Dice")
        else:
            make_transparent = QGraphicsOpacityEffect(self)
            make_transparent.setOpacity(0.0)

            logo.setGraphicsEffect(make_transparent)
            logo.setAutoFillBackground(True)
            title = QLabel("New Game")

        title.setProperty("cssClass", "gameTitle")
        vertical_main_layout.addWidget(logo)
        vertical_main_layout.addWidget(title)

        for idx, difficulty in enumerate(self.difficulties):
            difficulty_button = QPushButton(difficulty)
            difficulty_button.setStatusTip(f"Start {difficulty} difficulty game")
            difficulty_button.clicked.connect(self.start_game_signals[idx].start_new_game.emit)
            vertical_main_layout.addWidget(difficulty_button)

        self.setLayout(vertical_main_layout)


class HowToPlayWidget(QWidget):

    def __init__(self, show_logo=True):
        """
        Widget for selecting difficulty
        """
        super(HowToPlayWidget, self).__init__()
        self.back_signal = GoBack()
        self.init_ui()

    def init_ui(self):
        vertical_main_layout = QVBoxLayout()
        vertical_main_layout.setSpacing(10)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.back_signal.back.emit)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)

        vertical_instructions_group = QGroupBox()
        vertical_instructions_layout = QVBoxLayout()
        how_to_play_label = QLabel()
        # TODO: add formatting (bold, italic, bullets), fix scrolling
        with open(howto_text, "r") as how_to_file_handle:
            how_to_play_label.setText(how_to_file_handle.read())

        how_to_play_label.setWordWrap(True)
        # size_policy = QSizePolicy()
        # size_policy.setHorizontalPolicy(QSizePolicy.MinimumExpanding)
        # how_to_play_label.setSizePolicy(size_policy)

        how_to_play_label.resize(100, 500)

        vertical_instructions_layout.addWidget(how_to_play_label)

        vertical_instructions_group.setLayout(vertical_instructions_layout)
        scroll_area.setWidget(vertical_instructions_group)

        vertical_main_layout.addWidget(back_button)
        vertical_main_layout.addWidget(scroll_area)
        self.setLayout(vertical_main_layout)


class MainWindow(QMainWindow):

    def __init__(self):
        """
        The main window. Everything takes place inside it.
        """
        super(MainWindow, self).__init__()
        self.central_widget = QStackedWidget()
        self.init_ui()

    def init_ui(self):
        """
        Initialize the central widget, along with the menubar and status bar.
        :return:
        """
        self.central_widget.addWidget(self.restart(show_logo=True))
        how_to_play_widget = HowToPlayWidget()
        how_to_play_widget.back_signal.back.connect(
            lambda: self.central_widget.setCurrentIndex(self.central_widget.currentIndex() - 1))
        self.central_widget.addWidget(how_to_play_widget)

        self.setCentralWidget(self.central_widget)

        new_game_action = QAction('New Game', self)
        new_game_action.setShortcut(QKeySequence.New)
        new_game_action.setStatusTip('Start a new game.')
        new_game_action.triggered.connect(lambda: self.restart(show_logo=False))

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
        self.setWindowIcon(QIcon("assets/images/dice_icon.png"))
        self.setObjectName("mainWindow")
        with open(stylesheet, "r") as fh:
            self.setStyleSheet(fh.read())
        self.show()

    def center(self):
        """
        Used to initialize the main window in the center of the screen
        :return:
        """
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def restart(self, show_logo):
        """
        Start a new game
        :return:
        """
        start_screen_widget = StartScreenWidget(show_logo=show_logo)

        for idx, signal in enumerate(start_screen_widget.start_game_signals):
            signal.start_new_game.connect(lambda: self.restart_aux(idx=idx))

        return start_screen_widget

    def restart_aux(self, idx: int):
        new_game_widget = MainWidget(difficulty=idx)
        self.central_widget.addWidget(new_game_widget)
        self.central_widget.setCurrentWidget(new_game_widget)

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
        """
        Show a window explaining how to play the game
        :return:
        """
        # Get a reference to the old central widget so that we can return to it
        self.central_widget.setCurrentIndex(1)

    @staticmethod
    def show_about():
        """
        Show some info about the game
        :return:
        """
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
