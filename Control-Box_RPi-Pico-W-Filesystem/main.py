# GROWING BEYOND EARTH CONTROL BOX
# RASPBERRY PI PICO / MICROPYTHON

# FAIRCHILD TROPICAL BOTANIC GARDEN

software_date = "2023-02-16"

# The Growing Beyond Earth (GBE) control box is a device that controls
# the LED lights and fan in a GBE growth chamber. It can also control
# accessories including a 12v water pump and environmental sensors.
# The device is based on a Raspberry Pi Pico W microcontroller running
# MicroPython.

# This program (main.py) runs automatically each time the device is
# powered up.

print("  ____ ____  _____")
print(" / ___| __ )| ____|   GROWING BEYOND EARTH(R)")
print("| |  _|  _ \|  _|     FAIRCHILD TROPICAL BOTANIC GARDEN")
print("| |_| | |_) | |___    Raspberry Pi Pico W / MicroPython")
print(" \____|____/|_____|   Software release date: " + software_date + "\n\n")


# ------------Load libraries built into MicroPython-------------

from sys import stdin, stdout, exit
import machine
from machine import Pin, PWM
import os
import utime, time
from time import sleep
import random
import json  # JSON for config files
import ubinascii  # Binary/ASCII conversion
import network  # Wifi
import urequests  # Communication with cloud server
import neopixel  # Status LED

try:
    import ntptime  # network time if supported
except:
    print("NTP not supported")


# --------------Read unique ID of Raspberry Pi Pico-------------

board_id = ""
mac_address = None
raw_id = machine.unique_id()
for bval in raw_id:
    board_id += str((hex(bval)[2:]))
try:
    mac_address = ubinascii.hexlify(network.WLAN().config("mac"), ":").decode()
except:
    print("Unable to read device MAC address")


# --------Load extra libraries from /lib/ if available----------

try:
    import gbeformat  # Functions for formatting and validation
except:
    print("gbeformat library not loaded into /lib/")

try:
    from ds3231 import DS3231  # I2C real time clock
except:
    print("ds3231 I2C clock library not loaded into /lib/")

try:
    import ina219  # Current sensor
except:
    print("ina210 I2C current sensor library not loaded into /lib/")

try:
    import seesaw, stemma_soil_sensor  # Soil moisture sensor
except:
    print("Seesaw I2C soil moisture sensor libraries not loaded into /lib/")

try:
    import aht10  # Temperature and humidity sensor
except:
    print("aht10 I2C temperature and humidity sensor libraries not loaded into /lib/")


# ---Load lights, fan, time zone configuration from JSON file---

with open("/config/gbe_settings.json") as settings_file:
    config = json.load(settings_file)
    settings_file.close()

# -----------Set up status LED and do a magenta pulse------------

np = neopixel.NeoPixel(machine.Pin(6), 1)
npc = {
    "red": [0, 1, 0],
    "green": [1, 0, 0],
    "blue": [0, 0, 1],
    "yellow": [0.6, 1, 0],
    "cyan": [0.8, 0, 0.8],
    "magenta": [0, 0.8, 0.8],
    "white": [0.6, 0.6, 0.6],
}

for val in range(255):
    np[0] = [0, val, val]
    np.write()
    time.sleep(0.002)
for val in range(255, -1, -1):
    np[0] = [0, val, val]
    np.write()
    time.sleep(0.002)


# ---------------------Set up networking------------------------

try:
    with open("/config/wifi_settings.json") as wifi_file:
        wifi_config = json.load(wifi_file)
        wifi_file.close()
except:
    print("Wifi settings not loaded")

try:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(wifi_config["NETWORK_NAME"], wifi_config["NETWORK_PASSWORD"])
except:
    print("Unable to connect to wifi")


# -----------Contact GBE cloud if wifi is connected-------------
device_name = None
startup_message = None
if wlan.isconnected():
    try:
        result = urequests.get(
            "http://growingbeyond.earth/phonehome.php?boa=" + board_id + "&mac=" + mac_address + "&sof=" + software_date
        )
        cloudinfo = json.loads(result.text)
        device_name = cloudinfo['site_name']
        startup_message = cloudinfo['startup_message']
        print("Connected to GBE Cloud")
    except:
        print("Unable to connect to GBE Cloud")


# -------Set up I2C bus 0 for devices inside the control box----

i2c0 = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))

try:
    ina = ina219.INA219(0.1, i2c0)
    ina.configure()
    print("Connected to LED panel current sensor")
except:
    ina = False


# ----Set up I2C bus 1 for devices outside the control box-------

i2c1 = machine.I2C(1, sda=machine.Pin(18), scl=machine.Pin(19), freq=400000)

