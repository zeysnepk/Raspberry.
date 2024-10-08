import RPi.GPIO as GPIO
import time

# GPIO ayarları
GPIO.setmode(GPIO.BCM)
SENSOR_PIN = 17  # E3Z-LL86 sensörünün bağlı olduğu GPIO pini

# GPIO girişini pull-down ile ayarla
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

try:
    while True:
        if GPIO.input(SENSOR_PIN) == GPIO.HIGH:
            print("Nesne algılandı!")
        else:
            print("Nesne algılanmadı.")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Çıkış yapılıyor...")

finally:
    GPIO.cleanup()
