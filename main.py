# GROWING BEYOND EARTH CONTROL BOX
# RASPBERRY PI PICO / MICROPYTHON

# FAIRCHILD TROPICAL BOTANIC GARDEN, SEPTEMBER 29, 2021

# The Growing Beyond Earth (GBE) control box is a device that controls
# the LED lights and fan in a GBE growth chamber. It can also control
# accessories including a 12v water pump and environmental sensors. 
# The device is based on a Raspberry Pi Pico microcontroller running 
# Micropython.

# This program (main.py) runs automatically each time the device is
# powered up.

# -----------------------------------------------------------

# DEFAULT SETTINGS FOR LIGHTS AND FAN
# LIGHTS -- Time values are hh:mm strings based on a 24h clock;  
#           brightness values are integers from 0 to 255 that set the
#           PWM duty cycle

lights_on_time = "07:00"
lights_off_time = "19:00"

red_brightness = 72
green_brightness = 60
blue_brightness = 44
white_brightness = 52


# FAN -- Fan power is an integer from 0 to 255 that sets the PWM
#        duty cycle

fan_power_when_lights_on = 255
fan_power_when_lights_off = 128

# -----------------------------------------------------------




# Load required libraries from /lib/

from sys import stdin, stdout, exit
import machine
import time
import utime
import ds3231              # Hardware real time clock
import ina219              # Current sensor


# Status LED 
led = machine.PWM(machine.Pin(6))
led.freq(1000)


# Set up I2C bus 0 for devices inside the control box

i2c0 = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))

ina = ina219.INA219(0.1,i2c0)   # Current sensor


# Set up LED and fan control
# Connect 24v MOSFETs to PWM channels on GPIO Pins 0-4
# Set PWM frequency on all channels

r=machine.PWM(machine.Pin(0)); r.freq(20000)   # Red channel
g=machine.PWM(machine.Pin(1)); g.freq(20000)   # Green channel
b=machine.PWM(machine.Pin(2)); b.freq(20000)   # Blue channel
w=machine.PWM(machine.Pin(3)); w.freq(20000)   # White channel
f=machine.PWM(machine.Pin(4)); f.freq(20000)   # Fan

#Clean up lights in case of a crash
r.duty_u16(0)
g.duty_u16(0)
b.duty_u16(0)
w.duty_u16(0)


# Set up time Real time clock
rtc=ds3231.DS3231(i2c0) #read Time from Hardware RTC
rtc_time_tuple = rtc.DateTime() #Create a string with Time from Hardware RTC
rtci = machine.RTC()
rtci.datetime([x for x in rtc_time_tuple] + [0]) #Set local Machine time from Hardware RTC and add a 0 at the end. 

# Translate the specified on/off times to seconds since midnight

onh, onm = map(int, lights_on_time.split(':')); on_seconds = (onh*60 + onm) * 60
offh, offm = map(int, lights_off_time.split(':')); off_seconds = (offh*60 + offm) * 60


# Print information at startup

print("\nGROWING BEYOND EARTH, FAIRCHILD TROPICAL BOTANIC GARDEN\n")

print ("Software release date:\n     2021-9-29\n")

print ("Internal clock time:")
print ("     " + str(rtci.datetime()[0]) + "-" + str(rtci.datetime()[1]) + "-" + str(rtci.datetime()[2]) + "   " + str(rtci.datetime()[4]) + ":" + str(rtci.datetime()[5]) + ":" + str(rtci.datetime()[6]) + "\n") 

# Read from the i2c current sensor

try:
    ina.configure()

    print("Voltage/current/power sensor readings:")
    print("     Bus Voltage: %.3f V" % ina.voltage())
    print("     Current: %.3f mA" % ina.current())
    print("     Power: %.3f mW" % ina.power())
    
except:
    print("Error reading from the current sensor")


# The main loop repeats every second

while True:    
    # Attempt to read the time from the hardware (i2c) real time clock and
    # catch any errors
      
    try:
       rtc_dt=rtci.datetime()
    except:
      print("An exception has occurred with the internal RTC")
   
     
    rtc_seconds = ((((rtc_dt[4])*60) + rtc_dt[5]) * 60) + rtc_dt[6]
        
    # Control lights and fan according to schedule
       
    if rtc_seconds >= on_seconds and rtc_seconds < off_seconds:
        # Lights on
        r.duty_u16(int(red_brightness)*256)
        g.duty_u16(int(green_brightness)*256)
        b.duty_u16(int(blue_brightness)*256)
        w.duty_u16(int(white_brightness)*256)
        f.duty_u16(fan_power_when_lights_on * 256)
    else:
        # Lights off
        r.duty_u16(int(red_brightness)*0)
        g.duty_u16(int(green_brightness)*0)
        b.duty_u16(int(blue_brightness)*0)
        w.duty_u16(int(white_brightness)*0)
        f.duty_u16(fan_power_when_lights_off * 256)

    # fade status LED on & off three times
    for blink in range(3):
        for duty in range(45000): led.duty_u16(duty); time.sleep(0.0001)
        for duty in range(45000, 0, -1): led.duty_u16(duty); time.sleep(0.0001)
    
