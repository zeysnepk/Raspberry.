import smbus, json
import time
import struct
import socket
import threading

ARDUİNO_ADDRESS = 0X07
I2C_ADDRESS_1 = 0x08
I2C_ADDRESS_2 = 0x09

bus = smbus.SMBus(1) 

UDP_IP = "pc_ip"  
UDP_PORT = 5000

TCP_IP = "raspi_ip"
TCP_PORT = 2222

last_valid_data = {
    "sicaklik_1": 0.0,
    "sicaklik_2": 0.0,
    "serit_sayisi": 0.0,
    "konum": 0.0,
    "hiz": 0.0,
    "ivme": 0.0,
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0,
    "guc" : 0.0
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_i2c_command(command):
    try:
        bus.write_byte(ARDUİNO_ADDRESS, ord(command))
    except Exception as e:
        print("I2C hatası: ", e)
    
def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((TCP_IP, TCP_PORT))
        server_socket.listen(5)
        print("TCP sunucusu başlatıldı ve komut bekleniyor...")
    except Exception as e:
        print(f"Error: {e}")

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Bağlantı kabul edildi: {client_address}")

            command = client_socket.recv(1024).decode('utf-8')
            send_i2c_command(command) 
            print("Arduino ya komut gönderildi --->", command)

        except Exception as e:
            print(f"TCP hatası: {e}")

def read_float(data, index):
    return struct.unpack('f', bytes(data[index:index+4]))[0]

def read_data():
    global last_valid_data
    while True:
        try:
            data = bus.read_i2c_block_data(I2C_ADDRESS_1, 0, 20)

            sicaklik_1 = read_float(data, 0)
            serit_sayisi = read_float(data, 4)
            konum = read_float(data, 8)
            hiz = read_float(data, 12)
            ivme = read_float(data, 16)
 
            
            last_valid_data["sicaklik_1"] = sicaklik_1
            last_valid_data["serit_sayisi"] = serit_sayisi
            last_valid_data["konum"] = konum
            last_valid_data["hiz"] = hiz
            last_valid_data["ivme"] = ivme
        except Exception as e:
                print("ir ve sicaklik verileri okunamadı:", e)

        try:
            data_2 = bus.read_i2c_block_data(I2C_ADDRESS_2, 0, 20)
            
            roll = read_float(data_2, 0)
            pitch = read_float(data_2, 4)
            yaw = read_float(data_2, 8)
            sicaklik_2 = read_float(data_2, 12)
            guc = read_float(data_2, 16)
            
            last_valid_data["roll"] = roll
            last_valid_data["pitch"] = pitch
            last_valid_data["yaw"] = yaw
            last_valid_data["sicaklik_2"] = sicaklik_2
            last_valid_data["guc"] = guc
        except Exception as e:
            print("güç ve gyro verileri okunamadı:", e)
            
        try:
            encoded = json.dumps(last_valid_data)
            sock.sendto(encoded.encode("utf-8"), (UDP_IP, UDP_PORT))
            print("Veri UDP ile gönderildi:")
            for key, value in last_valid_data.items():
                print(f"{key}: {value}")
        except Exception as e:
            print("Veri UDP ile gönderilemedi", e)
        time.sleep(0.5)

if __name__ == "__main__":
    tcp_thread = threading.Thread(target=start_tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()
    
    try:
        read_data()
    except KeyboardInterrupt:
        print("Program sonlandırıldı")
    finally:
        sock.close()
