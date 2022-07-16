from __future__ import annotations

import logging
import os
import sys
import threading
from io import StringIO

from PyQt5 import QtGui, QtWidgets, uic

from hikload.hikvisionapi.classes import HikvisionServer
from hikload.uifiles.MainWindow import Ui_MainWindow
from hikload.uifiles.Startup import Ui_Startup

from .download import (create_folder_and_chdir, download_recording,
                       search_for_recordings, search_for_recordings_mock)

log_stream = StringIO()


class downloadThread(threading.Thread):
    def __init__(self, window: MainWindow, server: HikvisionServer, args):
        threading.Thread.__init__(self)
        self.window = window
        self.running = True
        self.server = server
        self.args = args
        self.recordings = None
        self.finished = 0

        if not args:
            raise ValueError("args is not set correctly")

    def run(self):
        logger = logging.getLogger('hikload')
        logger.info("Download thread started")
        logger.debug(f"{self.args=}")

        if self.args.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        if self.args.mock:
            recordings = search_for_recordings_mock(self.args)
        else:
            recordings = search_for_recordings(self.server, self.args)
        self.recordings = recordings

        self.window.ui.progressBar.setMaximum(len(recordings))
        self.window.ui.progressBar.setValue(0)
        create_folder_and_chdir(self.args.downloads)
        original_path = os.path.abspath(os.getcwd())

        self.window.ui.treeWidget.clear()
        i = 0
        for recording in recordings:
            item = QtWidgets.QTreeWidgetItem([str(recording)])
            self.window.ui.treeWidget.insertTopLevelItems(i, [item])
            i += 1

        for recordingobj in recordings:
            if self.running is False:
                return
            self.window.ui.progressBar.setValue(self.finished)

            download_recording(self.server, self.args,
                               recordingobj, original_path)
            self.window.ui.treeWidget.takeTopLevelItem(0)

            self.finished += 1
        self.window.ui.progressBar.setValue(len(recordings))
        logger.info("Finished downloading all recordings")
        logger.info("download thread finished")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, args=None):
        super(MainWindow, self).__init__()
        self.args = None
        startup = Startup(parent=self, args=args)
        startup.show()
        startup.exec_()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(
            QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

        server = HikvisionServer(
            self.args.server, self.args.username, self.args.password)
        self.downloadthread = downloadThread(self, server, args)
        self.downloadthread.start()

        while True:
            QtGui.QGuiApplication.processEvents()
            self.ui.textEdit.textCursor().selectionEnd()
            value = log_stream.getvalue()
            if len(value) != 0:
                self.ui.textEdit.append(value[:-1])
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
        super(Startup, self).__init__()
        self.ui = Ui_Startup()
        self.ui.setupUi(self)
        self.args = args
        self.populate_with_args(args)

        self.ui.downloads_folder_button.clicked.connect(
            self.select_download_folder)
        self.ui.test_connection_button.clicked.connect(self.test_connection)
        self.ui.start_downloading_button.clicked.connect(
            self.start_downloading)

        self.ui.start_date.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.ui.end_date.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.parent = parent
        self.skipclosing = False
        self.ui.start_downloading_button.setEnabled(False)

    def populate_with_args(self, args=None):
        self.ui.server_ip.setText(args.server)
        self.ui.downloads_folder.setText(args.downloads)
        self.ui.username.setText(args.username)
        self.ui.password.setText(args.password)
        self.ui.folder_behavior.setCurrentIndex(list.index(
            [None, 'onepercamera', 'oneperday', 'onepermonth', 'oneperyear'], args.folders))
        if args.photos:
            self.ui.download_type.setCurrentIndex(1)
        self.ui.video_format.setCurrentIndex(
            list.index(['mkv', 'mp4', 'avi'], args.videoformat))
        self.ui.start_date.setDateTime(args.starttime)
        self.ui.end_date.setDateTime(args.endtime)
        self.ui.debug.setChecked(bool(args.debug))
        self.ui.force.setChecked(bool(args.force))
        self.ui.localtime.setChecked(bool(args.localtimefilenames))
        self.ui.ffmpeg.setChecked(bool(args.ffmpeg))
        self.ui.forcetranscoding.setChecked(bool(args.forcetranscoding))

    def get_args(self):
        self.args.server = self.ui.server_ip.text()
        self.args.downloads = self.ui.downloads_folder.text()
        self.args.username = self.ui.username.text()
        self.args.password = self.ui.password.text()
        self.args.folders = [None, 'onepercamera', 'oneperday',
                             'onepermonth', 'oneperyear'][self.ui.folder_behavior.currentIndex()]
        self.args.photos = self.ui.download_type.currentIndex() == 1
        self.args.videoformat = ['mkv', 'mp4',
                                 'avi'][self.ui.video_format.currentIndex()]
        self.args.starttime = self.ui.start_date.dateTime().toPyDateTime()
        self.args.endtime = self.ui.end_date.dateTime().toPyDateTime()
        self.args.debug = self.ui.debug.isChecked()
        self.args.force = self.ui.force.isChecked()
        self.args.localtimefilenames = self.ui.localtime.isChecked()
        self.args.ffmpeg = self.ui.ffmpeg.isChecked()
        self.args.forcetranscoding = self.ui.forcetranscoding.isChecked()
        cameras = []
        for i in self.ui.cameras.selectedIndexes():
            cameras.append(self.ui.cameras.model().data(i))
        self.args.cameras = cameras
        return self.args

    def select_download_folder(self):
        file = str(QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Directory"))
        self.ui.downloads_folder.setText(file)

    def start_downloading(self):
        self.skipclosing = True
        self.parent.args = self.get_args()
        self.close()

    def test_connection(self):
        if not self.args.mock:
            try:
                server = HikvisionServer(self.ui.server_ip.text(
                ), self.ui.username.text(), self.ui.password.text())
                server.test_connection()
                channelList = server.Streaming.getChannels()
                self.ui.cameras.clear()
                i = 0
                for channel in channelList['StreamingChannelList']['StreamingChannel']:
                    item = QtWidgets.QTreeWidgetItem([channel['id']])
                    self.ui.cameras.insertTopLevelItems(i, [item])
                    i += 1
                self.ui.cameras.selectAll()
            except Exception as exc:
                ErrorDialog(
                    f"Could not connect to the server.\n{exc}").exec_()
                logging.error(exc)
                return
        else:
            self.ui.cameras.clear()
            i = 0
            for channel in ["101", "201", "301"]:
                item = QtWidgets.QTreeWidgetItem([channel])
                self.ui.cameras.insertTopLevelItems(i, [item])
                i += 1
            self.ui.cameras.selectAll()
        QtWidgets.QMessageBox.information(
            self, "Success", "Successfully connected to the server")
        self.ui.start_downloading_button.setEnabled(True)

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
    main()
