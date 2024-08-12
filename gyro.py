import smbus, json
import time
import struct
import socket

I2C_ADDRESS = 0x08
bus = smbus.SMBus(1) 

UDP_IP = "ip"  
UDP_PORT = 5000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def read_float(data, index):
    return struct.unpack('f', bytes(data[index:index+4]))[0]

last_valid_data = {
    "acc_x": 0.0,
    "acc_y": 0.0,
    "acc_z": 0.0,
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
}

try:
    while True:
        try:
            data = bus.read_i2c_block_data(I2C_ADDRESS, 0, 24)
          
            acc_x = read_float(data, 0)
            acc_y = read_float(data, 4)
            acc_z = read_float(data, 8)
            roll = read_float(data, 12)
            pitch = read_float(data, 16)
            yaw = read_float(data, 20)
            
            last_valid_data["position"] = acc_x
            last_valid_data["velocity"] = acc_y
            last_valid_data["acceleration"] = acc_z
            last_valid_data["roll"] = roll
            last_valid_data["pitch"] = pitch
            last_valid_data["yaw"] = yaw
            
            print(f"acc_x: {acc_x:.2f}, acc_y: {acc_y:.2f}, acc_z: {acc_z:.2f}, roll: {roll:.2f}, pitch: {pitch:.2f}, yaw: {yaw:.2f}")
            encoded = json.dumps(last_valid_data)
            sock.sendto(encoded.encode(), (UDP_IP, UDP_PORT))
            print("Veri UDP ile gönderildi")
        except IOError:
            print("Veri okunamadı")
        
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Program sonlandırıldı")
finally:
    sock.close()
