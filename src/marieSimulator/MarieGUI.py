import sys
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QToolBar, QPushButton, QStatusBar, QFileDialog, QTableWidgetItem, QTableWidget, QAbstractItemView, QHeaderView, QInputDialog, QMessageBox
from PySide6.QtGui import QAction, QDesktopServices, QColor, QPalette

from .Marie import Marie
from .MarieReader import MarieReader

app = QApplication(sys.argv)

class MarieGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Setup
        self.setWindowTitle("Marie Simulator")
        self.setFixedSize(800, 600)

        # Variables
        self.filename = None
        self.M = []
        self.symbolTable = {}

        # Marie Variables
        self.marie = None
        self.marieReader = None

        # Widgets
        self.programTableWidget = None
        self.symbolTableWidget = None
        self.registerTableWidget = None
        self.memoryTableWidget = None

        # Define GUI
        self.setup()
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._advance)
    
    
    def setup(self):

        self.setupToolBarAndMenuBar()

        self.programTableWidget = QTableWidget()
        self.programTableWidget.setFixedSize(270, 250)
        self.programTableWidget.setStatusTip("Program Table")
        self.programTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.programTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.symbolTableWidget = QTableWidget()
        self.symbolTableWidget.setFixedSize(220, 250)
        self.symbolTableWidget.setStatusTip("Symbol Table")
        self.symbolTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.symbolTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.registerTableWidget = QTableWidget(7, 1, self)
        self.registerTableWidget.setStatusTip("Register Table")
        self.registerTableWidget.setHorizontalHeaderLabels(["Register", "Value"])
        self.registerTableWidget.setVerticalHeaderLabels(["AC", "PC", "MAR", "MBR", "IR", "InReg", "OutReg"])
        self.registerTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.registerTableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.updateRegisterTableWidget()

        self.memoryTableWidget = QTableWidget(self)
        self.memoryTableWidget.setStatusTip("Memory Table")
        self.updateMemoryTableWidget()
    
        grid = QGridLayout()
        grid.addWidget(self.programTableWidget, 0, 0, 1, 1)
        grid.addWidget(self.symbolTableWidget, 0, 1, 1, 1)
        grid.addWidget(self.registerTableWidget, 0, 2, 1, 1)
        grid.addWidget(self.memoryTableWidget, 1, 0, 1, 3)
        container = QWidget()
        container.setLayout(grid)
        self.setCentralWidget(container)

    def setupToolBarAndMenuBar(self):
        toolbar = QToolBar(self)
        statusbar = QStatusBar(self)
        menu = self.menuBar()

        runButton = QPushButton("Run", self)
        stepButton = QPushButton("Step", self)
        resetButton = QPushButton("Reset", self)
        runButton.setStatusTip("Run the program")
        stepButton.setStatusTip("Step through the program")
        resetButton.setStatusTip("Reset the Registers and keep the Memory")
        runButton.clicked.connect(self.guiRun)
        stepButton.clicked.connect(self.guiStep)
        resetButton.clicked.connect(self.guiReset)
        toolbar.addWidget(runButton)
        toolbar.addWidget(stepButton)
        toolbar.addWidget(resetButton)

        self.addToolBar(toolbar)
        self.setStatusBar(statusbar)

        def loadFunc():
            fileDialog = QFileDialog()
            fileDialog.setFileMode(QFileDialog.ExistingFile)
            filename = fileDialog.getOpenFileName(self, "Open File", "")[0]
            if filename:
                self.fileName = filename
                reloadFunc()
        
        def reloadFunc():
            if not hasattr(self, 'fileName'):
                return
            self.timer.stop()
            try:
                self.marieReader = MarieReader(self.fileName)
            except (OSError, ValueError) as error:
                QMessageBox.warning(self, "Assembly error", str(error))
                return
            self.marie = self._newMachine()

            self.M = self.marie.M[:]
            self.symbolTable = self.marie.symbolTable.copy()

            self.updateRegisterTableWidget()
            self.updateProgramTableWidget()
            self.updateSymbolTableWidget()
            self.updateMemoryTableWidget()

        def quitFunc():
            sys.exit(self.close())
        
        def editFunc():
            pass
        
        def saveFunc():
            pass
        
        def helpFunc():
            QDesktopServices.openUrl(QtCore.QUrl("https://github.com/dehadeaaryan/MarieSimulator/issues"))
        
        def aboutFunc():
            QDesktopServices.openUrl(QtCore.QUrl("https://github.com/dehadeaaryan/MarieSimulator/blob/main/README.md"))

        fileMenu = menu.addMenu("&File")
        fileLoad = QAction("&Load", self, shortcut="Ctrl+O")
        fileReload = QAction("&Reload", self, shortcut="Ctrl+R")
        fileClose = QAction("&Close", self)
        fileLoad.triggered.connect(loadFunc)
        fileReload.triggered.connect(reloadFunc)
        fileClose.triggered.connect(quitFunc)
        fileMenu.addActions([fileLoad, fileReload, fileClose])

        editMenu = menu.addMenu("&Edit")
        editEdit = QAction("&Edit", self)
        editSave = QAction("&Save", self)
        editEdit.triggered.connect(editFunc)
        editSave.triggered.connect(saveFunc)
        editMenu.addActions([editEdit, editSave])

        helpMenu = menu.addMenu("&Help")
        helpHelp = QAction("&Help", self)
        helpAbout = QAction("&More", self)
        helpHelp.setStatusTip("Open help")
        helpAbout.setStatusTip("About the application")
        helpHelp.triggered.connect(helpFunc)
        helpAbout.triggered.connect(aboutFunc)
        helpMenu.addActions([helpHelp, helpAbout])



    def updateProgramTableWidget(self):
        listing = self.marieReader.program.listing
        self.programTableWidget.setRowCount(len(listing))
        self.programTableWidget.setColumnCount(4)
        self.programTableWidget.setHorizontalHeaderLabels(["Label", "Opcode", "Address", "HEX"])
        self.programTableWidget.setVerticalHeaderLabels([f"{row['address']:03X}" for row in listing])
        for i, row in enumerate(listing):
            tokens = row['source'].split('/')[0].split(';')[0].split()
            operand = tokens[-1] if row['operation'] not in ('INPUT','OUTPUT','HALT','CLEAR') else '000'
            for j, value in enumerate((row['label'] or '', row['operation'], operand, f"{row['word']:04X}")):
                self.programTableWidget.setItem(i, j, QTableWidgetItem(value))

    def updateSymbolTableWidget(self):
        self.symbolTableWidget.setRowCount(len(self.symbolTable))
        self.symbolTableWidget.setColumnCount(2)
        self.symbolTableWidget.setHorizontalHeaderLabels(["Label", "Address"])
        self.symbolTableWidget.setVerticalHeaderLabels([str(i) for i in range(len(self.symbolTable))])
        for i, (label, address) in enumerate(self.symbolTable.items()):
            self.symbolTableWidget.setItem(i, 0, QTableWidgetItem(label))
            self.symbolTableWidget.setItem(i, 1, QTableWidgetItem(hex(address)[2:].zfill(3).upper()))
    
    def updateRegisterTableWidget(self):
        if self.marie == None:
            self.AC = 0
            self.PC = 0
            self.MAR = 0
            self.MBR = 0
            self.IR = 0
            self.InReg = 0
            self.OutReg =  0

            temp = [self.AC, self.PC, self.MAR, self.MBR, self.IR, self.InReg, self.OutReg]
            for i in range(7):
                self.registerTableWidget.setItem(i, 0, QTableWidgetItem(hex(temp[i])[2:].zfill(4).upper()))

        else:
            self.AC = self.marie.AC
            self.PC = self.marie.PC
            self.MAR = self.marie.MAR
            self.MBR = self.marie.MBR
            self.IR = self.marie.IR
            self.InReg = self.marie.InReg
            self.OutReg =  self.marie.OutReg
            self.M = self.marie.M

            temp = [self.AC, self.PC, self.MAR, self.MBR, self.IR, self.InReg, self.OutReg]
            for i in range(7):
                self.registerTableWidget.setItem(i, 0, QTableWidgetItem(hex(temp[i])[2:].zfill(4).upper()))
            
            self.updateMemoryTableWidget()

    def updateMemoryTableWidget(self):
        self.memoryTableWidget.setRowCount(16**2)
        self.memoryTableWidget.setColumnCount(16)
        self.memoryTableWidget.setVerticalHeaderLabels([(hex(i)[2:].zfill(2) + "0").upper() for i in range(16**2)])
        self.memoryTableWidget.setHorizontalHeaderLabels([("+" + hex(i)[2:].zfill(1)).upper() for i in range(16)])
        self.memoryTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.memoryTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.M = self.marie.M if self.marie != None else [0] * (16**3)
        for i in range(16**2):
            for j in range(16):
                self.memoryTableWidget.setItem(i, j, QTableWidgetItem(hex(self.M[i*16+j])[2:].zfill(4).upper()))



    def _newMachine(self):
        machine = Marie(self.marieReader, input_provider=self._readInput)
        machine.GUI = True
        return machine

    def _readInput(self):
        self.timer.stop()
        text, accepted = QInputDialog.getText(self, "MARIE Input", "16-bit hexadecimal value (0000–FFFF):")
        if not accepted:
            raise ValueError("Input canceled. Reset to resume.")
        value = int(text, 16)
        if not 0 <= value <= 65535:
            raise ValueError("Input must be between 0000 and FFFF.")
        return value

    def guiRun(self):
        if self.marie and self.marie.canStep:
            self.timer.start()

    def guiStep(self):
        self.timer.stop()
        self._advance()

    def _advance(self):
        if not self.marie or not self.marie.canStep:
            self.timer.stop()
            return
        was_running = self.timer.isActive()
        try:
            changed = self.marie.step() or []
        except ValueError as error:
            self.timer.stop()
            self.marie.canStep = False
            QMessageBox.warning(self, "Execution error", str(error))
            return
        self.updateRegisterTableWidget()
        for i, row in enumerate(self.marieReader.program.listing):
            color = QColor(51, 102, 153) if row['address'] == self.marie.last_address else QColor(0, 0, 0, 0)
            self.setColortoRow(self.programTableWidget, i, color)
        for address in changed:
            self.memoryTableWidget.item(address // 16, address % 16).setBackground(QColor(51, 102, 153))
        if not self.marie.canStep:
            self.timer.stop()
        elif was_running:
            self.timer.start()

    def guiReset(self):
        self.timer.stop()
        if self.marieReader:
            self.marie = self._newMachine()
            for i in range(self.programTableWidget.rowCount()):
                self.setColortoRow(self.programTableWidget, i, QColor(0, 0, 0, 0))
            self.updateRegisterTableWidget()

    def setColortoRow(self, table, rowIndex, color):
        if 0 <= rowIndex < table.rowCount():
            for j in range(table.columnCount()):
                if table.item(rowIndex, j):
                    table.item(rowIndex, j).setBackground(color)


if __name__ == "__main__":

    window = MarieGUI()
    window.show()

    sys.exit(app.exec())