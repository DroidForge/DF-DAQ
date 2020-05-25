# -*- coding: utf-8 -*-
"""
Created on Tue May 02 10:17:41 2017

@author: Nick Arbanas
"""

import serial
import serial.tools.list_ports as PortList

class DF_DAQ():
    def __init__(self):
        print ('Class Initialized')
        self.ADCMult = 0.0078125
        self.Port = []
        self.Abort = False
        self.__Temperature = 'NA'
        self.__comOpen = False
        self.__reading = 0
    
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
        CommandList = {"Version"    :"v\n",#Firmware Version
                       "DataRate"   :"o" + data + "\n",    #[Command Type][Multiplier][]
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
        
    def zero(self):
        if(self.__reading):
            print('Zeroing the sensor')
            self.__SendCommand('Zero', self.__ser, '')
            return 1
        else:
            print('DAQ must be reading to zero the sensor')
            return 0
        
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
            
            self.__reading = 1
            
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
        
        self.reading = 0