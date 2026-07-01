from gpiozero import LED
from time import sleep

led = LED(17)  # Connect the LED to GPIO pin 17
led.on()  # Turn on the LED
sleep(1)  # Keep the LED on for 1 second
led.off()  # Turn off the LED