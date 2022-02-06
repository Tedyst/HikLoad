from PyQt5 import QtWidgets, uic, QtGui
import sys
import os
import logging
import time
from io import StringIO

from hikload.hikvisionapi.classes import HikvisionException, HikvisionServer
log_stream = StringIO()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, args=None):
        super(MainWindow, self).__init__()
        self.args = None
        path = os.path.dirname(__file__)
        startup = Startup(parent=self, args=args)
        startup.show()
        startup.exec_()

        uic.loadUi(os.path.join(path, 'MainWindow.ui'), self)
        self.show()
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

        logger = logging.getLogger('hikload')
        logger.info(args)

        while True:
            QtGui.QGuiApplication.processEvents()
            asd: QtWidgets.QTextEdit =self.textEdit
            asd.textCursor().selectionEnd()
            value = log_stream.getvalue()
            if len(value) != 0:
                self.textEdit.append(value[:-1])
            log_stream.truncate(0)




class ErrorDialog(QtWidgets.QMessageBox):
    def __init__(self, message):
        super(ErrorDialog, self).__init__()
        self.setIcon(QtWidgets.QMessageBox.Critical)
        self.setWindowTitle("Error")
        self.setText("Error while executing the action")
        self.setInformativeText(message)

class Startup(QtWidgets.QDialog):
    def __init__(self, parent=None, args=None):
        super(Startup, self).__init__() # Call the inherited classes __init__ method
        path = os.path.dirname(__file__)
        uic.loadUi(os.path.join(path, 'Startup.ui'), self) # Load the .ui file
        self.args = args
        self.populate_with_args(args)

        self.downloads_folder_button.clicked.connect(self.select_download_folder)
        self.test_connection_button.clicked.connect(self.test_connection)
        self.start_downloading_button.clicked.connect(self.start_downloading)

        self.start_date.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_date.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.parent = parent
        self.skipclosing = False
        self.start_downloading_button.setEnabled(False)

    def populate_with_args(self, args=None):
        self.server_ip.setText(args.server)
        self.downloads_folder.setText(args.downloads)
        self.username.setText(args.username)
        self.password.setText(args.password)
        self.folder_behavior.setCurrentIndex(list.index([None, 'onepercamera', 'oneperday', 'onepermonth', 'oneperyear'], args.folders))
        if args.photos:
            self.download_type.setCurrentIndex(1)
        self.video_format.setCurrentIndex(list.index(['mkv', 'mp4', 'avi'], args.videoformat))
        self.start_date.setDateTime(args.starttime)
        self.end_date.setDateTime(args.endtime)
        self.debug.setChecked(bool(args.debug))
        self.force.setChecked(bool(args.force))
        self.localtime.setChecked(bool(args.localtimefilenames))
        self.ffmpeg.setChecked(bool(args.ffmpeg))
        self.forcetranscoding.setChecked(bool(args.forcetranscoding))

    def get_args(self):
        self.args.server = self.server_ip.text()
        self.args.downloads = self.downloads_folder.text()
        self.args.username = self.username.text()
        self.args.password = self.password.text()
        self.args.folders = [None, 'onepercamera', 'oneperday', 'onepermonth', 'oneperyear'][self.folder_behavior.currentIndex()]
        self.args.photos = self.download_type.currentIndex() == 1
        self.args.videoformat = ['mkv', 'mp4', 'avi'][self.video_format.currentIndex()]
        self.args.starttime = self.start_date.dateTime().toPyDateTime()
        self.args.endtime = self.end_date.dateTime().toPyDateTime()
        self.args.debug = self.debug.isChecked()
        self.args.force = self.force.isChecked()
        self.args.localtimefilenames = self.localtime.isChecked()
        self.args.ffmpeg = self.ffmpeg.isChecked()
        self.args.forcetranscoding = self.forcetranscoding.isChecked()
        cameras = []
        for i in self.cameras.selectedIndexes():
            cameras.append(self.cameras.model().data(i))
        self.args.cameras = cameras
        return self.args

    def select_download_folder(self):
        file = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.downloads_folder.setText(file)

    def start_downloading(self):
        self.skipclosing = True
        self.parent.args = self.get_args()
        self.close()

    def test_connection(self):
        try:
            server = HikvisionServer(self.server_ip.text(), self.username.text(), self.password.text())
            server.test_connection()
            channelList = server.Streaming.getChannels()
            self.cameras.clear()
            for channel in channelList['StreamingChannelList']['StreamingChannel']:
                item = QtWidgets.QTreeWidgetItem(channel['id'])
                self.cameras.insertTopLevelItems(0, [item])
        except Exception as e:
            ErrorDialog("Could not connect to the server").exec_()
            logging.error(e)
            return
        QtWidgets.QMessageBox.information(self, "Success", "Successfully connected to the server")
        self.start_downloading_button.setEnabled(True)

    def closeEvent(self, event):
        event.accept()
        if self.skipclosing:
            return
        print("Exited by user", event.type())
        exit(0)

    def reject(self):
        exit(0)


def main(args=None):
    FORMAT = "[%(funcName)s] %(message)s"
    logger = logging.getLogger('hikload')
    if args.debug:
        logging.basicConfig(stream=log_stream, format=FORMAT)
        logger.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(stream=log_stream, format=FORMAT)
        logger.setLevel(logging.INFO)

    logger.info("started")

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(args)
    app.exec_()
    window.show()

if __name__ == '__main__':
    main()