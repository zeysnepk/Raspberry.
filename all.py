import smbus
import time
import struct
import socket
from threading import Thread
from mpu6050 import MPU6050
from mlx90614 import MLX90614

UDP_IP = "pc_ip"  
UDP_PORT = 5000

COMMAND_IP = "raspi_ip"
COMMAND_PORT = 5001

COMMAND_ADDRESS = 0x09

bus = smbus.SMBus(1) 

udp_socket_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

udp_socket_receive.bind((UDP_IP, UDP_PORT))

data_sensor = {"sicaklik_1": 0.0, "sicaklik_2": 0.0, "acc_x": 0.0, "acc_y": 0.0, "acc_z": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0}

def listen_stop():
    print("Komut alma başladı...")
    while True:
        data, addr = udp_socket_receive.recvfrom(1024)
        message = data.decode("utf-8")
        print(f"Alınan komut: {message}")
        try:
            bus.write_byte(COMMAND_ADDRESS, ord('S'))
            print("'S' komutu Arduino'ya gönderildi")
        except Exception as e:
            print(f"I2C iletişim hatası: {e}")
                
def read_gyro(mpu, old_accel, old_gyro):
    accel_data = mpu.get_acceleration()
    gyro_data = mpu.get_rotation()

    filtered_accel = MPU6050.apply_low_pass_filter(accel_data, old_accel)
    filtered_gyro = MPU6050.apply_low_pass_filter(gyro_data, old_gyro)

    # Verileri Güncelle
    data_sensor["acc_x"] = filtered_accel['x']
    data_sensor["acc_y"] = filtered_accel['y']
    data_sensor["acc_z"] = filtered_accel['z']
    data_sensor["roll"] = filtered_gyro['x']
    data_sensor["pitch"] = filtered_gyro['y']
    data_sensor["yaw"] = filtered_gyro['z']

    return filtered_accel, filtered_gyro
    
def read_temp(sensor):
    sicaklik_1 = sensor.readObjectTemperature()
    sicaklik_2 = sensor.readAmbientTemperature()
    data_sensor["sicaklik_1"] = sicaklik_1
    data_sensor["sicaklik_2"] = sicaklik_2
    print("1.Sıcaklık:", sicaklik_1)
    print("2.Sıcaklık:", sicaklik_2)

def read_arduino():
    try:
        for key, value in data_sensor.items():
            print(f"{key}: {value}") 
            print("---------------------------------")
            sock.sendto(data_sensor.encode("utf-8"), (UDP_IP, UDP_PORT))
            print("Veri gönderildi")
    except IOError:
            print("Veri okunamadı")
            time.sleep(0.5)
        
if __name__ == "__main__":
    command = Thread(target=listen_stop)
    command.start()
    
    mpu = MPU6050()
    print("Calibrating sensors. Please keep the MPU6050 still...")
    mpu.calibrate_sensors()
    print("Calibration complete.")
    
    sensor = MLX90614()
    
    old_accel = {'x': 0, 'y': 0, 'z': 0}
    old_gyro = {'x': 0, 'y': 0, 'z': 0}
    while True:
        old_accel, old_gyro = read_gyro(mpu, old_accel, old_gyro)
        read_temp(sensor)
        time.sleep(0.5)
