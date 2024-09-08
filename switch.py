import time
import RPi.GPIO as gpio

on = 8
off = 10
led = 13

gpio.setwarnings(False)
gpio.setmode(gpio.BOARD)
gpio.setup(on, gpio.OUT)
gpio.setup(off, gpio.OUT)
gpio.setup(led, gpio.OUT)

gpio.output(on, True)
gpio.output(off, True)
gpio.output(led, False)

while True:
    print("press enter to turn on", end="")
    input()

    gpio.output(led, True)
    print("> ON")
    for _ in range(3):
        gpio.output(on, False)
        time.sleep(.5)
        gpio.output(on, True)
        time.sleep(1)

    print("press enter to turn off", end="")
    input()

    gpio.output(led, False)
    print("> OFF")
    for _ in range(3):
        gpio.output(off, False)
        time.sleep(.5)
        gpio.output(off, True)
        time.sleep(1)
