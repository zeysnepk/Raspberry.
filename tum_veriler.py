import sys
import socket
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from new_design3 import Ui_MainWindow
import time, json
import random
import datetime
import psutil

UDP_IP = "172.20.10.7"  #uzak kontrol bilgisayarının IP adresi
UDP_PORT = 5000  #uzak kontrol bilgisayarının UDP portu

TCP_IP = "172.20.10.6" #Raspberry Pi'nin IP adresi
TCP_PORT = 2222 #Raspberry Pi'nin TCP portu

max_temp = 50 
max_power = 1000

class NetworkSpeedThread(QThread):
    speed_signal = pyqtSignal(str) #Network hızı için sinyal
    
    def __init__(self, interval=1):
        super().__init__()
        self.interval = interval #Süre (saniye)
        self._running = True #thread durdurulmadığı sürece çalışacak
        
    def run(self):
        while self._running: 
            old_value = psutil.net_io_counters() #network hızı başlangıç değeri
            time.sleep(self.interval)
            new_value = psutil.net_io_counters() #network hızı bitiş değeri

            recv = new_value.bytes_recv - old_value.bytes_recv #Network hızı artış miktarı

            self.speed_signal.emit(f"{recv / self.interval / 1024:.2f} KB") #sinyal ile network hızı gönder
    
    def stop(self):
        self._running = False #thread durduruluyor

class SocketThread(QThread):
    data_received = pyqtSignal(str) #UDP ile gelen veriler için sinyal
    
    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock: # UDP socket başlatılıyor
            sock.bind((UDP_IP, UDP_PORT)) # UDP socketin belli bir IP ve port üzerinde başlatılması
            sock.settimeout(1) # socket zaman aşımı yapar

            while self._running:
                try:
                    data, addr = sock.recvfrom(1024) # UDP mesajı alma
                    data = data.decode("utf-8") # UTF-8 decode edilip gelen veri
                    print(f"Mesaj: {data}")
                    self.data_received.emit(data) # sinyal ile veriler gönderiliyor
                except socket.timeout:
                    continue
                except Exception as e:
                    print("Veri alınamadı!", e)
    def stop(self):
        self._running = False
        self.wait() # Uzak bilgisayardan veri çıkarmaya devam edilmesini

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100): # MPL Canvas başlatılıyor
        figure = Figure(figsize=(width, height), dpi=dpi) # MPL Canvas'ın üzerinde bir çizim yapılıyor
        self.axes = figure.add_subplot(111) # MPL Canvas'ın eksenleri ekleniyor
        figure.set_facecolor('#323232')   # MPL Canvas'ın arka plan rengi ayarlanıyor
        figure.subplots_adjust(left=0.05, right=0.98, top=0.80, bottom=0.20) # MPL Canvas'ın boyutları düzenleniyor
        super(MplCanvas, self).__init__(figure) # MPL Canvas'ın ekrana çiziliyor
                    
