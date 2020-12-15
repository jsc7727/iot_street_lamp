# 소켓을 사용하기 위해서는 socket을 import해야 한다.
import pickle
import random
import socket
import struct
import threading
import time

import cv2


def makeStrFromDict(dic):
    retStr = ""
    for x in list(dic)[2:]:
        retStr += str(dic[x])
        retStr += ";"
    else:
        retStr = retStr[:-1]
    return retStr


def sendSensorData(client_socket: socket.socket, msg: str):
    sendMsg = msg
    sendData_Byte = sendMsg.encode('cp949')
    sendDataLength = len(sendData_Byte)
    client_socket.sendall(sendDataLength.to_bytes(4, byteorder='big'))
    client_socket.sendall(sendData_Byte)


def makeSockOfEachSensor(**sensor_config):
    while True:
        print(sensor_config['deviceType'], " : 시작")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.connect((host, port))
        try:
            deviceConfigStr = makeStrFromDict(sensor_config)

            print(deviceConfigStr, end="\n\n")
            client_socket.sendall(len(deviceConfigStr).to_bytes(4, byteorder='big'))
            client_socket.sendall(deviceConfigStr.encode('cp949'))

            while True:
                time.sleep(1.5)
                if sensor_config['deviceType'] == 'emergencySwitch':
                    sendMsg = str(random.randint(0, 1))  # 긴급 스위치가 눌렸으면 1 아니면 0
                    sendSensorData(client_socket, sendMsg)

                elif sensor_config['deviceType'] == 'distanceDetection':
                    # time.sleep(20)
                    sendMsg = str(random.randint(0, 1000))  # 소리 감지가 500 이상이면 사람이 있는것으로 봄
                    sendSensorData(client_socket, sendMsg)

                elif sensor_config['deviceType'] == 'lightDetection':
                    sendMsg = str(random.randint(0, 1000))  # 빛 감지가 200 이하면 밤이라고 본다.
                    sendSensorData(client_socket, sendMsg)
                else:
                    print('장치가 없음.')
                    break

        except socket.error as error:
            print(f"{sensor_config['deviceType']} : Caught exception socket.error : {error}")
        finally:
            client_socket.close()


def makeSockOfCamera(**sensor_config):
    while True:
        print(f"{sensor_config['deviceType']} : socket start")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.connect((host, port))

        client_socket.settimeout(10)
        try:
            deviceConfigStr = makeStrFromDict(sensor_config)
            print(deviceConfigStr, end="\n\n")
            client_socket.sendall(len(deviceConfigStr).to_bytes(4, byteorder='big'))
            client_socket.sendall(deviceConfigStr.encode('cp949'))

            cam = cv2.VideoCapture(0)
            cam.set(3, 320);
            cam.set(4, 240);
            img_counter = 0
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            while True:
                ret, frame = cam.read()
                result, frame = cv2.imencode('.jpg', frame, encode_param)
                data = pickle.dumps(frame, 0)
                size = len(data)
                # print("{}: {}".format(img_counter, size))
                client_socket.sendall(struct.pack(">L", size) + data)
                img_counter += 1
            cam.release()
            cv2.destroyAllWindows()
        except socket.error as error:
            print(f"{sensor_config['deviceType']} : Caught exception socket.error : {error}")
        finally:
            client_socket.close()


def makeSockOfActuator(**sensor_config):
    while True:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.connect((host, port))

        client_socket.settimeout(10)
        try:
            deviceConfigStr = makeStrFromDict(sensor_config)

            print(deviceConfigStr, end="\n\n")
            client_socket.sendall(len(deviceConfigStr).to_bytes(4, byteorder='big'))
            client_socket.sendall(deviceConfigStr.encode('cp949'))

            while True:
                data = client_socket.recv(4)
                length = int.from_bytes(data, "big")
                data = client_socket.recv(length)
                msg = data.decode(encoding="cp949")
                msg = msg.split('.')
                print(msg[0], end=" ")
                if msg[1] == '1':
                    print("Siren ON", end=" | ")
                else:
                    print("Siren OFF", end=" | ")
                if msg[2] == '1':
                    print("Lamp ON")
                else:
                    print("Lamp OFF")

        except socket.error as exc:
            print(f"{sensor_config['deviceType']} : Caught exception socket.error : {exc}")
        finally:
            client_socket.close()


if __name__ == '__main__':

    # host = '127.0.0.1'
    # port = 1234
    host = input("서버 ip 를 입력하시오 : ")
    port = int(input("서버 port 를 입력하시오 : "))
    
    latitude = 37.195318
    longitude = 127.020474
    locationNumber = 1
    deviceType = ""
    # deviceState = 0
    localtime = int(time.time())

    sensorList = ['emergencySwitch', 'distanceDetection', 'lightDetection']

    device_config = {
        'host': host,
        'port': port,
        'latitude': latitude,
        'longitude': longitude,
        'locationNumber': locationNumber,
        'deviceType': deviceType,
        # 'deviceState': deviceState,
        'localtime': localtime,
    }

    try:
        for i in sensorList:
            device_config['deviceType'] = i
            th = threading.Thread(target=makeSockOfEachSensor, kwargs=device_config)
            th.start()
        device_config['deviceType'] = "actuator"
        th = threading.Thread(target=makeSockOfActuator, kwargs=device_config)
        th.start()

        device_config['deviceType'] = "camera"
        th = threading.Thread(target=makeSockOfCamera, kwargs=device_config)
        th.start()

    except socket.error as exc:
        print(f"Caught exception socket.error : {exc}")
