#!/usr/bin/env python3

## To use the Application the arduino should have the Arduino
## sketch - non_blocking - uploaded and the components should be wired
## up following the circuit diagram. (to be drawn)



def ReadArduino( serialCon ):
    """ Try to read in a value from the Arduino. Sometimes we might read a value from the serial
        port before the arduino has sent anything. In such cases we will wait a small time, and read again.
        Until we pick up our first non empty integer value."""
    while True:
        #print("message1")
        val = serialCon.readline()
        #print(val)
        #print("message2")

        val = cleanThe(str(val))
        if val != '':
            return val


def cleanThe( lineVal ):
    """ The Arduino returns non-clean data back to us.
        We need to remove all the non-integer values to get
        a nice plottable integer value. Will accept '.' unconditionally for now,
        we may have to add conditions later. """
    S = {'1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.'}
    clean = ''
    for char in lineVal:
        if char in S:
            clean += char
    return clean

def drawAxes():
    """ Function used to draw axes on our graph element,
        we will also use it in conjunction with clearing
        the graph as a reset."""
    # Lets draw the axes on our graph
    graph.DrawLine((-100,0), (300,0))
    graph.DrawLine((0,-100), (0,100))
    for x in range(-100, 301, 25):
        graph.DrawLine((x,-3), (x,3))
        if x != 0:
            graph.DrawText(x, (x,-10), font='Helvetica, 7', color='green')
    for y in range(-100, 101, 25):
        graph.DrawLine((-3,y), (3,y))
        if y != 0:
            graph.DrawText(y, (-10,y), font='Helvetica, 7', color='blue')

def readyToWrite( buttonVal, dataConstruct ):
    """This function tests whether we are ready to write data
       to a file. The two conditions are, 1. we aren't still
       collecting data, 2. we have collected a non-zero amount
       of data. There are 3 return values which are used to
       determine which popup window to show the user."""
    if buttonVal != 'Go' and dataConstruct:
        return 'ready'
    elif buttonVal =='Go':
        return 'stillCollecting'
    elif not dataConstruct:
        # We haven't collected any data yet
        return 'noData'



import PySimpleGUI as sg
import serial
from datetime import datetime
import time

## -- Setting up the connection to the Arduino -- ##

sensor = "LightIntensity"
serial_port = '/dev/ttyACM0'
baud_rate = 9600
path = "%s_DATA_%s.txt" % (sensor, datetime.now())
# -- Where we keep our serial object
ser = []

## -- GUI window for connecting to the Arduino
layout = [
                  [sg.Text('Please ensure that the Arduino USB cable is connected.')],
                  [sg.Text('Pressing Ok will attempt to connect to the Arduino. It may take a few attempts to connect.')],
                  [sg.Text('The app will fail to connect if the device is not connected. Note the Arduino may take a few seconds to boot up if it was not connected before you started the Plot App.')],
                  [sg.Text('Attempts made: ', text_color='white'), sg.Text('0', size=(5,1), text_color='white', key='attempts')],
                  [sg.Text('Status : '), sg.Text('No Connection')],
                  [sg.ReadButton('Ok'), sg.ReadButton('Exit')]
                ]

connected = False
window = sg.Window('Arduino Connection').Layout(layout)
attempts = 0
while connected == False:
    print("In connection while loop")
    button, values = window.Read(timeout=300)
    if button in (None, 'Exit'):
        break
    if button == 'Ok':
        try:
            print("Attempting to connect")
            SER = serial.Serial(serial_port, baud_rate, timeout=0.02)
            print(SER)
            connected = True
            ser.append(SER)
        except:
            time.sleep(0.1)
            attempts += 1
            window.FindElement('attempts').Update(attempts)

# Close the window after we've connected, or the user asks to close.
window.close()

# User exited from the GUI connection window by clicking the small x.
if not connected:
    sys.exit(0)


# -- Start of main GUI code -- ##


