# -*- coding: utf-8 -*-
"""
Created on Tue May 02 10:17:41 2017

@author: Nick Arbanas
"""

from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QFileDialog, QApplication
import serial
import serial.tools.list_ports as PortList
import pandas as pd
import os
import datetime
import numpy as np
from time import sleep

class MaxtecDAQ():
    def __init__(self):
        print ('Class Initialized')
        self.ADCMult = 0.0078125
        self.Port = []
        self.Abort = False
        self.__Temperature = 'NA'
        self.__comOpen = False
    
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
    
    def SetTemp(self, Temp):
        if(Temp == 'Temp700'):
            print ('Using 700 Thermistor Equation')
            self.__Temperature = '700'
        elif(Temp == 'Temp800'):
            print ('Using 800 Thermistor Equation')
            self.__Temperature = '800'
        else:
            self.__Temperature = 'NA'
    
    def __SendCommand(self, Command, ser, data):
        CommandList = {"Start"      :"S\n",#Start
                       "Stop"       :"P\n",#Stop
                       "Version"    :"V\n",#Firmware Version
                       "DataRate"   :"o" + data + "\n",    #[Command Type][Multiplier][]
                       "Setup"      :"x\n",#Setup Info
                       "Read"       :"r\n"
                       }
        #print ('Command: ' + CommandList[Command])
        ser.write(CommandList[Command].encode('latin_1'))
        #print ('Command Written')
    
    def setLog(self, Log):
        self.Log = Log     
    
    def setRate(self, COM, rate):
        ser = serial.Serial()
        ser.baudrate = 250000
        ser.port = COM
        ser.timeout = 1
        
        rateInt = int(1000 / float(rate))
        print('Rate Int: ' + str(rateInt))
        
        rateString = ((rateInt & 0xff000000) >> 24).to_bytes(1, byteorder="little").decode('latin_1')
        rateString += ((rateInt & 0xff0000) >> 16).to_bytes(1, byteorder="little").decode('latin_1')
        rateString += ((rateInt & 0xff00) >> 8).to_bytes(1, byteorder="little").decode('latin_1')
        rateString += (rateInt & 0xff).to_bytes(1, byteorder="little").decode('latin_1')

        #print('rateString: ' + rateString)
        
        try:
            ser.open()
            print('Sending Rate Command')
            self.__SendCommand('DataRate', ser, str(rateString))
            print ('Command Sent')
            try:
                s = ser.readline().decode()
                print ('Returnded: ' + str(s))
            except:
                print ('ERROR - Nothing returned')
                s = 'NA'
            ser.close()
            print ('Serial on Poert: ' + COM + ' Closed')
            return str(s)
            
        except serial.SerialException:
            print (COM + 'Not Properly Closed')
            print ("Terminating 'setRate'")
            try:
                ser.close()
                print ('Serial on Port: ' + COM + ' Closed')
    
            except serial.SerialException:
                print ("Error, Serial Port Already Closed")
            return 'NA'
            
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
            self.__SendCommand('Setup', ser, "")
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
            self.__SendCommand('Version', ser, "")
            print ('Command Sent')
            s = ser.readline().decode()
            if(s[0] != 'S'): #Teensy did not respond to version command. 
                s = 'NA'
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

    # def __SaveExcelAs(self, fnameIn):
    #     fname = QFileDialog.getSaveFileName(self, 'Save file', fnameIn, "Excel files (*.xlsx)")
    #     if fname != '':
    #         self.__fname = fname
    
