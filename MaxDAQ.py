# -*- coding: utf-8 -*-
"""
**Author**
Nick Arbanas
DroidForge Engineering

**Revision History **
1.0.0 - 05/10/20 - Initial Release 

**Color Palet**
Green: #00aa00
Orange: #924900
Blue: #0000ff
Cyan: #3BBBE4
Purple: #900090
Red: #800000
"""

#Imports reqired to start the program 
from PyQt5.QtWidgets import QFrame, QTabWidget
from functools import partial
import pyqtgraph as pg
from random import randint

#==============================================================================
# Input Parameters: none
# Output Returns: none
#
# Description: This Class draws a horizontal line when called
#==============================================================================
class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

#==============================================================================
# Input Parameters: none
# Output Returns: none
#
# Description: This Class draws a horizontal line when called
#==============================================================================
class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)

#==============================================================================
# Input Parameters: QTabWidget
# Output Returns: none (PyQt GUI)
#
# Description: This the main function for the PyQt application
#==============================================================================
class tabdemo(QTabWidget):
    def __init__(self, parent = None):
        super(tabdemo, self).__init__(parent)

        CurrentSoftwareVersion = '1.0.0'                        #Update as needed. Don't forget to update the Revision History as well
        
        self.AppName = "Max-DAQ - " + CurrentSoftwareVersion    #Sets the name in the upper left hand corner of the GUI

        self.setWindowIcon(QIcon('MaxLogo1.ico'))   #Sets the GUI Icon

        self.pressureOptions = ['PSI','HPA','KPA','MBAR','BAR','CMH2O','INH2O','MMHG']
        self.oldRate = 0

        self.tab1 = QWidget()                       #Define Tab1
        self.tab2 = QWidget()                       #Define Tab2
        self.tab3 = QWidget()                       #Define Tab3
        self.tab4 = QWidget()                       #Define Tab4
	
        self.addTab(self.tab1,"Acquisition")       #Add Tab 1 to the QTabWidget
        self.addTab(self.tab2,"Plot")              #Add Tab 2 to the QTabWidget
        self.addTab(self.tab3,"Live Data")         #Add Live Data Tab to QTabWidget
        self.addTab(self.tab4,"Settings")          #Add Settings Tab to QTabWidget

        self.tab1UI()                               #Run the Tab 1 setup
        self.tab2UI()
        self.tab3UI()
        self.tab4UI()

        self.DAQ = MaxtecDAQ()                      #Create a MaxtecDAQ object
 
        self.logMsg('Date: ' + datetime.datetime.now().strftime('%m-%d-%y'), False, 'black')    #Write the Start Date to the Log
        self.logMsg('Software: ' + self.AppName, False, 'black')                                #Write the Software Version to the Log
 
        self.SearchCOMs()                       #Search the COM Ports for a Teensy
      
        self.setWindowTitle(self.AppName)
        self.setGeometry(650, 400, 610, 300)    #Sets the X and Y location to start up in and the Width and Height of the GUI (px)
        self.setMinimumHeight(350)                #Locks the height to 300 (px)
        self.setMinimumWidth(610)               #Locks the minimum width to 600 (px)
        
#==============================================================================
# Input Parameters: none
# Output Returns: none 
#
# Description: This function searches the COM Ports and populates the COM Port
# ComboBox with all avaliable Teensy Ports. 
#==============================================================================
    def SearchCOMs(self):
        COM = self.DAQ.findPort()   #Use the MaxtecDAQ 'findPort' method to autodetect the Teensy
        self.COMDis.clear()     #Reset the COM Port ComboBox

        if(len(COM) < 1):           #Teensy not found, list of COM Ports returned
            print('No Teensy Connected')
            self.COMDis.addItem('NA')           #Set the COM Port ComboBox to NA
            self.COMDis.setDisabled(True)       #Disable the COM Port ComboBox
            self.FirmDis.setText('NA')          #Set the Firmware LineEdit to NA
            self.DataOutput.setCurrentIndex(0)  #Set the Output ComboBox to the first index
            self.HardChannels.setText('NA')     #Set the Channels LineEdit to NA
            self.DataRate.setText('0')          #Set the Rate LineEdit to 0
            self.updateMult()                   #Update the Multiplier LineEdit
        else:                       #Teensy Found
            print('Teensy(s) Connected')
            if (len(COM) == 1):     #Only ONE Teensy Connected
                
                self.COMDis.addItem(str(COM[0]))                        #Add the prot to the COM Port ComboBox
                self.COMDis.setDisabled(True)                           #Disable the COM Port ComboBOx
            else:                   #Multiple Teensys Connected
                for i in range (0, len(COM)):                           #Loop Through all found COM Ports
                    self.COMDis.addItem(str(COM[i]))                    #Add all items to the COM Port ComboBox
                self.COMDis.setDisabled(False)                          #Enable the COM Port ComboBox
            #self.updateHardware()                                       #Update all the Hardware Information
            if (self.FirmDis.text() == 'NA'):
                self.DataRate.setText('-')
                self.DataPrefix.setText("")
                self.DataPrefix.setDisabled(True)
                self.removeTab(1)
                self.DataTime.setDisabled(True)
                self.DataMultiplier.setText('NA')
                self.DataTime.setText('NA')
                self.DataOutput.setDisabled(True)
                
                self.FileOutput.setText(str(os.getcwd()) + '\Temp.txt')
            