try:
    seesaw = stemma_soil_sensor.StemmaSoilSensor(i2c1)
    print("Connected to external soil moisture sensor")
except:
    seesaw = False

try:
    aht10 = aht10.AHT10(i2c1)
    print("Connected to external temperature and humidity sensor")
except:
    aht10 = False


# ---Set internal clock using network time or I2C realtime clock---

try:  # get local time from I2C RTC
    rtc = DS3231(i2c0)
    lt = [x for x in rtc.DateTime()] + [0]
except:
    rtc = False

# Use internal clock if its time is already set
if machine.RTC().datetime()[0] > 2021:
    lt = list(machine.RTC().datetime())

try:  # Use network time if available
    ntptime.settime()  # Set the internal RTC time to the network time in UTC
    ct = time.localtime(
        time.time() + (config["time zone"]["GMT offset"]) * 3600
    )  # Correct time for local time zone
    lt = [
        ct[0],
        ct[1],
        ct[2],
        ct[6],
        ct[3],
        ct[4],
        ct[5],
        0,
    ]  # Format time for setting RTC
    ntp = True
except:
    ntp = False

try:
    machine.RTC().datetime(lt)  # Set internal clock with best available time
except:
    lt = False

try:
    rtc.DateTime(machine.RTC().datetime())  # Set I2C RTC
except:
    rtc = False

if rtc:
    print("Connected to internal battery-powered clock")
if ntp:
    print("Connected to network time")
if lt:
    print("Clock set\n")


# ---------------Set up variables for logging--------------------

loghour = machine.RTC().datetime()[4]
log_avg = {
    "ent": 0,
    "red": 0,
    "gre": 0,
    "blu": 0,
    "whi": 0,
    "vol": 0,
    "mam": 0,
    "wat": 0,
    "fan": 0,
    "rpm": 0,
    "tem": 0,
    "hum": 0,
    "sst": 0,
    "ssm": 0,
}
sched = [{}]

# ---------------Set up LED and fan control--------------------
# Connect 24v MOSFETs to PWM channels on GPIO Pins 0-4
# Set PWM frequency on all channels

r = machine.PWM(machine.Pin(0))
r.freq(20000)  # Red channel
g = machine.PWM(machine.Pin(1))
g.freq(20000)  # Green channel
b = machine.PWM(machine.Pin(2))
b.freq(20000)  # Blue channel
w = machine.PWM(machine.Pin(3))
w.freq(20000)  # White channel
f = machine.PWM(machine.Pin(4))
f.freq(20000)  # Fan

# Initialize variables for counting fan RPMs
counter = 0
prev_ms = 0

# Clean up lights in case of a previous crash
r.duty_u16(0)
g.duty_u16(0)
b.duty_u16(0)
w.duty_u16(0)


# ----------------------Set up Functions -----------------------


def getRTC():
    # Read the time from the internal clock
    rtc_dt = machine.RTC().datetime()
    rtc_seconds = ((((rtc_dt[4]) * 60) + rtc_dt[5]) * 60) + rtc_dt[6]
    rtc_ms = time.ticks_ms()
    return rtc_dt, rtc_seconds, rtc_ms


def updateRTC(ntp):
    if wlan.isconnected() and ntp == False:
        try:  # Use network time if available
            ntptime.settime()  # Set the internal RTC time to the network time in UTC
            ct = time.localtime(
                time.time() - (abs(config["time zone"]["GMT offset"])) * 3600
            )  # Correct time for local time zone
            lt = [
                ct[0],
                ct[1],
                ct[2],
                ct[6],
                ct[3],
                ct[4],
                ct[5],
                0,
            ]  # Format time for setting RTC
            machine.RTC().datetime(lt)  # Set internal clock
        except:
            ntp = False

    try:
        rtc.DateTime(
            machine.RTC().datetime()
        )  # Set I2C RTC -- Done hourly to prevent drift
    except:
        rtc = False


def toSeconds(input_time):
    # Convert entered time from HH:MM to seconds since midnight
    inH, inM = map(int, input_time.split(":"))
    return (inH * 60 + inM) * 60


def controlLightsAndFan():
    if rtc_seconds >= toSeconds(
        config["lights"]["timer"]["on"]
    ) and rtc_seconds < toSeconds(config["lights"]["timer"]["off"]):
        # Lights on
        r.duty_u16(
            int(min(200, config["lights"]["duty"]["red"])) * 256
        )  # Maximum brightness = 200
        g.duty_u16(
            int(min(89, config["lights"]["duty"]["green"])) * 256
        )  #  Maximum brightness = 89
        b.duty_u16(
            int(min(94, config["lights"]["duty"]["blue"])) * 256
        )  #  Maximum brightness = 94
        w.duty_u16(
            int(min(146, config["lights"]["duty"]["white"])) * 256
        )  #  Maximum brightness = 146
        f.duty_u16(
            int(min(255, config["fan"]["duty"]["when lights on"])) * 256
        )  # Maximum fan power = 255
    else:
        # Lights off
        r.duty_u16(0)
        g.duty_u16(0)
        b.duty_u16(0)
        w.duty_u16(0)
        f.duty_u16(int(min(255, config["fan"]["duty"]["when lights off"])) * 256)


