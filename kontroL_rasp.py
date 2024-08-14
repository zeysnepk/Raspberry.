import smbus
import time
import struct
import socket
from threading import Thread
from mpu6050_2 import MPU6050
from mlx90614 import MLX90614
import json
import threading
import serial

UDP_IP = "192.168.1.102"  
UDP_PORT = 5000

TCP_IP = "10.42.1.122"
TCP_PORT = 2222

ser = serial.Serial('/dev/ttyUSB0', 9600)

bus = smbus.SMBus(1) 

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

data_sensor = {"sicaklik_1": 0.0, "sicaklik_2": 0.0, "acc_x": 0.0, "acc_y": 0.0, "acc_z": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0}

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((TCP_IP, TCP_PORT))
    server_socket.listen(1)
    
    print("Sunucu çalışıyor...")
    
    while True:
        conn, addr = server_socket.accept()
        print(f"Bağlantı sağlandı: {addr}")
        
        while True:
            data = conn.recv(1)  # 1 byte veri al
            if not data:
                break
            
            command = int.from_bytes(data, byteorder='big')
            if command == 0:
                print("Stop komutu alındı")
                ser.write(b'0')  # Arduino'ya 0 gönder
            elif command == 1:
                print("Start komutu alındı")
                ser.write(b'1')  # Arduino'ya 1 gönder
            else:
                print("Bilinmeyen komut")
        
        conn.close()
		
                
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
    
    #print("acc_x:", data_sensor["acc_x"])
    #print("acc_y:", data_sensor["acc_y"])
    #print("acc_z:", data_sensor["acc_z"])
    #print("roll:", data_sensor["roll"])
    #print("pitch:", data_sensor["pitch"])
    #print("yaw:", data_sensor["yaw"])

    return filtered_accel, filtered_gyro
    
def read_temp(sensor):
    sicaklik_1 = sensor.readObjectTemperature()
    sicaklik_2 = sensor.readAmbientTemperature()
    data_sensor["sicaklik_1"] = sicaklik_1
    data_sensor["sicaklik_2"] = sicaklik_2
    #print("1.sicaklik:", sicaklik_1)
    #print("2.sicaklik:", sicaklik_2)

def read_arduino():
	try:
		for key, value in data_sensor.items():
			print(f"{key}: {value}") 
		print("---------------------------------")
		sock.sendto(json.dumps(data_sensor).encode("utf-8"), (UDP_IP, UDP_PORT))
		print("Veri gönderildi")
	except IOError:
		print("Veri okunamadı")
		time.sleep(0.5)
        
if __name__ == "__main__":
	tcp_thread = threading.Thread(target=start_tcp_server)
	tcp_thread.daemon = True
	tcp_thread.start()

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
		read_arduino()

		time.sleep(0.5)
