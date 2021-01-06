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

import pandas as pd

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
    serialBLE = pyqtSignal(object)

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
        self.kwargs['serialBLE_callback'] = self.signals.serialBLE
        
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
        self.COM = -1
        self.packetSize = 182 #size of the packet information sent from the BLE device
        self.lastCount = -1

    def findPort(self):
        print ('Finding Port')
        ports = list(PortList.comports()) #Get all COM Ports
        self.Port = [] #Clear the list of Teensy COM Ports

        for port in ports: #Loop through all the ports
            print ("Port HWID: " + str(port.hwid))
            if '239A:8022' in str(port.hwid): #Detect the Teensy Vid:Pid
                self.Port.append(str(port[0])) #Add COM Port to the list of found Ports
                print ('Teensy Port Found! ' + str(self.Port[-1])) #Confirmation
            elif '1A86:7523' in str(port.hwid): #Detect the Artiums Nano Vid:Pid
                self.Port.append(str(port[0])) #Add COM Port to the list of found Ports
                print ('Artimus Port Found! ' + str(self.Port[-1])) #Confirmation
        return self.Port #Return the list of Teensy COM Ports
    
    def _SendCommand(self, Command, data):
        #if(ser.in_waiting > 0):
        #self.ser.readline().decode('ascii','ignore') #clear serial buffer
        CommandList = {"Start"      :"s\n",
                       "Stop"       :"p\n",
                       "Info"       :"i\n",
                       "Version"    :"v\n",#Firmware Version
                       "Type"       :"t\n", #device type
                       "Units"      :"u" + data + "\n",
                       "DataRate"   :"o" + data + "\n",    #[Command Type][Sample Period][]
                       "Setup"      :"x\n",#Setup Info
                       "Read"       :"r\n",#Read Sensor
                       "Zero"       :"z\n",#Zero Sensor Reading
                       "Scan"       :"n2000\n",#Scan for BLE Devices
                       "Connect"    :"c" + data + "\n",#Connect to BLE
                       "List"       :"l\n",#List the BLE characteristic data 
                       "ConnectChar":"C" + data + "\n" #Connect to BLE characteristic 
                       }
        #print ('Command: ' + CommandList[Command])
        self.ser.write(CommandList[Command].encode('latin_1'))
        #print ('Command Written') 
        
    def getSetup(self):
        self.ser.timeout = 1
        
        print ('Sending Setup Command')
        self._SendCommand('Setup', "")
        print ('Command Sent')
        s = self.ser.readline().decode()
        if(len(s) == 0): #Teensy did not respond to version command. 
            s = 'NA'
        print ('Returned: ' + str(s))
        return str(s)

    def zero(self):
        if(self._reading):
            print('Zeroing the sensor')
            self._SendCommand('Zero', '')
            return 1
        else:
            print('DAQ must be reading to zero the sensor')
            return 0
    
    def setSamplingPeriod(self, samplingPeriod):
        self.ser.timeout = 1
        
        if(self._reading):
            print('Cannot change sample rate while logging')
            return False
        
        print('sending new sample period')
        self._SendCommand('DataRate', str(samplingPeriod))
        print('command sent')
        s = self.ser.readline().decode()
        if(len(s) == 0):
            s = 'NA'
        print('Returned: '+str(s))
        return str(s)
    
    def scanBLE(self):
        self.ser.timeout = 10

        print ('Sending Scan Command')
        self._SendCommand('Scan', "")
        print ('Command Sent')
        s = self.ser.readline().decode()
        print ('Returned: ' + str(s))
        self.ser.timeout = 1
        try:
            if(str(s[0]) == '*'):
                print('Error: ' + str(s))
                return 'NA'
            else:
                return str(s)
        except: #nothing returned
            return 'NA'
    
    def connectBLE(self, index):
        self.ser.timeout = 2
        retry = 0
        while(1):
            print('Connecting to Device at index = ' + str(index))
            self._SendCommand('Connect', str(index))
            s = self.ser.readline().decode()
            print ('Returned: ' + str(s))
            if(str(s[0]) == '*'):    
                print('Error: ' + str(s))
                return 0
            elif(str(s[0]) == '&'):
                return 1
            else:
                retry += 1
                print('Timeout' + str(retry) + '...')
                if(retry > 5):
                    print('...cannot connect')
                    return 0
                else:
                    print('...retrying')
    
    def BLECharList(self):
        self.ser.timeout = 2
        
        print ('Sending Characteristic List Command')
        self._SendCommand('List', "")
        print ('Command Sent')
        s = self.ser.readline().decode()
        print ('Returned: ' + str(s))
        self.ser.timeout = 1
        try:
            if(str(s[0]) == '*'):
                print('Error: ' + str(s))
                return 'NA'
            else:
                return str(s)
        except: #nothing returned
            return 'NA'
                
    
    def connectBLEChar(self, index):
        self.ser.timeout = 2
        retry = 0
        while(1):
            print('Connecting to Characteristic at index = ' + str(index))
            self._SendCommand('ConnectChar', str(index))
            s = self.ser.readline().decode()
            print ('Returned: ' + str(s))
            try:
                if(str(s[0]) == '*'):
                    print('Error: ' + str(s))
                    return 0
                elif(str(s[0]) == '&'):
                    return 1
                else:
                    retry += 1
                    print('Timeout' + str(retry) + '...')
                    if(retry > 5):
                        print('...cannot connect')
                        return 0
                    else:
                        print('...retrying')
            except: #nothing returned
                retry += 1
                print('Timeout' + str(retry) + '...')
                if(retry > 5):
                    print('...cannot connect')
                    return 'NA'
    
    def getFirmVer(self):
        self.ser.timeout = 2

        print ('Sending Version Command')
        self._SendCommand('Version', "")
        print ('Command Sent')
        s = self.ser.readline().decode()
        print ('Returned: ' + str(s))
        return str(s)

    def restartBLEDevice(self):
        print ('Disconnecting from BLE Device')
        self.COMDisconnect()
        print ('Connection to BLE Device')
        self.COMConnect(self.COM)

    def readBLEDataUntilStop(self, serialData_callback, serialBLE_callback):
        self.Abort = False
        self.ser.timeout = 1
    
        self._reading = 1
        
        self._SendCommand("Start", '')
        print('sent start command')
        
        while(self._reading == 1):
            if(self.Abort):
                self._SendCommand("Stop", '')
                print('sent stop command')
                self._reading = 0
            try:
                data = self.ser.read(self.packetSize)
                
                if(self._decodePacketData(data)): #decode the incoming byte stream
                    serialBLE_callback.emit(self.df) #retrun data in pandas DF
            except:
                print("Timeout on data collection")
                self.ser.reset_output_buffer()
                
        self.ser.reset_output_buffer()

    def _decodePacketData(self, data):
        if(len(data) == 0):
            print("No Data to Parse:" + str(data))
            return False
        elif(len(data) != 182):
            print("Data length incorrect: " + str(len(data)))
            return False
        
        dCount = 0
        dAx = []
        dAy = []
        dAz = []
        dGx = []
        dGy = []
        dGz = []
        
        def reverse(lst):
            lst.reverse()
            return lst
        
        for i in range (0, self.packetSize // 12): #loop through each packet in the received data
            try:
                dAx.append(int.from_bytes([data[1 + (i*12)], data[0 + (i*12)]], byteorder = 'big', signed = True))
                dAy.append(int.from_bytes([data[3 + (i*12)], data[2 + (i*12)]], byteorder = 'big', signed = True))
                dAz.append(int.from_bytes([data[5 + (i*12)], data[4 + (i*12)]], byteorder = 'big', signed = True))
                dGx.append(int.from_bytes([data[7 + (i*12)], data[6 + (i*12)]], byteorder = 'big', signed = True))
                dGy.append(int.from_bytes([data[9 + (i*12)], data[8 + (i*12)]], byteorder = 'big', signed = True))
                dGz.append(int.from_bytes([data[11 + (i*12)], data[10 + (i*12)]], byteorder = 'big', signed = True))
            except:
                print('Index: ' + str(i) + ' of Size: ' + str(len(data)))
                print('---Aborting Decode---')
                return
                    
            
        dCount = int.from_bytes([data[self.packetSize - 1], data[self.packetSize - 2]], byteorder = 'big', signed = False)
        
        if(self.lastCount == -1): self.lastCount = dCount - 15
        
        if(self.lastCount != (dCount - 15)):
            print("----------------------------------------")
            print("----------------------------------------")
            print("-----------------ERRROR-----------------")
            print("--------------MISSED PACKET-------------")
            print("--------------    " + str((dCount - self.lastCount - 15)//15) + "    --------------")
            print("----------------------------------------")
            print("----------------------------------------")
        
        self.lastCount = dCount
        #print(str(dAx) + str(dAy) +str(dAz) +str(dCount))
        
        self.df = pd.DataFrame(list(zip(dAx, dAy, dAz, dGx, dGy, dGz)), columns = ['dAx', 'dAy', 'dAz', 'dGx', 'dGy', 'dGz'])
        
        return(True)

    def readDataUntilStop(self, serialData_callback, serialBLE_callback):
        self.Abort = False
        self.ser.timeout = 1
    
        self._reading = 1
        
        self._SendCommand("Start", '')
        print('sent start command')
        
        while(self._reading == 1):
            if(self.Abort):
                self._SendCommand("Stop", '')
                print('sent stop command')
                self._reading = 0
            data = self.ser.readline().decode()
            serialData_callback.emit(data)

    def Read(self):
        if(not(self._comOpen)):
            self.ser.timeout = 1
            
            self._reading = 1

        self._SendCommand('Read', "")
        try:
            s = self.ser.readline().decode()
            #print('Returned: ' + str(s))
        except:
            print('ERROR - Nothing Returned')
            s = '0.0'
        
        return float(s)
    
    def COMConnect(self, COM):
        print ('Opening COM: ' + str(COM))
        self.ser = serial.Serial()
        self.ser.baudrate = 250000
        self.ser.port = COM
        self.ser.timeout = 1
        self.COM = COM
        self._comOpen = True
        
        try:
            print ('Opening Serial')
            self.ser.open()
            self.ser.readline().decode('ascii','ignore') #clear serial buffer
            return 1
            
        except serial.SerialException:
            print (COM + ' Not Properly Closed')
            return 0
        
    def COMDisconnect(self):
        self._reading = 0
        self._comOpen = False
        
        if(self.COM != -1):
            try:
                self.ser.close()
            except serial.SerialException:
                print ('COM' + self.COM + ' already closed!')