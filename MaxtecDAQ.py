# -*- coding: utf-8 -*-
"""
Created on Tue May 02 10:17:41 2017

@author: Nick Arbanas
"""

from PyQt5.QtGui import QTextCursor
import serial
import serial.tools.list_ports as PortList
import os
import datetime

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
    
    def __SendCommand(self, Command, ser, data):
        CommandList = {"Version"    :"V\n",#Firmware Version
                       "DataRate"   :"o" + data + "\n",    #[Command Type][Multiplier][]
                       "Setup"      :"x\n",#Setup Info
                       "Read"       :"r\n"
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