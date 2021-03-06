# Allow access to command-line arguments
import sys
import threading

# Import the core and GUI elements of Qt
from typing import Union

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtWebEngineWidgets import QWebEngineView
from bs4 import BeautifulSoup

from io import StringIO
from ui.main_widget import MainWidget, playercolors
from ui.sliding_stacked_widget import SlidingStackedWidget

howto_text = "assets/howto.html"
stylesheet = "assets/style.qss"

about_text = f"Liar's Dice implemented in Python, with Cognitive Model opponents.<br>" \
             f"Developed for the Cognitive Modelling: Complex Behavior course at the University of "\
             f"Groningen.<br>"\
             f"Model: Oscar de Vries<br>"\
             f"View: Andrei Miculita<br>"\
             f"Controller: Tomasso Parisotto<br>"\
             f"GitHub: <a href='https://github.com/AndreiMiculita/pyliarsdice'>link</a><br>" \
             f"Image asset sources:<br>" \
             f"<a href='https://game-icons.net/tags/dice.html'>Dice images</a><br>" \
             f"<a href='https://tenor.com/view/dice-gif-4717877'>Rolling dice image</a><br>" \
             f"<a href='https://tenor.com/view/waiting-bored-skeleton-gif-13733904'>Waiting skeleton</a><br>" \
             f"<a href='https://loading.io'>Thinking loader</a><br>"\
             f"<a href='https://commons.wikimedia.org/wiki/File:Exclamation-mark_animated.gif'>Doubting exclamation</a><br>" \
             f"<a href='http://clipart-library.com/clipart/rcjKBA5Mi.htm>Believing checkmark</a><br>" \
             f"<a href='https://iconarchive.com/show/farm-fresh-icons-by-fatcow.html'>Believe/call bluff buttons</a><br>"

# Minimum and maximum limit to number of opponents
opponent_limits = (1, 4)


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
        self.difficulties = ["Play against Random Opponent(s) [Easy mode]",
                             "Play against Cognitive Model Opponent(s) [Fun mode]"]
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

        self.select_enemies_spinbox.setFixedHeight(45)
        self.select_enemies_spinbox.setFixedWidth(60)
        self.select_enemies_spinbox.setRange(*opponent_limits)
        self.select_enemies_spinbox.setProperty("cssClass", "biglabel")

        # self.select_enemies_spinbox.setMaximumWidth(50)

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


class BigTextTabWidget(QWidget):

    def __init__(self, text_file: Union[str, StringIO]):
        """
        Widget for displaying how to play, or reasoning_file
        """
        super(BigTextTabWidget, self).__init__()
        self.text_file = text_file
        self.back_signal = GoBack()
        self.big_text_view = QWebEngineView()
        self.init_ui()

    def init_ui(self):
        vertical_main_layout = QVBoxLayout()
        vertical_main_layout.setSpacing(10)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.back_signal.back.emit)

        vertical_main_layout.addWidget(back_button)

        self.update_text(self.text_file)

        vertical_main_layout.addWidget(self.big_text_view)

        self.setLayout(vertical_main_layout)

    def update_text(self, text_file):
        """
        Update the text in the reasoning tab
        Everything in the parameter will be put between two body tags
        :param text_file:
        :return:
        """
        if isinstance(self.text_file, StringIO):
            # this will close all open tags, it's really smart
            nice_html = BeautifulSoup(
                f"<!DOCTYPE html><html><head>"
                f"<style>"
                f".t1{{color:{playercolors[1]};}}"
                f".t2{{color:{playercolors[2]};}}"
                f".t3{{color:{playercolors[3]};}}"
                f".t4{{color:{playercolors[4]};}}" 
                f".topbox{{position:fixed; top: 0px; left: 50%; transform: translateX(-50%);}}" 
                f".playerbox{{text-align:center;width:70px;display:inline-block;"
                                      f"float:left;border-radius:7px;margin:3px;"
                                      f"box-shadow:0px 0px 10px rgba(0,0,0,0.5);}}"
                f".roundbox{{border: 1px solid white; border-radius: 7px; padding: 5px;}}" 
                f".roundtitle{{text-align:center;position:sticky;top:35px;background-color:white;color:black;" 
                f"border-radius:7px;}}" 
                f".turntitle{{text-align:center;position:sticky;top:65px;color:white;border-radius:7px;}}"
                f".tn0{{background-color:white;color:black;}}"
                f".tn1{{background-color:{playercolors[1]};}}"
                f".tn2{{background-color:{playercolors[2]};}}"
                f".tn3{{background-color:{playercolors[3]};}}"
                f".tn4{{background-color:{playercolors[4]};}}" 
                f"</style> </head><body style='"
                f"background-color:#004400;"
                f"color:white;"
                f"font-family:sans-serif;"
                f"max-width: 400px;"
                f"margin: auto;'></head>"
                f"<body> {text_file.getvalue()}</body></html>", 'lxml').prettify()
            self.big_text_view.setHtml(nice_html)
        else:
            with open(text_file, "r") as file_handle:
                # this will close all open tags, it's really smart
                nice_html = BeautifulSoup(file_handle.read(), 'lxml').prettify()
                self.big_text_view.setHtml(nice_html)
        self.big_text_view.page().runJavaScript("window.scrollTo(0,document.body.scrollHeight);")  # scroll to bottom


