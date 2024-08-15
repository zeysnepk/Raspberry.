import smbus
import time
import struct
import socket
from mpu6050 import MPU6050
from mlx90614 import MLX90614
import json
import threading
import Motor

UDP_IP = "pc_ip"  
UDP_PORT = 5000

TCP_IP = "172.20.10.6"
TCP_PORT = 2222

I2C_ADDRESS = 0x08

bus = smbus.SMBus(1) 

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

data_sensor = {"sicaklik_1": 0.0, "sicaklik_2": 0.0, "acc_x": 0.0, "acc_y": 0.0, "acc_z": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0, "serit_sayisi": 0.0, "konum": 0.0, "hiz": 0.0, "ivme": 0.0, "guc" : 0.0}

def run_motor(command):
    try:
        Motor.motor_control(command)
        print(f"Motorlar {command} olarak calisiyor...")
    except Exception as e:
        print("Motor kontrolu basarisiz oldu:", e)
    finally:
        Motor.cleanup()
		
def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((TCP_IP, TCP_PORT))
        server_socket.listen(5)
        print("TCP sunucusu baslatildi ve komut bekleniyor...")
    except Exception as e:
        print(f"Error: {e}")

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Baglanti kabul edildi: {client_address}")

            command = client_socket.recv(1024).decode('utf-8')
            run_motor(command) 
            print("Motora komut gönderildi --->", command)

        except Exception as e:
            print(f"TCP hatasi: {e}")
		
def read_gyro(mpu, old_accel, old_gyro):
    try:
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
    except Exception as e:
        print("Gyro verileri okunamadi: ", e)

def read_temp(sensor):
	try:
		sicaklik_1 = sensor.readObjectTemperature()
		sicaklik_2 = sensor.readAmbientTemperature()
		data_sensor["sicaklik_1"] = sicaklik_1
		data_sensor["sicaklik_2"] = sicaklik_2
	except Exception as e:
		print("Temperatura okunamadi: ", e)

def send_gui():
	try:
		for key, value in data_sensor.items():
			print(f"{key}: {value}") 
		print("---------------------------------")
		sock.sendto(json.dumps(data_sensor).encode("utf-8"), (UDP_IP, UDP_PORT))
		print("Veri gonderildi")
	except Exception as e:
		print("Veri gonderilemedi", e)
		time.sleep(0.5)
  
def read_float(data, index):
    return struct.unpack('f', bytes(data[index:index+4]))[0]

def read_data():
    global data_sensor
    try:
        data = bus.read_i2c_block_data(I2C_ADDRESS, 0, 24)

        serit_sayisi = read_float(data, 4)
        konum = read_float(data, 8)
        hiz = read_float(data, 12)
        ivme = read_float(data, 16)
        guc = read_float(data, 20)

        data_sensor["serit_sayisi"] = serit_sayisi
        data_sensor["konum"] = konum
        data_sensor["hiz"] = hiz
        data_sensor["ivme"] = ivme
        data_sensor["guc"] = guc
        
    except Exception as e:
            print("ir ve sicaklik verileri okunamadı:", e)
        
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
        #read_data()
        send_gui()
        time.sleep(0.5)
