# 소켓을 사용하기 위해서는 socket을 import해야 한다.
import pickle
import socket
import struct
import threading
import time
from datetime import datetime

import cv2

from mod.RecModule import file
from mod.cacheIO import addSocketInTable, delSocketInTable, noticeError

lock = threading.Lock()
structure = ['latitude', 'longitude', 'locationNumber', 'deviceType', 'localtime']


def sendCommand(cs, sendMsg: str):
    sendData_Byte = sendMsg.encode('cp949')
    sendDataLength = len(sendData_Byte)
    cs.sendall(sendDataLength.to_bytes(4, byteorder='big'))
    cs.sendall(sendData_Byte)


def sendCommandForActuator(cs: socket.socket, ad, f: file):
    time.sleep(2.0)
    now = datetime.now()
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    sendMsg = ""
    sendMsg += (date_time + ".")
    sendMsg += str(sensorDataOfClient[ad[0]]['emergencySwitch'])  # " / 경찰 신고 접수"  # actuator 동작 코드 전송 부분
    lock.acquire()
    if sensorDataOfClient[ad[0]]['emergencySwitch'] == 1:
        f.logWriter(
            "위도 : " + dnsTable[ad[0]][0]['latitude'] + ", 경도 : " + dnsTable[ad[0]][0]['longitude'] + " : 긴급 신고 접수 \n\n",
            ad)
        print(
            "위도 : " + dnsTable[ad[0]][0]['latitude'] + ", 경도 : " + dnsTable[ad[0]][0]['longitude'] + " : 긴급 신고 접수 ")
    if sensorDataOfClient[ad[0]]['lightDetection'] < 200 and sensorDataOfClient[ad[0]]['distanceDetection'] > 500:
        sendMsg += '.1'  # " /  어두움 + 거리가 좁혀짐 = 점등"  # actuator 동작 코드 전송 부분
    else:
        sendMsg += '.0'  # " /  아무 작업 안함."  # actuator 동작 코드 전송 부분
    lock.release()
    sendCommand(cs, sendMsg)
    return sendMsg


def binder(client_socket: socket.socket, binder_addr, binder_log: file):
    global dnsTable

    print('Connected by', binder_addr)

    client_socket_config = {
        # "client_socket": client_socket,
    }

    try:
        data = client_socket.recv(4)
        length = int.from_bytes(data, "big")
        data = client_socket.recv(length)
        msg = data.decode(encoding="cp949")

        client_socket_config_list = msg.split(';')

        for a, b in zip(structure, client_socket_config_list):
            client_socket_config[a] = b

        print('Received from', binder_addr, msg)

        duplicateCheck = addSocketInTable(dnsTable, lock, binder_addr[0], client_socket_config)

        if not duplicateCheck:
            return False

        print(dnsTable)
        if not binder_addr[0] in sensorDataOfClient:
            sensorDataOfClient[binder_addr[0]] = {'emergencySwitch': 0, 'distanceDetection': 0, 'lightDetection': 0}
        while True:
            client_socket.settimeout(10)

            if client_socket_config['deviceType'] == 'actuator':
                msg = sendCommandForActuator(client_socket, binder_addr, binder_log)
                print(binder_addr[0], " : ", sensorDataOfClient[binder_addr[0]], " / ", msg)
                binder_log.logWriter(msg + "\n\n", binder_addr)


            elif client_socket_config['deviceType'] == 'camera':
                data = b""
                payload_size = struct.calcsize(">L")
                while True:
                    while len(data) < payload_size:
                        data += client_socket.recv(4096)
                    packed_msg_size = data[:payload_size]
                    data = data[payload_size:]
                    msg_size = struct.unpack(">L", packed_msg_size)[0]
                    while len(data) < msg_size:
                        data += client_socket.recv(4096)
                    frame_data = data[:msg_size]
                    data = data[msg_size:]

                    frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
                    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                    cv2.imshow(str(binder_addr), frame)
                    cv2.waitKey(1)
            else:
                data = client_socket.recv(4)
                length = int.from_bytes(data, "big")
                data = client_socket.recv(length)
                msg = data.decode(encoding="cp949")
                lock.acquire()
                sensorDataOfClient[binder_addr[0]][client_socket_config["deviceType"]] = int(msg)
                print(client_socket_config["deviceType"], " : ",
                      sensorDataOfClient[binder_addr[0]][client_socket_config["deviceType"]])
                lock.release()
                binder_log.logWriter(str(sensorDataOfClient[binder_addr[0]]) + "\n\n", binder_addr)

    except socket.error as exc:
        print(f"{client_socket_config['deviceType']} : Caught exception socket.error : {exc}")

    finally:
        if duplicateCheck:
            delSocketInTable(dnsTable, lock, binder_addr[0], client_socket_config)

        if client_socket_config['deviceType'] == 'camera':
            cv2.destroyAllWindows()

        noticeError(client_socket_config["deviceType"] + " : socket end")
        client_socket.close()


# 소켓을 만든다.
while True:
    if __name__ == '__main__':
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = int(input("port 를 입력하시오 : "))
        server_socket.bind(('', port))
        server_socket.listen()

        global dnsTable
        global sensorDataOfClient

        log = file("log.txt", 'a+')
        dnsTable = {}
        sensorDataOfClient = {}

        try:
            while True:
                client_socket, addr = server_socket.accept()
                th = threading.Thread(target=binder, args=(client_socket, addr, log))
                th.start()
        except:
            print("server")
        finally:
            server_socket.close()
