import RPi.GPIO as GPIO
import time

in1 = 24
in2 = 23
en = 25
temp1 = 1

GPIO.setmode(GPIO.BCM)
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(en, GPIO.OUT)
GPIO.output(in1, GPIO.LOW)
GPIO.output(in2, GPIO.LOW)
p = GPIO.PWM(en, 1000)

p.start(0)  # PWM sinyalini başlangıçta 0 olarak ayarla, motoru tamamen durdur

def run_motor():
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
    
def stop_motor():
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
    

def motor_control(command):
    if command == 'D':
        run_motor()   # Servo motoru 90 dereceye getir
        time.sleep(5)         # 5 saniye bekle
        stop_motor()    # Servo motoru başlangıç pozisyonuna getir
        
def cleanup():
    GPIO.cleanup()  # GPIO pinlerini serbest bırak

