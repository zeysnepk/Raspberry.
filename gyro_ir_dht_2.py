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
    "temp": 0.0,
    "motor_temp": 0.0,
    "position": 0.0,
    "velocity": 0.0,
    "acceleration": 0.0,
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
}

try:
    while True:
        try:
            data = bus.read_i2c_block_data(I2C_ADDRESS, 0, 32)

            temp = read_float(data, 0)
            motor_temp = read_float(data, 4)
            position = read_float(data, 8)
            velocity = read_float(data, 12)
            acceleration = read_float(data, 16)
            roll = read_float(data, 20)
            pitch = read_float(data, 24)
            yaw = read_float(data, 28)
            
            last_valid_data["temp"] = temp
            last_valid_data["motor_temp"] = motor_temp
            last_valid_data["position"] = position
            last_valid_data["velocity"] = velocity
            last_valid_data["acceleration"] = acceleration
            last_valid_data["roll"] = roll
            last_valid_data["pitch"] = pitch
            last_valid_data["yaw"] = yaw
            
            print(f"temp: {temp:.2f}, motor_temp: {motor_temp:.2f}, position: {position:.2f}, velocity: {velocity:.2f}, acceleration: {acceleration:.2f}, roll: {roll:.2f}, pitch: {pitch:.2f}, yaw: {yaw:.2f}")
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