#==============================================================================
# Input Parameters: none
# Output Returns: none
#
# Description: This function sets all the Hardware information with for the 
# selected COM Port.
#==============================================================================                
                
    def updateHardware(self):
        self.logMsg('Searching for Attached Hardware...<br>', False, 'black')
        #self.FirmDis.setText(self.DAQ.getFirmVer(str(self.COMDis.currentText())))      #Use the MaxtecDAQ 'getFirmVer' method to get the current firmware form the selected Teensy
        FirmStartup = self.DAQ.getSetup(str(self.COMDis.currentText())).split('-')
        
        self.logMsg('DF Board: ' + str(self.COMDis.currentText()), False, 'black')   #Write the Teensy COM Port to the Log
        #self.logMsg('Firmware: ' + self.FirmDis.text(), False, 'black') #Write the Firmware Version to the Log
        
        if(FirmStartup[0] == 'P'):
            self.DataOutput.clear()
            for key in self.pressureOptions:
                self.DataOutput.addItem(str(key))
            index = self.DataOutput.findText(FirmStartup[1], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.DataOutput.setCurrentIndex(index)
            self.logMsg('Hardware Type: Pressure', False, 'black')
            self.DataTime.setText('--') #Disable rate
            
        else: #Other Firmware Detected
            self.HardChannels.setText('NA') #Set the Channesl LineEdit to NA
            self.DataRate.setText('0')      #Set the Rate LineEdit to 0
            self.rateMax = 0
            
        self.HardChannels.setText(FirmStartup[2])
        self.rateMax = float(FirmStartup[3])
        self.logMsg('Max Sample Rate: ' + str(self.rateMax), False, 'black')
        self.DataRate.setText(str(int(FirmStartup[4])))
            
#==============================================================================
# Input Parameters: msg (Str), bold (Bool), color (Str)
# Output Returns: none
#
# Description: This function takes in a mesage and writes it to the Log TextEdit.
# If bold is True, the line is bolded. Color sets the color of the line, set to
# 'black' for default. 
#==============================================================================
    def logMsg(self, msg, bold, color):             
        boldStart = '<b>'                           #Bold Start Character
        boldEnd = '</b>'                            #Bold End Character
        colorStart = '<font color = ' + color + '>' #Color Start Character + color 
        colorEnd = '</font>'                        #Color End Character
        
        if bold:
            msg = boldStart + str(msg) + boldEnd    #Add Bold HTML Characters
        msg = colorStart + str(msg) + colorEnd      #Add Color HTML Characters
        self.Log.moveCursor(QTextCursor.Start)      #Move the cursor to the beginning of the TextEdit
        self.Log.insertHtml(str(datetime.datetime.now().strftime('%H:%M:%S  -  ')) + msg + '<br>') #Add the TimeStamp, Message Text and finally a return
        QApplication.processEvents()    #Update the Log in the GUI

#==============================================================================
# Input Parameters: none
# Output Returns: none (Tab 1 Layout)
#
# Description: This funcition defines the layout for the first Tab and associated
# widgets. 
#==============================================================================
    def tab1UI(self):
        #Define all the different Layouts
        hlayout = QHBoxLayout()     #Main Layer
        h2layout = QHBoxLayout()    
        h4layout = QHBoxLayout()
        h6layout = QHBoxLayout()
        h7layout = QHBoxLayout()
        h8layout = QHBoxLayout()
        h9layout = QHBoxLayout()
        h10layout = QHBoxLayout()
        glayout = QGridLayout()
        glayout2 = QGridLayout()
        vlayout = QVBoxLayout()
        v2layout = QVBoxLayout()
        v3layout = QVBoxLayout()
        
        #Creat a font style to bold the headers
        headerFont = QFont()
        headerFont.setBold(True)
        
        #Run Time Log
        self.Log = QTextEdit()
        self.Log.setReadOnly(True)
        self.Log.setToolTip('Run Time Log')
        self.Log.setMinimumWidth(270)

        #COM Port
        self.COMDis = QComboBox()
        self.COMDis.setMinimumWidth(58)
        self.COMDis.setToolTip('COM Port')
        self.COMDis.currentIndexChanged.connect(self.updateHardware)
        
        #COM Refresh Button
        self.RefreshCOM = QPushButton()
        self.RefreshCOM.setMaximumWidth(22)
        self.RefreshCOM.setMaximumHeight(22)
        self.RefreshCOM.setToolTip('Refresh COM Port List')
        self.RefreshCOM.setIcon(QIcon('refresh.png'))
        self.RefreshCOM.clicked.connect(self.RefreshCOMs)
        
        #Firmware
        self.FirmDis = QLineEdit()
        self.FirmDis.setReadOnly(True)
        self.FirmDis.setDisabled(True)
        self.FirmDis.setMaximumWidth(80)
        self.FirmDis.setToolTip('Firmware on Teensy')
        
        #Channels
        self.HardChannels = QLineEdit()
        self.HardChannels.setMaximumWidth(80)
        self.HardChannels.setReadOnly(True)
        self.HardChannels.setDisabled(True)
        self.HardChannels.setToolTip('Number of channels on the hardware')        
        
        #Start Button
        self.ButtonStart = QPushButton()
        self.ButtonStart.setText('Start')
        self.ButtonStart.setMaximumWidth(315)
        self.ButtonStart.clicked.connect(self.ToggleStartStop)
        self.ButtonStart.setToolTip('Start Recording Data')
        self.Start = False  #Start boolean. (toggles when the Start Button is pressed)
        
        #Add a refresh button to the COM Port List
        h9layout.addWidget(self.COMDis)
        h9layout.addWidget(self.RefreshCOM)
        
        #Hardware Column - Grid Layout
        space = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Expanding)        
        
        glayout.addWidget(QLabel('COM Port'), 1, 3)
        glayout.addLayout(h9layout, 1, 5)
        glayout.addWidget(QLabel('Firmware'), 3, 3)
        glayout.addWidget(self.FirmDis, 3, 5)
        glayout.addWidget(QLabel('Channels'), 5, 3)
        glayout.addWidget(self.HardChannels, 5, 5)
        glayout.addItem(space, 7, 5)
        
        #Prefix
        self.DataPrefix = QLineEdit()
        self.DataPrefix.setText('POS')
        self.DataPrefix.setToolTip('Sets the prefix for the recorded data')
        self.DataPrefix.setMaximumWidth(80)
        
        self.OutputOptions = {'Voltage':'0.0078125', 'Resistance':'0.0468749', 'Temp 700':'0.0468749', 'Temp 800':'0.0468749', 'Raw':'1', 'Custom':''}        
        
        #Output
        self.DataOutput = QComboBox()
        self.DataOutput.setMaximumWidth(80)
        for key in self.OutputOptions:
            self.DataOutput.addItem(str(key))
        self.DataOutput.model().sort(0)
        self.DataOutput.setToolTip('Sets the Multiplier for the incomming data')
        #self.DataOutput.currentIndexChanged.connect(self.updateMult)        
        
        #Multiplier
        self.DataMultiplier = QLineEdit()
        self.DataMultiplier.setMaximumWidth(80)
        self.DataMultiplier.setToolTip('Sets a multiplier to conver the AD reading into Volts or Ohms')
        self.DataMultiplier.textChanged.connect(self.OnlyAllowInt)
        self.DataMultiplier.setDisabled(True)
        
        #Test Time
        self.DataTime = QLineEdit()
        self.DataTime.setMaximumWidth(55)
        self.DataTime.setText('--')
        self.DataTime.setToolTip('Length of recording (seconds)')
        self.DataTime.textChanged.connect(self.OnlyAllowInt2)
        
        #Rate
        self.DataRate = QLineEdit()
        self.DataRate.setMaximumWidth(55)
        self.DataRate.setToolTip('Sets the rate of the firmware in Samples/Second')
        self.DataRate.setText('5')
        self.DataRate.textChanged.connect(self.SetRate)
        
        #Add a label to the Test Time Grid Point
        h7layout.addWidget(self.DataTime)
        h7layout.addWidget(QLabel('Sec'))    
        
        #Add a label to the Rate Grid Point
        h8layout.addWidget(self.DataRate)
        h8layout.addWidget(QLabel('Hz'))
        
        h10layout.addStretch(1)