class MainWindow(QMainWindow):

    def __init__(self):
        """
        The main window. Everything takes place inside it.
        """
        super(MainWindow, self).__init__()
        self.reasoning_file = StringIO("Start a game to see the enemies' reasoning.")
        self.how_to_play_widget = BigTextTabWidget(text_file=howto_text)
        self.reasoning_widget = BigTextTabWidget(text_file=self.reasoning_file)
        self.select_enemies_spinbox = QSpinBox()
        self.central_widget = SlidingStackedWidget()
        self.game_widget = None
        self.init_ui()

    def init_ui(self):
        """
        Initialize the central widget, along with the menubar and status bar.
        :return:
        """
        self.restart()
        self.how_to_play_widget.back_signal.back.connect(
            lambda: self.central_widget.slideInIdx(self.central_widget.currentIndex() - 1))

        self.setCentralWidget(self.central_widget)

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
        how_to_play_action.triggered.connect(lambda: self.show_how_to_play())

        reasoning_action = QAction('Show reasoning', self)
        reasoning_action.setStatusTip('View model reasoning.')
        reasoning_action.setShortcut("F2")
        reasoning_action.triggered.connect(lambda: self.show_reasoning())

        about_action = QAction('About', self)
        about_action.setShortcut("F3")
        about_action.setStatusTip("About Liar's Dice.")
        about_action.triggered.connect(lambda: self.show_msg(title="About", text=about_text))

        self.statusBar()

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(new_game_action)
        file_menu.addAction(exit_action)
        help_menu = menubar.addMenu('&Help')
        help_menu.addAction(how_to_play_action)
        help_menu.addAction(reasoning_action)
        help_menu.addAction(about_action)

        self.resize(450, 690)
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

    def restart(self):
        """
        Start a new game
        :return:
        """

        if self.central_widget.count() == 0:
            start_screen_widget = StartScreenWidget(select_enemies_spinbox=self.select_enemies_spinbox)
            start_screen_widget.start_game_signals[0].start_new_random_game.connect(lambda: self.start_game_and_switch(difficulty=0))
            start_screen_widget.start_game_signals[1].start_new_game.connect(lambda: self.start_game_and_switch(difficulty=1))
            self.central_widget.addWidget(start_screen_widget)

        if self.game_widget is not None:
            self.central_widget.removeWidget(self.game_widget)
            self.game_widget = None
        if self.central_widget.currentIndex() != 0:
            self.central_widget.slideInIdx(0)

    def start_game_and_switch(self, difficulty: int):
        self.game_widget = MainWidget(difficulty=difficulty, n_opponents=int(self.select_enemies_spinbox.value()),
                                      reasoning_file=self.reasoning_file)
        self.central_widget.insertWidget(1, self.game_widget)
        self.central_widget.slideInIdx(1)
        self.center()

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

    def show_how_to_play(self):
        """
        Show a window explaining how to play the game
        :return:
        """
        self.how_to_play_widget.back_signal.back.connect(self.go_back)
        # Add it if it doesn't exist
        if self.central_widget.indexOf(self.how_to_play_widget) == -1:
            self.central_widget.addWidget(self.how_to_play_widget)
        # Move to it
        self.central_widget.slideInWgt(self.how_to_play_widget)

    def show_reasoning(self):
        self.reasoning_widget.back_signal.back.connect(self.go_back)

        self.reasoning_widget.update_text(self.reasoning_file)
        # Add it if it doesn't exist
        if self.central_widget.indexOf(self.reasoning_widget) == -1:
            self.central_widget.addWidget(self.reasoning_widget)
        # Move to it
        self.central_widget.slideInWgt(self.reasoning_widget)

    def go_back(self):
        if self.game_widget is not None:
            self.central_widget.slideInIdx(1)
        else:
            self.central_widget.slideInIdx(0)

    @staticmethod
    def show_msg(title, text):
        """
        Show some info about the game
        :return:
        """
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(text)
        msg_box.exec_()


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
