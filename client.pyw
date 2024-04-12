from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtPrintSupport import QPrintDialog
import socket, ssl, pickle, os, dotenv

dotenv.load_dotenv()

HOST = os.getenv('IP_ADDR', 'localhost')
PORT = int(os.getenv('PORT', '5555'))
CERT_FILE = os.getenv('CERT_FILE', None)

if (not CERT_FILE):
    print("Required SSL Certificate file not found")
    exit(1)

class Connection(qtc.QThread):

    getlogs=qtc.pyqtSignal()
    sendlogs=qtc.pyqtSignal(list)
    finished=qtc.pyqtSignal()
    progress=qtc.pyqtSignal(dict)
    errorsignal=qtc.pyqtSignal(str)
    closewin=qtc.pyqtSignal()
    sendmessage=qtc.pyqtSignal(str)
    connected=qtc.pyqtSignal()
    handleuser=qtc.pyqtSignal()

    def __init__(self, room, username):
        super().__init__()
        self.loop=True
        self.room=room
        self.username=username
        self.finished.connect(self.terminate)
        self.getlogs.connect(self.fetch_logs)

    def run(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self.ssl_context.load_verify_locations(CERT_FILE)
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
        self.client_socket.send(pickle.dumps({'room': self.room, 'username':self.username, 'logs':['joined', self.username, qtc.QTime.currentTime().toString(), qtc.QDate.currentDate().toString()]}))
        self.receive_messages(self.client_socket)

    def receive_messages(self, client_socket):
        while self.loop:
            try:
                data = client_socket.recv(20480)
                data = pickle.loads(data)
                if 'error' in data:
                    self.handleuser.emit()
                elif 'message' in data:
                    self.progress.emit(data)
                else:
                    if 'users' in data:
                        self.sendusers.emit(data['users'], self.username)
                    else:
                        self.sendlogs.emit(data['logs'])
            except Exception as e:
                print(e)
                self.errorsignal.emit('Could not connect to the server')
                return

    def send_message(self, message):
        emb={
            'room': self.room,
            'message': message if message else None,
            'logs': ['edited', self.username, qtc.QTime.currentTime().toString(), qtc.QDate.currentDate().toString()]
        }
        self.client_socket.send(pickle.dumps(emb))

    def fetch_logs(self):
        self.client_socket.send(pickle.dumps({'room': self.room, 'logs':''}))

    def terminate(self):
        self.loop=False
        try:
            self.client_socket.send(pickle.dumps({'room': self.room, 'message': '', 'username':self.username, 'logs':['left', self.username, qtc.QTime.currentTime().toString(), qtc.QDate.currentDate().toString()]}))
        except:
            pass
        return super().terminate()

class PlainTextEdit(qtw.QPlainTextEdit):

    updatestatus = qtc.pyqtSignal(str)

    def setConnection(self, connection):
        self.connection = connection
        self.prev=''

    def keyReleaseEvent(self, e):
        if self.prev!=self.toPlainText():
            self.communicate()
        return super().keyReleaseEvent(e)

    def communicate(self):
        self.connection.sendmessage.emit(self.toPlainText())
        self.updatestatus.emit('edited')
        self.prev=self.toPlainText()

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
        self.layout().addWidget(self.text1, 9, 0, 2, 0, qtc.Qt.AlignCenter)

        self.text2 = qtw.QLabel('Enter the code:')
        self.text2.setFont(qtg.QFont('Arial', 27))
        self.layout().addWidget(self.text2, 12, 0, 4, 0, qtc.Qt.AlignCenter)

        self.code = qtw.QLineEdit()
        self.layout().addWidget(self.code, 16, 0, 5, 0, qtc.Qt.AlignHCenter)
        self.code.setFont(qtg.QFont('Arial', 27))
        self.code.setFocus()
        self.code.setFixedWidth(800)
        self.code.setAlignment(qtc.Qt.AlignCenter)

        self.text3 = qtw.QLabel('Enter your name:')
        self.text3.setFont(qtg.QFont('Arial', 27))
        self.layout().addWidget(self.text3, 22, 0, 4, 0, qtc.Qt.AlignCenter)

        self.name = qtw.QLineEdit()
        self.layout().addWidget(self.name, 26, 0, 5, 0, qtc.Qt.AlignHCenter)
        self.name.setFont(qtg.QFont('Arial', 27))
        self.name.setFixedWidth(800)
        self.name.setAlignment(qtc.Qt.AlignCenter)
        self.code.returnPressed.connect(self.name.setFocus)
        self.name.returnPressed.connect(self.connectionwin)

        self.but1 = qtw.QPushButton('Create or Connect to the room')
        self.but1.setFont(qtg.QFont('Arial', 25))
        self.but1.setCursor(qtc.Qt.PointingHandCursor)
        self.but1.clicked.connect(self.connectionwin)
        self.layout().addWidget(self.but1, 32, 0, 13, 0, qtc.Qt.AlignHCenter)

    def connectionwin(self):
        if (self.code.text()=='' or len(self.code.text())<4 or len(self.code.text())>10 or not self.code.text().isalnum()):
            self.showerror('Invalid Code', 'Please enter a valid code')
            return
        if (self.name.text()=='' or len(self.name.text())<4 or len(self.name.text())>10 or not self.name.text().isalnum()):
            self.showerror('Invalid Username', 'Please enter a valid username')
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
        self.room=self.code.text()
        self.username=self.name.text()
        self.create_connection()

    def create_connection(self):
        self.win.setFocus()
        def handler(err):
            try:
                self.textwin.close()
            except:
                pass
            self.showerror('Connection Error', err)
        def userhandler():
            try:
                self.textwin.close()
            except:
                pass
            self.showerror('User Exists', 'The username provided is already in use.\nPlease use a different username.')
            self.connection.finished.emit()
            del self.connection
            return
        try:
            self.textwin
            self.showerror('Error', 'A connection already exists')
            self.win.close()
            return
        except:
            pass
        self.connection = Connection(self.room, self.username)
        self.connection.closewin.connect(self.win.close)
        self.connection.errorsignal.connect(handler)
        self.connection.connected.connect(self.textwindow)
        self.connection.sendlogs.connect(self.showhistory)
        self.connection.handleuser.connect(userhandler)
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
        self.textwin.editor.updatestatus.connect(self.updatestatus)
        self.connection.progress.connect(self.updatewin)
        self.textwin.fixedfont = qtg.QFontDatabase.systemFont(qtg.QFontDatabase.FixedFont)
        self.textwin.fixedfont.setPointSize(20)
        self.textwin.editor.setFont(self.textwin.fixedfont)
        self.textwin.layout.addWidget(self.textwin.editor)
    
        self.textwin.container = qtw.QWidget(self.textwin)
        self.textwin.container.setLayout(self.textwin.layout)
        self.textwin.setCentralWidget(self.textwin.container)

        self.textwin.status = qtw.QStatusBar()
        self.textwin.setStatusBar(self.textwin.status)
        self.textwin.statusText = qtw.QLabel()
        self.textwin.statusText.setFont(qtg.QFont('Arial', 18))
        self.textwin.status.addWidget(self.textwin.statusText)

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

        self.textwin.hist_action = qtw.QAction("See History", self)
        self.textwin.hist_action.setStatusTip("See all history")
        self.textwin.hist_action.triggered.connect(self.connection.getlogs.emit)
        self.textwin.edit_toolbar.addAction(self.textwin.hist_action)
        self.textwin.editor.updatestatus.emit('joined')
        
        self.textwin.show()

    def showhistory(self, data):
        self.histwin = qtw.QWidget()
        self.histwin.setWindowTitle('History')
        self.histwin.setGeometry(100, 100, 800, 400)
        self.histwin.setMaximumHeight(400)
        self.histwin.setMaximumWidth(800)
        self.histwin.setWindowFlags(self.histwin.windowFlags() | qtc.Qt.CustomizeWindowHint)
        self.histwin.setWindowFlags(self.histwin.windowFlags() & ~qtc.Qt.WindowMaximizeButtonHint)
        self.histwin.setLayout(qtw.QVBoxLayout())
        self.histwin.text = qtw.QTextEdit()
        self.histwin.text.setFont(qtg.QFont('Arial', 20))
        self.histwin.text.setReadOnly(True)
        self.histwin.layout().addWidget(self.histwin.text)
        self.histwin.show()
        self.histwin.text.clear()
        for i in data:
            if i[0]=='joined':
                self.histwin.text.append(i[3]+' '+i[2]+': '+i[1]+' joined the room')
            elif i[0]=='left':
                self.histwin.text.append(i[3]+' '+i[2]+': '+i[1]+' left the room')
            else:
                self.histwin.text.append(i[3]+' '+i[2]+': '+i[1]+' edited the text')

    def updatewin(self, data):
        if 'message' in data:
            if data['message']:
                self.textwin.editor.setPlainText(data['message'])
            else:
                self.textwin.editor.clear()
        if 'logs' in data:
            if "edited" in data['logs']:
                self.textwin.statusText.setText("Edited by "+data['logs'][1]+" at "+data['logs'][2]+" "+data['logs'][3])
            elif "joined" in data['logs']:
                self.textwin.statusText.setText(data['logs'][1]+" joined the room")
            else:
                self.textwin.statusText.setText(data['logs'][1]+" left the room")

    def updatestatus(self, status):
        if status=='edited':
            self.textwin.statusText.setText("Edited by "+self.username+" at "+qtc.QTime.currentTime().toString()+" "+qtc.QDate.currentDate().toString())
        elif status=='joined':
            self.textwin.statusText.setText(self.username+" joined the room")

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
                self.textwin.editor.communicate()

    def redo_new(self):
        self.textwin.editor.redo()
        self.textwin.editor.communicate()

    def paste_new(self):
        self.textwin.editor.paste()
        self.textwin.editor.communicate()

    def undo_new(self):
        self.textwin.editor.undo()
        self.textwin.editor.communicate()

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