class Main(QMainWindow):
    def __init__(self):
        super().__init__() # QMainWindow sınıfından miras alınıyor
        
        self.main = Ui_MainWindow() # UI dosyasından gerekli özellikler yüklendi
        self.main.setupUi(self) # UI ekranını başlatıyor
        self.setWindowTitle("HYPERUSH") # Pencere başlığı düzenleniyor
        
        self.create_lists() #Veri yapıları için foksiyon
        
        self.main.label_info.setText("") 
        
        #self.socket_thread = SocketThread() # UDP için SocketThread başlatılıyor
        #self.socket_thread.data_received.connect(self.data_convert) #emit ile gönderilen sinyal fonksiyona gönderiliyor
        
        self.start_time = time.time() # Başlangıç zamanı
        
        self.main.pushButton_start.clicked.connect(self.start) # Basla butonuna tıklandığında start fonsiyonuna bağlanıyor
        self.main.pushButton_stop.clicked.connect(self.stop) # Durdur butonuna tıklandığında stop fonsiyonuna bağlanıyor
        self.main.pushButton_go.clicked.connect(self.go) # İleri butonuna tıklandığında go fonsiyonuna bağlanıyor
        self.main.pushButton_back.clicked.connect(self.back) # Geri butonuna tıklandığında back fonsiyonuna bağlanıyor
        
        self.label_time_timer = QTimer()   # Zamanlayıcı başlatılıyor
        self.label_time_timer.timeout.connect(self.update_time_label) # Zamanlayıcı sıklıkla çağrılıyor
        #self.elapsed_time = 0
        
        self.network_thread = NetworkSpeedThread() # Network hızı için NetworkSpeedThread başlatılıyor
        self.network_thread.speed_signal.connect(self.update_network_speed) # Network hızı sıklıkla çağrılıyor
        
    def komut_gonder_tcp(self, RPI_IP, RPI_PORT, command):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP socket başlatılıyor
            client_socket.connect((TCP_IP, TCP_PORT)) # TCP socket'a bağlanılıyor

            client_socket.send(command.encode('utf-8')) # komut utf-8 ile encodelanıp gönderiliyor
        except Exception as e:
            print("TCP Hata:", e)
        
    def update_time_label(self):
        self.elapsed_time = int(time.time() - self.start_time)  # Zamanı tutan değişken
        self.main.label_time.setText(str(self.elapsed_time)) # Ekrana zamanı yazılıyor
        
        
    def update_network_speed(self, speed):
        self.main.label_data_speed.setText(speed) # Ekrana network hızı yazılıyor
        
    def start(self):
        self.main.label_stat.setStyleSheet("font:700 30pt \"Chakra Petch\";\n"
"color: rgb(50,205,50);") 
        self.main.label_stat.setText("ON")
        
        self.start_time = time.time()  
        self.label_time_timer.start(1000) # Zamanlayıcı başlatılıyor
        #self.socket_thread.start() # UDP socket başlatılıyor
        self.network_thread.start() # Network hızı başlatılıyor
        
        self.komut_gonder_tcp(TCP_IP, TCP_PORT, 'B') # Raspberry Pi'ye Başlat komutu gönderiliyor
    
    def stop(self):
        self.main.label_stat.setStyleSheet("font:700 30pt \"Chakra Petch\";\n"
"color: rgb(148, 17, 0);")
        self.main.label_stat.setText("OFF")
        
        self.label_time_timer.stop() # Zamanlayıcı durduruluyor
        
        #self.socket_thread.stop() # UDP socket durduruluyor
        
        self.network_thread.stop() # Network hızı durduruluyor
        self.network_thread.wait() # Uzak bilgisayardan veri çıkarmaya devam edilmesini
        
        self.komut_gonder_tcp(TCP_IP, TCP_PORT, 'D') # Raspberry Pi'ye Durdur komutu gönderiliyor
        
    def go(self):
        self.komut_gonder_tcp(TCP_IP, TCP_PORT, 'I') # Raspberry Pi'ye İleri komutu gönderiliyor
    
    def back(self):
        self.komut_gonder_tcp(TCP_IP, TCP_PORT, 'G') # Raspberry Pi'ye Geri komutu gönderiliyor
        
    def create_lists(self):
        self.x_pos = []
        self.y_pos = []
        self.z_pos = []
        
        self.x_speed = []
        self.y_speed = []
        self.z_speed = []
        
        self.x_acc = []
        self.y_acc = []
        self.z_acc = []
        
        self.x_ori = []
        self.y_ori = []
        self.z_ori = []
        
        self.time = []
        
        self.battery_percentage = 0
        
    def data_convert(self, data):
        try:
            data = json.loads(data) # JSON stringi dict'e çevriliyor
            print(data)
            # Bu kısımda    ilgili data alınarak listeye ekleniyor
            self.x_pos.append(random.randint(1,100))
            self.y_pos.append(random.randint(1,100))
            self.z_pos.append(random.randint(1, 100))
        
            self.x_speed.append(random.randint(1,100))
            self.y_speed.append(random.randint(1, 10))
            self.z_speed.append(random.randint(1, 10))
        
            self.x_acc.append(float(data["acc_x"]))
            self.y_acc.append(float(data["acc_y"]))
            self.z_acc.append(float(data["acc_z"]))
        
            self.x_ori.append(float(data["roll"]))
            self.y_ori.append(float(data["pitch"]))
            self.z_ori.append(float(data["yaw"]))
        
            self.temp_1 = float(data["sicaklik_1"])
            self.temp_2 = float(data["sicaklik_2"])
            self.power = random.randint(1, max_power)
            #self.power = float(data["guc"])
            
            self.battery_percentage = (self.power / max_power) * 100 #bateri yüzdesi ayarlanıyor

            self.time.append(time.time() - self.start_time) 
        
            #Gelen verilerle grafik çizdirme
            self.draw_graph(self.main.graph_position, self.time, self.x_pos, self.y_pos, self.z_pos, "Konum (cm)")
            self.draw_graph(self.main.graph_speed, self.time, self.x_speed, self.y_speed, self.z_speed, "Hız (m/s)")
            self.draw_graph(self.main.graph_acc, self.time, self.x_acc, self.y_acc, self.z_acc, "İvme (m/s²)")
            self.draw_graph(self.main.graph_ori, self.time, self.x_ori, self.y_ori, self.z_ori, "Yönelim ()")
        
            #Gelen verileri gui da gösterme
            self.main.label_position.setText(f"X --> {self.x_pos[-1]:.2f} cm\nY --> {self.y_pos[-1]:.2f} cm\nZ --> {self.z_pos[-1]:.2f} cm")
            self.main.label_speed.setText(f"X --> {self.x_speed[-1]:.2f} m/s\nY --> {self.y_speed[-1]:.2f} m/s\nZ --> {self.z_speed[-1]:.2f} m/s")
            self.main.label_acc.setText(f"X --> {self.x_acc[-1]:.2f} m/s²\nY --> {self.y_acc[-1]:.2f} m/s²\nZ --> {self.z_acc[-1]:.2f} m/s²")
            self.main.label_ori.setText(f"X --> {self.x_ori[-1]:.2f}\nY --> {self.y_ori[-1]:.2f}\nZ --> {self.z_ori[-1]:.2f}")
        
            self.draw_temp() # Grafik üzerinde sıcaklık göstergesi
            self.main.label_temp.setText(f"T1 --> {self.temp_1} °C\nT2 --> {self.temp_2:.2f} °C") # Sıcaklık verilerini GUI üzerinde gösterme
    
            self.draw_power() # Grafik üzerinde güç göstergesi
            self.main.label_watt.setText(f"{self.power:.2f} W") # Güç verilerini GUI üzerinde gösterme
            self.main.label_watt_2.setText(f"{self.power:.2f} W")
            
            self.main.label_date.setText(datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")) # Tarih ve saat göstergesi
            
            self.main.label_batarya.setText(f"{self.battery_percentage:.2f}%") # Batarya verilerini GUI üzerinde gösterme
            
        except Exception as e:
            print(f"Veri hatası: {e}")     
        
    def draw_graph(self, frame, t, y1, y2, y3, title):
        graph = MplCanvas(frame, width=5, height=4, dpi=100) # Grafik ekranı oluşturuluyor
        
        # Grafik düzenlemeleri yapılıyor
        graph.axes.plot(t, y1, color='red',label='X') 
        graph.axes.plot(t, y2, color='green',label='Y')
        graph.axes.plot(t, y3, color='blue',label='Z')
        
        if len(t) > 5:
            graph.axes.set_xlim(t[-5], t[-1])  
            
        elif len(t) == 1:
            graph.axes.set_xlim(0, 1) 
        else:
            graph.axes.set_xlim(t[0], t[-1])
        
        graph.axes.set_facecolor('#323232') # Grafik rengi
        graph.axes.set_title(title, color='white')
        legend = graph.axes.legend(loc='upper right') #Grafiğin sağ üst köşesine legend çiziliyor
            
        for label in graph.axes.get_xticklabels() + graph.axes.get_yticklabels(): # X ve Y eksenindeki labellerin rengi değiştiriliyor
            label.set_color('white')
        
        layout = frame.layout() # Frame'ın layout'ı alınıyor
        
        # Layout'daki widgetler temizleniyor ve yeniden ekleniyor
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        
        layout.addWidget(graph)
        
    def draw_temp(self):
        #Sıcaklık verileri için bir gösterge oluşturuluyor
        base_style =("#frame_t1{\n"
"    background-color: qlineargradient(spread:pad, x1:1, y1:1, x2:1, y2:0, stop:{STOP_1} rgba(69, 150, 255, 255), stop:{STOP_2} rgba(255, 255, 255, 0));\n"
"}")
        
        temp_progress_p1 = self.temp_1 / max_temp
        temp_progress_p2 = self.temp_2 / max_temp

        stop_1_p1 = str(temp_progress_p1 - 0.001)
        stop_2_p1 = str(temp_progress_p1)

        stop_1_p2 = str(temp_progress_p2 - 0.001)
        stop_2_p2 = str(temp_progress_p2)

        if temp_progress_p1 > 0.008 * max_temp and temp_progress_p2 > 0.008 * max_temp:
            new_style_p1 = base_style.replace("{STOP_1}", stop_1_p1).replace("{STOP_2}", stop_2_p1).replace("rgba(69, 150, 255, 255)", "rgba(216, 82, 55, 255)")
            new_style_p2 = base_style.replace("{STOP_1}", stop_1_p2).replace("{STOP_2}", stop_2_p2).replace("frame_t1", "frame_t2").replace("rgba(69, 150, 255, 255)", "rgba(216, 82, 55, 255)")
            self.main.frame_full.setStyleSheet("""#frame_full{
	background-color: rgba(216, 82, 55, 255);
	border-radius:22px
}""")
            
        else:
            new_style_p1 = base_style.replace("{STOP_1}", stop_1_p1).replace("{STOP_2}", stop_2_p1)
            new_style_p2 = base_style.replace("{STOP_1}", stop_1_p2).replace("{STOP_2}", stop_2_p2).replace("frame_t1", "frame_t2")
            self.main.frame_full.setStyleSheet("""#frame_full{
	background-color: rgb(69, 150, 255);
	border-radius:22px
}""")

        self.main.frame_t1.setStyleSheet(new_style_p1)
        self.main.frame_t2.setStyleSheet(new_style_p2)

        
    def draw_power(self):
        # Güç verileri için bir gösterge oluşturuluyor
        base_style =("#frame_power{\n"
"background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:{STOP_1} rgba(255, 255, 255, 0), stop:{STOP_2} rgba(69, 150, 255, 255));\n"
"border-radius:90px\n"
"}")

        watt_pressure = float((max_power-self.power) / (max_power))

        stop_1 = str(watt_pressure - 0.001)
        stop_2 = str(watt_pressure)

        new_style = base_style.replace("{STOP_1}", stop_1).replace("{STOP_2}", stop_2)

        self.main.frame_power.setStyleSheet(new_style)
        
if __name__ == "__main__":
    app = QApplication(sys.argv) # QApplication objesi oluşturuluyor
    main = Main() # Ana ekran objesi
    main.show() # Ana ekran açılıyor
    sys.exit(app.exec_()) # QApplication'ın işini bitirmesi için çağrılıyor
