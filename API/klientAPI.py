import socket
import random
import time
import ssl
import threading

import API.SendReciveData as SendReciveData

class klientAPI:

    def __init__(self):
        self.DEVICE_NAME = f"sensor_v1_{random.randint(1000, 9999)}"
        self.DESTINATION_NAME = f"Server"
        self.serverAddr = (SendReciveData.SERVER_ip,SendReciveData.PORT)
        self.logs = list()

        self.__context = None
        self.__client = None
        self.__secureClient = None
        self.clientThread = None
        self.__lock = threading.Lock()

        self.data_to_send=None
        self.commands=[]

    def __client_startTLS(self):
        if self.__client == None:
            self.__context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self.__context.load_verify_locations('cert.pem')
            self.__context.check_hostname = False

            self.__client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.__client.connect(self.serverAddr)

            self.__secureClient = self.__context.wrap_socket(self.__client, server_hostname=SendReciveData.SERVER_ip)

            connected = True
            while connected:
                msg = SendReciveData.recive_msg(self.__secureClient)
                connected = self.__next_action(msg,self.__secureClient)
                
            self.__secureClient.close()

    def __client_start(self):
        if self.__client == None:
            self.__client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.__client.connect((SendReciveData.SERVER_ip,SendReciveData.PORT))

            connected = True
            while connected != False:
                msg = SendReciveData.recive_msg(self.__client)
                connected = self.__next_action(msg,self.__client)
                
            self.__client.close()
    
    def start(self,TLS=False):
        if TLS:
            self.clientThread = threading.Thread(target=self.__client_startTLS)
            self.clientThread.start()
        else:
            self.clientThread = threading.Thread(target=self.__client_start)
            self.clientThread.start()

    def __next_action(self,data,conn):
        data = SendReciveData.data_typ_deserialize(data)

        if data.get('action') == "DATA":
            self.logs.append(f"Urządzenie: {self.DEVICE_NAME} przesłało DATA do serwera")
            SendReciveData.send_msg(SendReciveData.data_type_serialized("DATA","OK",self.data_to_send()),conn)

        if data.get('action') == "ALIVE":
            self.logs.append(f"Urządzenie: {self.DEVICE_NAME} przesłało ALIVE do serwera")
            SendReciveData.send_response_msg(conn,"ALIVE","OK")

        if data.get('action') == "COMMAND":
            self.__execute_command(data)
            self.logs.append(f"Urządzenie: {self.DEVICE_NAME} OTRZYMAŁO KOMENDE do serwera")
            SendReciveData.send_response_msg(conn,"ALIVE","OK")

        if data.get('action') == SendReciveData.DISCONNECT_MESSAGE:
            return False

        return True
        
    def __execute_command(self,data):
        command,value = data.get('data').split(":")
        with self.__lock:
            self.commands.append({f"{command}:{value}"})

    def get_commands(self):
        with self.__lock:
            comands =  list(self.commands)
            self.commands = []
            return comands
        
