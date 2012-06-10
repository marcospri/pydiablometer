import pyHook
import pythoncom
import Queue as queue

from multiprocessing import Process, Queue

from PySide.QtCore import QThread, Signal
from PySide.QtUiTools import QUiLoader
from PySide import QtGui
from PySide.QtCore import QFile, QSize
from PySide.QtGui import QLCDNumber

WINDOW_NAMES = ["Diablo III"]


class EventListener(Process):
    """
    Catches event using pyHook

    Can't get it working in anything but a different process
    """

    def __init__(self, queue):
        super(EventListener, self).__init__()
        self.queue = queue

    def on_event(self, event):
        if event.WindowName in WINDOW_NAMES:
            self.queue.put(event)
        return True

    def run(self):
        hm = pyHook.HookManager()
        hm.SubscribeMouseAllButtonsDown(self.on_event)
        hm.SubscribeKeyUp(self.on_event)
        hm.HookMouse()
        hm.HookKeyboard()
        pythoncom.PumpMessages()
        hm.UnhookMouse()
        hm.HookKeyboard()


class EventProcessor(QThread):
    """
    Gets the events from the EventListener process on a queue
    """
    dataReady = Signal(object)

    def __init__(self, queue):
        super(EventProcessor, self).__init__()
        self.queue = queue
        self.running = True

    def run(self):
        while self.running:
            try:
                event = self.queue.get(timeout=1)
            except queue.Empty:
                pass
            else:
                self.dataReady.emit(event)


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Diablo Meter")

        size = QSize(530, 470)
        self.resize(size)

        # Load ui from gui definition file
        try:
            loader = QUiLoader()
            file = QFile("widgets/widgets.ui")
            file.open(QFile.ReadOnly)
            mainWindow = loader.load(file, self)
            file.close()
        except:
            self.warning_message("Error loading file", "An error occurred while loading a UI definition file")
            exit()

        #Reference to the components
        self.left_click_lcd = mainWindow.findChild(QLCDNumber, "left_click_lcd")
        self.right_click_lcd = mainWindow.findChild(QLCDNumber, "right_click_lcd")
        self.action_keys_lcds = [mainWindow.findChild(QLCDNumber, "action_1_lcd"),
                mainWindow.findChild(QLCDNumber, "action_2_lcd"),
                mainWindow.findChild(QLCDNumber, "action_3_lcd"),
                mainWindow.findChild(QLCDNumber, "action_4_lcd")]

        options_menu = self.menuBar().addMenu("&Options")
        options_menu.addAction(QtGui.QAction("&Restart Counters", self, triggered=self.restart_counters))

        #Queue to share messsages to the message pupm on EventListener
        q = Queue()
        self.event_listener = EventListener(q)
        self.event_listener.start()

        self.thread = EventProcessor(q)
        self.thread.dataReady.connect(self.on_hook_event)
        self.thread.start()

        #Key Names we are interested in. The order in the tuple
        #determines to which action key it's mapped
        self.key_maps = ("1", "2", "3", "4")

    def restart_counters(self):
        [lcd.display(0) for lcd in [self.left_click_lcd, self.right_click_lcd] + self.action_keys_lcds]

    def on_hook_event(self, event):
        if event.MessageName == "mouse left down":
            self.left_click()
        elif event.MessageName == "mouse right down":
            self.right_click()
        elif hasattr(event, "Key"):
            self.key_event(event.Key)

    def closeEvent(self, event):
        self.event_listener.terminate()
        if self.thread.isRunning():
            self.thread.running = False
            self.thread.wait()

    def left_click(self):
        self.left_click_lcd.display(self.left_click_lcd.value() + 1)

    def right_click(self):
        self.right_click_lcd.display(self.right_click_lcd.value() + 1)

    def key_event(self, key):
        if key in self.key_maps:
            lcd = self.action_keys_lcds[self.key_maps.index(key)]
            lcd.display(lcd.value() + 1)


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
