import time

class mpu6050:
    #
    
    def get_gyro_data_degrees(self, dt):
        """Gets and returns the X, Y and Z values from the gyroscope in degrees.

        dt -- time delta in seconds since the last reading
        Returns the read values in a dictionary.
        """
        x = self.read_i2c_word(self.GYRO_XOUT0)
        y = self.read_i2c_word(self.GYRO_YOUT0)
        z = self.read_i2c_word(self.GYRO_ZOUT0)

        gyro_scale_modifier = None
        gyro_range = self.read_gyro_range(True)

        if gyro_range == self.GYRO_RANGE_250DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_250DEG
        elif gyro_range == self.GYRO_RANGE_500DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_500DEG
        elif gyro_range == self.GYRO_RANGE_1000DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_1000DEG
        elif gyro_range == self.GYRO_RANGE_2000DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_2000DEG
        else:
            print("Unknown range - gyro_scale_modifier set to self.GYRO_SCALE_MODIFIER_250DEG")
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_250DEG

        x = (x / gyro_scale_modifier) * dt
        y = (y / gyro_scale_modifier) * dt
        z = (z / gyro_scale_modifier) * dt

        return {'x': x, 'y': y, 'z': z}

if __name__ == "__main__":
    mpu = mpu6050(0x68)
    last_time = time.time()

    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        gyro_data = mpu.get_gyro_data_degrees(dt)
        print(f"Gyro X: {gyro_data['x']} degrees")
        print(f"Gyro Y: {gyro_data['y']} degrees")
        print(f"Gyro Z: {gyro_data['z']} degrees")
        time.sleep(0.1)
