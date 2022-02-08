from src import modbuser as mb
from src import camera_setup as cam
import os

# device = mb.instrument(25, 9600, "/dev/ttyS3")
# alarm = mb.instrument(25, 9600, "/dev/ttyS3")
device = mb.instrument(25, 9600, "/dev/ttyUSB0")
alarm = mb.instrument(25, 9600, "/dev/ttyUSB0")
camera_device = os.getenv('CAMERA_DEVICE')
camera = None

read_motion_loop_index = 0
motion_final_index = 3
motion_final = 0
motion_ = False
motion__ = False
motion = 0

outage = 0
cut_alarm = 0
heat = 0
cut_heat = 0
cut_motion = 0
read_sens_loop_index = 0

alarmState = False
sensorData = False

def isCameraOn():
    if camera_device != "0": return True
    return False

def camSetup():
    global camera
    camera = cam.device(camera_device)
    return camera

def close():
    mb.close_port(device)
    mb.close_port(alarm)
    return True

def setAlarm(state):
    global alarmState
    alarmState = state

def readMotion(motion_pin):
    global motion, motion_final, motion_final_index, motion_, read_motion_loop_index

    motion_filter_top = 0
    motion_filter_bottom = 10
    read_motion_loop_count = 35
    motion_final_count = 3

    if read_motion_loop_index == read_motion_loop_count:
        if motion >= (read_motion_loop_count / 2) - motion_filter_bottom and motion <= (read_motion_loop_count - motion_filter_top):
            motion_final += 1

        motion = 0
        if motion_final_index > 1:
            motion_final_index -= 1

        else:
            motion_ = False

            if motion_final >= (motion_final_count - 1):
                motion_ = True

            motion_final_index = motion_final_count
            motion_final = 0

        read_motion_loop_index = 0

    else:
        motion += not motion_pin
        read_motion_loop_index += 1

    return motion_

def readSensor():
    global motion__, read_sens_loop_index, outage, cut_alarm, heat, cut_heat, cut_motion
    read_sens_loop_count = 7

    if read_sens_loop_index is read_sens_loop_count:
        sensorData = {
            'motion': int(motion__),
            'outage': round(outage / read_sens_loop_count),
            'cut_alarm': round(cut_alarm / read_sens_loop_count),
            'heat': round(heat / read_sens_loop_count),
            'cut_heat': round(cut_heat / read_sens_loop_count),
            'cut_motion': int(cut_motion)
        }

        read_sens_loop_index = 0
        capture_name = cam.capture_name()
        if capture_name is not None: sensorData['motion_image'] = f'{capture_name}.jpg'

        motion__ = False
        outage = 0
        cut_alarm = 0
        heat = 0
        cut_heat = 0
        cut_motion = 0
        return sensorData

    else:
        sensors = mb.read_pool(device, 8)
        if sensors:
            motion__ = not cam.motion_record() if camera is not None else not readMotion(sensors[2])
            cut_alarm += not mb.write_pool(alarm, 0, alarmState)
            heat += not sensors[4]
            cut_heat += sensors[3]
            outage += sensors[7]
            cut_motion = cam.motion_cut
            read_sens_loop_index += 1

        # print(f'{sensors[2]}, {int(motion__)}, {cut_alarm}, {heat}, {cut_heat}, {outage}')
        # print(cut_motion)
        return False