# layout - write the layout using rows
layout = [[sg.Text('Force: ', size=(15, 1), font='Helvetica, 12'), sg.Text('0', size=(7, 1), font='Helvetica, 12', key='answer')],
          [sg.Graph(canvas_size=(400, 200), graph_bottom_left=(-100, -100), graph_top_right=(300, 100),background_color='white' , key='graph')],
          [sg.Text('Live plot of light intensity vs time', font='Helvetica, 10')],
          # graph_bottom_left=(-5, -5), graph_top_right=(500, 1000)
          [sg.Text()],
          [sg.ReadButton('Go'), sg.ReadButton('Stop'), sg.ReadButton('Erase')],
          [sg.ReadButton('Write'), sg.ReadButton('Upload')] ]

# create the window
window = sg.Window('Flexiforce Sensor Display').Layout(layout).Finalize()
graph = window['graph']

# Draw the axes
drawAxes()

# These variables will be used for controlling the data collection and display process

# -- Curent value of the sensor
sensorVal = [0]
# -- Time we've been receiving data for -- currently just in units, but we probably want this to be in seconds.
timeVal = [0]
# -- Value of the last button pressed on the GUI
buttonVal = ['']
# -- Co-ords of the most recent line point we plot
lineHead = [(0, 0), (0, 0)]


# It would be good if instead of immediately writing data to to a file,
# we could save the data to some kind of construct within python,
# and only write the data to a file, and then upload if the user asks us to from the GUI.
dataConstruct = []


dateObject = datetime.now()
dataConstruct.append(["Data recorded:", " %s-%s-%s \n " % (dateObject.day, dateObject.month, dateObject.year)])
# event loop
# loops and reads button values
while True:
    button, values = window.Read(timeout=80)

    # if the small top corner x is pressed to close the window
    if button is None:
        break

    # lets use the simplest process we can think of, we will start counting up from 0 when Go is pressed,
    # we will stop counting up and reset back to 0 if stop is pressed, and additional presses of Go
    # while already collecting data, will be ignored

    if buttonVal[0] == 'Go':
        # The last time a button was pressed, it was 'Go', so do one unit of sensorVal the input
        line = ReadArduino(ser[0])
        print(line)
        #line = str(ser[0].readline())
        #line = str(cleanThe(line))
        dataConstruct.append([line, " %s " % (datetime.now()).time(), " \n "])
        sensorVal[0] = int(line)
        timeVal[0] += 1
        window.FindElement('answer').Update(sensorVal[0])

        # Update the line head
        lineHead[0] = lineHead[1]
        lineHead[1] = (timeVal[0], sensorVal[0])

        # Then update our plot
        graph.DrawLine((lineHead[0][0], lineHead[0][1]), (lineHead[1][0], lineHead[1][1]))

    if button == 'Go':
        buttonVal = ['Go']
        print(ser[0])
        #ser[0].open()
        val1 = ser[0].readall()
        print(val1)


    if button == 'Stop':
        # Stop drawing the current line and reset our starting point
        sensorVal[0] = 0
        timeVal[0] = 0
        buttonVal[0] = 'Stop'
        lineHead[0] = (0, 0)
        lineHead[1] = (0, 0)
        window.FindElement('answer').Update(0)
        #ser[0].close()

    if button == 'Erase':
        # Erase all the lines we've already drawn on the graph
        sensorVal[0] = 0
        timeVal[0] = 0
        buttonVal[0] = 'Erase'
        graph.Erase()
        drawAxes()
        lineHead[0] = (0, 0)
        lineHead[1] = (0, 0)
        window.FindElement('answer').Update(0)
        dataConstruct.clear()

    if button == 'Write':
        # Are we ready to write data for the test to a file?
        ready = readyToWrite(buttonVal[0], dataConstruct )
        if ready == 'ready':
            with open(path, '+w') as f:
                for x in dataConstruct:
                    f.writelines(x)
        elif ready == 'stillCollecting':
            print("Still collecting data")
            sg.popup_ok('Error: Still collecting data', 'You must stop data collection before writing the data to a file.', 'Press \'Stop\' to stop collecting data.')
        elif ready == 'noData':
            print("No data recorded.")
            sg.popup_ok('Error: No data collected', 'You need to collect some data before writing to a file.', 'Press record and collect data for a period of time, then press stop to collect a data sample')


ser[0].close()
window.close()