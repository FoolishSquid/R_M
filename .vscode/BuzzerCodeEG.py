from gpiozero import Buzzer
from time import sleep

Buzzer = Buzzer(17)  # Connect the buzzer to GPIO pin 17
Buzzer.on()
sleep(1)
Buzzer.off()