#        h10layout.addWidget(self.SetRateButton)
        
        #Customize Data - Grid Layout
        glayout2.addWidget(QLabel('Prefix'), 1, 3)
        glayout2.addWidget(self.DataPrefix , 1, 5)
        glayout2.addWidget(QLabel('Output'), 3, 3)
        glayout2.addWidget(self.DataOutput, 3, 5)
        glayout2.addWidget(QLabel('Multiplier'), 5, 3)
        glayout2.addWidget(self.DataMultiplier , 5, 5)
        glayout2.addWidget(QLabel('Test Time'), 7, 3)
        glayout2.addLayout(h7layout, 7, 5)
        glayout2.addWidget(QLabel('Rate'), 9, 3)
        glayout2.addLayout(h8layout, 9, 5)
        glayout2.addLayout(h10layout, 11, 3, 1, 3)        
        
        CustomizeDataFrame = QGroupBox()
        CustomizeDataFrame.setTitle('Customize Data')
        CustomizeDataFrame.setLayout(glayout2)
        
        #Left Column
        v2layout.addLayout(h4layout)
        v2layout.addWidget(CustomizeDataFrame)

        HardwareFrame = QGroupBox()
        HardwareFrame.setTitle('Hardware')
        HardwareFrame.setLayout(glayout)

        #Right Column
        v3layout.addWidget(HardwareFrame)
        
        self.FileOutput = QLineEdit()
        self.FileOutput.setMaximumWidth(315)
        self.FileOutput.setMaximumHeight(22)
        self.FileOutput.setToolTip('File path to output file')
        self.FileOutput.setReadOnly(True)
        fileUnique = 1
        while(os.path.exists("Temp-" + str(fileUnique) + '.xlsx')):
            fileUnique += 1;
        self.fileUniqueStr = str(os.getcwd()) + '\Temp-' + str(fileUnique) + '.xlsx'
        self.FileOutput.setText(self.fileUniqueStr)
        
        self.SaveAs = QPushButton()
        self.SaveAs.setText('Save As')
        self.SaveAs.setMaximumWidth(50)
        self.SaveAs.setToolTip('Chose where to automatically save recorded data')
        self.SaveAs.clicked.connect(partial(self.SaveExcelAs, self.fileUniqueStr))
        
        #Left Side of the screen
        h2layout.addLayout(v2layout)
        h2layout.addLayout(v3layout)
        h2layout.addStretch(1)        
        
        #File Options Widgets
        h6layout.addWidget(QLabel('Output:'))
        h6layout.addWidget(self.FileOutput)    
        h6layout.addWidget(self.SaveAs)
        
        FileOptionsFrame = QGroupBox()
        FileOptionsFrame.setTitle('File Options')
        FileOptionsFrame.setLayout(h6layout)
        FileOptionsFrame.setMaximumWidth(315)
        #Left Size Vertical Layout
        vlayout.addWidget(QHLine())
        vlayout.addLayout(h2layout)
        vlayout.addWidget(FileOptionsFrame)
        vlayout.addStretch(1)
        vlayout.addWidget(self.ButtonStart)        
        
        #Main Layout
        hlayout.addLayout(vlayout)
        hlayout.addWidget(self.Log)     
        
        #Set the Tab Layout
        self.tab1.setLayout(hlayout)

    def update_plot_data(self):
        if(len(self.x) == 0):
            self.x = [0]
            self.xAll = []
            self.y = []
            self.yAll = []
        elif(len(self.x) < self.plotFixedWidth.value()):
            self.x.append(self.x[-1] + 1)
        else:
            self.x = self.x[1:]
            self.x.append(self.x[-1] + 1)
            self.y = self.y[1:]
        
        self.xAll.append(self.x[-1])
        
        self.y.append(self.DAQ.Read(str(self.COMDis.currentText())))
        self.yAll.append(self.y[-1])
    
        if(self.plotWidth.currentIndex() != 0):
            self.xLive = self.xAll[-(self.plotFixedWidth.value()):]
            self.yLive = self.yAll[-(self.plotFixedWidth.value()):]
        else:
            self.xLive, self.yLive = self.downsample(0, len(self.xAll))
    
        self.data_line.setData(self.xLive, self.yLive)

    def tab3UI(self):
        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()
        
        self.plot = pg.PlotWidget()
        self.plot.setBackground('w')
        self.plot.setTitle("Live Data Plot")
        self.plot.showGrid(x=True, y=True)
        
        self.pen = pg.mkPen(color=(59,187,228), width=2)
        self.penGray = pg.mkPen(color=(180,180,180), width=2)
        
        self.x = []#list(range(100))
        self.y = []#[randint(0,100) for _ in range(100)]
        self.xAll = self.x
        self.yAll = self.y
        
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)
        #self.timer.start()
        
        self.plotWidth = QComboBox()
        self.plotWidth.setMaximumWidth(80)
        self.plotWidth.addItem('All')
        self.plotWidth.addItem('Fixed Width')
        self.plotWidth.setToolTip('Sets the x window for streaming data')
        self.plotWidth.currentIndexChanged.connect(self.plotUpdateData)   
        
        self.plotFixedWidth = QSpinBox()
        self.plotFixedWidth.hide()
        self.plotFixedWidth.setMinimum(10)
        self.plotFixedWidth.setMaximum(100000)
        self.plotFixedWidth.setValue(100)
        self.plotFixedWidth.valueChanged.connect(self.plotUpdateData)
        
        self.plotStop = QPushButton()
        self.plotStop.setText('Stop')
        self.plotStop.setToolTip('Stops the data Stream')
        self.plotStop.clicked.connect(self.ToggleStartStop)
        
        vlayout.addWidget(self.plotWidth)
        vlayout.addWidget(self.plotFixedWidth)
        vlayout.addStretch(1)
        vlayout.addWidget(self.plotStop)
        
        hlayout.addLayout(vlayout)
        hlayout.addWidget(self.plot)
        
        self.tab3.setLayout(hlayout)

    def tab4UI(self):
        hlayout = QHBoxLayout()
        self.tab4.setLayout(hlayout)

