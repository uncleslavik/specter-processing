# ABEL INVERSE TRANSFORM FOR MULTIPLY 2D SPECTERS

# Author: Shcherbakov Viacheslav
# Email: uncle.slavik@gmail.com
# Version: 0.3
# Status: Development
# Date created: 01/12/2016
# Date last modified: 01/15/2016
# Python Version: 3.4
# Require modules: numpy, matplotlib, scipy, six, dateutil, pyparsing

# TODO:  batch specter processing, define spectral line parameters, temperature calculation, UI, documentation

import sys
import glob
import time
import random
from PyQt4 import QtGui,QtCore
import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MultipleLocator, FixedLocator
from matplotlib import cm
from abel import Abel
from specter import Specter
from temperature import Tempereture

class AppForm(QtGui.QMainWindow):
    def __init__(self, parent=None, specterCenter=0, columnNumber=0, windowLength=0):
        QtGui.QMainWindow.__init__(self, parent)
        #self.x, self.y = self.get_data()
        self.create_main_frame()
        self.specter=[]
        self.currentSpecter=0
        self.abelData=[]
        self.specterCenter=specterCenter
        self.columnNumber=columnNumber
        self.windowLength=windowLength

        exitAction = QtGui.QAction(QtGui.QIcon('icons/svg/power.svg'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtGui.qApp.quit)

        openAction = QtGui.QAction(QtGui.QIcon('icons/svg/folder-open.svg'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open file sequence')
        openAction.triggered.connect(self.loadSpecterFromFiles)

        nextSpecterAction = QtGui.QAction(QtGui.QIcon('icons/svg/chevron-right-outline.svg'), '&Next specter', self)
        nextSpecterAction.setStatusTip('Next specter')
        nextSpecterAction.triggered.connect(self.nextSpecter)

        self.currentSpecterInput = QtGui.QLabel()
        self.currentSpecterInput.setFixedWidth(500)

        self.totalSpecterLabel = QtGui.QLabel()
        self.totalSpecterLabel.setFixedWidth(40)

        prevSpecterAction = QtGui.QAction(QtGui.QIcon('icons/svg/chevron-left-outline.svg'), '&Next specter', self)
        prevSpecterAction.setStatusTip('Prev specter')
        prevSpecterAction.triggered.connect(self.prevSpecter)

        self.statusBar().showMessage('Ready')

        self.setWindowTitle('Abel transform and temperature calculation')

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

        self.toolbar = self.addToolBar('Main')
        self.toolbar.addAction(openAction)
        self.toolbar.addAction(prevSpecterAction)
        self.toolbar.addAction(nextSpecterAction)
        self.toolbar.addWidget(self.currentSpecterInput)
        self.toolbar.addWidget(self.totalSpecterLabel)



    def create_main_frame(self):
        self.main_frame = QtGui.QWidget()
        self.fig = Figure((10.0, 8.0), dpi=72)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.canvas.setFocus()
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        self.table = QtGui.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['L1', "L2","LNIST","Aki","Ek","g"])
        header = self.table.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.Stretch)
        self.table.itemChanged.connect(self.setLine)
        self.buttonAddLine = QtGui.QPushButton("Add a line")
        self.buttonAddLine.clicked.connect(self.addLine)
        self.buttonComputeTemp = QtGui.QPushButton("Compute temperature")
        self.buttonComputeTemp.clicked.connect(self.computeTemp)
        self.lines=[]

        vbox = QtGui.QGridLayout()
        vbox.addWidget(self.table, 0, 0, 1, 1)
        vbox.addWidget(self.buttonAddLine, 1, 0, 1, 1)
        vbox.addWidget(self.buttonComputeTemp, 2, 0, 1, 1)
        vbox.addWidget(self.canvas, 0, 1, 1, 4)  # the matplotlib canvas
        vbox.addWidget(self.mpl_toolbar, 1, 1, 1, 4)
        vbox.setColumnStretch(1,5)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

    def on_draw(self):
        self.fig.clear()
        gs = gridspec.GridSpec(2, 1, left=0.05, bottom=0.05, right=0.95, top=0.95, height_ratios=[2,1],)
        self.axes1 = self.fig.add_subplot(gs[0])
        self.axes2 = self.fig.add_subplot(gs[1])
        self.drawSpecter()

    def drawSpecter(self):
        self.axes1.minorticks_on()
        self.axes1.grid(which='both')
        self.axes1.set_xlim([min(self.specter.wavelength),max(self.specter.wavelength)])
        self.axes1.set_ylim([0,max(self.specter.data[:,0])*1.05])
        self.axes1.plot(self.specter.wavelength,self.specter.data[:,self.currentSpecter])

        for line in self.lines:
            self.axes1.axvline(x=int(line[0]), color='r', linestyle='-')
            self.axes1.axvline(x=int(line[1]), color='r', linestyle='-')

        if len(self.specter.temperature)>0:
            print(self.specter.temperature[self.currentSpecter])
            self.axes2.plot(self.specter.temperature[self.currentSpecter][0]['Ek'],self.specter.temperature[self.currentSpecter][0]['nkgk'],'.')

        self.canvas.draw()

    def loadSpecterFromFiles(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self.main_frame, "Open Directory","D:")
        self.specter=Specter(np.loadtxt(fileName),fileName,self.windowLength)

        if len(self.specter.data[0])>0:
            self.currentSpecter=0

        self.updateSpecterInput()

        self.on_draw()

    def nextSpecter(self):
        if self.currentSpecter<(len(self.specter.data[0])-1):
            self.currentSpecter+=1
            self.updateSpecterInput()
            self.on_draw()

    def prevSpecter(self):
        if self.currentSpecter>0:
            self.currentSpecter-=1
            self.updateSpecterInput()
            self.on_draw()

    def updateSpecterInput(self):
        self.currentSpecterInput.setText(str(self.currentSpecter+1) + ' / ' + str(len(self.specter.data[0])) + ' (' +self.specter.name+ ')')

    def addLine(self):
        #self.lines.append((0,0,0,0,0,0))

        #test case
        self.lines.append((244,265,250,10,3000,2))
        self.lines.append((305,343,325,10,2000,2))
        self.updateTable()
        self.on_draw()

    def setLine(self,item):
        lineNum=item.row()
        self.lines[lineNum]=(
            int(self.table.item(lineNum,0).text()),
            int(self.table.item(lineNum,1).text()),
            float(self.table.item(lineNum,2).text()),
            float(self.table.item(lineNum,3).text()),
            float(self.table.item(lineNum,4).text()),
            float(self.table.item(lineNum,5).text())
        )
        self.on_draw()

    def computeTemp(self):
        for specter in self.specter.data.T:
            self.specter.temperature.append(Tempereture.compute(specter,self.lines))

        #print(self.specter.temperature)
        self.on_draw()


    def updateTable(self):
        self.table.setRowCount(0)
        for line in self.lines:
            currentRowCount = self.table.rowCount()
            self.table.insertRow(currentRowCount)
            for col, value in enumerate(line):
                self.table.setItem(currentRowCount, col, QtGui.QTableWidgetItem(str(value)))

        self.on_draw()

    def saveDataToFile(self, data, fileName):
        np.savetxt(fileName,data, fmt='%10.5f')


def main():
    app = QtGui.QApplication(sys.argv)
    form = AppForm(specterCenter=130, columnNumber=255, windowLength=51)
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()