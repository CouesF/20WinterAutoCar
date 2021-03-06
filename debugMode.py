#!/usr/bin/env python
import cv2
import serial
import math
import time 
import cv2
import numpy as np
import rospy
from std_msgs.msg import Float32MultiArray
from std_msgs.msg import MultiArrayDimension
from std_msgs.msg import MultiArrayLayout
import qrtools

import tkinter as tk
from tkinter import *
pi = 3.141592653589793

clickX = 0
clickY = 0
templateWidth = 90

MKSDLC = '/dev/MKSDLC'
MKSGEN = '/dev/MKSGEN'

templateCam = '/dev/cam4TemplateMatching'
qrCodeCam = '/dev/cam4QRCode'

qrCodeCap = cv2.VideoCapture(qrCodeCam)
templateCap = cv2.VideoCapture(templateCam)

speed = [0, 0, 0, 0]# A B C D
botCurGlobalPos = [0,0,0] #x,y,dir float
firstLevelOrder = [0,0,0] #red__1 green__2  blue__3
secondLevelOrder = [0,0,0]



baud = 115200
genSerial = serial.Serial(
    port=MKSGEN,\
    baudrate=baud,\
    bytesize=serial.EIGHTBITS,\
    parity=serial.PARITY_NONE,\
    stopbits=serial.STOPBITS_ONE,\
    timeout=5)
print(genSerial.name)         # check which port was really used
pass
dlcSerial = serial.Serial(
    port=MKSDLC,\
    baudrate=baud,\
    bytesize=serial.EIGHTBITS,\
    parity=serial.PARITY_NONE,\
    stopbits=serial.STOPBITS_ONE,\
    timeout=5)
print(dlcSerial.name)         # check which port was really used
pass
def callback(rawPositionData):
    #rospy.loginfo(rospy.get_caller_id() + "i heard %s", rawPositionData.data)
    botCurGlobalPos[0] = rawPositionData.data[0]
    botCurGlobalPos[1] = rawPositionData.data[1]
    botCurGlobalPos[2] = rawPositionData.data[2]
    #print(botCurGlobalPos)
def setSpeed(__direction,__speed,__rotation):
    getSpeed(__direction,__speed,__rotation)
    mesg = str.encode('S A'+str(int(speed[0]))+' B'+str(int(speed[1]))+' C'+str(int(speed[2]))+' D'+str(int(speed[3]))+' @')
    genSerial.write(mesg)
    print(mesg)

def getSpeed(direction, speedG, rotation):
    """
    docstring
    """
    direction = direction + (pi / 4.0)
    speed[0] = -speedG * math.cos(direction)
    speed[1] = -speedG * math.sin(direction)
    speed[2] = speedG * math.cos(direction)
    speed[3] = speedG * math.sin(direction)

    speed[0] += rotation
    speed[1] += rotation
    speed[2] += rotation
    speed[3] += rotation
    pass

def setMovement(_x,_y,_r):
    mesg = str.encode('P X'+str(int(_x))+' Y'+str(int(_y))+' R'+str(int(_r))+' @')
    genSerial.write(mesg)
    print(mesg)
#genSerial.write(str.encode('bnbs'))
#xxx = genSerial.read(5)
#print((xxx))
#temp = str.encode('S A50 B50 C50 D50 ')
#genSerial.write(temp)
#print(temp)

