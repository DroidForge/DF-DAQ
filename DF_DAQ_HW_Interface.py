# -*- coding: utf-8 -*-
"""
Created on Tue May 02 10:17:41 2017

@author: Nick Arbanas
"""
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import serial
import serial.tools.list_ports as PortList

import traceback, sys

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.
    
    Supported signals are:
        
    finished
        No data
    
    error
        `tuple` (exctype, value, traceback.format_exc() )
    
    result
        `object` data returned from processing, anything
    
    serialData
        `string` data returned from the serial port
        
    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    serialData = pyqtSignal(str)

class Worker(QRunnable):
    '''
    Worker Thread
    
    Inherits from QRunnable to handle worker thread setup, signals, and wrap-up
    
    :param callback: The function callback to run on this worker thread. Supplied
                     args and kwargs will be passed through to the runner
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    '''
    
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        
        #store constructor arguments
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
        # add callback to kwargs (pass serial data back to gui)
        self.kwargs['serialData_callback'] = self.signals.serialData
        
    @pyqtSlot()
    def run(self):
        '''
        Initialize the runner function with passed args, kwargs.
        '''
        
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class DF_DAQ():
    def __init__(self):
        print ('Class Initialized')
        self.ADCMult = 0.0078125
        self.Port = []
        self.Abort = False
        self._comOpen = False
        self._reading = 0

    def findPort(self):
        print ('Finding Port')
        ports = list(PortList.comports()) #Get all COM Ports
        self.Port = [] #Clear the list of Teensy COM Ports

        for port in ports: #Loop through all the ports
            print ("Port HWID: " + str(port.hwid))
            if '239A:8022' in str(port.hwid): #Detect the Teensy Vid:Pid
                self.Port.append(str(port[0])) #Add COM Port to the list of Teensy Ports
                print ('Port Found! ' + str(self.Port)) #Confirmation
        return self.Port #Return the list of Teensy COM Ports
    
    def _SendCommand(self, Command, ser, data):
        CommandList = {"Start"      :"s\n",
                       "Stop"       :"p\n",
                       "Info"       :"i\n",
                       "Version"    :"v\n",#Firmware Version
                       "Type"       :"t\n", #device type
                       "Units"      :"u" + data + "\n",
                       "DataRate"   :"o" + data + "\n",    #[Command Type][Sample Period][]
                       "Setup"      :"x\n",#Setup Info
                       "Read"       :"r\n",#Read Sensor
                       "Zero"       :"z\n" #Zero Sensor Reading
                       }
        #print ('Command: ' + CommandList[Command])
        ser.write(CommandList[Command].encode('latin_1'))
        #print ('Command Written') 
            
    def getSetup(self, COM):
        print ('Opening COM: ' + str(COM))
        ser = serial.Serial()
        ser.baudrate = 250000
        ser.port = COM
        ser.timeout = 1
        
        try:
            print ('Opening Serial')
            ser.open()
            print ('Sending Setup Command')
            self._SendCommand('Setup', ser, "")
            print ('Command Sent')
            s = ser.readline().decode()
            if(len(s) == 0): #Teensy did not respond to version command. 
                s = 'NA'
            print ('Returned: ' + str(s))
            ser.close()
            print ('Serial on Port: ' + COM + ' Closed')
            return str(s)
            
        except serial.SerialException:
            print (COM + ' Not Properly Closed')
            print ("Terminating 'getSetup'")
            try:
                ser.close()
                print ('Serial on Port: ' + COM + ' Closed')
    
            except serial.SerialException:
                print ("Error, Serial Port Already Closed")
            return 'NA'
        
    def zero(self):
        if(self._reading):
            print('Zeroing the sensor')
            self._SendCommand('Zero', self._ser, '')
            return 1
        else:
            print('DAQ must be reading to zero the sensor')
            return 0
    
    def setSamplingPeriod(self, samplingPeriod, COM):
        print ('Opening COM: ' + str(COM))
        ser = serial.Serial()
        ser.baudrate = 250000
        ser.port = COM
        ser.timeout = 1
        
        try:
            print ('Opening Serial')
            ser.open()
            print('sending new sample period')
            self._SendCommand('DataRate', ser, str(samplingPeriod))
            print('command sent')
            s = ser.readline().decode()
            if(len(s) == 0):
                s = 'NA'
            print('Returned: '+str(s))
            ser.close()
            print('Serial on Port: ' + COM + 'Closed')
            return str(s)
        except serial.SerialException:
            print (COM + ' Not Properly Closed')
            print ("Terminating 'getSetup'")
            try:
                ser.close()
                print ('Serial on Port: ' + COM + ' Closed')
    
            except serial.SerialException:
                print ("Error, Serial Port Already Closed")
            return 'NA'
            
        if(self._reading):
            print('Cannot change sample rate while logging')
            return False
        else:
            
            return True
        
    def getFirmVer(self, COM):
        print ('Opening COM: ' + str(COM))
        ser = serial.Serial()
        ser.baudrate = 250000
        ser.port = COM
        ser.timeout = 1
        
        try:
            print ('Opening Serial')
            ser.open()
            print ('Sending Version Command')
            self._SendCommand('Version', ser, "")
            print ('Command Sent')
            s = ser.readline().decode()
            print ('Returned: ' + str(s))
            ser.close()
            print ('Serial on Port: ' + COM + ' Closed')
            return str(s)
            
        except serial.SerialException:
            print (COM + ' Not Properly Closed')
            print ("Terminating 'getFirmVer'")
            try:
                ser.close()
                print ('Serial on Port: ' + COM + ' Closed')
    
            except serial.SerialException:
                print ("Error, Serial Port Already Closed")
            return 'NA'    

    def readDataUntilStop(self, COM, serialData_callback):
        self.Abort = False
        self._ser = serial.Serial()
        self._ser.baudrate = 250000
        self._ser.port = COM
        self._ser.timeout = 1
        
        self._reading = 1
        
        try:
            self._ser.open()
            print ('Serial Opened on Port for Reading: ' + COM)
            self._comOpen = True
        except serial.SerialException:
            print (COM + ' Not Properly Closed, Restarting the COM Port')
            self._ser.close()
            self._ser.open()
            self._comOpen = True
        
        self._SendCommand("Start", self._ser, '')
        print('sent start command')
        
        while(self._reading == 1):
            if(self.Abort):
                self._SendCommand("Stop", self._ser, '')
                print('sent stop command')
                self._reading = 0
            data = self._ser.readline().decode()
            serialData_callback.emit(data)

    def Read(self, Com):
        if(not(self._comOpen)):
            self._ser = serial.Serial()
            self._ser.baudrate = 250000
            self._ser.port = Com
            self._ser.timeout = 1
            
            self._reading = 1
            
            try:
                self._ser.open()
                print ('Serial Opened on Port for Reading: ' + Com)
                self._comOpen = True
            except serial.SerialException:
                print (Com + ' Not Properly Closed, Restarting the COM Port')
                self._ser.close()
                self._ser.open()
                self._comOpen = True
        
        self._SendCommand('Read', self.__ser, "")
        try:
            s = self._ser.readline().decode()
            #print('Returned: ' + str(s))
        except:
            print('ERROR - Nothing Returned')
            s = '0.0'
        
        return float(s)
    
    def CloseCOM(self):
        self._ser.close()
        self._comOpen = False
        
        self.reading = 0