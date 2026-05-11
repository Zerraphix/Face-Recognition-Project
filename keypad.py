import time
import RPi.GPIO as GPIO

KEYPAD = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]

ROWS = [1, 6, 19, 21]
COLS = [7, 16, 20, 26]


def setup_keypad():
    GPIO.setmode(GPIO.BCM)

    for row in ROWS:
        GPIO.setup(row, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    for col in COLS:
        GPIO.setup(col, GPIO.OUT)
        GPIO.output(col, GPIO.HIGH)


def hent_tast():

    for col in range(4):

        GPIO.output(COLS[col], GPIO.LOW)

        for row in range(4):

            if GPIO.input(ROWS[row]) == GPIO.LOW:

                tast = KEYPAD[col][row]

                time.sleep(0.15)

                while GPIO.input(ROWS[row]) == GPIO.LOW:
                    pass

                GPIO.output(COLS[col], GPIO.HIGH)

                return tast

        GPIO.output(COLS[col], GPIO.HIGH)

    return None


def ryd_gpio():
    GPIO.cleanup()