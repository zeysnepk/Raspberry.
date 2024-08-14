import smbus
import time
import struct
import socket
import threading
from mpu6050_2 import MPU6050
from mlx90614 import MLX90614
import json

UDP_IP = "10.42.1.111"  
UDP_PORT = 5000

TCP_IP = "10.42.1.122"
TCP_PORT = 2222

I2C_ADDRESS = 0x08
COMMAND_ADDRESS = 0x09

bus = smbus.SMBus(1) 
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

data_sensor = {
    "sicaklik_1": 0.0, "sicaklik_2": 0.0, 
    "acc_x": 0.0, "acc_y": 0.0, "acc_z": 0.0, 
    "roll": 0.0, "pitch": 0.0, "yaw": 0.0, 
    "serit_sayisi": 0.0, "konum": 0.0, 
    "hiz": 0.0, "ivme": 0.0
}

def send_i2c_command(command):
    try:
        bus.write_byte(COMMAND_ADDRESS, ord(command))
        print("Arduino'ya komut gönderildi:", command)
    except Exception as e:
        print("I2C Hatası:", e)

def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((TCP_IP, TCP_PORT))
        server_socket.listen(5)
        print("TCP başlatıldı")
    except Exception as e:
        print("TCP başlatılamadı:", e)
        return

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print("Bağlantı kabul edildi:", client_address)
            command = client_socket.recv(1024).decode("utf-8")
            send_i2c_command(command)
        except Exception as e:
            print("Arduino'ya komut gönderilemedi:", e)

def read_gyro(mpu, old_accel, old_gyro):
    accel_data = mpu.get_acceleration()
    gyro_data = mpu.get_rotation()

    filtered_accel = MPU6050.apply_low_pass_filter(accel_data, old_accel)
    filtered_gyro = MPU6050.apply_low_pass_filter(gyro_data, old_gyro)

    data_sensor.update({
        "acc_x": filtered_accel['x'], "acc_y": filtered_accel['y'], "acc_z": filtered_accel['z'],
        "roll": filtered_gyro['x'], "pitch": filtered_gyro['y'], "yaw": filtered_gyro['z']
    })

    return filtered_accel, filtered_gyro
    
def read_temp(sensor):
    try:
        sicaklik_1 = sensor.readObjectTemperature()
        sicaklik_2 = sensor.readAmbientTemperature()
        data_sensor.update({"sicaklik_1": sicaklik_1, "sicaklik_2": sicaklik_2})
    except Exception as e:
        print("Sıcaklık sensörü okunamadı:", e)

def send_sensors():
    try:
        sock.sendto(json.dumps(data_sensor).encode("utf-8"), (UDP_IP, UDP_PORT))
        print("Veri gönderildi")
    except IOError as e:
        print("Veri gönderilemedi:", e)

def read_float(data, index):
    return struct.unpack('f', bytes(data[index:index+4]))[0]

def read_arduino():
    try:
        data = bus.read_i2c_block_data(I2C_ADDRESS, 0, 16)
        data_sensor.update({
            "serit_sayisi": read_float(data, 0),
            "konum": read_float(data, 4),
            "hiz": read_float(data, 8),
            "ivme": read_float(data, 12)
        })
    except Exception as e:
        print("Arduino'dan sensörler okunamadı:", e)

if __name__ == "__main__":
    tcp_thread = threading.Thread(target=start_tcp_server, daemon=True)
    tcp_thread.start()

    mpu = MPU6050()
    print("Kalibrasyon başladı...")
    mpu.calibrate_sensors()
    print("Kalibrasyon tamamlandı.")

    sensor = MLX90614()
    old_accel = {'x': 0, 'y': 0, 'z': 0}
    old_gyro = {'x': 0, 'y': 0, 'z': 0}

    while True:
        old_accel, old_gyro = read_gyro(mpu, old_accel, old_gyro)
        read_temp(sensor)
        read_arduino()
        send_sensors()
        time.sleep(0.5)