#==============================================================================
# Input Parameters: none
# Output Returns: none (Tab 2 Layout)
#
# Description: This funcition defines the layout for the second Tab and associated
# widgets. 
#==============================================================================
    def tab2UI(self):
        #Define all the different Layouts
        vlayout = QVBoxLayout() #Main Layout
        v2layout = QVBoxLayout()
        hlayout = QHBoxLayout()
        h2layout = QHBoxLayout()
        glayout = QGridLayout()
        h3layout = QHBoxLayout()
        
        #Creat a font style to bold the headers
        headerFont = QFont()
        headerFont.setBold(True)        
        
        #Loaded File Location
        self.pFileName = QLineEdit()
        self.pFileName.setMaximumHeight(22)
        self.pFileName.setReadOnly(True)
        self.pFileName.setToolTip('Location of data to plot')
        
        #Import Button
        self.pImport = QPushButton()
        self.pImport.setMaximumWidth(80)
        self.pImport.setText('Import')
        self.pImport.setToolTip('Import Data to plot')
        self.pImport.clicked.connect(self.OpenExcel)
        
        #Plot Button
        self.pPlot = QPushButton()
        self.pPlot.setMaximumWidth(80)
        self.pPlot.setText('Plot')
        self.pPlot.setToolTip('Plot the data')
        self.pPlot.setDisabled(True)
        self.pPlot.clicked.connect(self.PlotData)
        
        #Individual Radio Button
        self.pAllLines = QRadioButton('Individual')
        self.pAllLines.setChecked(True)
        self.pAllLines.setToolTip('Gives each line a unique color')
        
        #By Cup Radio Button
        self.pCupLines = QRadioButton('By Cup')
        self.pCupLines.setToolTip('Highlights the data by cup')
        
        #Hightlighting Header
        highlight = QLabel('Highlighting')
        highlight.setFont(headerFont)        
        
        #Highlighting Data
        glayout.addWidget(self.pAllLines, 1, 3)
        glayout.addWidget(self.pCupLines, 1, 5)        
        
        HighlightingFrame = QGroupBox()
        HighlightingFrame.setTitle('Highlighting')
        HighlightingFrame.setLayout(glayout)        
        
        #Left Column
        v2layout.addWidget(HighlightingFrame)
        v2layout.addStretch(1)        
        
        #Main Horizontal Layout for Columns
        h3layout.addLayout(v2layout)
        h3layout.addStretch(1)
        
        #Import Layout
        hlayout.addWidget(QLabel('Import:'))
        hlayout.addWidget(self.pFileName)
        hlayout.addWidget(self.pImport)        
        
        #Plot button
        h2layout.addStretch(1)
        h2layout.addWidget(self.pPlot)        
        
        #Main Layout
        vlayout.addWidget(QHLine())
        vlayout.addLayout(hlayout)
        vlayout.addLayout(h3layout)
        vlayout.addStretch(1)
        vlayout.addLayout(h2layout)
        
        #Set the Layout for Tab2
        self.tab2.setLayout(vlayout)

