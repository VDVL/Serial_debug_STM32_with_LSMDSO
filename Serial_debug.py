from tkinter import *
import tkinter.font
import serial
import time
import re
import sys,os, time
import platform
from random import randint
import serial,serial.tools.list_ports
import struct


#global var
old_var = [0,0,0]       #store previous value in case of checksum error
cpt_flt = 0             #number of faults
cpt     = 0             #number of cycles


#Find all Serial Ports activated and select only the port of the STM32 board--------------------------------------------------------------
def find_USB_device():
    #serial.tools.list_ports -> trouve les periphériques connéctés
    myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]  

    #Look over all ports connected for "STM" port
    for p in myports:                                                       
        if "STM" in p[1]:                                                   # Select STM32 port COM 
            return p[0]                                                     #PORT FOUND
    return None;                                                            #PORT NOT FOUND


#RECEIVE AND TREAT DATAS FROM FRAME---------------------------------------------------------------------------------------------------------------
def read_datas(port_com):
    nb_octet = 77       #number of bytes in the frame
    checksum = 0        #checksum of frame
    timeout_UART = 0    #counter for timeout (UART)
    carac =''           #store bytes frome serial reading

    #global var
    global cpt     
    global cpt_flt
    global old_var

    #count one turn
    cpt +=1  

    #Set Serial parameters 
    ser = serial.Serial(port_com,
                        baudrate=921600, 
                        bytesize=serial.EIGHTBITS, 
                        parity=serial.PARITY_NONE, 
                        stopbits=serial.STOPBITS_ONE, 
                        timeout=5000) #Serial parameters

    #Wait for start character ($) until timeout
    while((not("$" in carac)) and (timeout_UART <=500)):         
        carac = str(ser.read())
        timeout_UART +=1

    #Check if timeout is exceed
    if(timeout_UART>=500):
        print("SERIAL COM NOT DETECTED")
        return False, 0, 0, 0, 0


    #Wait for entire byte frame
    while(ser.in_waiting <= nb_octet):
        pass 

    #Read next X bytes       
    s = ser.read(nb_octet)                       
    
    #Unpacked  bytes to original format (fff fff ffff fff fff fff B)  f->float B->Byte
    int_vals = struct.unpack('fffffffffffffffffffB', s)  

    #Unpacked each bytes in table to compute checksum  
    octets = struct.unpack('BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB', s)     

    #Compute checksum
    for i in octets[:-1]:
        checksum ^= i

    #Verif Checksum and extract interesting value 
    if(checksum == octets[-1]):                    #(Octets[-1] = last byte is the checksum)
        #YAW PITCH ROLL is store at 10 11 12 index "in int_vals"
        x_axis = int_vals[10]
        y_axis = int_vals[11]
        z_axis = int_vals[12]
        #Saves values in case of chesksum mistake
        old_var[0] = x_axis
        old_var[1] = y_axis
        old_var[2] = z_axis
        #print("x: {0:.1f}".format(x_axis),"y: {0:.1f}".format(y_axis),"z: {0:.1f}".format(z_axis)) #debug

    #In case of Value error print additionnal infos and return saved values
    else:
        print("CHECKSUM ERROR --","Calc:",checksum ,"Read:",octets[-1]," -- ERROR RATE: ", round((cpt_flt/cpt)*100,1),"%")
        cpt_flt +=1
        x_axis = old_var[0]
        y_axis = old_var[1]
        z_axis = old_var[2]
        #print(x_axis)

    return True, 0, x_axis, y_axis, z_axis 
        


#main Window using Tk-----------------------------------------------------------------------------------------------------------------------
win = Tk()

win.title("v1.0")
win.geometry('400x300')
win.configure(background=("Grey"))

#Labels with text----------------------------------------------------------
temp = Label(win, text = "T °C   " ,fg="Blue",font=("Arial", 18,"bold",))
temp.place(x=50, y=50)

x_axis = Label(win, text = "YAW" ,fg="Green",font=("Arial", 18,"bold",))
x_axis.place(x=50, y=100)

y_axis = Label(win, text = "PITCH" ,fg="Orange",font=("Arial", 18,"bold",))
y_axis.place(x=50, y=150)

z_axis = Label(win, text = "ROLL" ,fg="Red",font=("Arial", 18,"bold",))
z_axis.place(x=50, y=200)

#Labels with values---------------------------------------------------------
temp_val = Label(win, text = "val",fg="Black",font=("Arial", 18,"bold",))
temp_val.place(x=150, y=50)

x_axis_val = Label(win, text = "val",fg="Black",font=("Arial", 18,"bold",))
x_axis_val.place(x=150, y=100)

y_axis_val = Label(win, text = "val",fg="Black",font=("Arial", 18,"bold",))
y_axis_val.place(x=150, y=150)

z_axis_val = Label(win, text = "val",fg="Black",font=("Arial", 18,"bold",))
z_axis_val.place(x=150, y=200)


#Recursive function to refresh Window
def live_update():
    #Read GYRO datas from Serial port
    active, temp, x_axis, y_axis, z_axis = read_datas(port_com)

    #Print datas on Window
    temp_val['text'] = temp
    x_axis_val['text'] = round(x_axis,2)
    y_axis_val['text'] = round(y_axis,2)
    z_axis_val['text'] = round(z_axis,2)

    #Refresh or Exit
    if(active==False):
        win.after(20,win.destroy)
    else:
        win.after(1, live_update) # 1000 is equivalent to 1 second (closest you'll get)


#Connection to STM32 USB PORT--------------------------------------------------------------------------------------------------------
port_com =  find_USB_device()
#PORT NOT FOUND--------------
if (port_com == None):
    print("DEVICE NOT FOUND")
    active = False
#PORT FOUND - RUN PROG-------
else:
    active = True
    live_update() 

 