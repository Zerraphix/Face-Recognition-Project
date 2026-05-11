import time

from lcd import skriv_tekst, ryd_lcd
from keypad import setup_keypad, hent_tast, ryd_gpio


setup_keypad()

skriv_tekst("BFA System\nTryk paa keypad")

try:
    while True:
        tast = hent_tast()

        if tast is not None:
            print("Tast:", tast)
            skriv_tekst("Du trykkede:\n" + tast)

        time.sleep(0.05)

except KeyboardInterrupt:
    ryd_lcd()
    ryd_gpio()
    print("Program stoppet")