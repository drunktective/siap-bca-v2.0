import minimalmodbus

def instrument(address, baud, port, closePort=False):
    device = minimalmodbus.Instrument(port, address)
    device.serial.baudrate = baud
    device.close_port_after_each_call = closePort

    # dev.mode = minimalmodbus.MODE_RTU
    # dev.serial.timeout = 1
    # dev.debug = True

    return device

def write_pool(device, state):
    try:
        if state is False:
            device.write_register(1, 0, 0)
        else:
            device.write_register(1, 1, 0)

        return True

    except:
        return False

def read_pool(device, len):
    result = [0] * len
    try:
        result = device.read_registers(0, len)
        return result

    except:
        return False

def close_port(device):
    device.close_port = True
    return