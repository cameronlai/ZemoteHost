# This file is part of ZemoteHost.
# 
# ZemoteHost is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# ZemoteHost is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with ZemoteHost.  If not, see <http://www.gnu.org/licenses/>.

import serial
import glob
import threading
import time
import wx

__version__ = '2015.07.28'

class ZemoteCore():
    def __init__(self):
        self.title = 'Zemote Host'
        self.s = None
        self.read_thread = None
        self.debug = False
        self.connected = False
        self.port = None
        self.baudrate = None

        self.read_thread = None
        self.continue_read_thread = False
        self.read_thread_buffer = None

        self.programMode = False

        self.SerialBuffer = []
        self.SerialBufferTargetLen = 0

        self.numSoftButtons = 9 # includes all buttons and channels
        self.activtButtonIndex = -1 # -1 means invalid
        self.simpleModeEnabled = False
        self.buttonLengthList = ['0'] * self.numSoftButtons

        # Call back functions for UI
        self.display_msg_cb = None # Call back function for line read from serial port        
        self.display_connection_action_cb = None # Call back for connection action
        self.display_status_cb = None # Call back for status bar update
        self.display_program_mode_cb = None # Call back for program button
        self.display_cmd_length_cb = None # Call back to update UI command lengths
        self.display_mode_cb = None # Call back to display mode text

    def connect(self, port = None, baudrate = None):
        if port is not None:
            self.port = port
        if baudrate is not None:
            self.baudrate = baudrate
        if self.port is not None and self.baudrate is not None:
            try:                
                self.s = serial.Serial(self.port, self.baudrate, timeout=1)
                self.connected = True

                # UI
                wx.CallAfter(self.display_connection_action_cb, 'Disconnect')
                wx.CallAfter(self.display_status_cb, self.title + ' is connected!')
                # Read thread
                self.continue_read_thread = True        
                self.read_thread = threading.Thread(target = self._listen)
                self.read_thread.start()
                time.sleep(2)

                # Initialization routine
                self.getAllButtonLength()
                time.sleep(1)
                self.getMode()

                if self.debug:
                    print('Serial device is connected!')                
                return True
            except:
                if self.debug:
                    print('Serial device cannot be connected!')
                return False
    
    def disconnect(self):
        try:
            self.s.close()
            self.connected = False
            # Read thread
            self.continue_read_thread = False
            if self.read_thread:
                if threading.current_thread() != self.read_thread:
                    self.read_thread.join()
            # UI
            wx.CallAfter(self.display_connection_action_cb, 'Connect')
            wx.CallAfter(self.display_status_cb, self.title + ' is disconnected!')
            if self.debug:
                print('Serial device is disconnected!')
            return True
        except:
            if self.debug:
                print('Serial device cannot be disconnected!')     
            return False
        
    def scanSerialPort(self):
        portList = []
        for g in ['/dev/ttyUSB*', '/dev/ttyACM*', "/dev/tty.*", "/dev/cu.*", "/dev/rfcomm*"]:
            portList += glob.glob(g)
        if self.debug:
            print portList
        return portList
    
    def send(self, cmd):
        sendCmd = cmd + '\n'
        returnString =''
        try:
            self.s.write(sendCmd.encode())
            wx.CallAfter(self.display_msg_cb, '>>> ' + sendCmd)
            if self.debug:
                print 'SND:' + cmd
            return True
        except:
            if not self.connected:
                wx.CallAfter(self.display_status_cb, self.title + ' is not connected')
            else:
                wx.CallAfter(self.display_status_cb, 'Fail to write to ' + self.title)            
            return False

    def _listen(self):
        while self.continue_read_thread:
            try:
                line = self.s.readline()
                if line is not '':     
                    if self.SerialBufferTargetLen > 0:
                        self.SerialBuffer.append(line)
                        self.SerialBufferTargetLen -= 1
                    wx.CallAfter(self.display_msg_cb, line)
                    if 'ok - F' in line: # end of program mode
                        self.programMode = False
                        wx.CallAfter(self.display_program_mode_cb, 'Program')

                        tmpLen = line[6]
                        self.buttonLengthList[self.activeBtnIdx] = tmpLen
                        wx.CallAfter(self.display_cmd_length_cb, self.activeBtnIdx, tmpLen)
                        self.activeBtnIdx = -1 # Reset to invalid value
                    if self.debug:
                        print 'RCV:' + line
            except:                
                self.disconnect()
                if self.debug:
                    print('Failed to receive from serial device. Disconnected.')
                continue               

    # Centralized UI Call back functions

    def setDisplayMsgCallBack(self, function):
        self.display_msg_cb = function

    def setDisplayActionCallBack(self, function):
        self.display_connection_action_cb = function

    def setDisplayStatusCallBack(self, function):
        self.display_status_cb = function

    def setDisplayProgramModeCallBack(self, function):
        self.display_program_mode_cb = function

    def setDisplayCmdLengthCallBack(self, function):
        self.display_cmd_length_cb = function

    def setDisplayModeCallBack(self, function):
        self.display_mode_cb = function

    # All functions below are based on pre-defined protocols

    def startProgramMode(self, btnIndex):
        ret = self.send('P'+str(btnIndex))
        self.activeBtnIdx = btnIndex
        if ret:
            self.programMode = True
        return ret

    def endProgramMode(self):        
        ret = self.send('F')
        if ret:
            self.programMode = False
        return ret
            
    def getAllButtonLength(self):
        self.SerialBufferTargetLen = self.numSoftButtons
        self.SerialBuffer = []
        ret = self.send('L')
        if ret:
            while(self.SerialBufferTargetLen > 0):
                pass
            for i in range(self.numSoftButtons):
                tmpLen = self.SerialBuffer[i].rstrip()
                self.buttonLengthList[i] = tmpLen
                wx.CallAfter(self.display_cmd_length_cb, i, tmpLen)
        return ret

    def getButtonInfo(self, btnIndex):
        return self.send('G' + str(btnIndex))

    def testButton(self, btnIndex):
        return self.send('T'+str(btnIndex))

    def saveToEEPROM(self):
        return self.send('S')
    
    def resetAllToEEPROM(self):
        return self.send('R')

    def getMode(self):
        self.SerialBufferTargetLen = 1
        self.SerialBuffer = []
        ret = self.send('M')
        if ret:
            while(self.SerialBufferTargetLen > 0):
                pass
            if 'Simple' in self.SerialBuffer[0]:
                self.simpleModeEnabled = True
            else:
                self.simpleModeEnabled = False
            wx.CallAfter(self.display_mode_cb)
        return ret          

    def switchMode(self):
        if self.simpleModeEnabled:
            cmd = 'X0'
        else:
            cmd = 'X1'
        ret = self.send(cmd)
        if ret:
            self.simpleModeEnabled = not self.simpleModeEnabled
            wx.CallAfter(self.display_mode_cb)
        return ret