#getTemplate()
def moveTo(targetX,targetY,targetDir):#will sent one record of moving data
    maxSpeed = 220
    returnValue = 0
    deltaX = targetX - botCurGlobalPos[0]
    deltaY = targetY - botCurGlobalPos[1]
    deltaRotation = targetDir - botCurGlobalPos[2]
    dist = math.sqrt(math.pow(deltaX,2)+math.pow(deltaY,2))
    print(deltaX,deltaY,dist)    
    moveDir = math.atan2(deltaY,deltaX)
    print(moveDir,botCurGlobalPos[2])
    moveDir -=  botCurGlobalPos[2]
    
    if(dist > 0.5):
        movingSpeed = maxSpeed * 0.9
        returnValue += 1
    elif(dist>0.1):
        movingSpeed = maxSpeed * dist/1.2
        returnValue += 2
    elif(dist>0.08):
        movingSpeed = maxSpeed * 0.15/1.2
        returnValue += 3
    else:
        movingSpeed = 0

    if(abs(deltaRotation) > pi/2.0):
        rotationSpeed = 50
        returnValue +=10
    elif(abs(deltaRotation) > pi/8.0):
        rotationSpeed = 30
        returnValue +=20
    elif(abs(deltaRotation) > pi/50.0):
        rotationSpeed = 15
        returnValue +=20

    elif(abs(deltaRotation) > pi/70.0):
        rotationSpeed = 5
        returnValue +=30

    else:
        rotationSpeed = 0

    rotationSpeed *=np.sign(deltaRotation)
    print(moveDir,movingSpeed,rotationSpeed)
    setSpeed(moveDir,movingSpeed,rotationSpeed)
    #setSpeed(moveDir,movingSpeed,0)
    sleepFor(0.6)
    return returnValue

    pass

def waitUntilMovedTo(_x,_y,_dir):
    while(moveTo(_x,_y,_dir)!=0):
        pass
    pass


def openListener():
    rospy.init_node('mainPython',anonymous=True)
    rospy.Subscriber('RobotPositionInfo',Float32MultiArray,callback)
    #rospy.spin()


def test1():
    count = 3
    while(count>0):
    
        count=count-1

        time.sleep(1)

        setSpeed(-pi,80,0)
        time.sleep(1)
 
        setSpeed(-pi,120,0)
        time.sleep(2)

        setSpeed(-pi,30,0)
        time.sleep(1)


        time.sleep(2)
        setSpeed(0,0,0)
        print('set done\n')
    pass

def getAndSaveQrcode():
    _,imgggg =qrCodeCap.read()
    #cv2.imshow('qrcode',imgggg)
    cv2.imwrite("qrcode.png",imgggg)
    pass
def decodeQRCode():
    qr = qrtools.QR()
    qr.decode("qrcode.png")
    print('a',qr.data)
    if(qr.data == u'NULL'):
        return False

    flag = True
    for i in range(0,3):
        if(int(qr.data[i])!=1 and int(qr.data[i])!=2 and int(qr.data[i])!=3):
            flag = False
            break
        if(int(qr.data[i+4])!=1 and int(qr.data[i+4])!=2 and int(qr.data[i+4])!=3):
            flag = False
            break
        firstLevelOrder[i] = int(qr.data[i])
        secondLevelOrder[i] = int(qr.data[i+4])
        pass
    if(flag==False):
        return False
    else:
        root = tk.Tk()
        tp = Toplevel(root)
        tp.attributes('-topmost',True)
        lb = Label(tp,text=qr.data,font=("Courier",55))
        lb.pack()
        tp.update()
        print(firstLevelOrder,secondLevelOrder)
        return True
def detectAndDecodeQRCode():#TODO:important,not todo
    '''
    requirement:open qrCodeCap
    output:set the 2 list of order
    '''
    getAndSaveQrcode()
    decodeQRCode()
    pass
def test4Template():
    cv2.waitKey(0)
    pass
def openAndSetCap():
   
    templateCap.set(10,0.8)#brightness
    #templateCap.set(15,10)#exposure
    #templateCap.set(11,0.3)#contrast
    print(templateCap.get(10),'\n')
    print(templateCap.get(11),'\n')
    print(templateCap.get(15),'\n')
    time.sleep(0.2)
    pass      
  
def getTemplatePosition():
    pass
