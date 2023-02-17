# GROWING BEYOND EARTH CONTROL BOX
# RASPBERRY PI PICO / MICROPYTHON

# FAIRCHILD TROPICAL BOTANIC GARDEN

software_date = "2023-02-16"

# Run this program to set up the GBE Control Box

import neopixel
import network
import time
import json
import re


def isValidTime(time):
    regex = "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    p = re.compile(regex)
    if time == "":
        return False
    m = re.search(p, time)
    if m is None:
        return False
    else:
        return True


np = neopixel.NeoPixel(machine.Pin(6), 1)
np[0] = [128, 255, 0]
np.write()  # Status LED on


print("\n\n\n\n\n\n\n\n\n\n")
print("  ____ ____  _____")
print(" / ___| __ )| ____|   GROWING BEYOND EARTH(R)")
print("| |  _|  _ \|  _|     FAIRCHILD TROPICAL BOTANIC GARDEN")
print("| |_| | |_) | |___    Raspberry Pi Pico W / MicroPython")
print(" \____|____/|_____|   Software release date: " + software_date + "\n\n")
print("N E T W O R K   A N D   H A R D W A R E    S E T U P\n\n")


while True:
    print("Select an option:\n")
    print("1. Set up wifi")
    print("2. Select time zone")
    print("3. Configure lights and fan")
    print("4. Reset lights and fan to factory settings")
    print("5. Quit\n")

    choose = input("Click below and enter 1, 2, 3, 4, or 5:\n")

    if choose == str(1):
        while True:
            SSID = input("\n1. Enter the name of your wireless access point (SSID):\n")
            if SSID:
                break
        while True:
            PASS = input("\n2. Enter the password for " + SSID + ":\n")
            if PASS:
                break
        cred = {"NETWORK_NAME": SSID, "NETWORK_PASSWORD": PASS}
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.disconnect()
        wlan.connect(SSID, PASS)

        tryNum = 0
        while not wlan.isconnected():
            print("\nConnecting...")
            np[0] = [128, 255, 0]
            np.write()
            time.sleep(0.5)  # Status LED blink yellow
            np[0] = [0, 0, 0]
            np.write()
            time.sleep(0.5)
            tryNum += 1
            if tryNum > 9:
                print("\nUnable to connect to '" + SSID + "'")
                break

        if wlan.isconnected():
            print("\nConnected to '" + SSID + "'")
            np[0] = [0, 0, 255]
            np.write()  # Status LED blue
            wifi_json_file = open("/config/wifi_settings.json", "w")
            wifi_json_file.write(json.dumps(cred))
            wifi_json_file.close()
            print("\n--> Wifi settings have been saved.\n\n")

    elif choose == str(2):
        with open("/config/gbe_settings.json") as settings_file:
            config = json.load(settings_file)
            settings_file.close()

        print(
            "\nInput your time zone as a GMT offset (positive or negative integer). Examples from the USA:\n "
        )
        print("Atlantic:  -4")
        print("Eastern :  -5    Eastern Daylight Savings : -4")
        print("Central :  -6    Central Daylight Savings : -5")
        print("Mountain:  -7    Mountain Daylight Savings: -6")
        print("Pacific :  -8    Pacific Daylight Savings : -7")
        print("Alaska  :  -9    Alaska Daylight Savings  : -8")
        print("Aleutian: -10    Aleutian Daylight Savings: -9")
        print("Hawaii  : -10\n")
        ctz = input(
            "Enter your time zone offset or leave blank to keep the current setting ("
            + str(config["time zone"]["GMT offset"])
            + "):\n"
        )
        try:
            if int(ctz) >= -11 and int(ctz) <= 13:
                config["time zone"]["GMT offset"] = int(ctz)
        except:
            ctz = False

        if ctz:
            settings_file = open("/config/gbe_settings.json", "w")
            settings_file.write(json.dumps(config))
            settings_file.close()
            print("\n--> Time zone set to " + ctz + ".\n")

    elif choose == str(3):
        with open("/config/gbe_settings.json") as settings_file:
            config = json.load(settings_file)
            settings_file.close()

        con = input(
            "\nEnter the lights ON time as HH:MM, or leave blank to keep the current setting ("
            + config["lights"]["timer"]["on"]
            + "):\n"
        )
        cof = input(
            "\nEnter the lights OFF time as HH:MM, or leave blank to keep the current setting ("
            + config["lights"]["timer"]["off"]
            + "):\n"
        )

        cre = input(
            "\nEnter the red light brightness (duty cycle) as an integer from 0 to 200,\nor leave blank to keep the current setting ("
            + str(config["lights"]["duty"]["red"])
            + "):\n"
        )
        cgr = input(
            "\nEnter the green light brightness (duty cycle) as an integer from 0 to 89,\nor leave blank to keep the current setting ("
            + str(config["lights"]["duty"]["green"])
            + "):\n"
        )
        cbl = input(
            "\nEnter the blue light brightness (duty cycle) as an integer from 0 to 94,\nor leave blank to keep the current setting ("
            + str(config["lights"]["duty"]["blue"])
            + "):\n"
        )
        cwh = input(
            "\nEnter the white light brightness (duty cycle) as an integer from 0 to 146,\nor leave blank to keep the current setting ("
            + str(config["lights"]["duty"]["white"])
            + "):\n"
        )

        cf1 = input(
            "\nEnter the fan power (duty cycle) setting to use when the lights are ON\nas an integer from 0 to 255, or leave blank to keep the current setting ("
            + str(config["fan"]["duty"]["when lights on"])
            + "):\n"
        )
        cf0 = input(
            "\nEnter the fan power (duty cycle) setting to use when the lights are OFF\nas an integer from 0 to 255, or leave blank to keep the current setting ("
            + str(config["fan"]["duty"]["when lights off"])
            + "):\n"
        )

        try:
            if isValidTime(con):
                config["lights"]["timer"]["on"] = con
        except:
            con = False
        try:
            if isValidTime(cof):
                config["lights"]["timer"]["off"] = cof
        except:
            cof = False

        try:
            if int(cre) >= 0 and int(cre) <= 200:
                config["lights"]["duty"]["red"] = int(cre)
        except:
            cre = False
        try:
            if int(cgr) >= 0 and int(cgr) <= 89:
                config["lights"]["duty"]["green"] = int(cgr)
        except:
            cgr = False
        try:
            if int(cbl) >= 0 and int(cbl) <= 94:
                config["lights"]["duty"]["blue"] = int(cbl)
        except:
            cbl = False
        try:
            if int(cwh) >= 0 and int(cwh) <= 146:
                config["lights"]["duty"]["white"] = int(cwh)
        except:
            cwh = False
        try:
            if int(cf1) >= 0 and int(cf1) <= 255:
                config["fan"]["duty"]["when lights on"] = int(cf1)
        except:
            cf1 = False
        try:
            if int(cf0) >= 0 and int(cf0) <= 255:
                config["fan"]["duty"]["when lights off"] = int(cf0)
        except:
            cf0 = False

        settings_file = open("/config/gbe_settings.json", "w")
        settings_file.write(json.dumps(config))
        settings_file.close()
        print("\n--> Settings for lights and fan saved\n")

    elif choose == str(4):
        with open("/config/gbe_settings.json") as settings_file:
            config = json.load(settings_file)
            settings_file.close()

        config["lights"]["timer"]["on"] = "07:00"
        config["lights"]["timer"]["off"] = "19:00"
        config["lights"]["duty"]["red"] = 72
        config["lights"]["duty"]["green"] = 60
        config["lights"]["duty"]["blue"] = 52
        config["lights"]["duty"]["white"] = 44
        config["fan"]["duty"]["when lights on"] = 255
        config["fan"]["duty"]["when lights off"] = 128

        settings_file = open("/config/gbe_settings.json", "w")
        settings_file.write(json.dumps(config))
        settings_file.close()
        print("\n--> Lights and fan set to factory settings\n")

    elif choose == str(5):
        np[0] = [255, 0, 0]
        np.write()  # Status LED green
        break