#==============================================================================
# Input Parameters: msg (Str), bold (Bool), color (Str)
# Output Returns: none
#
# Description: This function takes in a mesage and writes it to the Log TextEdit.
# If bold is True, the line is bolded. Color sets the color of the line, set to
# 'black' for default. 
#==============================================================================
    def logMsg(self, msg):            

        self.Log.moveCursor(QTextCursor.Start)      #Move the cursor to the beginning of the TextEdit
        self.Log.insertHtml(str(datetime.datetime.now().strftime('%H:%M:%S,')) + str(msg) + '<br>') #Add the TimeStamp, Message Text and finally a return    
    
    def Read(self, Com):
        if(not(self.__comOpen)):
            self.__ser = serial.Serial()
            self.__ser.baudrate = 250000
            self.__ser.port = Com
            self.__ser.timeout = 1
            
            try:
                self.__ser.open()
                print ('Serial Opened on Port for Reading: ' + Com)
                self.__comOpen = True
            except serial.SerialException:
                print (Com + ' Not Properly Closed, Restarting the COM Port')
                self.__ser.close()
                self.__ser.open()
                self.__comOpen = True
        
        self.__SendCommand('Read', self.__ser, "")
        try:
            s = self.__ser.readline().decode()
            #print('Returned: ' + str(s))
        except:
            print('ERROR - Nothing Returned')
            s = '0.0'
        
        return float(s)
    
    def CloseCOM(self, Com):
        self.__ser.close()
        self.__comOpen = False
    
    def ReadStreamStart(self, Com):
        Loop = True
        self.Log.setText("")
    
        ser = serial.Serial()
        ser.baudrate = 250000
        ser.port = Com
        ser.timeout = 0
        
        try:
            ser.open()
            print ('Serial Opened on Port: ' + Com)
        except serial.SerialException:
            print (Com + ' Not Properly Closed, Restarting the COM Port')
            ser.close()
            ser.open()            
        
        print ('--Start COM Recording--')            
        
        i = 0
        
        while Loop:
            try:
                self.logMsg(ser.readline().decode())
            except serial.SerialTimeoutException:
                print ("No Serial Data")
                self.Abort = 1
            
            
            QApplication.processEvents()

            print ('N: ' + str(i))
            i = i + 1

            if(self.Abort): #Only Retry 3 times 
                print ('--Stop COM Recording--') 
                Loop = False    
    
    def ReadStart(self, ReadList, SampleNum, Com, Rate):
        self.__ReadList = ReadList

        Loop = True        
        
        print (')Number of Samples: ' + str(SampleNum))
        #self.__SaveExcelAs()
        
        ser = serial.Serial()
        ser.baudrate = 250000
        ser.port = Com
        ser.timeout = int(1 / Rate) + 1
        
        try:
            ser.open()
            print ('Serial Opened on Port: ' + Com)
        except serial.SerialException:
            print (Com + ' Not Properly Closed, Restarting the COM Port')
            ser.close()
            ser.open()
        
        print ('Starting DF')
        self.df = pd.DataFrame(columns=ReadList)
        
        print ('--Start Teensy--')
        self.__SendCommand("Start", ser, "")    
        
        i = 0

        self.Abort = False
    
        while True:
            try:
                while Loop:
                    self.s = ser.readline().decode()
                    DataList = map(lambda x:(x * self.ADCMult), map(int, self.s.split(',')))
                    QApplication.processEvents()
                    if ((len(DataList) != len(ReadList)) and not(self.Abort)):
                        i = i #Get another sample
                    else:
                        print ('N: ' + str(i))
                        self.df.loc[i] = DataList
                        i = i + 1

                        if((i >= SampleNum) or (self.Abort)): #Only Retry 3 times 
                            print ('--Stop Teensy--')
                            Loop = False
                            self.__SendCommand("Stop", ser, "") #Stop the Teensy
                            sleep(.1) #Wait
                            self.__SendCommand("Stop", ser, "") #Double check the Teensy is stopped
                            sleep(.1) #Wait
                            self.__SendCommand("Stop", ser, "") #OK, The Teensy has to be stopped but just to be safe
                            
                            if(self.__Temperature == '700'): #Convert to Temperature? 700
                                print ('Crunching Data...')
                                self.df = self.df.apply(lambda x: ((1/(0.003354-np.log(1.0018523/(x**0.00028249))))-273.15))
                                print ('...Data Crunched!')
                            elif(self.__Temperature == '800'): #Convert to Temperature? 800
                                print ('Crunching Data...')
                                self.df = self.df.apply(lambda x: ((1/(0.003354-np.log(1.0018901/(x**0.00028249))))-273.15))
                                print ('...Data Crunched!')
                break
            except ValueError:
                print ("ERROR, Incorrect or No serial information recieved")
                print (self.s)
                break
            except serial.SerialTimeoutException:
                print ("Connection Lost...")
                print ("     ...Attempting to Reconnect")
                self.__SendCommand("Start", ser, "")

        try:
            ser.close()
            print ('Serial on Port: ' + Com + ' Closed')

        except serial.SerialException:
            print ("Error, Serial Port Already Closed")

    def SaveData(self, fname):
        print ("Saving to Excel")
        try:
            self.df.to_excel(str(fname))
            print ("File Saved!")
            return True
        except:
            print ("ERROR - Could not save Excel File!")
            RecoveryPath = str(os.getcwd()) + 'Recovery-' + str(datetime.datetime.now().strftime('%H%M%S'))
            self.df.to_excel(RecoveryPath)
            print ("File Recovery avaliable at: " + RecoveryPath)
            return False

List = ['POS01', 'POS02', 'POS03', 'POS04', 'POS05', 'POS06', 'POS07', 'POS08', 'POS09', 'POS10', 'POS11', 'POS12', 'POS13', 'POS14', 'POS15', 'POS16', 'POS17', 'POS18', 'POS19', 'POS20', 'POS21', 'POS22', 'POS23', 'POS24', 'POS25', 'POS26', 'POS27', 'POS28', 'POS29', 'POS30', 'POS31', 'POS32']