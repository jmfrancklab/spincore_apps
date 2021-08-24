from serial.tools.list_ports import comports
cport = comports()
if type(cport) is list and hasattr(cport[0],'device'):
    portlist = [j.device for j in comports() if 'Arduino Due' in j.description]
print(portlist)
