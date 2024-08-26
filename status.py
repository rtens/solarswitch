import time
import threading
import growattServer
import os
import datetime
import json

try:
    import RPi.GPIO as gpio

    gpio.setmode(gpio.BOARD)
    gpio.setup(13, gpio.OUT)

    def led_set(to=True):
        gpio.output(13, to)

    def led_cleanup():
        gpio.cleanup()

except Exception:

    def led_set(to=True):
        print(status, end="")
        print("LED " + ("on " if to else "off") + "\r", end="")
        print(bcolors.end, end="")

    def led_cleanup():
        pass

def led_flash(on, off):
    while running:
        led_set(True)
        for _ in range(int(on*10)):
            time.sleep(.1)
            if not running: return
        led_set(False)
        for _ in range(int(off*10)):
            time.sleep(.1)
            if not running: return

class bcolors:
    blue = '\033[94m'
    cyan = '\033[96m'
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    hide = '\033[?25l'
    show = '\033[?25h'
    end = '\033[0m'


def log(message):
    with open("log.txt", "a") as log:
        stamp = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
        log.write(stamp + " " + message + "\n")


def multibar(parts, max=6.5):
    length = 65
    bars = "".join([sym * int(float(val) * length/max) for (sym, val) in parts])
    return "|" + bars + (" " * (length-len(bars))) + "|"

log("started")

try:
    with open("history.json") as f:
        history = json.load(f)
except Exception:
    history = []

threshold = 1

switch = None
logins = 1

try:
    with open("login.json") as f:
        login = json.load(f)
except Exception:
    login = {
        "usr": input("user: "),
        "pwd": input("password: ")
    }
    with open("login.json", "w") as f:
        json.dump(login, f)

api = growattServer.GrowattApi(False, "MIC55555")
login_response = api.login(login["usr"], login["pwd"])

while True:
    try:
        plants = api.plant_list(login_response['user']['id'])
    except Exception:
        logins += 1
        log("login again: " + json.dumps(login_response))
        login_response = api.login(login["usr"], login["pwd"])
        if not login_response["success"]:
            log("login error: " + json.dumps(login_response))
            print(login_response["error"])
            exit(1)
        plants = api.plant_list(login_response['user']['id'])

    plant_id = plants['data'][0]["plantId"]
    plant_info = api.plant_info(plant_id)
    device_sn = plant_info["deviceList"][0]["deviceSn"]
    mix_status = api.mix_system_status(device_sn, plant_id)

    history.append(round(float(mix_status["ppv"]) - float(mix_status["pLocalLoad"]), 2))
    if len(history) > 7: history.pop(0)

    with open("history.json", "w") as f:
        json.dump(history, f)

    average_net = round(sum(history) / len(history), 2)

    soc = float(mix_status["SOC"])

    if average_net >= threshold:
        threshold = 0
        status = bcolors.green

        if switch == False or switch == None:
            switch = True
            log("switched on")

        if soc >= 95:
            thread = threading.Thread(target=led_set, args=(True,))
        else:
            thread = threading.Thread(target=led_flash, args=(2, .1))
    else:
        if switch == True or switch == None:
            switch = False
            log("switched off")

        if average_net >= 0:
            status = bcolors.blue
            thread = threading.Thread(target=led_flash, args=(1, .5))
        elif soc >= 15:
            threshold = .5
            status = bcolors.yellow
            thread = threading.Thread(target=led_flash, args=(1, 2))
        else:
            threshold = 1
            status = bcolors.red
            thread = threading.Thread(target=led_flash, args=(.1, 5))

    print(bcolors.hide, end="")
    print(status, end="")
    print("Updated:    ", datetime.datetime.now().strftime("%H:%M:%S"))
    print("Logins:     ", logins)
    print("Using:      ", mix_status["pLocalLoad"], "kW")
    print("Generating: ", mix_status["ppv"], "kW")
    print("Battery:    ", mix_status["SOC"], "%")
    print("Charging:   ", mix_status["chargePower"], "kW")
    print("Discharging:", mix_status["pdisCharge1"], "kW")
    print("Importing:  ", mix_status["pactouser"], "kW")
    print("Exporting:  ", mix_status["pactogrid"], "kW")
    print("History:    ", average_net, history)
    print("Threshold:  ", threshold)
    print("Switch:     ", switch)

    print()
    print(multibar((("=", soc-10),), 90))
    print(multibar((
        ("#", mix_status["pLocalLoad"]),
        ("+", mix_status["chargePower"]),
        (">", mix_status["pactogrid"]),
    )))
    print(multibar((
        ("*", mix_status["ppv"]),
        ("-", mix_status["pdisCharge1"]),
        ("<", mix_status["pactouser"]),
    )))
    print()

    print(bcolors.end, flush=True)

    running = True
    thread.start()

    try:
        time.sleep(3*60)
    except KeyboardInterrupt:
        print()
        print(bcolors.show + bcolors.end + "bye")
        running = False
        led_cleanup()
        exit()

    running = False
    thread.join()
    led_set(False)
    os.system("clear")
