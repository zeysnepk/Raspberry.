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

# Calibration variables
accel_offset = {'x': 0, 'y': 0, 'z': 0}
gyro_offset = {'x': 0, 'y': 0, 'z': 0}

def mpu_init():
    # Wake up the MPU6050
    bus.write_byte_data(DEVICE_ADDRESS, PWR_MGMT_1, 0)
    
    # Set sample rate to 1kHz
    bus.write_byte_data(DEVICE_ADDRESS, SMPLRT_DIV, 7)
    
    # Set gyro full scale range to ±250°/s
    bus.write_byte_data(DEVICE_ADDRESS, GYRO_CONFIG, 0)
    
    # Set accelerometer full scale range to ±2g
    bus.write_byte_data(DEVICE_ADDRESS, ACCEL_CONFIG, 0)

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

    x = (x / ACCEL_SCALE_MODIFIER_2G) - accel_offset['x']
    y = (y / ACCEL_SCALE_MODIFIER_2G) - accel_offset['y']
    z = (z / ACCEL_SCALE_MODIFIER_2G) - accel_offset['z']

    return {'x': x, 'y': y, 'z': z}

def get_rotation():
    x = read_i2c_word(DEVICE_ADDRESS, GYRO_XOUT_H)
    y = read_i2c_word(DEVICE_ADDRESS, GYRO_YOUT_H)
    z = read_i2c_word(DEVICE_ADDRESS, GYRO_ZOUT_H)

    x = (x / GYRO_SCALE_MODIFIER_250DEG) - gyro_offset['x']
    y = (y / GYRO_SCALE_MODIFIER_250DEG) - gyro_offset['y']
    z = (z / GYRO_SCALE_MODIFIER_250DEG) - gyro_offset['z']

    return {'x': x, 'y': y, 'z': z}

def calibrate_sensors(samples=100):
    global accel_offset, gyro_offset
    accel_sum = {'x': 0, 'y': 0, 'z': 0}
    gyro_sum = {'x': 0, 'y': 0, 'z': 0}

    for _ in range(samples):
        accel = get_acceleration()
        gyro = get_rotation()
        
        for axis in ['x', 'y', 'z']:
            accel_sum[axis] += accel[axis]
            gyro_sum[axis] += gyro[axis]
        
        time.sleep(0.01)

    for axis in ['x', 'y', 'z']:
        accel_offset[axis] = accel_sum[axis] / samples
        gyro_offset[axis] = gyro_sum[axis] / samples
    
    # Remove gravity from z-axis of accelerometer
    accel_offset['z'] -= 1

def apply_low_pass_filter(new_values, old_values, alpha=0.2):
    filtered = {}
    for axis in ['x', 'y', 'z']:
        filtered[axis] = alpha * new_values[axis] + (1 - alpha) * old_values[axis]
    return filtered

def main():
    mpu_init()
    print("Calibrating sensors. Please keep the MPU6050 still...")
    calibrate_sensors()
    print("Calibration complete.")

    old_accel = {'x': 0, 'y': 0, 'z': 0}
    old_gyro = {'x': 0, 'y': 0, 'z': 0}
    
    while True:
        accel_data = get_acceleration()
        gyro_data = get_rotation()

        filtered_accel = apply_low_pass_filter(accel_data, old_accel)
        filtered_gyro = apply_low_pass_filter(gyro_data, old_gyro)

        print("Accelerometer data")
        print("x: {:.4f}".format(filtered_accel['x']))
        print("y: {:.4f}".format(filtered_accel['y']))
        print("z: {:.4f}".format(filtered_accel['z']))

        print("\nGyroscope data")
        print("x: {:.4f}".format(filtered_gyro['x']))
        print("y: {:.4f}".format(filtered_gyro['y']))
        print("z: {:.4f}".format(filtered_gyro['z']))

        print("\n")

        old_accel = filtered_accel
        old_gyro = filtered_gyro

        time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interrupted by user")
