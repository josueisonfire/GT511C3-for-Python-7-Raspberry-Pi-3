import time
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)

led = GPIO.PWM(7, 100)
led.start(0)

# slightly light up LED.
def dim(pt = 0.001):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(7, GPIO.OUT)
    led = GPIO.PWM(7, 100)
    led.start(0)
    pause_time = pt
    for i in range(0, 100+1):
        led.ChangeDutyCycle(i)
        time.sleep(pause_time)
    for i in range(100, -1, -1):
        led.ChangeDutyCycle(i)
        time.sleep(pause_time)
    

def turnLEDON():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(7, GPIO.OUT)
    GPIO.output(7, True)

def turnLEDOFF(pt = 0.001):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(7, GPIO.OUT)
    GPIO.output(7, False)
        
def cleanup():
    GPIO.cleanup()


dim()

turnLEDON()

time.sleep(3)

turnLEDOFF()

cleanup()
