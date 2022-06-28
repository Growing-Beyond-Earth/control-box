# GROWING BEYOND EARTH CONTROL BOX
# RASPBERRY PI PICO / MICROPYTHON

# FAIRCHILD TROPICAL BOTANIC GARDEN, JUNE 28, 2022

# The Growing Beyond Earth (GBE) control box is a device that controls
# the LED lights and fan in a GBE growth chamber. It can also control
# accessories including a 12v water pump and environmental sensors. 
# The device is based on a Raspberry Pi Pico microcontroller running 
# Micropython.

# This program (main.py) runs automatically each time the device is
# powered up.



# ----------------SETTINGS FOR LIGHTS AND FAN-------------------

# LIGHTS -- Time values are hh:mm strings based on a 24h clock;  
#           brightness values are integers from 0 to 255 that set the
#           PWM duty cycle. Each channel has an upper limit, noted
#           below, to prevent overheating the LEDs

lights_on_time =  "07:00"
lights_off_time = "19:00"

red_brightness =    72   # Maximum = 200
green_brightness =  60   # Maximum =  89
blue_brightness =   44   # Maximum =  94
white_brightness =  52   # Maximum = 146


# FAN -- Fan power is an integer from 0 to 255 that sets the PWM
#        duty cycle

fan_power_when_lights_on =  255
fan_power_when_lights_off = 128

# --------------------------------------------------------------




# -----------------Load required libraries from /lib/-----------

from sys import stdin, stdout, exit
import machine
from machine import Pin, PWM
import utime, time
from time import sleep
from ds3231 import DS3231  # I2C real time clock
import ina219              # Current sensor
import uselect


# --------------Read unique ID of Raspberry Pi Pico-------------
board_id=""
raw_id = machine.unique_id()
for bval in raw_id : board_id += str((hex(bval)[2:]))


# ----------------Set up status LED on Control Box--------------
led = machine.PWM(machine.Pin(6)); led.freq(1000)


# -------Set up I2C bus 0 for devices inside the control box---

i2c0 = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))
ina = ina219.INA219(0.1,i2c0)   # Current sensor


# -------------Set up real time clock on I2C bus 0--------------
rtc = DS3231(i2c0) # Read Time from I2C RTC
rtc_time_tuple = rtc.DateTime() # Create a tuple with Time from I2C RTC
rtci = machine.RTC()
rtci.datetime([x for x in rtc_time_tuple] + [0]) # Set local Machine time from I2C RTC and add a 0 at the end.
loghour = rtci.datetime()[4] # Set a variable for hourly logging 

# Translate the specified on/off times to seconds since midnight

onh, onm = map(int, lights_on_time.split(':')); on_seconds = (onh*60 + onm) * 60
offh, offm = map(int, lights_off_time.split(':')); off_seconds = (offh*60 + offm) * 60


# ---------------Set up LED and fan control--------------------
# Connect 24v MOSFETs to PWM channels on GPIO Pins 0-4
# Set PWM frequency on all channels

r=machine.PWM(machine.Pin(0)); r.freq(20000)   # Red channel
g=machine.PWM(machine.Pin(1)); g.freq(20000)   # Green channel
b=machine.PWM(machine.Pin(2)); b.freq(20000)   # Blue channel
w=machine.PWM(machine.Pin(3)); w.freq(20000)   # White channel
f=machine.PWM(machine.Pin(4)); f.freq(20000)   # Fan

# Clean up lights in case of a previous crash
r.duty_u16(0)
g.duty_u16(0)
b.duty_u16(0)
w.duty_u16(0)

# Initialize variables for counting fan RPMs
counter = 0
prev_ms = 0


# Setup serial stream
spoll=uselect.poll()
spoll.register(stdin,uselect.POLLIN)


# ----------------------Set up Functions -----------------------

def getRTC():
    # Attempt to read the time from the internal real time clock and
    # catch any errors
    try:
       rtc_dt=rtci.datetime()
       #Debug RTC
    except Exception as e:
      print("An exception has occurred with the RTC: ", e)
     
    rtc_seconds = ((((rtc_dt[4])*60) + rtc_dt[5]) * 60) + rtc_dt[6]
    rtc_ms = time.ticks_ms()

    return rtc_dt, rtc_seconds, rtc_ms

