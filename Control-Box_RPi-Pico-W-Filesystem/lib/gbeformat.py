# GROWING BEYOND EARTH CONTROL BOX
# RASPBERRY PI PICO / MICROPYTHON

# FAIRCHILD TROPICAL BOTANIC GARDEN, FEBRUARY 16, 2023


import re


def columns(stat):
    if stat["tem"] == 0:
        stat["tem"] = stat["sst"]
    return (
        str(stat["yea"])
        + "-"
        + str("%02d" % stat["mon"])
        + "-"
        + str("%02d" % stat["day"])
        + " "
        + str("%02d" % stat["hou"])
        + ":"
        + str("%02d" % stat["min"])
        + ":"
        + str("%02d" % stat["sec"])
        + "  "
        + str("%3.f" % stat["red"])
        + " "
        + str("%3.f" % stat["gre"])
        + " "
        + str("%3.f" % stat["blu"])
        + " "
        + str("%3.f" % stat["whi"])
        + "  "
        + str("%5.2f" % stat["vol"])
        + " "
        + str("%4.f" % stat["mam"])
        + " "
        + str("%5.2f" % stat["wat"])
        + "  "
        + str("%3.f" % stat["fan"])
        + " "
        + str("%4.f" % stat["rpm"])
        + "  "
        + str("%5.2f" % stat["tem"])
        + " "
        + str("%5.2f" % stat["hum"])
        + " "
        + str("%4.f" % stat["ssm"])
    )


def ymd(stat):
    return (
        str(stat["yea"])
        + "-"
        + str("%02d" % stat["mon"])
        + "-"
        + str("%02d" % stat["day"])
    )


def hourlog_head():
    return "Date\tTime\tRed\tGreen\tBlue\tWhite\tVolts\tMilliamps\tWatts\tFan\tFan RPM\tTemperature\tHumidity\tSoil moisture"


def hourlog(stat, log_avg):
    if stat["tem"] == 0:
        stat["tem"] = stat["sst"]
    return (
        str(stat["yea"])
        + "-"
        + str("%02d" % stat["mon"])
        + "-"
        + str("%02d" % stat["day"])
        + "\t"
        + str("%02d" % stat["hou"])
        + ":"
        + str("%02d" % stat["min"])
        + "\t"
        + str(round(log_avg["red"]))
        + "\t"
        + str(round(log_avg["gre"]))
        + "\t"
        + str(round(log_avg["blu"]))
        + "\t"
        + str(round(log_avg["whi"]))
        + "\t"
        + str(round(log_avg["vol"], 2))
        + "\t"
        + str(round(log_avg["mam"]))
        + "\t"
        + str("%.2f" % round(log_avg["wat"], 2))
        + "\t"
        + str(round(log_avg["fan"]))
        + "\t"
        + str(round(log_avg["rpm"]))
        + "\t"
        + str(log_avg["tem"])
        + "\t"
        + str(log_avg["hum"])
        + "\t"
        + str(round(log_avg["ssm"]))
    )


def url_query(stat, log_avg):
    return (
        "boa="
        + str(stat["boa"])
        + "&"
        "sof="
        + str(stat["sof"])
        + "&"
        + "dat="
        + str(stat["yea"])
        + "-"
        + str("%02d" % stat["mon"])
        + "-"
        + str("%02d" % stat["day"])
        + "&"
        + "tim="
        + str("%02d" % stat["hou"])
        + ":"
        + str("%02d" % stat["min"])
        + "&"
        + "red="
        + str(round(log_avg["red"]))
        + "&"
        + "gre="
        + str(round(log_avg["gre"]))
        + "&"
        + "blu="
        + str(round(log_avg["blu"]))
        + "&"
        + "whi="
        + str(round(log_avg["whi"]))
        + "&"
        + "vol="
        + str(round(log_avg["vol"], 2))
        + "&"
        + "mam="
        + str(round(log_avg["mam"]))
        + "&"
        + "wat="
        + str(round(log_avg["wat"], 2))
        + "&"
        + "fan="
        + str(round(log_avg["fan"]))
        + "&"
        + "rpm="
        + str(round(log_avg["rpm"]))
        + "&"
        + "tem="
        + str(round(log_avg["tem"], 2))
        + "&"
        + "hum="
        + str(round(log_avg["hum"], 2))
        + "&"
        + "sst="
        + str(round(log_avg["sst"], 2))
        + "&"
        + "ssm="
        + str(round(log_avg["ssm"]))
        + "&"
        + "con="
        + str(stat["con"])
        + "&"
        + "cof="
        + str(stat["cof"])
        + "&"
        + "cf0="
        + str(stat["cf0"])
        + "&"
        + "cf1="
        + str(stat["cf1"])
        + "&"
        + "cre="
        + str(stat["cre"])
        + "&"
        + "cgr="
        + str(stat["cgr"])
        + "&"
        + "cbl="
        + str(stat["cbl"])
        + "&"
        + "cwh="
        + str(stat["cwh"])
        + "&"
        + "ctz="
        + str(stat["ctz"])
    )


def valid_config(config):
    # time
    regex = "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    p = re.compile(regex)
    try:
        if re.search(p, config["lights"]["timer"]["on"]) is None:
            return False
    except:
        return False
    try:
        if re.search(p, config["lights"]["timer"]["off"]) is None:
            return False
    except:
        return False

    # lights and fan
    try:
        if (
            isinstance(config["lights"]["duty"]["red"], int)
            and config["lights"]["duty"]["red"] >= 0
            and config["lights"]["duty"]["red"] <= 200
        ):
            pass
        else:
            return False
    except:
        return False
    try:
        if (
            isinstance(config["lights"]["duty"]["green"], int)
            and config["lights"]["duty"]["green"] >= 0
            and config["lights"]["duty"]["green"] <= 89
        ):
            pass
        else:
            return False
    except:
        return False
    try:
        if (
            isinstance(config["lights"]["duty"]["blue"], int)
            and config["lights"]["duty"]["blue"] >= 0
            and config["lights"]["duty"]["blue"] <= 94
        ):
            pass
        else:
            return False
    except:
        return False
    try:
        if (
            isinstance(config["lights"]["duty"]["white"], int)
            and config["lights"]["duty"]["white"] >= 0
            and config["lights"]["duty"]["white"] <= 146
        ):
            pass
        else:
            return False
    except:
        return False
    try:
        if (
            isinstance(config["fan"]["duty"]["when lights on"], int)
            and config["fan"]["duty"]["when lights on"] >= 0
            and config["fan"]["duty"]["when lights on"] <= 255
        ):
            pass
        else:
            return False
    except:
        return False
    try:
        if (
            isinstance(config["fan"]["duty"]["when lights off"], int)
            and config["fan"]["duty"]["when lights off"] >= 0
            and config["fan"]["duty"]["when lights off"] <= 255
        ):
            pass
        else:
            return False
    except:
        return False
    try:
        if (
            config["time zone"]["GMT offset"] >= -11
            and config["time zone"]["GMT offset"] <= 13
        ):
            pass
        else:
            return False
    except:
        return False

    return True