def resetToStartStatus():
    camPos(0)
    sleepFor(0.06)
    resetDlc()
    sleepFor(2)
    clawDirection(2)
    sleepFor(1)
    clawHeight(2)
    lockMotors()
    sleepFor(0.2)
def claw(_state):
    #0-1-2
    mesg = str.encode('zm'+str(_state)+'@')
    dlcSerial.write(mesg)
    pass
def clawHeight(_state):
    #0-1-2-3
    mesg = str.encode('ah'+str(_state)+'@')
    dlcSerial.write(mesg)
    pass
def getCurentExecutionTime():
    return time.time()
def clawDirection(_state):
    #0-1-2-3
    mesg = str.encode('dt'+str(_state)+'@')
    dlcSerial.write(mesg)
    pass
def camPos(_state):
    #0-1
    mesg = str.encode('cn'+str(_state)+'@')
    dlcSerial.write(mesg)
    pass
def resetDlc():
    mesg = str.encode('r@')
    dlcSerial.write(mesg)
    pass
def unlockMotors():
    mesg = str.encode('f@')
    genSerial.write(mesg)
    pass
def lockMotors():
    mesg = str.encode('h@')
    genSerial.write(mesg)
    pass
def unlockClaw():
    mesg = str.encode('f@')
    dlcSerial.write(mesg)
    pass
def sleepFor(_seconds):
    time.sleep(_seconds)
    pass
def preCatch(zone):
    if(zone==1):
        catchHeight=1
        sleepHeight=0.5
    elif(zone==2):
        catchHeight=4
        sleepHeight=1.5
    else:
        catchHeight=5
        sleepHeight=2

    lockMotors()
    clawHeight(catchHeight)
    sleepFor(sleepHeight)
    claw(2)
    setMovement(0,20,0)
    sleepFor(2)
    claw(0)
    setMovement(0,-20,0)
    sleepFor(2)
def putToStorage(order):
    # need to move backward first
    if(order==0):
        clawHeight(2)
        sleepFor(0.6)
        clawDirection(3)
        sleepFor(2.6)
        clawHeight(3)
        sleepFor(0.3)
        claw(1)
        sleepFor(0.3)
        clawHeight(2)
        sleepFor(0.3)
        clawDirection(0)
    elif(order==1):
        clawHeight(2)
        sleepFor(0.6)
        clawDirection(2)
        sleepFor(2.3)
        clawHeight(3)
        sleepFor(0.3)
        claw(1)
        sleepFor(0.3)
        clawHeight(2)
        sleepFor(0.3)
        clawDirection(0)
    elif(order==2):
        clawHeight(2)
        sleepFor(0.05)
        clawDirection(1)
        sleepFor(2)
        clawHeight(3)
        sleepFor(0.2)
        claw(1)
        clawHeight(2)
        sleepFor(0.3)
        clawDirection(0)
def click_event(event, x, y, flags, params): 
  
    # checking for left mouse clicks 
    if event == cv2.EVENT_LBUTTONDOWN: 
  
        # displaying the coordinates 
        # on the Shell 
        print(x, ' ', y) 
  
        # displaying the coordinates 
        # on the image window 
        font = cv2.FONT_HERSHEY_SIMPLEX 
        cv2.putText(img, str(x) + ',' +
                    str(y), (x,y), font, 
                    1, (255, 0, 0), 2) 
        cv2.imshow('image', img) 
  
    # checking for right mouse clicks      
    if event==cv2.EVENT_RBUTTONDOWN:
        # displaying the coordinates 
        # on the Shell 
        print(x, ' ', y)
        # displaying the coordinates 
        # on the image window 
        font = cv2.FONT_HERSHEY_SIMPLEX 
        b = img[y, x, 0] 
        g = img[y, x, 1] 
        r = img[y, x, 2] 
        cv2.putText(img, str(b) + ',' +
                    str(g) + ',' + str(r), 
                    (x,y), font, 1, 
                    (255, 255, 0), 2) 
        cv2.imshow('image', img)
