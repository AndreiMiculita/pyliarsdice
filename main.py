# Allow access to command-line arguments
import sys

# Import the core and GUI elements of Qt
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Example(QMainWindow):

    def __init__(self):
        super(Example, self).__init__()
        self.init_ui()

    def init_ui(self):
        QToolTip.setFont(QFont('SansSerif', 10))

        self.setToolTip('This is a <b>QWidget</b> widget')

        # TODO: align to right border
        bet_btn = QPushButton('BET', self)
        bet_btn.setToolTip('Bet')
        bet_btn.resize(bet_btn.sizeHint())
        bet_btn.move(200, 450)

        call_bluff_btn = QPushButton('CALL BLUFF', self)
        call_bluff_btn.setToolTip('Call bluff')
        call_bluff_btn.resize(call_bluff_btn.sizeHint())
        call_bluff_btn.move(200, 480)

        exit_action = QAction('Exit', self)
        exit_action.setShortcut(QKeySequence.Close)
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)

        how_to_play_action = QAction('How to play', self)
        how_to_play_action.setShortcut(QKeySequence.HelpContents)

        about_action = QAction('About', self)

        self.statusBar()

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(exit_action)
        help_menu = menubar.addMenu('&Help')
        help_menu.addAction(how_to_play_action)
        help_menu.addAction(about_action)

        # toolbar = self.addToolBar('Exit')
        # toolbar.addAction(exit_action)

        self.resize(350, 550)
        self.center()
        self.setWindowTitle("Liar's Dice")
        self.setWindowIcon(QIcon('dice_icon.png'))

        self.show()

    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def center(self):

        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


def main():
    # Every Qt application must have one and only one QApplication object;
    # it receives the command line arguments passed to the script, as they
    # can be used to customize the application's appearance and behavior
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