def controlLightsAndFan():
    readtext = read1()
    if readtext:
        # Lights all white for photo
        r.duty_u16(0)
        g.duty_u16(0)
        b.duty_u16(0)
        w.duty_u16(255 * 256)
    elif rtc_seconds >= on_seconds and rtc_seconds < off_seconds:
        # Lights on
        r.duty_u16(int(min(200,red_brightness))*256)   # Maximum brightness = 200
        g.duty_u16(int(min(89,green_brightness))*256)  # Maximum brightness = 89
        b.duty_u16(int(min(94,blue_brightness))*256)   # Maximum brightness = 94
        w.duty_u16(int(min(146,white_brightness))*256) # Maximum brightness = 146
        f.duty_u16(int(min(255,fan_power_when_lights_on)) * 256) # Maximum fan power = 255
    else:
        # Lights off
        r.duty_u16(0)
        g.duty_u16(0)
        b.duty_u16(0)
        w.duty_u16(0)
        f.duty_u16(int(min(255,fan_power_when_lights_off)) * 256)

def pwmLED():
    try:
       for duty in range(45000): led.duty_u16(duty); time.sleep(0.0001)
       for duty in range(45000, 0, -1): led.duty_u16(duty); time.sleep(0.0001)
    

    except Exception as e:
      print("An exception has occurred with the LED: ", e)
      
def GotIrq(pin):
    global counter
    counter += 1

def printStatus():
    try:
        print(board_id + "  " 
              + str(rtc_dt[0]) + "-"
              + str("%02d" % rtc_dt[1]) + "-"
              + str("%02d" % rtc_dt[2])
              + " " + str("%02d" % rtc_dt[4]) + ":"
              + str("%02d" % rtc_dt[5]) + ":"
              + str("%02d" % rtc_dt[6])
              + "  " + str("%3.f" % (r.duty_u16()/256))
              + " " + str("%3.f" % (g.duty_u16()/256))
              + " " + str("%3.f" % (b.duty_u16()/256))
              + " " + str("%3.f" % (w.duty_u16()/256)) + "  "
              + str("%5.2f" % ina.voltage()) + " "
              + str("%4.f" % ina.current()) + " "
              + str("%5.2f" % (ina.power()/1000)) + "  "
              + str("%3.f" % (f.duty_u16()/256)) + " "
              + str("%4.f" % (counter/(rtc_ms-prev_ms)*30000)))
    except Exception as e:
        print("An exception has occurred: ", e)
       
def currentSensor():     
    try:
       ina.configure()
    except:
        print("Error reading from the current sensor", e)
        
def read1():
    # Read data from serial port
    return(stdin.read(1) if spoll.poll(0) else None)


# ----------------------------Main Start----------------------------
# Print information at startup
print("\nGROWING BEYOND EARTH, FAIRCHILD TROPICAL BOTANIC GARDEN\n")

print ("Software release date: 2021-11-19\n")

currentSensor()

print ("-----RPI-PICO-ID -------DATE ----TIME  RED-GRN-BLU-WHT  LED-V---mA-----W  FAN--RPM")

# Set up a trigger to count fan rotations for RPM calculation
p5 = Pin(5, Pin.IN, Pin.PULL_UP)
p5.irq(trigger=Pin.IRQ_FALLING, handler=GotIrq)

#Main Loop    
while True:
    try:
        rtc_dt, rtc_seconds, rtc_ms = getRTC()
        controlLightsAndFan()
        printStatus()
        prev_ms = rtc_ms; counter = 0 # reset fan RPM counter
        if loghour != rtc_dt[4]:
            rtc.DateTime(rtc_dt) # Set the I2C RTC to prevent drift
            loghour = rtc_dt[4]
        pwmLED() # pulse status LED
    except Exception as e:
        print("Failed Main Loop! Trying again: ", e)
    time.sleep(2) # Wait few seconds before repeating

