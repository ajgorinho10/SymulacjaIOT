import tkinter as tk
import API.klientAPI as klientAPI
import threading
import random
import time

class Device:
    def __init__(self):
        self.klient = klientAPI.klientAPI()

    def generate_sensor_data(self):
        temperature = round(random.uniform(18.0, 25.0), 2)
        humidity = random.randint(40, 60)
        data = {
            "device_id": self.klient.DEVICE_NAME,
            "timestamp": time.time(),
            "temperature": temperature,
            "humidity": humidity
        }
        return data
    
    def start(self,TLS):
        self.klient.data_to_send = self.generate_sensor_data
        self.klient.start(TLS)

class KlientGUI:
    def __init__(self,root):
        self.root = root
        self.root.title("Klient")
        self.root.geometry("800x600")
        self.___createWindow()

        self.TLS = True
        self.deviceListThread = list()
        th = threading.Thread(target=self.petla)
        th.start()

    def ___createWindow(self):
        #menu
        self.selected_option = tk.StringVar(value="Bez TLS")
        main_menu = tk.Menu(self.root)
        self.root.config(menu=main_menu)

        options_menu = tk.Menu(main_menu, tearoff=0)
        main_menu.add_cascade(label="Typ połączenia", menu=options_menu)

        options_menu.add_radiobutton(
            label="Bez TLS", 
            variable=self.selected_option, 
            value="Bez TLS",
            command=self.on_option_change
        )
        options_menu.add_radiobutton(
            label="Z TLS", 
            variable=self.selected_option, 
            value="Z TLS",
            command=self.on_option_change
        )


        #Lista urządzeń
        left_frame = tk.Frame(self.root,background="#777272",width=100,relief="ridge",borderwidth=3) 
        left_frame.pack(side=tk.LEFT,expand=False,fill=tk.Y)
        self.deviceListLabel = tk.Label(left_frame,text="Urządzenia",background="#777272").pack(padx=5,pady=5,side=tk.TOP)

        scrollBar = tk.Scrollbar(left_frame, orient=tk.VERTICAL)
        self.deviceList = tk.Listbox(left_frame, yscrollcommand=scrollBar.set, height=15, width=40)
        scrollBar.config(command=self.deviceList.yview)
        
        scrollBar.pack(side=tk.RIGHT, fill=tk.Y)
        self.deviceList.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        #Wszystkie urządzenia
        top_frame = tk.Frame(self.root,background="#948F8F",relief="ridge",borderwidth=3)
        top_frame.pack(fill=tk.BOTH)
        
        self.startNewDevice = tk.Button(top_frame,text="Dodaj urządzenie",command=self.__startNewDevice).pack(side=tk.RIGHT,padx=5,pady=5)

        #Logi
        bottom_frame = tk.Frame(self.root,background="#948F8F",relief="ridge",borderwidth=3)
        bottom_frame.pack(fill=tk.BOTH,pady=2,expand=True)

        bottom_frame_info = tk.Frame(bottom_frame,background="#948F8F")
        bottom_frame_info.pack(fill=tk.BOTH,expand=False)
        bottom_frame_label = tk.Label(bottom_frame_info,text="Logi",background="#948F8F").pack(side=tk.LEFT,padx=5,pady=5,expand=False)
        self.clearLogButton = tk.Button(bottom_frame_info,text="Wyczyść logi",command=self.__clearLog).pack(side=tk.RIGHT,padx=5,pady=5,expand=False)

        bottom_frame_log = tk.Scrollbar(bottom_frame, orient=tk.VERTICAL)
        self.logText = tk.Text(bottom_frame, state="disabled", yscrollcommand=bottom_frame_log.set, height=10, bg="#f0f0f0")
        bottom_frame_log.config(command=self.logText.yview)

        bottom_frame_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.logText.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.__log("Aplikacja uruchomiona. Uruchom klienta!")

    def on_option_change(self):

        if len(self.deviceListThread) == 0:
            new_value = self.selected_option.get()
            if new_value == "Z TLS":
                self.TLS = True
            else:
                self.TLS = False
            
            self.__log(f"Wybrane połączenie: {new_value}")
        
        else:
            self.__log(f"Odłącz urządzenia aby zmienić typ połączenia")

    def __startNewDevice(self):
        device = Device()
        device.start(self.TLS)

        self.deviceListThread.append(device)
        self.deviceList.insert(tk.END,device.klient.DEVICE_NAME)

    def __log(self, message):
        self.logText.config(state="normal")
        self.logText.insert(tk.END, str(message) + "\n")
        self.logText.see(tk.END)
        self.logText.config(state="disabled")
    
    def __clearLog(self):
        self.logText.config(state="normal")
        self.logText.delete("1.0", tk.END)
        self.logText.config(state="disabled")

    def usun_klienta_po_nazwie(self,listbox, nazwa_klienta):

        wszystkie_elementy = listbox.get(0, tk.END)
        indeks_do_usuniecia = -1

        for i, element in enumerate(wszystkie_elementy):
            if element == nazwa_klienta:
                indeks_do_usuniecia = i
                break

        if indeks_do_usuniecia != -1:
            listbox.delete(indeks_do_usuniecia)

    def __appendLogFromDevice(self):
        for device in self.deviceListThread:

            if not device.klient.clientThread.is_alive():
                self.__log(f"Urządzenie:{device.klient.DEVICE_NAME} zostało rozłączone")
                self.usun_klienta_po_nazwie(self.deviceList,device.klient.DEVICE_NAME)
                self.deviceListThread.remove(device)

            if not device.klient.logs:
                continue

            self.__log(device.klient.logs)
            device.klient.logs = list()

    def petla(self):
        while True:
            self.__appendLogFromDevice()
            time.sleep(1)


if __name__ == "__main__":
    root = tk.Tk()
    app = KlientGUI(root)
    root.mainloop()     