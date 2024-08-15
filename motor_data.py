import smbus, json
import time
import struct
import socket
import threading
import Motor_2

bus = smbus.SMBus(1) 

TCP_IP = "raspi_ip"
TCP_PORT = 2222

def run_motor(command):
    try:
        Motor_2.motor_control(command)
        print(f"Motorlar {command} olarak çalışıyor...")
    except Exception as e:
        print("Motor kontrolü başarısız oldu:", e)
    finally:
        Motor_2.cleanup()

    
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
            run_motor(command) 
            print("Arduino ya komut gönderildi --->", command)

        except Exception as e:
            print(f"TCP hatası: {e}")


if __name__ == "__main__":
    tcp_thread = threading.Thread(target=start_tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()
    
    while True:
        time.sleep(1)
