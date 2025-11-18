import socket
import json
import random
import time

HEADER = 64
PORT = 5050
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
DEVICE_NAME = ""
DEVICE_ID = ""
DESTINATION_NAME = ""
SERVER_ip = "127.0.0.1"


def send_msg(msg, client):
    message = msg.encode(FORMAT)
    msg_lenght = len(message)
    send_lenght = str(msg_lenght).encode(FORMAT)
    send_lenght += b' ' * (HEADER - len(send_lenght))
    client.send(send_lenght)
    client.send(message)


def recive_msg(conn):
    try:
        msg_lenght = conn.recv(HEADER).decode(FORMAT)
        if msg_lenght:
            msg_lenght = int(msg_lenght)
            msg = conn.recv(msg_lenght).decode(FORMAT)

            if (msg == DISCONNECT_MESSAGE):
                return False

            return msg
        return None
    except Exception:
        return False


def data_type(action, status, data=None):
    if data is None:
        return {"action": action, "status": status}
    else:
        return {"action": action, "status": status, "data": data}

def data_type_serialized(action, status, data=None):
    tmp = data_type(action, status, data)
    return json.dumps(tmp)

def data_typ_deserialize(data):
    if data:
        try:
            data = json.loads(data)
            return data
        except json.JSONDecodeError:
            return False
    return False


def send_response_msg(conn, action_type, status="OK", data=None):
    tmp = data_type_serialized(action_type, status, data)
    send_msg(tmp, conn)


def ALIVE_MSG(conn):
    newData = data_type_serialized("ALIVE", "REQUEST")
    send_msg(newData, conn)
    
    response = recive_msg(conn)
    return data_typ_deserialize(response)

def GET_DATA_MSG(conn):
    tmp = data_type_serialized("DATA", "REQUEST")
    send_msg(tmp, conn)

    response = recive_msg(conn)
    return data_typ_deserialize(response)

def COMMAND_MSG(conn, command, value):
    tmp = data_type_serialized("COMMAND", "REQUEST", f"{command}:{value}")
    send_msg(tmp, conn)

    response = recive_msg(conn)
    return data_typ_deserialize(response)

def disconnect_MSG(conn):
    tmp = data_type_serialized(DISCONNECT_MESSAGE, "OK")
    send_msg(tmp, conn)