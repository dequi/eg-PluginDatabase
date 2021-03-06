# This file is part of EventGhost.
# Copyright (C) 2005 Lars-Peter Voss <bitmonster@eventghost.org>
# 
# EventGhost is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# EventGhost is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with EventGhost; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#
# $LastChangedDate$
# $LastChangedRevision$
# $LastChangedBy$

eg.RegisterPlugin(
    name = "TechnoTrend Budget Receiver",
    author = "mastalee",
    version = "0.1",
    kind = "remote",
    description = (
        'Hardware plugin for the '
        'Onboard IR Receiver of '
        'TechnoTrend Budget Cards (C-1501)'
        '\n\n<p>'
    ),
)


from ctypes import *
from ctypes.wintypes import *
import os

#enum  	DEVICE_CAT {
UNKNOWN = 0
BUDGET_2 = 1
BUDGET_3 = 2
USB_2 = 3
USB_2_PINNACLE = 4
USB_2_DSS = 5
  
#typedef void(* PIRCBFCN)(PVOID Context, DWORD *Buf)
#Infrared callback function.
#Parameters:
#    	Context 	Can be used for a context pointer in the calling application. This parameter can be NULL.
#    	Buf 	Contains the remote code. If RC5 then the low word is used. If RC6 then the whole DWORD is used. 
PIRCBFCN = CFUNCTYPE(
    c_void_p, # return type
    c_void_p, # context
    POINTER(DWORD)
)
#    typedef void (*PIRCBFCN) (PVOID Context, PVOID Buf, ULONG len, // buffer length in bytes
#                                USBIR_MODES IRMode, HANDLE hOpen, BYTE DevIdx);
#IRCALLBACKFUNC = CFUNCTYPE(
#    c_void_p, # return type
#    c_void_p, # Context
#    POINTER(DWORD), # Buf
#    ULONG, # len (buffer length in bytes)
#    c_int, # IRMode (of enum USBIR_MODES)
#    HANDLE, # hOpen
#    BYTE # DevIdx
#)


class TTIR(eg.RawReceiverPlugin):
    
    def __start__(self):
        #print "TTIR:__start__"
        self.dll = None
        dll = None
        self.hOpen = None
        self.cCallback = None
        pluginDir = os.path.abspath(os.path.split(__file__)[0])
        #print "pluginDir=%s" % pluginDir
        dll = cdll.LoadLibrary(os.path.join(pluginDir, "ttBdaDrvApi_Dll.dll"))
        if dll is not None:
            self.dll = dll
            #print "dll=", dll
            cnt_budget_2 = dll.bdaapiEnumerate(BUDGET_2)
            cnt_budget_3 = dll.bdaapiEnumerate(BUDGET_3)
            cnt_unknown  = dll.bdaapiEnumerate(UNKNOWN)
            cnt_usb2       = dll.bdaapiEnumerate(USB_2)
            cnt_usb2p     = dll.bdaapiEnumerate(USB_2_PINNACLE)
            cnt_usb2dss  = dll.bdaapiEnumerate(USB_2_DSS)
            #print "budget_2=%d" % cnt_budget_2, "budget_3=%d" % cnt_budget_3
            print "TTIR: b2:%(cnt_budget_2)d b3:%(cnt_budget_3)d unk:%(cnt_unknown)d usb2:%(cnt_usb2)d usb2p:%(cnt_usb2p)d usb2dss:%(cnt_usb2dss)d" % vars()
            self.cCallback = PIRCBFCN(self.bdaIrCallback)
            if cnt_budget_2>0:
                self.hOpen = dll.bdaapiOpen(BUDGET_2,0)
            elif cnt_budget_3>0:
                self.hOpen = dll.bdaapiOpen(BUDGET_3,0)
            elif cnt_usb2>0:
                self.hOpen = dll.bdaapiOpen(USB_2,0)
            elif cnt_usb2p>0:
                self.hOpen = dll.bdaapiOpen(USB_2_PINNACLE,0)
            elif cnt_usb2dss>0:
                self.hOpen = dll.bdaapiOpen(USB_2_DSS,0)
            else:
                self.hOpen = dll.bdaapiOpen(UNKNOWN,0)

            if self.hOpen>0:
                irReg = dll.bdaapiOpenIR(self.hOpen, self.cCallback, 0)
            else:
                raise self.Exceptions.DeviceNotFound
            #print "hOpen= ",self.hOpen," cCallback= ",self.cCallback, "irReg= ",irReg
            
        else:
            raise eg.Exception("Error: can't load ttBdaDrvApi_Dll")
    
    def OnComputerSuspend(self, dummySuspendType):
        #TODO: close dll handle 
        #self.dll.irClose(self.hOpen)
        pass
    
    
    def OnComputerResume(self, dummySuspendType):
        #TODO: reopen dll handle 
        #self.hOpen = self.dll.irOpen(
            #0, USBIR_MODE_DIV, self.cCallback, 0
        #)
        #if self.hOpen == -1:
            #raise self.Exceptions.DeviceNotFound
        pass
            
    def __stop__(self):
        if self.dll is not None:
            if self.hOpen is not None:
                self.dll.bdaapiCloseIR(self.hOpen)
                self.dll.bdaapiClose(self.hOpen)
    
    def bdaIrCallback(self, context, buf):
        #print "%08X" % buf[0]
        toggle = (buf[0] & 0x0800)
        code = (buf[0] & 0xF7FF)
        #print "TTIR:bdaIrCallback toggle ", (toggle>>11)
        self.TriggerEvent("%08X" % code)
    
   
    