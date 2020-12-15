import threading

from win10toast import ToastNotifier


def addSocketInTable(dnsTable: dict, lock: threading.Lock, addr: str, client_socket_config: dict):
    lock.acquire()
    if addr in dnsTable:
        for x in dnsTable[addr]:
            if x['deviceType'] == client_socket_config['deviceType']:
                lock.release()
                return False
        dnsTable[addr].append(client_socket_config)
    else:
        dnsTable[addr] = [client_socket_config, ]
    lock.release()
    return True


def delSocketInTable(dnsTable: dict, lock: threading.Lock, addr: str, client_socket_config: dict):
    """
    :param dnsTable: dns table of main server
    :type lock: thread lock for synchronize from server
    :param addr: client ip address
    :param client_socket_config: dict structure
            client_socket_config = {
                'host': host,
                'port': port,
                'latitude': latitude,
                'longitude': longitude,
                'locationNumber': locationNumber,
                'sensorType': sensorType,
                'sensorState': sensorState,
                'localtime': localtime,
            }
    """
    sensorType: str = client_socket_config['deviceType']
    lock.acquire()
    ret = next((index for (index, item) in enumerate(dnsTable[addr]) if item['deviceType'] == sensorType))
    print("삭제할 위치 : ", ret)
    dnsTable[addr].pop(ret)
    if len(dnsTable[addr]) == 0:
        del (dnsTable[addr])
    lock.release()


def noticeError(msg):
    ToastNotifier().show_toast("Notice Error",
                               msg,
                               icon_path=None,
                               duration=10,
                               threaded=False)

# def saveImageFromClient(camId=0, path='./picture'):
#     cam = cv2.VideoCapture(camId)
#     if cam.isOpened() == False:
#         print('cant open the cam (%d)' % camId)
#         return None
#     ret, frame = cam.read()
#     if frame is None:
#         print('frame is not exist')
#         return None
#     imageName = strftime("%Y-%m-%d %a %H_%M_%S", localtime()) + ".png"
#
#     cv2.imwrite(os.path.join(path, imageName), frame, params=[cv2.IMWRITE_PNG_COMPRESSION, 0])
#     cam.release()
