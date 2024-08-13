from mpu6050 import mpu6050
import time

# MPU6050 sensorunu başlat
sensor = mpu6050(0x68)

while True:
    # İvme verilerini oku
    accel_data = sensor.get_accel_data()
    print("Ivme X:", accel_data['x'])
    print("Ivme Y:", accel_data['y'])
    print("Ivme Z:", accel_data['z'])

    # Gyro verilerini oku
    gyro_data = sensor.get_gyro_data()
    print("Gyro X:", gyro_data['x'])
    print("Gyro Y:", gyro_data['y'])
    print("Gyro Z:", gyro_data['z'])

    # 1 saniye bekle
    time.sleep(1)