#==============================================================================
# Input Parameters: none
# Output Returns: none
#
# Description: This function updates the DataMultiplier LineEdit based on the 
# selected DataOutput ComboBox
#==============================================================================
    def updateMult(self):
        self.DataMultiplier.setText(self.OutputOptions[str(self.DataOutput.currentText())])
        key = self.DataOutput.currentText()
        self.DataMultiplier.setDisabled(True)
        if(key == 'Temp 700'):
            self.DataMultiplier.setToolTip('A custom equation is required to convert to temperature<br><b>700 Ohm Thermistors</b>')
        elif(key == 'Temp 800'):
            self.DataMultiplier.setToolTip('A custom equation is required to convert to temperature<br><b>800 Ohm Thermistors</b>')            
        elif(key == 'Custom'):
            self.DataMultiplier.setToolTip('Enter in a Custom Multiplier to convert the A to D signal')
            self.DataMultiplier.setDisabled(False)
        else:
            self.DataMultiplier.setToolTip('Multiplier to convert the A to D signal')

#==============================================================================
# Input Parameters: none
# Output Returns: none (HTML Plot of Selected Data)
#
# Description: This function imports XLSX information, takes a couple user inputs
# and then plots the file to an HTML file using Bokeh.
#==============================================================================
    def PlotData(self):
        print ('Plotting Data')
        
        numlines = len(self.dfData.columns) #Number of Columns
            
        if(self.pAllLines.isChecked()):     #Individual Radio Button Selected
            #Palet containing 64 unique colors
            mypalette = ['black','dimgray','lightgrey','rosybrown','brown','maroon','red','salmon','sienna','chocolate','saddlebrown','sandybrown','orange','darkgoldenrod','gold','olivedrab','yellowgreen','darkolivegreen','chartreuse','darkseagreen','limegreen','darkgreen','green','lime','springgreen','mediumspringgreen','mediumaquamarine','aquamarine','turquoise','mediumturquoise','lightseagreen','darkcyan','aqua','cadetblue','deepskyblue','skyblue','lightskyblue','steelblue','royalblue','midnightblue','blue','navy','slateblue','mediumslateblue','darkorchid','mediumpurple','darkviolet','indigo','darkviolet','darkorchid','purple','darkmagenta','orchid','magenta','deeppink','crimson','pink','mediumvioletred','palevioletred','darkorange','peru','tan','coral','dodgerblue']        
            
            #Legend separating the data by the 'Line' on the MUX
            #Note: Using a unique legend for each column makes the legend too big 
            legends = ['Line 1','Line 2','Line 3','Line 4','Line 5','Line 6','Line 7','Line 8'] * 8
            
        elif(self.pCupLines.isChecked()):   #By Cup Radio Button Selected
            Palette1 = ['firebrick'] * 16   #Set Cup 1 to a single color
            Palette2 = ['seagreen'] * 16    #Set Cup 2 to a single color
            Palette3 = ['navy'] * 16        #Set Cup 3 to a single color
            Palette4 = ['darkmagenta'] * 16 #Set Cup 4 to a single color
            
            mypalette = Palette1 + Palette2 + Palette3 + Palette4 #Creat a Master List of Colors 
            
            #Give each Cup a legend
            legends = ['Cup1'] * 16 + ['Cup2'] * 16 + ['Cup3'] * 16 + ['Cup4'] * 16
            
        #Bokeh Plot Object
        p = figure(toolbar_location = 'above', plot_width = 1650, plot_height = 800, tools = ['box_zoom', 'pan', 'wheel_zoom', 'reset', 'save'])
        
        xs=[self.dfData.index.values]*numlines                  #List of a List of X Index values
        ys = [self.dfData[name].values for name in self.dfData] #List of a List of Y Values
        
        #Loop through all the data and add a line plot for each Channel
        for (colr, leg, x, y) in zip(mypalette, legends, xs, ys):
            p.line(x, y, color = colr, legend = leg)    #Bokeh Line with given color and legend
        
        p.legend.click_policy = 'hide'  #Allows the legend to be clicked to hide/show data
        
        show(p)#Show the resulting Plot

        print ('Data Plotted!')

