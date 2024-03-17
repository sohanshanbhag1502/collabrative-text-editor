from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtPrintSupport import QPrintDialog
import socket, ssl, pickle

HOST = '20.193.141.135'
PORT = 5555
class Connection(qtc.QThread):

    finished=qtc.pyqtSignal()
    progress=qtc.pyqtSignal(list)
    errorsignal=qtc.pyqtSignal(str)
    closewin=qtc.pyqtSignal()
    sendmessage=qtc.pyqtSignal(str)
    connected=qtc.pyqtSignal()

    def __init__(self, room):
        super().__init__()
        self.loop=True
        self.room=room
        self.finished.connect(self.terminate)

    def run(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self.ssl_context.load_verify_locations("domain.crt")
        self.ssl_context.check_hostname = False  
        self.ssl_context.verify_mode = ssl.CERT_NONE

        try:
            self.client_socket.connect((HOST, PORT))
            self.client_socket = self.ssl_context.wrap_socket(self.client_socket, 
                server_hostname=HOST)
        except Exception:
            self.closewin.emit()
            self.errorsignal.emit('Could not connect to the server')
            return

        self.closewin.emit()
        self.connected.emit()
        self.sendmessage.connect(self.send_message)
        self.client_socket.send(pickle.dumps({'room': self.room}))
        self.receive_messages(self.client_socket)

    def receive_messages(self, client_socket):
        while self.loop:
            try:
                data = client_socket.recv(1024)
                data = pickle.loads(data)
                self.progress.emit(data)
            except Exception:
                self.errorsignal.emit('Could not connect to the server')
                return

    def send_message(self, message):
        emb={
            'room': self.room,
            'message': message if message else None
        }
        self.client_socket.send(pickle.dumps(emb))

    def terminate(self):
        self.loop=False
        try:
            self.client_socket.send(pickle.dumps({'room': self.room, 'message': ''}))
        except:
            pass
        return super().terminate()

class PlainTextEdit(qtw.QPlainTextEdit):
    def setConnection(self, connection):
        self.connection = connection

    def keyReleaseEvent(self, e: qtg.QKeyEvent):
        self.connection.sendmessage.emit(self.toPlainText())
        return super().keyReleaseEvent(e)

class MainWindow(qtw.QMainWindow):

    delvar = qtc.pyqtSignal()

    def __init__(self, connection):
        super().__init__()
        self.connection = connection

    def closeEvent(self, a0: qtg.QCloseEvent) -> None:
        self.connection.finished.emit()
        self.delvar.emit()
        return super().closeEvent(a0)

class Window(qtw.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Collabrative Text Editor')
        self.setLayout(qtw.QGridLayout())
        self.setGeometry(100, 100, 1000, 450)
        self.setMaximumHeight(450)
        self.setMaximumWidth(1000)
        self.setWindowFlags(self.windowFlags() | qtc.Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~qtc.Qt.WindowMaximizeButtonHint)
        self.setStyleSheet('QPushButton{border-radius:20px;backgound-color:white;color:black;hover:backgound-color:lightblue;padding:15px;border:3px solid blue;}')
        self.createcomponents()
        self.show()

    def createcomponents(self):
        self.title= qtw.QLabel('Text Editor')
        self.title.setFont(qtg.QFont('Arial', 35))
        self.layout().addWidget(self.title, 0, 0, 0, 0, qtc.Qt.AlignTop | qtc.Qt.AlignHCenter)

        self.text1 = qtw.QLabel('Welcome to Text Editor\nEnter a code or create a new one to get started')
        self.text1.setFont(qtg.QFont('Arial', 25))
        self.text1.setAlignment(qtc.Qt.AlignCenter)
        self.layout().addWidget(self.text1, 5, 0, 2, 0, qtc.Qt.AlignCenter)

        self.text2 = qtw.QLabel('Enter the code:')
        self.text2.setFont(qtg.QFont('Arial', 27))
        self.layout().addWidget(self.text2, 8, 0, 4, 0, qtc.Qt.AlignCenter)

        self.code = qtw.QLineEdit()
        self.layout().addWidget(self.code, 11, 0, 5, 0, qtc.Qt.AlignHCenter)
        self.code.setFont(qtg.QFont('Arial', 27))
        self.code.setFocus()
        self.code.setFixedWidth(800)
        self.code.setAlignment(qtc.Qt.AlignCenter)

        self.but1 = qtw.QPushButton('Create or Connect to the room')
        self.but1.setFont(qtg.QFont('Arial', 25))
        self.but1.setCursor(qtc.Qt.PointingHandCursor)
        self.but1.clicked.connect(self.connectionwin)
        self.layout().addWidget(self.but1, 13, 0, 13, 0, qtc.Qt.AlignHCenter)

    def connectionwin(self):
        if (self.code.text()=='' or self.code.text().isspace() or len(self.code.text())<4 or len(self.code.text())>10 or not self.code.text().isalnum()):
            self.showerror('Invalid Code', 'Please enter a valid code')
            return

        self.win = qtw.QWidget()
        self.win.setWindowTitle('Connecting to the room')
        self.win.setLayout(qtw.QGridLayout())
        self.win.setGeometry(150, 350, 1000, 700)
        self.win.setMaximumHeight(150)
        self.win.setMaximumWidth(350)
        self.win.setWindowFlags(self.win.windowFlags() | qtc.Qt.CustomizeWindowHint)
        self.win.setWindowFlags(self.win.windowFlags() & ~qtc.Qt.WindowMaximizeButtonHint)
        self.label1 = qtw.QLabel('Connecting to the room')
        self.label1.setFont(qtg.QFont('Arial', 25))
        self.win.layout().addWidget(self.label1, 0, 0, 0, 0, qtc.Qt.AlignCenter)
        self.win.show()
        
        self.create_connection()

    def create_connection(self):
        self.win.setFocus()
        def handler(err):
            try:
                self.textwin.close()
            except:
                pass
            self.showerror('Connection Error', err)
        try:
            self.textwin
            self.showerror('Error', 'A connection already exists')
            self.win.close()
            return
        except:
            pass
        self.room=self.code.text()
        self.connection = Connection(self.room)
        self.connection.closewin.connect(lambda:(self.win.close()))
        self.connection.errorsignal.connect(handler)
        self.connection.connected.connect(self.textwindow)
        self.connection.start()
        self.win.close()

    def delwin(self):
        del self.textwin

    def textwindow(self):
        self.textwin=MainWindow(self.connection)
        self.textwin.setGeometry(100, 100, 600, 400)
        self.textwin.setWindowTitle('Room: '+self.room)
        self.textwin.layout = qtw.QVBoxLayout()
        self.textwin.delvar.connect(self.delwin)
        self.textwin.editor = PlainTextEdit()
        self.textwin.editor.setConnection(self.connection)
        self.connection.progress.connect(lambda data:self.textwin.editor.setPlainText(data[0]) if data[0] else self.textwin.editor.clear())
        self.textwin.fixedfont = qtg.QFontDatabase.systemFont(qtg.QFontDatabase.FixedFont)
        self.textwin.fixedfont.setPointSize(20)
        self.textwin.editor.setFont(self.textwin.fixedfont)
        self.textwin.layout.addWidget(self.textwin.editor)
    
        self.textwin.container = qtw.QWidget(self.textwin)
        self.textwin.container.setLayout(self.textwin.layout)
        self.textwin.setCentralWidget(self.textwin.container)

        self.textwin.status = qtw.QStatusBar()
        self.textwin.setStatusBar(self.textwin.status)

        self.textwin.file_toolbar = qtw.QToolBar("File")
        self.textwin.addToolBar(self.textwin.file_toolbar)
        self.textwin.open_file_action = qtw.QAction("Open file", self)
        self.textwin.open_file_action.setStatusTip("Open file")
        self.textwin.open_file_action.triggered.connect(self.file_open)

        self.textwin.file_toolbar.addAction(self.textwin.open_file_action)
        self.textwin.save_file_action = qtw.QAction("Save", self)
        self.textwin.save_file_action.setStatusTip("Save current page")
        self.textwin.save_file_action.triggered.connect(self.file_save)

        self.textwin.file_toolbar.addAction(self.textwin.save_file_action)
        self.textwin.saveas_file_action = qtw.QAction("Save As", self)
        self.textwin.saveas_file_action.setStatusTip("Save current page to specified file")
        self.textwin.saveas_file_action.triggered.connect(self.file_saveas)

        self.textwin.file_toolbar.addAction(self.textwin.saveas_file_action)
        self.textwin.print_action = qtw.QAction("Print", self)
        self.textwin.print_action.setStatusTip("Print current page")
        self.textwin.print_action.triggered.connect(self.file_print)

        self.textwin.file_toolbar.addAction(self.textwin.print_action)
        self.textwin.edit_toolbar = qtw.QToolBar("Edit")
        self.textwin.addToolBar(self.textwin.edit_toolbar)

        self.textwin.undo_action = qtw.QAction("Undo", self.textwin)
        self.textwin.undo_action.setStatusTip("Undo last change")
        self.textwin.undo_action.triggered.connect(self.undo_new)
        self.textwin.edit_toolbar.addAction(self.textwin.undo_action)

        self.textwin.redo_action = qtw.QAction("Redo", self.textwin)
        self.textwin.redo_action.setStatusTip("Redo last change")
        self.textwin.redo_action.triggered.connect(self.redo_new)
        self.textwin.edit_toolbar.addAction(self.textwin.redo_action)

        self.textwin.cut_action = qtw.QAction("Cut", self.textwin)
        self.textwin.cut_action.setStatusTip("Cut selected text")
        self.textwin.cut_action.triggered.connect(self.textwin.editor.cut)
        self.textwin.edit_toolbar.addAction(self.textwin.cut_action)

        self.textwin.copy_action = qtw.QAction("Copy", self)
        self.textwin.copy_action.setStatusTip("Copy selected text")
        self.textwin.copy_action.triggered.connect(self.textwin.editor.copy)
        self.textwin.edit_toolbar.addAction(self.textwin.copy_action)

        self.textwin.paste_action = qtw.QAction("Paste", self)
        self.textwin.paste_action.setStatusTip("Paste from clipboard")
        self.textwin.paste_action.triggered.connect(self.paste_new)
        self.textwin.edit_toolbar.addAction(self.textwin.paste_action)

        self.textwin.select_action = qtw.QAction("Select all", self)
        self.textwin.select_action.setStatusTip("Select all text")
        self.textwin.select_action.triggered.connect(self.textwin.editor.selectAll)
        self.textwin.edit_toolbar.addAction(self.textwin.select_action)
        
        self.textwin.show()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", 
                    "Text documents (*.txt)")
        if path:
            try:
                with open(path, 'r') as f:
                    text = f.read()
            except Exception as e:
                self.showerror('File Not Found', 'Please provide a valid text file')
            else:
                self.textwin.path = path
                self.textwin.editor.setPlainText(text)
                self.connection.sendmessage.emit(text)

    def redo_new(self):
        self.textwin.editor.redo()
        self.connection.sendmessage.emit(self.textwin.editor.toPlainText())

    def paste_new(self):
        self.textwin.editor.paste()
        self.connection.sendmessage.emit(self.textwin.editor.toPlainText())

    def undo_new(self):
        self.textwin.editor.undo()
        self.connection.sendmessage.emit(self.textwin.editor.toPlainText())

    def file_save(self):
        if self.textwin.path is None:
            return self.file_saveas()
        self.textwin._save_to_path(self.textwin.path)

    def file_saveas(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save file", "", 
                "Text documents (*.txt)")
        if not path:
            return
        self._save_to_path(path)

    def _save_to_path(self, path):
        text = self.textwin.editor.toPlainText()
        try:
            with open(path, 'w') as f:
                f.write(text)
        except Exception as e:
            self.showerror('Error', 'Could not save the file')

    def file_print(self):
        dlg = QPrintDialog()
        if dlg.exec_():
            self.textwin.editor.print_(dlg.printer())

    def showerror(self, title, text):
        self.error=qtw.QMessageBox(self)
        self.error.setIcon(qtw.QMessageBox.Critical)
        self.error.setWindowTitle(title)
        self.error.setText(text)
        self.error.exec_()
        self.error.setFocus()

    def closeEvent(self, QCloseEvent):
        try:
            self.connection.finished.emit()
        except:
            pass
        try:
            self.textwin.close()
        except:
            pass
        try:
            self.error.close()
        except:
            pass
        return super().closeEvent(QCloseEvent)

if __name__=='__main__':
    app = qtw.QApplication([])
    win = Window()
    app.exec_()