def waitForStart():
    while(genSerial.readline()==''):
        pass
    print('start')
    pass
def debugMode():
    mode = 'a'
    while(mode!='quit'):
        mode = raw_input("\
                w-waitForstart\n\
                s-move to position;p-movement;\n\
                l-lockMotors,f-unlock\n\
                x-special;\nj-QRCamForColor\
                \nq-qrcodeCam;t-templateCam\n\
                ps-putToStorage\n\
                o-setSpeed\nquit")
        if(mode == 's'):
            gx,gy,gdir = input('x,'),input('y,'),input('dir')
            gx = float(gx) 
            gy = float(gy)
            gdir =float(gdir)
            gdir = gdir/180.0*pi
            waitUntilMovedTo(gx,gy,gdir)
            print("moved to!\n")
        elif(mode =='f'):
            print('unlockMotors')
            unlockMotors()
            pass
        elif(mode =='ps'):
            print('putToStorage')
            putToStorage()
            pass
        elif(mode =='w'):
            print('waitForStart')
            waitForStart()
            pass
        elif(mode =='p'):
            gx,gy,gdir = input('x,'),input('y,'),input('dir')
            gx = float(gx) 
            gy = float(gy)
            gdir = float(gdir)

            gdir = gdir/180.0*pi
            setMovement(gx,gy,gdir)
        elif(mode =='o'):
            gx,gy,gdir = input('speed,'),input('rotation,'),input('dir')
            gx = int(gx) 
            gy = int(gy)
            gdir = int(gdir)

            gdir = gdir/180.0*pi
            setSpeed(gdir,gx,gy)

        elif(mode =='x'):
            detailMode,__state__ = raw_input('a-claw;b-height;c-dir;d-camPos;e-reset;f-unlockMotor;g-unlockClaw'),raw_input('state')
            __state__ = int(__state__)
            if(detailMode == 'a'):
                claw(__state__)
            elif(detailMode == 'b'):
                clawHeight(__state__)
            elif(detailMode == 'c'):
                clawDirection(__state__)
            elif(detailMode == 'd'):
                camPos(__state__)    
            elif(detailMode == 'e'):
                resetDlc()
            elif(detailMode == 'f'):
                unlockMotors()
            elif(detailMode == 'g'):
                unlockClaw()

            else:
                pass
        elif(mode=='j'):
            _,_img = qrCodeCap.read()
            _,__img = templateCap.read()
            cv2.imshow('qrCamColor',_img)
            cv2.imshow('temColor',__img)
            while(cv2.waitKey(39) != ord('e')):
                _,_img = qrCodeCap.read()
                _,__img = templateCap.read()
                cv2.imshow('qrCamColor',_img)
                cv2.imshow('temColor',__img)
                pass
            cv2.destroyAllWindows()
            pass
        elif(mode=='q'):
            _,_img = qrCodeCap.read()
            getAndSaveQrcode()
            decodeQRCode()
            #cv2.imshow('image',_img)
            #cv2.setMouseCallback('image', click_event)
            #cv2.waitKey(0)
            #cv2.destroyAllWindows()
        pass


#########################################
#test4Template()
#openAndSetCap()

#openGen()
#test1()
if __name__ == "__main__":
    openListener()
    time.sleep(2)
    debugMode()
    templateCap.release()
    qrCodeCap.release()

    pass








#genSerial.close()
#dlcSerial.close()


# while expression:
#     pass



# #1. Move backward for a fixed distance
# x = ser.read()          # read one byte
# s = ser.read(10)        # read up to ten bytes (timeout)
# ...     line = ser.readline()   # read a '\n' terminated line EOL

# #2. take a photo
# ret, frame = templateCap.read()
# cv2.imshow('test',ret)

# #3. cut and resize it


# #4. save it to the correct path
# cv2.waitKey(0)

# templateCap.release()
# cv2.destroyAllWindows()
