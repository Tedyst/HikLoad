from PyQt5 import QtWidgets, uic, QtGui
import sys
import os
import logging
from io import StringIO
import threading
from .download import parse_args, search_for_recordings, search_for_recordings_mock, create_folder_and_chdir, download_recording

from hikload.hikvisionapi.classes import HikvisionServer
log_stream = StringIO()

class downloadThread(threading.Thread):
    def __init__(self, window: QtWidgets.QMainWindow, server: HikvisionServer, args):
        threading.Thread.__init__(self)
        self.window = window
        self.running = True
        self.server = server
        self.args = args
        self.recordings = None
        self.finished = 0

    def run(self):
        logger = logging.getLogger('hikload')
        logger.info("download thread started")
        logger.debug("args: %s", self.args)

        if self.args.mock:
            recordings = search_for_recordings_mock()
        else:
            recordings = search_for_recordings(self.args)
        self.recordings = recordings

        self.window.progressBar.setMaximum(len(recordings))
        self.window.progressBar.setValue(0)
        original_path = os.path.abspath(os.getcwd())
        if self.args.downloads:
            create_folder_and_chdir(self.args.downloads)

        self.window.treeWidget.clear()
        i = 0
        for recording in recordings:
            item = QtWidgets.QTreeWidgetItem([str(recording)])
            self.window.treeWidget.insertTopLevelItems(i, [item])
            i += 1

        for recordingobj in recordings:
            if self.running is False:
                return
            self.window.progressBar.setValue(self.finished)

            download_recording(self.server, self.args, recordingobj, original_path)
            asd: QtWidgets.QTreeWidget = self.window.treeWidget
            asd.takeTopLevelItem(0)

            self.finished += 1
        self.window.progressBar.setValue(len(recordings))
        logger.info("Finished downloading all recordings")
        logger.info("download thread finished")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, args=None):
        super(MainWindow, self).__init__()
        self.args = None
        startup = Startup(parent=self, args=args)
        startup.show()
        startup.exec_()

        path = os.path.dirname(__file__)
        uic.loadUi(os.path.join(path, 'MainWindow.ui'), self)
        self.show()
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

        server = HikvisionServer(self.args.server, self.args.username, self.args.password)
        self.downloadthread = downloadThread(self, server, args)
        self.downloadthread.start()

        while True:
            QtGui.QGuiApplication.processEvents()
            asd: QtWidgets.QTextEdit = self.textEdit
            asd.textCursor().selectionEnd()
            value = log_stream.getvalue()
            if len(value) != 0:
                self.textEdit.append(value[:-1])
            log_stream.truncate(0)

    def closeEvent(self, event):
        self.downloadthread.running = False
        sys.exit(0)

    def reject(self):
        sys.exit(0)




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
        if not self.args.mock:
            try:
                server = HikvisionServer(self.server_ip.text(), self.username.text(), self.password.text())
                server.test_connection()
                channelList = server.Streaming.getChannels()
                self.cameras.clear()
                i = 0
                for channel in channelList['StreamingChannelList']['StreamingChannel']:
                    item = QtWidgets.QTreeWidgetItem([channel['id']])
                    self.cameras.insertTopLevelItems(i, [item])
                    i += 1
                self.cameras.selectAll()
            except Exception as e:
                ErrorDialog("Could not connect to the server").exec_()
                logging.error(e)
                return
        else:
            self.cameras.clear()
            i = 0
            for channel in ["101", "201", "301"]:
                item = QtWidgets.QTreeWidgetItem([channel])
                self.cameras.insertTopLevelItems(i, [item])
                i += 1
            self.cameras.selectAll()
        QtWidgets.QMessageBox.information(self, "Success", "Successfully connected to the server")
        self.start_downloading_button.setEnabled(True)

    def closeEvent(self, event):
        event.accept()
        if self.skipclosing:
            return
        print("Exited by user", event.type())
        sys.exit(0)

    def reject(self):
        sys.exit(0)


def main(args=None):
    FORMAT = "[%(funcName)s] %(message)s"
    logger = logging.getLogger('hikload')
    if args.debug:
        logging.basicConfig(stream=log_stream, format=FORMAT)
        logger.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(stream=log_stream, format=FORMAT)
        logger.setLevel(logging.INFO)

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(args)
    app.exec_()
    window.show()

if __name__ == '__main__':
    if GUI == False:
        print("PyQt5 is not installed, can not run GUI")
    else:
        main()