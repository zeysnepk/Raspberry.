import smbus
import time

class MPU6050:
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

    def __init__(self, bus_number=1):
        self.bus = smbus.SMBus(bus_number)
        self.accel_offset = {'x': 0, 'y': 0, 'z': 0}
        self.gyro_offset = {'x': 0, 'y': 0, 'z': 0}
        self.mpu_init()

    def mpu_init(self):
        # Wake up the MPU6050
        self.bus.write_byte_data(self.DEVICE_ADDRESS, self.PWR_MGMT_1, 0)
        
        # Set sample rate to 1kHz
        self.bus.write_byte_data(self.DEVICE_ADDRESS, self.SMPLRT_DIV, 7)
        
        # Set gyro full scale range to ±250°/s
        self.bus.write_byte_data(self.DEVICE_ADDRESS, self.GYRO_CONFIG, 0)
        
        # Set accelerometer full scale range to ±2g
        self.bus.write_byte_data(self.DEVICE_ADDRESS, self.ACCEL_CONFIG, 0)

    def read_i2c_word(self, register):
        # Read 2 bytes from the specified register
        high = self.bus.read_byte_data(self.DEVICE_ADDRESS, register)
        low = self.bus.read_byte_data(self.DEVICE_ADDRESS, register + 1)
        value = (high << 8) + low

        if value >= 0x8000:
            return -((65535 - value) + 1)
        else:
            return value

    def get_acceleration(self):
        x = self.read_i2c_word(self.ACCEL_XOUT_H)
        y = self.read_i2c_word(self.ACCEL_YOUT_H)
        z = self.read_i2c_word(self.ACCEL_ZOUT_H)

        x = (x / self.ACCEL_SCALE_MODIFIER_2G) - self.accel_offset['x']
        y = (y / self.ACCEL_SCALE_MODIFIER_2G) - self.accel_offset['y']
        z = (z / self.ACCEL_SCALE_MODIFIER_2G) - self.accel_offset['z']

        return {'x': x, 'y': y, 'z': z}

    def get_rotation(self):
        x = self.read_i2c_word(self.GYRO_XOUT_H)
        y = self.read_i2c_word(self.GYRO_YOUT_H)
        z = self.read_i2c_word(self.GYRO_ZOUT_H)

        x = (x / self.GYRO_SCALE_MODIFIER_250DEG) - self.gyro_offset['x']
        y = (y / self.GYRO_SCALE_MODIFIER_250DEG) - self.gyro_offset['y']
        z = (z / self.GYRO_SCALE_MODIFIER_250DEG) - self.gyro_offset['z']

        return {'x': x, 'y': y, 'z': z}

    def calibrate_sensors(self, samples=100):
        accel_sum = {'x': 0, 'y': 0, 'z': 0}
        gyro_sum = {'x': 0, 'y': 0, 'z': 0}

        for _ in range(samples):
            accel = self.get_acceleration()
            gyro = self.get_rotation()
            
            for axis in ['x', 'y', 'z']:
                accel_sum[axis] += accel[axis]
                gyro_sum[axis] += gyro[axis]
            
            time.sleep(0.01)

        for axis in ['x', 'y', 'z']:
            self.accel_offset[axis] = accel_sum[axis] / samples
            self.gyro_offset[axis] = gyro_sum[axis] / samples
        
        # Remove gravity from z-axis of accelerometer
        self.accel_offset['z'] -= 1

    @staticmethod
    def apply_low_pass_filter(new_values, old_values, alpha=0.2):
        filtered = {}
        for axis in ['x', 'y', 'z']:
            filtered[axis] = alpha * new_values[axis] + (1 - alpha) * old_values[axis]
        return filtered