#==============================================================================
# Input Parameters: none
# Output Returns: none
#
# Description: This function is connected to a 'textChanged' event from the rate
# and will auto update the firmware rate
#==============================================================================
    def SetRate(self):
        rate = self.DataRate.text()        
        
        if float(rate) > self.rateMax: 
            rate = str(self.rateMax)
            self.DataRate.setText(rate)
            self.logMsg('Warning! - Maximum rate is ' + rate + 'Hz', True, 'orange')

        newRate = int(1000 / float(self.DataRate.text()))

        if(newRate != self.oldRate):
            self.timer.setInterval(newRate)
            self.logMsg('<b>Sample Time: ' + str(newRate) + 'ms</b>', False, 'blue')
            self.oldRate = newRate

#==============================================================================
# Input Parameters: Argument (string) *Automatically passed in I guess
# Output Returns: self.DataMultiplier.setText (string)
#
# Description: This function is connected to a 'textChanged' event from either
# a QTextEdit or QLineEdit object. Whenever a text value is inputed in the text
# field by the user, this function will look at the typed character and remove
# it from the resulting string if that character is not an integer, (0-9) a 
# period (.) or a minus (-) symbol.
#==============================================================================
    def OnlyAllowInt(self, arg):
        #Setup a list of valid characters
        valid = ['-','.','0','1','2','3','4','5','6','7','8','9']

        #Loop through the inputed argument
        for c in range(0, len(arg)):
            #Look at the specific character of the string and check to see if it is valid
            if arg[c] not in valid:
                #If there is an invalid character, replace the character with an empty string ('')
                if len(arg)>0: arg=arg.replace(arg[c],'')
        
        #Set the text in DataMultiplier to the 'cleaned' argument
        self.DataMultiplier.blockSignals(True)
        self.DataMultiplier.setText(arg)
        self.DataMultiplier.blockSignals(False)

#==============================================================================
# Input Parameters: Argument (string) *Automatically passed in I guess
# Output Returns: self.DataTime.setText (string)
#
# Description: This function is connected to a 'textChanged' event from either
# a QTextEdit or QLineEdit object. Whenever a text value is inputed in the text
# field by the user, this function will look at the typed character and remove
# it from the resulting string if that character is not an integer, (0-9).
#==============================================================================
    def OnlyAllowInt2(self, arg):
        #Setup a list of valid characters
        valid = ['0','1','2','3','4','5','6','7','8','9']

        #Loop through the inputed argument
        for c in range(0, len(arg)):
            #Look at the specific character of the string and check to see if it is valid
            if arg[c] not in valid:
                #If there is an invalid character, replace the character with an empty string ('')
                if len(arg)>0: arg=arg.replace(arg[c],'')
        
        #Set the text in DataTime to the 'cleaned' argument
        self.DataTime.blockSignals(True)
        self.DataTime.setText(arg)
        self.DataTime.blockSignals(False)

#==============================================================================
# Input Parameters: none
# Output Returns: none
#
# Description: This function opens the window file dialog to save a file
#==============================================================================
    def SaveExcelAs(self, fnameIn):
        if (os.path.exists(fnameIn)): #file already exists
            x = fnameIn.split('-')
            y = len(x)
            m = 1
            
            fnameIn = x[0]
            
            if (y > 2):
                i = 2
                while (y > i):
                    fnameIn = fnameIn + '-' + x[i-1]
                    i += 1
                    
            if (len(x[y-1]) > 0):
                z = x[y-1].split('.xlsx')
                if (len(z[0]) > 0):
                    m = int(z[0]) + 1
                          
            fnameIn = fnameIn + '-' + str(m) + '.xlsx'
            
        fname = QFileDialog.getSaveFileName(self, 'Save file', fnameIn, "Excel files (*.xlsx)")
        if fname != '':
            #print('Save File As: ' + str(fname))
            self.FileOutput.setText(fname[0])
            self.fileUniqueStr = fname[0]


