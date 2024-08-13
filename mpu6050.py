import smbus
import math
import time

# MPU6050 Registers
PWR_MGMT_1 = 0x6B
SMPLRT_DIV = 0x19
CONFIG = 0x1A
GYRO_CONFIG = 0x1B
ACCEL_CONFIG = 0x1C
INT_ENABLE = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H = 0x43
GYRO_YOUT_H = 0x45
GYRO_ZOUT_H = 0x47

# MPU6050 I2C Address
DEVICE_ADDRESS = 0x68

# Scale Modifiers
ACCEL_SCALE_MODIFIER_2G = 16384.0
GYRO_SCALE_MODIFIER_250DEG = 131.0

# Initialize I2C bus
bus = smbus.SMBus(1)

def mpu_init():
    # Wake up the MPU6050
    bus.write_byte_data(DEVICE_ADDRESS, PWR_MGMT_1, 0)

def read_i2c_word(address, register):
    # Read 2 bytes from the specified register
    high = bus.read_byte_data(address, register)
    low = bus.read_byte_data(address, register + 1)
    value = (high << 8) + low

    if value >= 0x8000:
        return -((65535 - value) + 1)
    else:
        return value

def get_acceleration():
    x = read_i2c_word(DEVICE_ADDRESS, ACCEL_XOUT_H)
    y = read_i2c_word(DEVICE_ADDRESS, ACCEL_YOUT_H)
    z = read_i2c_word(DEVICE_ADDRESS, ACCEL_ZOUT_H)

    x = x / ACCEL_SCALE_MODIFIER_2G
    y = y / ACCEL_SCALE_MODIFIER_2G
    z = z / ACCEL_SCALE_MODIFIER_2G

    return {'x': x, 'y': y, 'z': z}

def get_rotation():
    x = read_i2c_word(DEVICE_ADDRESS, GYRO_XOUT_H)
    y = read_i2c_word(DEVICE_ADDRESS, GYRO_YOUT_H)
    z = read_i2c_word(DEVICE_ADDRESS, GYRO_ZOUT_H)

    x = x / GYRO_SCALE_MODIFIER_250DEG
    y = y / GYRO_SCALE_MODIFIER_250DEG
    z = z / GYRO_SCALE_MODIFIER_250DEG

    return {'x': x, 'y': y, 'z': z}

def main():
    mpu_init()
    
    while True:
        accel_data = get_acceleration()
        gyro_data = get_rotation()

        print("Accelerometer data")
        print("x: {:.4f}".format(accel_data['x']))
        print("y: {:.4f}".format(accel_data['y']))
        print("z: {:.4f}".format(accel_data['z']))

        print("\nGyroscope data")
        print("x: {:.4f}".format(gyro_data['x']))
        print("y: {:.4f}".format(gyro_data['y']))
        print("z: {:.4f}".format(gyro_data['z']))

        print("\n")

        time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interrupted by user")
