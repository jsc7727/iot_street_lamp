from time import strftime, localtime


def addTime():
    return strftime("%Y-%m-%d %a %H:%M:%S ", localtime())


class file:
    def __init__(self, path, option):
        self.f = open(path, option)

    def write(self, message):
        return self.f.write(message)

    def read(self):
        return self.f.read().split()

    def logWriter(self,logMsg, address=""):
        log = file("log.txt", 'a+')
        if address == "":
            log.write(f"{addTime()} | {logMsg}")
        else:
            log.write(f"{addTime()} | {address} |{logMsg}")
        log.f.close()


if __name__ == '__main__':
    rec1 = file("test.txt", 'a+')
    rec1.write("test")
