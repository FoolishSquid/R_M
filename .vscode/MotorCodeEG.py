import curses
from gpiozero import Motor, PWMOutputDevice


class Vehicle:
    def _init_(self):
        self.left_motor = Motor(forward=17, backward=22)  # Connect left motor to GPIO pins 17 and 22
        self.right_motor = Motor(forward=18, backward=23)  # Connect right motor to GPIO pins 18 and 23
        self.left_pwm = PWMOutputDevice(13)  # Connect left PWM to GPIO pin 13
        self.right_pwm = PWMOutputDevice(12)  # Connect right PWM to GPIO pin 12
        self.left_pwm.value = 0  # Set initial PWM value for left motor
        self.right_pwm.value = 0  # Set initial PWM value for right motor

    def move_forward(self):
        self.left_motor.forward()
        self.right_motor.forward()
        self.left_pwm.value = 1  # Set PWM value for left motor
        self.right_pwm.value = 1  # Set PWM value for right motor
        #time.sleep(1)  # Move forward for 1 second
    
    def move_backward(self):
        self.left_motor.backward()
        self.right_motor.backward()
        self.left_pwm.value = 1  # Set PWM value for left motor
        self.right_pwm.value = 1  # Set PWM value for right motor
        #time.sleep(1)  # Move backward for 1 second
    
    def turn_left(self):#check here with the machine for the omni wheels
        self.left_motor.backward()
        self.right_motor.forward()
        self.left_pwm.value = 1  # Set PWM value for left motor
        self.right_pwm.value = 1  # Set PWM value for right motor
        #time.sleep(0.5)  # Turn left for 0.5 seconds

    def turn_right(self):#check here with the machine for the omni wheels
        self.left_motor.forward()
        self.right_motor.backward()
        self.left_pwm.value = 1  # Set PWM value for left motor
        self.right_pwm.value = 1  # Set PWM value for right motor
        #time.sleep(0.5)  # Turn right for 0.5 seconds
# this is for testing  how the wheels will move and the time it will take to move in the desired direction. The time.sleep() function is commented out for now, but can be uncommented for testing purposes.
    def map_key_to_command(self, key):
        mapa = {
            curses.KEY_UP: self.move_forward,
            curses.KEY_DOWN: self.move_backward,
            curses.KEY_LEFT: self.turn_left,
            curses.KEY_RIGHT: self.turn_right,
        }
        return mapa[key]
    # same as previous 
    def control(self, key):
        return self.map_key_to_command(key)

#after this point everything is for testing the movement of the vehicle using the arrow keys. The curses library is used to capture key presses and control the vehicle accordingly.
rpi_vehicle = Vehicle()

def main(window):
    next_key = None
    while True:
        curses.halfdelay(1)
        if next_key is None:
            key = window.getch()
            print(key)
        else:
            key = next_key
            next_key = None
        if key!=-1:
            #key pressed
            curses.halfdelay(1)
            action = rpi_vehicle.control(key)
            if action:
                action()
            next_key = key
            while next_key == key:
                next_key = window.getch()
            # key released
            rpi_vehicle.left_motor.stop()
            rpi_vehicle.right_motor.stop()


curses.wrapper(main)
    
