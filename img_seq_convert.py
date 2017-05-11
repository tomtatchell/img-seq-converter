import sys
from os import path, getcwd, chdir
import pyseq
import pexpect
from PyQt5.QtWidgets import (QWidget, QMainWindow, QProgressBar,
                             qApp, QMessageBox, QApplication, QLabel)
from PyQt5.QtGui import QPalette, QImage, QBrush
from PyQt5.QtCore import Qt, QSize


# chdir(path.dirname(sys.executable))

frozen = 'not'
if getattr(sys, 'frozen', False):
    frozen = 'very'
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = path.dirname(path.abspath(__file__))
print('we are',frozen,'frozen')
print('bundle dir is', bundle_dir)
print('sys.argv[0] is', sys.argv[0])
print('sys.executable is', sys.executable)
print('os.getcwd is', getcwd())


class BackgroundWidget(QWidget):
    def __init__(self):
        super(BackgroundWidget, self).__init__()
        palette = QPalette()
        oImage = QImage('/Users/bbmp03/PycharmProjects/pyqt/img_seq_convert/BBLOGO.png')
        sImage = oImage.scaled(QSize(404, 466))
        palette.setBrush(QPalette.Background, QBrush(sImage))
        self.setAutoFillBackground(True)
        self.setPalette(palette)


class Example(QMainWindow):
    # TODO: Add text elements to UI
    # TODO: Possibly add button to go after confirming output?
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setAcceptDrops(True)

    def initUI(self):
        self._widget = BackgroundWidget()
        self.setCentralWidget(self._widget)

        self.setWindowTitle('Simple drag & drop')
        self.setGeometry(750, 100, 808, 466)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.progress = QProgressBar(self)
        self.progress.setGeometry(101, 80, 200, 30)
        self.completed = 0
        print("Current working directory: ", getcwd())
        self.lbl = QLabel(self)
        self.lbl.move(5, 233)

        frozen = 'not'
        if getattr(sys, 'frozen', False):
            frozen = 'very'
            bundle_dir = sys._MEIPASS
        else:
            bundle_dir = path.dirname(path.abspath(__file__))
        self.lbl.setText("frozen: {}, \n"
                         "Bundle dir: {}, \n"
                         "sys.argv[0]: {}, \n"
                         "sys.executable: {}, \n"
                         "os.getcwd: {}".format(frozen, bundle_dir, sys.argv[0], sys.executable, getcwd()))
        # self.lbl.setText("Current working directory: {}".format(getcwd()))
        self.lbl.setWordWrap(True)
        self.lbl.adjustSize()



    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat('text/uri-list'):
            e.acceptProposedAction()
        else:
            super(Example, self).dragMoveEvent(e)

    def dragMoveEvent(self, e):
        super(Example, self).dragMoveEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasFormat('text/uri-list'):
            for url in e.mimeData().urls():  # for every folder dropped
                seq_path = url.path()  # get the path
                if path.isdir(seq_path):  # if it's a path
                    seqs = pyseq.get_sequences(seq_path)  # get the sequence
                    # TODO: Implement check for missing files from sequence
                    for s in seqs:
                        paddedName = s.format('%h%p%t')
                        sequenceName = s.format('%h')
                        cmd = 'ffmpeg -i {} -pix_fmt yuv420p {}.mov'.format(seq_path + paddedName,
                                                                            seq_path + sequenceName)
                        thread = pexpect.spawn(cmd)
                        print("started {}".format(cmd))
                        cpl = thread.compile_pattern_list([
                            pexpect.EOF,
                            'frame= \s*\d+',
                            '(.+)',
                        ])
                        while True:
                            i = thread.expect_list(cpl, timeout=None)
                            if i == 0:  # EOF
                                print("the sub process exited")
                                break
                            elif i == 1:
                                frame_number_bytes = thread.match.group(0)
                                fn_str = frame_number_bytes.decode("utf-8")
                                formatted_fn = fn_str.rsplit('= ', 1)[1]
                                percentage = (int(formatted_fn.lstrip()) / int(s.length())) * 100
                                print("frame: {} of {}  --  {}%".format(formatted_fn,
                                                                        s.length(),
                                                                        int(percentage)))
                                self.progress.setValue(percentage)
                                qApp.processEvents()



                        thread.close()
                        self.progress.setValue(0)

        else:
            super(Example, self).dragMoveEvent(e)

    def mousePressEvent(self, event):
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        x = event.globalX()
        y = event.globalY()
        x_w = self.offset.x()
        y_w = self.offset.y()
        self.move(x - x_w, y - y_w)

    def closeEvent(self, e):
        reply = QMessageBox.question(
            self, "Message",
            "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            app.quit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.closeEvent(e)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    app.exec_()
