import time
from lcd import write_text, clear_lcd
from keypad import setup_keypad, get_number
from led import setup_leds, green_on, green_off, red_on, red_off, clear_gpio

KODE = "1234"
kode_input = ""
setup_keypad()
setup_leds()

write_text("Indtast kode")
try:
    while True:
        tast = get_number()
        if tast is not None:
            print(tast)
            kode_input += tast
            write_text(kode_input)

            if len(kode_input) == 4:
                if kode_input == KODE:
                    write_text("Korrekt kode")
                    green_on()
                    red_off()

                else:
                    write_text("Forkert kode")
                    red_on()
                    green_off()
                time.sleep(2)

                kode_input = ""
                write_text("Indtast kode")
        time.sleep(0.05)
except KeyboardInterrupt:

    clear_lcd()
    clear_gpio()