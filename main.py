# GROWING BEYOND EARTH CONTROL BOX
# RASPBERRY PI PICO / MICROPYTHON

# FAIRCHILD TROPICAL BOTANIC GARDEN, NOVEMBER 4, 2021

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
from ds3231 import DS3231  # Hardware (I2C) real time clock
import ina219              # Current sensor


# ----------------Set up status LED on Control Box--------------
led = machine.PWM(machine.Pin(6))
led.freq(1000)


# -------Set up I2C bus 0 for devices inside the control box---

i2c0 = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))
ina = ina219.INA219(0.1,i2c0)   # Current sensor


# -------------Set up real time clock on I2C bus 0--------------
rtc = DS3231(i2c0) # Read Time from hardware RTC
rtc_time_tuple = rtc.DateTime() # Create a tuple with Time from Hardware RTC
rtci = machine.RTC()
rtci.datetime([x for x in rtc_time_tuple] + [0]) # Set local Machine time from Hardware RTC and add a 0 at the end. 
print(rtci.datetime())


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


# ----------------------Set up Functions -----------------------

def getRTC():
	# Attempt to read the time from the i2c real time clock and
	# catch any errors
	try:
	   rtc_dt=rtci.datetime()
	   #Debug RTC
	except Exception as e:
	  print("An exception has occurred with the RTC: ", e)
	 
	rtc_seconds = ((((rtc_dt[4])*60) + rtc_dt[5]) * 60) + rtc_dt[6]
	#print("Seconds ",rtc_seconds) # Show Seconds 

	return rtc_dt, rtc_seconds

def controlLightsAndFan():
	if rtc_seconds >= on_seconds and rtc_seconds < off_seconds:
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

def printStatus():
    try:
        print(str(rtc_dt[0]) + "-" + str("%02d" % rtc_dt[1]) + "-" + str("%02d" % rtc_dt[2])
              + " " + str(rtc_dt[4]) + ":" + str("%02d" % rtc_dt[5]) + ":" + str("%02d" % rtc_dt[6])
              + "   R=" + str("%3.0f" % (r.duty_u16()/255))
              + "  G=" + str("%3.0f" % (g.duty_u16()/255))
              + "  B=" + str("%3.0f" % (b.duty_u16()/255))
              + "  W=" + str("%3.0f" % (w.duty_u16()/255)) + "   "
              + str("%5.2f" % ina.voltage()) + " V  "
              + str("%4.0f" % ina.current()) + " mA  "
              + str("%5.2f" % (ina.power()/1000)) + " W")
    except Exception as e:
	  print("An exception has occurred: ", e)
       


def currentSensor():     
	try:
	   ina.configure()	
	except:
		print("Error reading from the current sensor", e)    


# ----------------------------Main Start----------------------------
# Print information at startup
print("\nGROWING BEYOND EARTH, FAIRCHILD TROPICAL BOTANIC GARDEN\n")


print ("Raspberry Pi Pico Unique ID:")

board_id=""
raw_id = machine.unique_id()
for bval in raw_id : board_id += str((hex(bval)[2:]))
print (board_id)

print ("\nSoftware release date:\n2021-11-04\n")
print ("Internal clock time:")
print (str(rtci.datetime()[0]) + "-" + str("%02d" % rtci.datetime()[1]) + "-" + str("%02d" % rtci.datetime()[2]) + " " + str("%02d" % rtci.datetime()[4]) + ":" + str("%02d" % rtci.datetime()[5]) + ":" + str("%02d" % rtci.datetime()[6]) + "\n") 
currentSensor()
print ("\n")

#Main Loop    
while True:
	try:
		rtc_dt, rtc_seconds = getRTC()
		controlLightsAndFan()
		printStatus()
		pwmLED()
		time.sleep(2) # Wait few seconds before repeating
	except Exception as e:
		print("Failed Main Loop! Trying again: ", e)
