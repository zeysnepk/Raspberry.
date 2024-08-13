import smbus
import time

# MLX90614 I2C adresi
MLX90614_I2C_ADDR = 0x5A

# MLX90614 register adresleri
MLX90614_TA = 0x06
MLX90614_TOBJ1 = 0x07

class MLX90614:
    def __init__(self, bus=1, address=MLX90614_I2C_ADDR):
        self.bus = smbus.SMBus(bus)
        self.address = address

    def read_word(self, register):
        """I2C'den 16-bit bir kelime oku."""
        low = self.bus.read_byte_data(self.address, register)
        high = self.bus.read_byte_data(self.address, register + 1)
        value = (high << 8) + low
        return value

    def read_temperature(self, register):
        """Sensörden sıcaklık oku ve Celsius'a dönüştür."""
        temp = self.read_word(register)
        temp = temp * 0.02 - 273.15
        return temp

    def get_ambient_temperature(self):
        """Ortam sıcaklığını oku."""
        return self.read_temperature(MLX90614_TA)

    def get_object_temperature(self):
        """Motor gibi bir nesnenin sıcaklığını oku."""
        return self.read_temperature(MLX90614_TOBJ1)

if __name__ == "__main__":
    sensor = MLX90614()
    
    while True:
        ambient_temp = sensor.get_ambient_temperature()
        motor_temp = sensor.get_object_temperature()

        print(f"Ortam Sıcaklığı: {ambient_temp:.2f} °C")
        print(f"Motor Sıcaklığı: {motor_temp:.2f} °C")
        print("-----------------------------")

        time.sleep(1)
