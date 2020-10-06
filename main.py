# Allow access to command-line arguments
import sys
import threading

# Import the core and GUI elements of Qt
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtWebEngineWidgets import QWebEngineView

from ui.main_widget import MainWidget
from ui.sliding_stacked_widget import SlidingStackedWidget

howto_text = "assets/howto.html"
stylesheet = "assets/style.qss"

# Minimum and maximum limit to number of opponents
opponent_limits = (1, 3)


class CommunicateRandom(QObject):
    # This is a class attribute, so it gets reassigned every time it's changed in an instance
    # Couldn't fix it by making an instance attribute
    start_new_random_game = Signal()


class CommunicateCogMod(QObject):
    # This is a class attribute, so it gets reassigned every time it's changed in an instance
    # Couldn't fix it by making an instance attribute
    start_new_game = Signal()


class GoBack(QObject):
    # This is a class attribute, so it gets reassigned every time it's changed in an instance
    # Couldn't fix it by making an instance attribute
    back = Signal()


class StartScreenWidget(QWidget):

    def __init__(self, select_enemies_spinbox: QSpinBox, show_logo=True):
        """
        Widget for selecting difficulty
        """
        super(StartScreenWidget, self).__init__()
        self.select_enemies_spinbox = select_enemies_spinbox
        self.difficulties = ["Play against Random Opponent(s) [Easy mode]", "Play against Cognitive Model Opponent(s) [Fun mode]"]
        self.start_game_signals = [CommunicateRandom(), CommunicateCogMod()]
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

        # This could be anything, I think
        self.select_enemies_spinbox.setRange(*opponent_limits)
        self.select_enemies_spinbox.setMaximumWidth(50)

        select_enemies_group = QGroupBox("Select number of opponents ({0}-{1})".format(*opponent_limits))
        select_enemies_layout = QVBoxLayout()
        select_enemies_layout.addWidget(self.select_enemies_spinbox)
        select_enemies_layout.setAlignment(Qt.AlignCenter)
        select_enemies_group.setLayout(select_enemies_layout)

        vertical_main_layout.addWidget(select_enemies_group)

        random_difficulty_button = QPushButton(text=self.difficulties[0])
        random_difficulty_button.setStatusTip(f"Start game against one or more opponents that take random actions.")
        random_difficulty_button.clicked.connect(self.start_game_signals[0].start_new_random_game.emit)
        vertical_main_layout.addWidget(random_difficulty_button)

        new_cog_mod_game_button = QPushButton(text=self.difficulties[1])
        new_cog_mod_game_button.setStatusTip(f"Start game against one or more cognitive models.")
        new_cog_mod_game_button.clicked.connect(self.start_game_signals[1].start_new_game.emit)
        vertical_main_layout.addWidget(new_cog_mod_game_button)

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

        how_to_play_label = QWebEngineView()
        with open(howto_text, "r") as how_to_file_handle:
            how_to_play_label.setHtml(how_to_file_handle.read())
            # how_to_play_label.setAttribute(Qt.WA_TranslucentBackground, True)
            # how_to_play_label.page.setBackgroundColor(Qt.transparent)

        vertical_main_layout.addWidget(back_button)
        vertical_main_layout.addWidget(how_to_play_label)
        self.setLayout(vertical_main_layout)


class MainWindow(QMainWindow):

    def __init__(self):
        """
        The main window. Everything takes place inside it.
        """
        super(MainWindow, self).__init__()
        self.how_to_play_action = QAction('How to play', self)
        self.how_to_play_widget = HowToPlayWidget()
        self.select_enemies_spinbox = QSpinBox()
        self.central_widget = SlidingStackedWidget()
        self.game_widget = None
        self.init_ui()

    def init_ui(self):
        """
        Initialize the central widget, along with the menubar and status bar.
        :return:
        """
        self.central_widget.addWidget(self.restart(show_logo=True))
        self.how_to_play_widget.back_signal.back.connect(
            lambda: self.central_widget.slideInIdx(self.central_widget.currentIndex() - 1))

        self.setCentralWidget(self.central_widget)

        new_game_action = QAction('New Game', self)
        new_game_action.setShortcut(QKeySequence.New)
        new_game_action.setStatusTip('Start a new game.')
        new_game_action.triggered.connect(lambda: self.central_widget.slideInIdx(0))

        exit_action = QAction('Exit', self)
        exit_action.setShortcut(QKeySequence.Close)
        exit_action.setStatusTip('Exit application.')
        exit_action.triggered.connect(self.close)

        self.how_to_play_action.setStatusTip('View game instructions.')
        self.how_to_play_action.setShortcut(QKeySequence.HelpContents)
        self.how_to_play_action.triggered.connect(lambda: self.show_how_to_play(prv_ind=0))

        about_action = QAction('About', self)
        about_action.setStatusTip("About Liar's Dice.")
        about_action.triggered.connect(self.show_about)

        self.statusBar()

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(new_game_action)
        file_menu.addAction(exit_action)
        help_menu = menubar.addMenu('&Help')
        help_menu.addAction(self.how_to_play_action)
        help_menu.addAction(about_action)

        self.resize(450, 550)
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

        if self.game_widget is not None:
            self.central_widget.removeWidget(self.game_widget)

        start_screen_widget = StartScreenWidget(select_enemies_spinbox=self.select_enemies_spinbox, show_logo=show_logo)

        start_screen_widget.start_game_signals[0].start_new_random_game.connect(lambda: self.restart_aux(idx=0))
        start_screen_widget.start_game_signals[1].start_new_game.connect(lambda: self.restart_aux(idx=1))
        self.how_to_play_action.triggered.connect(lambda: self.show_how_to_play(prv_ind=0))

        return start_screen_widget

    def restart_aux(self, idx: int):

        self.game_widget = MainWidget(difficulty=idx, n_opponents=int(self.select_enemies_spinbox.value()))
        self.central_widget.addWidget(self.game_widget)
        self.central_widget.slideInWgt(self.game_widget)
        self.how_to_play_action.triggered.connect(lambda: self.show_how_to_play(prv_ind=1))

    def closeEvent(self, event):
        """
        Confirming that you really want to close.
        Don't rename this, it won't work anymore.
        :param event: the close event
        """
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if isinstance(self.central_widget.currentWidget(), MainWidget):
                self.central_widget.currentWidget().q.put("-1")
                print("quit")
            event.accept()
        else:
            event.ignore()

    def show_how_to_play(self, prv_ind: int):
        """
        Show a window explaining how to play the game
        :return:
        """
        print(f"prv_ind={prv_ind}")
        self.how_to_play_widget.back_signal.back.connect(
            lambda: self.central_widget.slideInIdx(prv_ind))
        # Add it if it doesn't exist
        if self.central_widget.indexOf(self.how_to_play_widget) == -1:
            self.central_widget.addWidget(self.how_to_play_widget)
        # Move to it
        self.central_widget.slideInWgt(self.how_to_play_widget)

    @staticmethod
    def show_about():
        """
        Show some info about the game
        :return:
        """
        about_box = QMessageBox()
        about_box.setWindowTitle("About")
        about_box.setTextFormat(Qt.RichText)
        about_box.setText(f"Liar's Dice implemented in Python, with Cognitive Model opponents.<br>"
                          f"Developed for the Cognitive Modelling: Complex Behavior course at the University of "
                          f"Groningen.<br>"
                          f"Model: Oscar de Vries<br>"
                          f"View: Andrei Miculita<br>"
                          f"Controller: Tomasso Parisotto<br>"
                          f"GitHub: <a href='https://github.com/AndreiMiculita/pyliarsdice'>link</a>")
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
