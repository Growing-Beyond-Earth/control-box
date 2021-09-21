# GROWNG BEYOND EARTH CONTROL BOX
# RASPBERRY PI PICO / MICROPYTHON

# FAIRCHILD TROPICAL BOTANIC GARDEN, JULY 9, 2021

# The Growing Beyond Earth (GBE) control box is a device that controls
# the LED lights and fan in a GBE growth chamber. It can also control
# accessories including a 12v water pump and environmental sensors. 
# The device is based on a Raspberry Pi Pico microcontroller running 
# Micropython.

# This program (main.py) runs automatically each time the device is
# powered up.  


# -----------------------------------------------------------

# DEFAULT SETTINGS FOR LIGHTS, FAN, AND WATER PUMP


# LIGHTS -- Time values are hh:mm strings based on a 24h clock;  
#           brightness values are integers from 0 to 255 that set the
#           PWM duty cycle

lights_on_time = "07:00"
lights_off_time = "19:00"

red_brightness = 50
green_brightness = 30
blue_brightness = 50
white_brightness = 100


# FAN -- Fan power is an integer from 0 to 255 that sets the PWM
#        duty cycle

fan_power_when_lights_on = 255
fan_power_when_lights_off = 128


# WATER PUMP -- Sets satering times each day based on a
#               24h clock as a string in hh:mm format

pump_run_times = ["0:00", "6:00", "12:00", "18:00"]
soil_moisture_min = 650
pump_volume_mL = 100


# -----------------------------------------------------------


loghour=""

# Load required libraries from /lib/

from sys import stdin, stdout, exit
import machine
import utime
import time
import ds3231                       # Real time clock library
import seesaw, stemma_soil_sensor  # i2C soil moisture sensor library
import ina219                      # current sensor library


# Set up I2C bus 0 for devices inside the control box

i2c0 = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))
rtc=ds3231.DS3231(i2c0)       # Real time clock
ina = ina219.INA219(0.1,i2c0)   # Current sensor


# Set up I2C bus 1 for devices outside the control box

i2c1 = machine.I2C(1, sda=machine.Pin(26), scl=machine.Pin(27), freq=400000)
seesaw = stemma_soil_sensor.StemmaSoilSensor(i2c1)   # Soil moisture sensor


# Set up LED and fan control
# Connect 24v MOSFETs to PWM channels on GPIO Pins 0-4
# Set PWM frequency on all channels

r=machine.PWM(machine.Pin(0)); r.freq(20000)   # Red channel
g=machine.PWM(machine.Pin(2)); g.freq(20000)   # Green channel
b=machine.PWM(machine.Pin(1)); b.freq(20000)   # Blue channel
w=machine.PWM(machine.Pin(3)); w.freq(20000)   # White channel
f=machine.PWM(machine.Pin(4)); f.freq(20000)   # Fan


# Connect 12v MOSFET to GPIO Pin 6 for on/off control of water pump

pump=machine.Pin(6, machine.Pin.OUT)


# Translate the specified on/off times for lights and water pump
# to seconds since midnight

onh, onm = map(int, lights_on_time.split(':')); on_seconds = (onh*60 + onm) * 60
offh, offm = map(int, lights_off_time.split(':')); off_seconds = (offh*60 + offm) * 60

pump_on_seconds = []; pump_off_seconds = []

for t in range(len(pump_run_times)):
    pumph, pumpm = map(int, pump_run_times[t].split(':'))
    pump_on_seconds.insert(t, (pumph*60 + pumpm) * 60)

    # Determine how long to run pump based on volume specified.
    # Peristaltic pump flow rate = 100 mL per minute

    pump_off_seconds.insert(t, (int(pump_on_seconds[t] + ((pump_volume_mL / 100) * 60))))



# The main loop repeats every second

while True:
    
    # Attempt to read the time from the i2c real time clock and
    # catch any errors
      
    try:
       rtc_dt=rtc.DateTime()
    except:
      print("An exception has occurred with the RTC")
     
    rtc_seconds = ((((rtc_dt[4])*60) + rtc_dt[5]) * 60) + rtc_dt[6]
     

    #    rtc_dt=utime.localtime()
    #    rtc_seconds = ((((rtc_dt[3])*60) + rtc_dt[4]) * 60) + rtc_dt[5]
    
    
    # Control lights and fan accoding to schedule
       
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
    
    
    # Control water pump accoding to schedule
    
    try:
        moisture = seesaw.get_moisture()
    except:
        moisture = 1000
        print("An exception has occurred with the moisture sensor")
    
    for t in range(len(pump_on_seconds)):
        if rtc_seconds >= pump_on_seconds[t] and rtc_seconds < pump_off_seconds[t] and moisture < soil_moisture_min:
             pump.value(1)  # Pump on
             break
        else:
             pump.value(0)  # Pump off

    if loghour != rtc_dt[4]:
        loghour = rtc_dt[4]
        logf=open("log.txt", "a")
        logf.write(str(rtc_dt[4]) + ":" + str(rtc_dt[5]) + ":" + str(rtc_dt[6]) + " Soil Moisture: " + str(moisture) + "\n")
        logf.close()

    print(str(rtc_dt[4]) + ":" + str(rtc_dt[5]) + ":" + str(rtc_dt[6]) + " Soil Moisture: " + str(moisture) + "\n")

    time.sleep(1) # Wait 1 second before repeating
    
    
