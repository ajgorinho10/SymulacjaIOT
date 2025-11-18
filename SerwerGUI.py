import tkinter as tk
import API.serwerAPI as serwerAPI
from tkinter import messagebox
import time
import threading

class DoubleEntryDialog(tk.Toplevel):
    """
    Niestandardowe okno dialogowe do wprowadzenia dwóch wartości.
    """
    def __init__(self, parent, title="Wprowadź dwie wartości"):
        super().__init__(parent)
        self.title(title)
        self.parent = parent
        
        # Zmienna do przechowywania wyników
        self.result = None 

        # --- Tworzenie widżetów ---
        
        # Ramka na pola tekstowe
        entry_frame = tk.Frame(self, padx=15, pady=10)
        entry_frame.pack()

        # Pierwsza wartość
        self.label1 = tk.Label(entry_frame, text="Wartość 1:")
        self.label1.grid(row=0, column=0, sticky="w", pady=5)
        self.entry1 = tk.Entry(entry_frame)
        self.entry1.grid(row=0, column=1)

        # Druga wartość
        self.label2 = tk.Label(entry_frame, text="Wartość 2:")
        self.label2.grid(row=1, column=0, sticky="w", pady=5)
        self.entry2 = tk.Entry(entry_frame)
        self.entry2.grid(row=1, column=1)
        
        # Ramka na przyciski
        button_frame = tk.Frame(self)
        button_frame.pack(pady=(0, 10))

        self.ok_button = tk.Button(button_frame, text="OK", command=self.on_ok)
        self.ok_button.pack(side=tk.LEFT, padx=10)
        
        self.cancel_button = tk.Button(button_frame, text="Anuluj", command=self.on_cancel)
        self.cancel_button.pack(side=tk.LEFT, padx=10)

        # --- Kluczowa mechanika (blokowanie) ---

        # Ustaw fokus na pierwszym polu
        self.entry1.focus_set()
        
        # Powiąż klawisz Enter z funkcją on_ok
        self.bind("<Return>", self.on_ok)
        # Powiąż klawisz Escape z funkcją on_cancel
        self.bind("<Escape>", self.on_cancel)

        # 1. Uczyń okno "transient" (zawsze na wierzchu)
        self.transient(parent)
        
        # 2. Zablokuj interakcje z oknem nadrzędnym
        self.grab_set()
        
        # 3. Wstrzymaj działanie kodu nadrzędnego, dopóki to okno nie zostanie zamknięte
        self.wait_window(self)

    def on_ok(self, event=None):
        """Obsługa kliknięcia OK lub naciśnięcia Enter."""
        val1 = self.entry1.get()
        val2 = self.entry2.get()

        # Prosta walidacja (opcjonalna)
        if not val1 or not val2:
            messagebox.showwarning("Błąd", "Wszystkie pola muszą być wypełnione!", parent=self)
            return

        self.result = (val1, val2)
        self.destroy() # Zamknij to okno

    def on_cancel(self, event=None):
        """Obsługa kliknięcia Anuluj lub naciśnięcia Escape."""
        self.result = None # Sygnalizuj anulowanie
        self.destroy() # Zamknij to okno

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Serwer")
        self.root.geometry("800x600")

        self.serwer = serwerAPI.serwerApi()
        self.serwerTLS = False
        self.refreshThread = None

        self.selectedDevice = ()
        self.stopRefresh = threading.Event()

        self.__createWindow()

    def __createWindow(self):
        
        #menu
        self.selected_option = tk.StringVar(value="Bez TLS")
        main_menu = tk.Menu(self.root)
        self.root.config(menu=main_menu)
        server_menu = tk.Menu(main_menu, tearoff=0)
        main_menu.add_cascade(label="Serwer", menu=server_menu)

        server_menu.add_command(label="Uruchom serwer", command=self.__start_server)
        server_menu.add_command(label="Zatrzymaj serwer", command=self.__stop_server)
        server_menu.add_separator()
        server_menu.add_command(label="Wyjście", command=self.quit_app)

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
        self.refreshButton = tk.Button(left_frame,text="Odświerz listę urządzeń",command=self.__refreshAllDevices).pack(side=tk.BOTTOM,expand=False,fill=tk.BOTH,padx=5,pady=5)
        left_frame.pack(side=tk.LEFT,expand=False,fill=tk.Y)
        self.deviceListLabel = tk.Label(left_frame,text="Połączone urządzenia",background="#777272").pack(padx=5,pady=5,side=tk.TOP)

        scrollBar = tk.Scrollbar(left_frame, orient=tk.VERTICAL)
        self.deviceList = tk.Listbox(left_frame, yscrollcommand=scrollBar.set, height=15, width=40)
        scrollBar.config(command=self.deviceList.yview)
        
        scrollBar.pack(side=tk.RIGHT, fill=tk.Y)
        self.deviceList.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


        #Wszystkie urządzenia
        top_frame = tk.Frame(self.root,background="#948F8F",relief="ridge",borderwidth=3)
        top_frame.pack(fill=tk.BOTH)
        
        top_frame_label = tk.Label(top_frame,text="Akcje dla wszyskich urzadzen",background="#948F8F").pack(anchor="w",padx=5,pady=5)
        self.getAllDataButtonButton = tk.Button(top_frame,text="Pobierz dane ",command=self.__getAllData).pack(side=tk.LEFT,padx=5,pady=5)
        self.refreshAllDevicesButton = tk.Button(top_frame,text="Odświerz urzadzenia",command=self.__refreshAllDevices).pack(side=tk.LEFT,padx=5,pady=5)
        self.disconnectAllDevicesButton = tk.Button(top_frame,text="Rozłącz",command=self.__disconnectAllDevices).pack(side=tk.RIGHT,padx=5,pady=5)


        #Wybrane urządzenie
        midle_frame = tk.Frame(self.root,background="#948F8F",relief="ridge",borderwidth=3)
        midle_frame.pack(fill=tk.BOTH,pady=5)
        midle_frame_label = tk.Label(midle_frame,text="Akcje dla wybranego urządzenia",background="#948F8F").pack(anchor="w",padx=5,pady=5)
        self.getDataButton = tk.Button(midle_frame,text="Pobierz dane ",command=self.__getData).pack(side=tk.LEFT,padx=5)
        self.refreshDeviceButton = tk.Button(midle_frame,text="Odświerz urzadzenie",command=self.__refreshDevice).pack(side=tk.LEFT,padx=5)
        self.disconnectDeviceButton = tk.Button(midle_frame,text="Rozłącz",command=self.__disconnectDevice).pack(side=tk.RIGHT,padx=5,pady=5)
        self.sendCommandButton = tk.Button(midle_frame,text="Wprowadz komende",command=self.__insertCommand).pack(side=tk.LEFT,padx=5,pady=5)


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
        self.__log("Aplikacja uruchomiona. Uruchom serwer!")

    def __start_server(self):
        if self.serwer.serverThred != None:
            self.__log("Serwer jest już uruchomiony!")
            return
        
        if self.serwerTLS:
            self.__log("Uruchamianie Serwera w trybie TLS...")
            self.serwer.startWithTLS()
        else:
            self.__log("Uruchamianie Serwera...")
            self.serwer.start()
        
        self.__log("Serwer działa!")
        self.refreshThread = threading.Thread(target=self.refreshBy3sec)
        self.refreshThread.start()

    def __stop_server(self):
        self.__log("Czekaj!, zatrzymanie Serwera...")
        self.serwer.DisconnedAllDevices()
        self.serwer.stop()
        
        self.deviceList.delete(0,tk.END)
        self.stopRefresh.set()
        self.refreshThread.join()
        self.__log("Serwer wyłączony!")

    def __refreshAllDevices(self):
        selected_text = None
        try:
            selected_indices = self.deviceList.curselection()
            if selected_indices:
                selected_index = selected_indices[0]
                selected_text = self.deviceList.get(selected_index)
        except tk.TclError:
            pass

        self.serwer.IsDevicesAlive()
        device_keys = list(self.serwer.ActiveDevices.keys())

        self.deviceList.delete(0, tk.END) 

        if not device_keys:
            return

        for addr_str in device_keys:
            self.deviceList.insert(tk.END, addr_str)

        if selected_text:
            try:
                new_index = device_keys.index(selected_text)
                self.deviceList.select_set(new_index)
                self.deviceList.activate(new_index)
                self.deviceList.see(new_index)
                
            except ValueError:
                pass
 
    def __refreshDevice(self):
        addr,conn = self.__GetSelectedDevice()
        if addr and conn :
            Connected = self.serwer.IsDeviceAlive(conn,addr)
            if Connected:
                self.__log(f"Urządzenie {addr} jest aktywne!")
            else:
                self.__log(f"Urządzenie {addr} nie jest aktywne!")
        else:
            return

    def __getAllData(self):
        data = self.serwer.GetDataFromAllDevices()
        if data == []:
            self.__log("Brak połączonych urządzeń")
        else:
            self.__log(data)

    def __getData(self):
        addr,conn = self.__GetSelectedDevice()
        if addr and conn :
            self.__log(self.serwer.GetDataFromDevice(conn,addr))
        else:
            return
        
    def __disconnectAllDevices(self):
        
        device_keys = list(self.serwer.ActiveDevices.keys())
        if len(device_keys) != 0:
            self.serwer.DisconnedAllDevices()
            self.deviceList.delete(0,tk.END)
        else:
            self.__log("Brak połączonych urządzeń")

    def __disconnectDevice(self):
        addr,conn = self.__GetSelectedDevice()
        if addr and conn :
            self.__log(f"Rozłączono z {addr}")
            self.serwer.DisconnedFromDevice(conn,addr)
        else:
            return

    def __insertCommand(self):
        addr,conn = self.__GetSelectedDevice()
        if addr and conn :
            dialog = DoubleEntryDialog(self.root,title="Podaj komende i wartość")
            if dialog.result:
                command, value = dialog.result
                result = self.serwer.SendCommand(conn,command,value)
                if result:
                    self.__log(f"Komenda: {command} o wartości: {value} wykonana pomyślnie!")
                else:
                    self.__log(f"Komenda: {command} o wartości: {value} nie została wykonana!")
        else:
            return

    def __GetSelectedDevice(self):
        try:
            selected_index = self.deviceList.curselection()[0]
            selected_addr = self.deviceList.get(selected_index)
            with self.serwer.lock:
                selected_conn = self.serwer.ActiveDevices[selected_addr]
                self.selectedDevice = (selected_addr,selected_conn)
            return selected_addr, selected_conn
        except (IndexError, KeyError):
            messagebox.showerror("Błąd", "Nie wybrano żadnego urządzenia z listy.")
            return None, None

    def __log(self, message):
        self.logText.config(state="normal")
        self.logText.insert(tk.END, str(message) + "\n")
        self.logText.see(tk.END)
        self.logText.config(state="disabled")

    def __clearLog(self):
        self.logText.config(state="normal")
        self.logText.delete("1.0", tk.END)
        self.logText.config(state="disabled")

    def on_option_change(self):
        new_value = self.selected_option.get()
        if new_value == "Z TLS":
            self.serwerTLS = True
        else:
            self.serwerTLS = False
        
        self.__log(f"Wybrane połączenie: {new_value}")

    def quit_app(self):
        if messagebox.askokcancel("Wyjście", "Czy na pewno chcesz zamknąć aplikację?"):
            self.root.destroy()

    def refreshBy3sec(self):
        while not self.stopRefresh.is_set():
            self.__refreshAllDevices()

            interrupted = self.stopRefresh.wait(timeout=3.0) 
            if interrupted:
                break
        
        self.refreshThread = None
        self.stopRefresh = threading.Event()

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()