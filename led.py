import RPi.GPIO as GPIO

LED_ROED = 13
LED_GRON = 12


def setup_leds():

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(LED_ROED, GPIO.OUT)
    GPIO.setup(LED_GRON, GPIO.OUT)

    all_leds_off()


def red_on():
    GPIO.output(LED_ROED, GPIO.HIGH)


def red_off():
    GPIO.output(LED_ROED, GPIO.LOW)


def green_on():
    GPIO.output(LED_GRON, GPIO.HIGH)


def green_off():
    GPIO.output(LED_GRON, GPIO.LOW)


def all_leds_off():

    GPIO.output(LED_ROED, GPIO.LOW)
    GPIO.output(LED_GRON, GPIO.LOW)


def clear_gpio():
    GPIO.cleanup()