#==============================================================================
# Input Parameters: none
# Output Returns: none
#
# Description: This function opens the window file dialog to open a file and then
# Reads the Sheet1 of the file into a pandas Data Frame
#==============================================================================
    def OpenExcel(self):
        fname = QFileDialog.getOpenFileName(self, 'Save file', 'c:\\',"Excel files (*.xlsx)")
        if fname != '':
            self.pFileName.setText(fname)  
        print ('Opening File')
        try:
            self.dfData = pd.read_excel(open(fname, 'rb'), sheet_name = 'Sheet1')
            print ('Data Extracted from File!')
            numlines = len(self.dfData.columns) #Number of Columns
            if(numlines != 64):
                self.pPlot.setDisabled(True)
                print (')ERROR - Plotter can only plot data with 64 Columns!')
            else:
                self.pPlot.setDisabled(False)
        except:
            print ('ERROR - Could not Extract data from file!')
            print ('Ensure desired data is on sheet 1 of the file')
            self.dfData = None 
            self.pPlot.setDisabled(True)
#==============================================================================
# Input Parameters: none
# Output Returns: none
#
# Description: This function Refreshes the COM Port List
#==============================================================================
    def RefreshCOMs(self):
        self.logMsg('Refresh COM Ports<br>', False, 'black')
        self.SearchCOMs()
        
    def plotUpdateData(self):
        if(self.plotWidth.currentIndex() != 0):
            self.plotFixedWidth.show()
            self.x = self.xAll[(len(self.xAll) - self.plotFixedWidth.value()):]
            self.y = self.yAll[(len(self.yAll) - self.plotFixedWidth.value()):]
        else:
            self.plotFixedWidth.hide()
    
    def downsample(self, xstart, xend):
        max_points = self.plotFixedWidth.value()
        origXData = np.asarray(self.xAll)
        origYData = np.asarray(self.yAll)
        mask = (origXData > xstart) & (origXData < xend)
        mask = np.convolve([1,1], mask, mode='same').astype(bool)
        ratio = max(np.sum(mask) // max_points, 1)
        
        xdata = origXData[mask]
        ydata = origYData[mask]
        
        xdata = xdata[::ratio]
        ydata = ydata[::ratio]
        
        return xdata, ydata
        
#==============================================================================
# Input Parameters: none
# Output Returns: none
#
# Description: This function Starts and Stops the Data Acqusition. This function
# will either stop after all the Samples have been taken or when the user presses
# the 'Stop' button.
#==============================================================================
    def ToggleStartStop(self):
        self.Start = not(self.Start)
        if(not(self.Start)):
            print ('Abort Test')
            self.timer.stop()
            self.DAQ.Abort = True
            self.DAQ.CloseCOM(str(self.COMDis.currentText()))
            
            self.plot.clear()
            self.data_line = self.plot.plot(self.xLive, self.yLive, pen=self.penGray)
            self.setCurrentIndex(0)
            
            #Reset the start button
            self.ButtonStart.setText('Start')
            self.ButtonStart.setToolTip('Start Recording Data')
            
        else:
            print ('Starting Test')
            self.ButtonStart.setText('Stop')
            self.ButtonStart.setToolTip('Stop Recording Data')
            
            self.setCurrentIndex(2)
            
            self.plot.clear()
            self.x=[]
            self.y=[]
            self.data_line = self.plot.plot(self.x, self.y, pen=self.pen)
            
            self.timer.start()
            COMPort = str(self.COMDis.currentText())
            print (COMPort)
            # if(COMPort != 'NA'):            
            #     if(self.FirmDis.text() != 'NA'):
            #         self.logMsg('--DAQ Settings--<br><br>', True, '#900090')
            #         self.logMsg('Hardware Detected: ' + COMPort, False, 'black')
                    
            #         #Set the ADC Multiplier
            #         self.DAQ.SetTemp('NA') #Set the Temp variable in the MaxtecDAQ Class to NA
            #         if(self.DataMultiplier.text() == ''):   #Make sure there is a multiplier value
            #             self.DataMultiplier.setText('1')    #Default to 1
                        
            #         if(self.DataOutput.currentText() == 'Temp 700'):  #Check if the output is a Temperature
            #             self.DAQ.SetTemp('Temp700') #Set the Temp variable in the MaxtecDAQ Class to convert the final results 
                        
            #         elif(self.DataOutput.currentText() == 'Temp 800'):  #Check if the output is a Temperature
            #             self.DAQ.SetTemp('Temp800') #Set the Temp variable in the MaxtecDAQ Class to convert the final results                     
    
            #         self.DAQ.ADCMult = float(self.DataMultiplier.text())
            #         print ('ADCMult set to: ' + str(self.DataMultiplier.text()))
            #         self.logMsg('Multiplier: ' + str(self.DAQ.ADCMult), False, 'black')
                    
            #         #Set the Recording Time
            #         Time = self.DataTime.text()
            #         self.logMsg('Record Time: ' + Time + ' Sec', False, 'black')
                    
            #         #Set the Sample Rate
            #         SampRate = float(self.DataRate.text())
            #         self.logMsg('Sample Rate: ' + str(SampRate) + ' Samp/Sec', False, 'black')         
                    
            #         #Set the number of Samples
            #         SampNum = int(int(Time) * SampRate)
            #         self.logMsg('Number of Samples: ' + str(SampNum) + ' Samp', False, 'black')
                    
            #         Prefix = self.DataPrefix.text()
            #         self.logMsg('Header Names: ' + Prefix + 'xx', False, 'black')
            #         self.logMsg('Channels: ' + str(self.HardChannels.text()), False, 'black')
                    
            #         #Get Firmware Version
            #         FirmVer = self.DAQ.getFirmVer(COMPort)
            #         if(FirmVer != 'NA'):
            #             self.logMsg('Firmware: ' + str(FirmVer), False, 'black')
            #             self.FirmDis.setText(FirmVer)
            #         else:
            #             self.logMsg('ERROR! - Could not get Firmware from Teensy', True, 'red')
            #             self.FirmDis.setText('NA')
            #         List = []
            #         for i in range(0, int(self.HardChannels.text())):
            #             if(i < 9):
            #                 List.append(str(Prefix + '0' + str(i + 1)))
            #             else:
            #                 List.append(str(Prefix + str(i + 1)))
            #         print (List)          

            #         #Start Recording Data
            #         self.logMsg('Data Recording Started...', True, '#0000ff')                
            #         self.DAQ.ReadStart(List, SampNum, COMPort, SampRate)
            #         self.logMsg('...Data Recording Stopped', True, '#0000ff')
            #         self.logMsg('Saving Data...', True, '#00aa00')                
            #         if(self.DAQ.SaveData(self.fileUniqueStr)):
            #             self.logMsg(self.FileOutput.text(), False, 'black')
            #             self.logMsg('...Data Saved!', True, '#00aa00')
            #         else:
            #             self.logMsg('...Data Could Not be Saved', True, 'red')
            #             self.logMsg('Check Recovery Files', True, 'red')

            #     else:
            #         self.DAQ.ReadStreamStart(COMPort)                      
            #         with open(self.FileOutput.text(), "w") as text_files:
            #             text_files.write(self.Log.toPlainText())
            #         self.logMsg('Data Saved', True, '#00aa00')
            #     #Reset the start latch
            #     self.Start = not(self.Start)
                
            #     #Reset the start button
            #     self.ButtonStart.setText('Start')
            #     self.ButtonStart.setToolTip('Start Recording Data')

            # else: # COM Port not found
            #     self.logMsg('ERROR! - Teensy COM Port NOT Found', True, 'red')
                
#==============================================================================
# Input Parameters: none
# Output Returns: none
#
# Description: This is the Main code that loads all the modules, controlls the 
# splash screen and starts the GUI.
#==============================================================================
if __name__ == '__main__':
    from PyQt5.QtWidgets import QSplashScreen, QApplication
    from PyQt5.QtGui import QPixmap
    from PyQt5 import QtCore
    from sys import argv
    
    app = 0
    app = QApplication(argv)
    
    offset = '          '

    # Create and display the splash screen
    splash_pix = QPixmap('MaxLogo4.png')

    splash = QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())

    #Message on splash screen
    splash.showMessage(offset + "Loading Modules:\n\n", QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)

    #Show the splash screen
    splash.show()
    app.processEvents()
	
    #Import modules
    splash.showMessage(offset + "Loading Modules: sys\n\n", QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
    import sys
    splash.showMessage(offset + "Loading Modules: pandas\n\n", QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
    import pandas as pd
    splash.showMessage(offset + "Loading Modules: datetime\n\n", QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
    import datetime
    splash.showMessage(offset + "Loading Modules: pyqt5.widgets\n\n", QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
    from PyQt5.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel, QVBoxLayout, QPushButton, QTextEdit, QGridLayout, QFileDialog, QApplication, QComboBox, QRadioButton, QGroupBox, QSizePolicy, QSpacerItem, QSpinBox
    from PyQt5.QtGui import QIcon, QTextCursor, QFont
    splash.showMessage(offset + "Loading Modules: bokeh.plotting\n\n", QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
    from bokeh.plotting import figure, show
    splash.showMessage(offset + "Loading Modules: os\n\n", QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
    import os
    splash.showMessage(offset + "Loading Modules: numpy\n\n", QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
    import numpy as np
    splash.showMessage(offset + "Loading Modules: scipy\n\n", QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
    import scipy

    from MaxtecDAQ import MaxtecDAQ
    #Start the GUI, (tabdemo)
    form = tabdemo()
    form.show()
    #Close the splash screen
    splash.finish(form)
    #Need this for some reason
    sys.exit(app.exec_())