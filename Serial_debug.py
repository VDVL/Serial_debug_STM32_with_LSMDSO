from tkinter import *
import tkinter.font
from PIL import Image, ImageTk
import serial
import time
import re
import sys,os, time
import platform
from random import randint
import serial,serial.tools.list_ports
import struct


#global var
old_var = [0,0,0,0,0,0]       #store previous value in case of checksum error
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
    


    #Unpacked  bytes to original format (iii iii ffff fff fff fff B)  f->float B->Byte
    int_vals = struct.unpack('iiiiiifffffffffffffB', s)  

    #Unpacked each bytes in table to compute checksum  
    octets = struct.unpack('BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB', s)     

    #Compute checksum
    for i in octets[:-1]:
        checksum ^= i

    #Verif Checksum and extract interesting value 
    if(checksum == octets[-1]):                    #(Octets[-1] = last byte is the checksum)
        #YAW PITCH ROLL is store at 10 11 12 index "in int_vals"
        yaw = int_vals[10]
        pitch = int_vals[11]
        roll = int_vals[12]
        X = int_vals[13]
        Y = int_vals[14]
        Z = int_vals[15]

        #Saves values in case of chesksum mistake
        old_var[0] = yaw
        old_var[1] = pitch
        old_var[2] = roll
        old_var[3] = X
        old_var[4] = Y
        old_var[5] = Z

        #print("x: {0:.1f}".format(yaw),"y: {0:.1f}".format(pitch),"z: {0:.1f}".format(roll)) #debug
        #print("x: {0:.2f}".format(int_vals[13]),"y: {0:.2f}".format(int_vals[14]),"z: {0:.2f}".format(int_vals[15]))
    #In case of Value error print additionnal infos and return saved values
    else:
        print("CHECKSUM ERROR --","Calc:",checksum ,"Read:",octets[-1]," -- ERROR RATE: ", round((cpt_flt/cpt)*100,1),"%")
        cpt_flt +=1
        yaw = old_var[0]
        pitch = old_var[1]
        roll = old_var[2]
        X = old_var[3]
        Y = old_var[4]
        Z = old_var[5]

    return True, yaw, pitch, roll, X, Y, Z 
        


#main Window using Tk-----------------------------------------------------------------------------------------------------------------------
win = Tk()

win.title("v1.0")
win.geometry('500x500')
win.configure(background=("white"))

#Def img---------------------------------------
img = PhotoImage(file = 'AXES_YAW_PITCH_ROLL.png', master=win)
panel = Label(win, image = img)
panel.pack(side = "bottom",pady="20")

#Labels with text----------------------------------------------------------------------------
temp = Label(win, text = "         AXIS         " ,fg="Black",font=("Arial", 18,"bold",))
temp.place(x=50, y=50)

yaw = Label(win, text = " YAW  " ,fg="Blue",font=("Arial", 18,"bold",))
yaw.place(x=50, y=100)

pitch = Label(win, text = " PITCH" ,fg="Green",font=("Arial", 18,"bold",))
pitch.place(x=50, y=150)

roll = Label(win, text = " ROLL " ,fg="Red",font=("Arial", 18,"bold",))
roll.place(x=50, y=200)

#-----------------------------------------------
temp = Label(win, text = " GRAVITY " ,fg="Black",font=("Arial", 18,"bold",))
temp.place(x=300, y=50)

X_g = Label(win, text = " X " ,fg="Blue",font=("Arial", 18,"bold",))
X_g.place(x=300, y=100)

Y_g = Label(win, text = " Y " ,fg="Green",font=("Arial", 18,"bold",))
Y_g.place(x=300, y=150)

Z_g = Label(win, text = " Z " ,fg="Red",font=("Arial", 18,"bold",))
Z_g.place(x=300, y=200)


#Labels with values--------------------------------------------------------------------
yaw_val = Label(win, text = "val",fg="Black",font=("Arial", 18,"bold",))
yaw_val.place(x=150, y=100)

pitch_val = Label(win, text = "val",fg="Black",font=("Arial", 18,"bold",))
pitch_val.place(x=150, y=150)

roll_val = Label(win, text = "val",fg="Black",font=("Arial", 18,"bold",))
roll_val.place(x=150, y=200)

#----------------------------------
X_g_val = Label(win, text = "val",fg="Black",font=("Arial", 18,"bold",))
X_g_val.place(x=360, y=100)

Y_g_val = Label(win, text = "val",fg="Black",font=("Arial", 18,"bold",))
Y_g_val.place(x=360, y=150)

Z_g_val = Label(win, text = "val",fg="Black",font=("Arial", 18,"bold",))
Z_g_val.place(x=360, y=200)


#Recursive function to refresh Window
def live_update():
    #Read GYRO datas from Serial port
    active, yaw, pitch, roll, X, Y, Z = read_datas(port_com)

    #Print datas on Window
    yaw_val['text'] = round(yaw,2)
    pitch_val['text'] = round(pitch,2)
    roll_val['text'] = round(roll,2)
    X_g_val['text'] = round(X,2)
    Y_g_val['text'] = round(Y,2)
    Z_g_val['text'] = round(Z,2)
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

 