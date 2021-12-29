from src import modbuser as mb

device = mb.instrument(25, 9600, "/dev/ttyUSB0")
# alarm = mb.instrument(25, 9600, "/dev/ttyUSB1")

read_motion_loop_index = 0
motion_final_index = 3
motion_final = 0
motion_ = False
motion__ = False
motion = 0

remove = 0
outage = 0
cut_alarm = 0
heat = 0
cut_heat = 0
read_sens_loop_index = 0

alarmState = False
sensorData = False

def close():
    mb.close_port(device)
    # mb.close_port(alarm)
    return True

def setAlarm(state):
    global alarmState
    alarmState = state

def readMotion(motion_pin):
    global motion, motion_final, motion_final_index, motion_, read_motion_loop_index

    read_motion_loop_count = 35
    if read_motion_loop_index == read_motion_loop_count:
        motion_filter_top = 0
        motion_filter_bottom = 10
        if motion >= (read_motion_loop_count / 2) - motion_filter_bottom and motion <= (read_motion_loop_count - motion_filter_top):
            motion_final += 1

        motion = 0
        if motion_final_index > 1:
            motion_final_index -= 1

        else:
            motion_final_count = 3

            motion_ = motion_final >= (motion_final_count - 1)
            motion_final_index = motion_final_count
            motion_final = 0

        read_motion_loop_index = 0

    else:
        motion += not motion_pin
        read_motion_loop_index += 1

    return motion_

def readSensor():
    global motion__, read_sens_loop_index, remove, outage, cut_alarm, heat, cut_heat
    read_sens_loop_count = 7

    if read_sens_loop_index is read_sens_loop_count:
        sensorData = {
            'motion': int(not motion__),
            'remove': round(remove / read_sens_loop_count),
            'outage': round(outage / read_sens_loop_count),
            'cut_alarm': round(cut_alarm / read_sens_loop_count),
            'heat': round(heat / read_sens_loop_count),
            'cut_heat': round(cut_heat / read_sens_loop_count)
        }

        motion__ = False
        remove = 0
        outage = 0
        cut_alarm = 0
        heat = 0
        cut_heat = 0

        read_sens_loop_index = 0

        return sensorData

    else:
        sensors = mb.read_pool(device, 6)
        
        if sensors:
            motion__ = readMotion(sensors[0])
            remove += not sensors[1]
            cut_alarm += sensors[2]
            heat += not sensors[3]
            cut_heat += not sensors[4]
            outage += sensors[5]
            read_sens_loop_index += 1

        print(sensors)
        return False