def steadyLED(color):
    np[0] = tuple([int(rgb * 255) for rgb in npc[color]])
    np.write()  # Status LED on


def pulseLED(color):  # Pulse the status LED with breathing effect
    try:
        for val in range(255):
            np[0] = tuple([int(rgb * val) for rgb in npc[color]])
            np.write()
            time.sleep(0.004)
        for val in range(255, -1, -1):
            np[0] = tuple([int(rgb * val) for rgb in npc[color]])
            np.write()
            time.sleep(0.004)
    except Exception as e:
        print("An exception has occurred with the status LED: ", e)


def fanPulse(pin):  # Count fan rotation, triggered twice per rotation
    global counter
    counter += 1


def tryGetINA():  # Read current sensor
    try:
        return ina.voltage(), ina.current(), ina.power()
    except:
        return 0, 0, 0


def tryGetSeesaw():  # Read soil moisture & temp sensor
    try:
        return seesaw.get_moisture(), seesaw.get_temp()
    except:
        return 0, 0


def tryGetAHT10():  # Read temperature & humidity sensor
    try:
        return aht10.temperature(), aht10.humidity()
    except:
        return 0, 0


def getStatus():
    vol, mam, mwa = tryGetINA()  # Read current sensor
    ssm, sst = tryGetSeesaw()  # Read soil moisture & temp sensor
    tem, hum = tryGetAHT10()  # Read temperature & humidity sensor

    return {
        "boa": board_id,  # Unique ID of Raspberry Pi Pico
        "sof": software_date,
        "tim": time.time(),  # Local time
        "yea": rtc_dt[0],  # Current year
        "mon": rtc_dt[1],  # Current month
        "day": rtc_dt[2],  # Current day
        "hou": rtc_dt[4],  # Current hour, local time
        "min": rtc_dt[5],  # Current minute, local time
        "sec": rtc_dt[6],  # Current second, local time
        "red": round(r.duty_u16() / 256),  # Red LED channel brightness
        "gre": round(g.duty_u16() / 256),  # Green LED channel brightness
        "blu": round(b.duty_u16() / 256),  # Blue LED channel brightness
        "whi": round(w.duty_u16() / 256),  # White LED channel brightness
        "vol": round(vol, 2),  # Sensor: INA219 voltage
        "mam": round(mam),  # Sensor: INA219 current (milliamps)
        "wat": round(mwa / 1000, 2),  # Sensor: INA219 power (watts)
        "fan": round(f.duty_u16() / 256),  # Fan speed setting
        "ssm": round(ssm),  # Sensor: Seesaw I2C soil moisture
        "sst": round(sst, 2),  # Sensor: Seesaw I2C temperature
        "tem": round(tem, 2),  # Sensor: AHT10 I2C temperature
        "hum": round(hum, 2),  # Sensor: AHT10 I2C humidity
        "rpm": counter / (rtc_ms - prev_ms) * 30000,  # Sensor: Fan RPM
        "con": config["lights"]["timer"]["on"],  # Config: Lights on time
        "cof": config["lights"]["timer"]["off"],  # Config: Lights off time
        "cf0": config["fan"]["duty"]["when lights off"],  # Config: Nighttime fan speed
        "cf1": config["fan"]["duty"]["when lights on"],  # Config: Daytime fan speed
        "cre": config["lights"]["duty"]["red"],  # Config: Red LED brightness
        "cgr": config["lights"]["duty"]["green"],  # Config: Green LED brightness
        "cbl": config["lights"]["duty"]["blue"],  # Config: Blue LED brightness
        "cwh": config["lights"]["duty"]["white"],  # Config: White LED brightness
        "ctz": config["time zone"]["GMT offset"]  # Config: Time zone
    }


# Remove old log files, keeping the specified number
def cleanLogs(keep_number):
    try:
        log_list = os.listdir("logs")
        del_files = range(len(log_list) - keep_number)
        for idx in del_files:
            os.remove("logs/" + log_list[idx])
    except:
        print("Error cleaning up log files:", e)


# Check to see if a file exists
def fileExists(filename):
    try:
        os.stat(filename)
        return True
    except OSError:
        return False


# ----------------------------Main Start----------------------------
# Print information at startup
net = wlan.ifconfig()

