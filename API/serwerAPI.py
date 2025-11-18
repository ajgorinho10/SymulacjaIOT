import socket
import threading
import time
import ssl

import API.SendReciveData as SendReciveData

class serwerApi:
    def __init__(self):
        self.ActiveDevices = {}
        self.TimeToCheckAlive = 10.0
        self.TimeToGetData = 30.0
        self.ADDR_SERVER = (SendReciveData.SERVER_ip,SendReciveData.PORT)
        self.serverThred = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

    def __start_serverTLS(self,cert=False):

        contex = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        try:
            contex.load_cert_chain(certfile="cert.pem",keyfile="key.key")
        except FileNotFoundError:
            print("certiticat file not found!")
            return

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(self.ADDR_SERVER)
        server.listen()
        server.settimeout(1.0)
        secureConn = contex.wrap_socket(server, server_side=True)

        while not self.stop_event.is_set():
            try:
                conn,addr = secureConn.accept()
                addr_str = f"{addr[0]}:{addr[1]}"

                with self.lock:
                    self.ActiveDevices[addr_str] = conn

            except socket.timeout:
                continue

            except Exception as e:
                print("Błąd")

        self.stop_event.clear()
        server.close()   

    def __start_server(self,cert=False):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(self.ADDR_SERVER)
        server.settimeout(1.0)
        server.listen()

        while not self.stop_event.is_set():
            try:
                conn,addr = server.accept()
                addr_str = f"{addr[0]}:{addr[1]}"
                with self.lock:
                    self.ActiveDevices[addr_str] = conn

            except socket.timeout:
                continue
        
        self.stop_event = threading.Event()
        server.close()

    def startWithTLS(self):
        self.serverThred = threading.Thread(target=self.__start_serverTLS)
        self.serverThred.start()

    def start(self):
        self.serverThred = threading.Thread(target=self.__start_server)
        self.serverThred.start()

    def stop(self):
        self.stop_event.set()
        self.serverThred.join()
        self.serverThred = None

    def IsDevicesAlive(self):

        deviceToRemove = []
        with self.lock:
            DevicesToCheck = list(self.ActiveDevices.items())

        for addr_str,conn in DevicesToCheck:
            try:
                conn.settimeout(3.0)
                response = SendReciveData.ALIVE_MSG(conn)
                conn.settimeout(None)

                if not response and response.get('action') != "ALIVE":
                    deviceToRemove.append(addr_str)
            
            except socket.timeout:
                deviceToRemove.append(addr_str)

            except Exception as e:
                deviceToRemove.append(addr_str)
                try:
                    conn.settimeout(None)
                except:
                    pass
                continue

        for addr_str in deviceToRemove:
            self.TryCloseConnection(addr_str)

    def IsDeviceAlive(self,conn,addr_str):
        deviceToRemove = ""
        with self.lock:
            DevicesToCheck = list(self.ActiveDevices.items())
        
        try:
            conn.settimeout(3.0)
            response = SendReciveData.ALIVE_MSG(conn)
            conn.settimeout(None)

            if not response and response.get('action') != "ALIVE":
                deviceToRemove = addr_str
            
        except socket.timeout:
                deviceToRemove = addr_str

        except Exception as e:
            deviceToRemove = addr_str
            try:
                conn.settimeout(None)
            except:
                pass
            
        if deviceToRemove == "":
            return True
        
        self.TryCloseConnection(addr_str)
        return False

        
                    
    def TryCloseConnection(self,addr_str):
        try:
            with self.lock:
                conn = self.ActiveDevices[addr_str]
                self.ActiveDevices.pop(addr_str)
            conn.close()
            return True
        
        except Exception as e:
            return False     

    def GetDataFromDevice(self,conn,addr):
        self.IsDeviceAlive(conn,addr)
        return SendReciveData.GET_DATA_MSG(conn)

    def GetDataFromAllDevices(self):
        self.IsDevicesAlive()

        with self.lock:
            Devices = list(self.ActiveDevices.items())
        data = []
        for addr_str,conn in Devices:
            response = SendReciveData.GET_DATA_MSG(conn)
            if response:
                data.append(response)
        
        return data
    
    def SendCommand(self,conn,command,value):
        response = SendReciveData.COMMAND_MSG(conn,command,value)
        if response and response.get('action') == "ALIVE":
            return True
        
        return False
    
    def DisconnedFromDevice(self,conn,addr_str):
        SendReciveData.disconnect_MSG(conn)
        return self.TryCloseConnection(addr_str)
    
    def DisconnedAllDevices(self):
        Devices = list(self.ActiveDevices.items())
        for addr_str,conn in Devices:
            SendReciveData.disconnect_MSG(conn)
            self.TryCloseConnection(addr_str)
    
    