if device_name:
    print("Device name:    " + device_name)
print("Hardware ID:    " + board_id)
if mac_address:
    print("MAC address:    " + mac_address)
print("IP Address:     " + net[0] + "\n")

if startup_message:
    print("Note: " + startup_message + "\n\n" +
          "      Run 'SETUP.PY' to set up wifi and program the lights and fan.")
else: print("Note: Run 'SETUP.PY' to set up wifi and program the lights and fan.")
print("      Check the 'logs' directory for hourly log entries.")
print("      More info @ http://growingbeyond.earth/device/" + board_id + "\n\n")

print(
    "------DATE ----TIME  RED-GRN-BLU-WHT  LED-V---mA-----W  FAN--RPM  -TEMP--HUMI-MOIS"
)

# Set up a trigger to count fan rotations for RPM calculation
p5 = Pin(5, Pin.IN, Pin.PULL_UP)
p5.irq(trigger=Pin.IRQ_FALLING, handler=fanPulse)

# Main Loop
while True:
    try:
        rtc_dt, rtc_seconds, rtc_ms = getRTC()
        controlLightsAndFan()

        status_now = getStatus()  # Read settings and sensor data
        prev_ms = rtc_ms
        counter = 0  # Reset fan RPM counter

        print(gbeformat.columns(status_now))  # Print status to the shell

        # If power is coming from USB, assume a computer is connected and halt program execution
        if log_avg["ent"] == 0 and status_now["vol"] < 18 and ina:
            print(
                "\n\n24v power not detected. Ending program to allow access to the filesystem . . .\n"
            )
            steadyLED("green")
            break

        # Calculate running average of sensor readings
        if (
            log_avg["ent"] > 0
        ):  # Skip the first sensor readings to let fan RPMs stabilize
            for idx, dic in enumerate(log_avg):
                if dic != "ent":
                    log_avg[dic] = round(
                        (log_avg[dic] * (log_avg["ent"] - 1) + status_now[dic])
                        / log_avg["ent"],
                        2,
                    )
        log_avg["ent"] += 1

        # If wifi is connected, upload hourly log and update clock at specified time, looping through
        # cached log entries. If upload fails, do not try again until a new entry is appended.
        if (
            wlan.isconnected()
            and "time" in sched[-1]
            and sched[-1]["time"] < time.time()
            and not sched[-1]["tried"]
        ):
            try:
                sched[-1]["tried"] = True
                for cache in sched:
                    result = urequests.get(
                        "http://growingbeyond.earth/log.php?" + cache["url"]
                    )
                    # Parse incoming JSON and update gbe_settings.json if valid
                    incoming_config = json.loads(result.text)
                    if gbeformat.valid_config(incoming_config):
                        config = incoming_config
                        settings_file = open("/config/gbe_settings.json", "w")
                        settings_file.write(json.dumps(config))
                        settings_file.close()
                    sched.pop(0)  # Remove the uploaded entry from the scheduled uploads
                    time.sleep(0.5)
                sched = [{}]
            except:
                while True:
                    if len(sched) > 48:
                        sched.pop(0)  # Cache http requests for 48 hours
                    else:
                        break
            updateRTC(ntp)

        # ----------Hourly log updates and clock maintenance-------------
        if loghour != rtc_dt[4]:
            loghour = rtc_dt[4]

            # write hourly log to today's log file
            try:
                logfile_path = "logs/" + gbeformat.ymd(status_now) + ".txt"
                if not fileExists(logfile_path):
                    logfile = open(logfile_path, "a")
                    logfile.write(gbeformat.hourlog_head() + "\n")
                    logfile.close()
                logfile = open(logfile_path, "a")
                logfile.write(gbeformat.hourlog(status_now, log_avg) + "\n")
                logfile.close()
            except:
                print("Error saving the log file:", e)

            # Schedule log upload and clock update for a random time in the next two minutes
            # to avoid having all devices hit the GBE and NTP servers at the same time
            # Use a list to cache http requests in RAM in case wifi is down temporarily
            if "time" in sched[-1]:
                sched.append({})
            sched[-1]["time"] = time.time() + random.randint(0, 120)
            sched[-1]["url"] = gbeformat.url_query(status_now, log_avg)
            sched[-1]["tried"] = False

            cleanLogs(30)  # Remove old log files, keeping 30

            for idx, dic in enumerate(log_avg):
                log_avg[dic] = 0  # Reset running averages

        if wlan.isconnected():
            pulseLED("blue")  # Pulse status LED
        else:
            pulseLED("white")

    except Exception as e:  # Catch-all error handler
        print("Failed Main Loop! Trying again: ", e)

    time.sleep(2)  # Wait few seconds before repeating
