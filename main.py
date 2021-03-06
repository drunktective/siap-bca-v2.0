from src import io_polls as io
from src import gateway
from src import camera_setup as cam
from time import sleep, time
from threading import Timer, Thread
import json

timeoutAlarmForceOff = None
timeoutGateway = None
frame = None
temp = {}

def gatewayRestart():
    raise Exception("[ERROR] gateway not connected")

def millis():
    return round(time() * 1000)

def alarmForceOffTask():
    global timeoutAlarmForceOff
    io.setAlarm(False)
    timeoutAlarmForceOff.cancel()
    timeoutAlarmForceOff = None
    gateway.setAlarmOff(True)

def compareData(sensorData):
    global temp, timeoutAlarmForceOff

    motion, outage, cut_alarm, heat, cut_heat = sensorData['motion'], sensorData['outage'], sensorData['cut_alarm'], sensorData['heat'], sensorData['cut_heat']

    isOperated = gateway.checkOperationTime()

    if not motion or outage or cut_alarm or heat or cut_heat:
        if not gateway.alarmForceOff:
            if (not motion or heat or cut_heat) and isOperated and timeoutAlarmForceOff is None:
                print("[VANDAL] Vandal detected on operational time!")
                io.setAlarm(True)
                timeoutAlarmForceOff = Timer(360, alarmForceOffTask)
                timeoutAlarmForceOff.start()

            elif (heat or cut_heat) and not isOperated and timeoutAlarmForceOff is None:
                print("[VANDAL] Heat problem!")
                io.setAlarm(True)
                timeoutAlarmForceOff = Timer(360, alarmForceOffTask)
                timeoutAlarmForceOff.start()

        else:
            io.setAlarm(False)
            if timeoutAlarmForceOff is not None:
                timeoutAlarmForceOff.cancel()
                timeoutAlarmForceOff = None

    else:
        io.setAlarm(False)
        gateway.setAlarmOff(False)
        if timeoutAlarmForceOff is not None:
            timeoutAlarmForceOff.cancel()
            timeoutAlarmForceOff = None

    finalData = json.dumps(sensorData)
    tempData = json.dumps(temp)

    if tempData != finalData:
        if gateway.isConnected is True:
            print(f'[VANDAL] Data: {sensorData}')
            gateway.client.publish(f'siap/{gateway.SERIALNUM}/vandal', finalData)

        temp = sensorData

def pingingGateway():
    global timeoutGateway

    deviceData = {
        'charging': 0,
        'standby': 0,
        'battery': 0,
        'dc_in': 0
    }

    deviceData = json.dumps(deviceData)
    if gateway.isConnected:
        if timeoutGateway is not None:
            timeoutGateway.cancel()
            timeoutGateway = None

        # print(f'[PING] Data: {deviceData}')
        gateway.client.publish(f'siap/{gateway.SERIALNUM}/ping', deviceData)
        return True

    else:
        if timeoutGateway is None:
            timeoutGateway = Timer(20, gatewayRestart)
            timeoutGateway.start()
            return True

    return False

def camera():
    print("[CAMERA] Checking camera connection...")
    camFirstCheck = 0

    while not cam.motion_cut:
        sleep(8.5)
        camFirstCheck += 1
        print(f'[CAMERA] Camera connecting count: {camFirstCheck}')
        if camFirstCheck >= 12:
            print("[CAMERA] Camera connection failed!") 
            cam.camera_cutset(1)

        if cam.checkLocalConnection(io.camera_device): 
            print("[CAMERA] Camera connected!")
            sleep(2)
            io.camSetup()
            cam.camera_cutset(0)
            break

    nextPing = millis()
    while not cam.motion_cut:
        global frame

        ms = millis()
        now = gateway.today()
        _, frame = io.camera.read()

        if frame is not None:
            cam.camera_cutset(0)
            if gateway.captureEvent:
                cam.captureUpload(f'manual-{gateway.SERIALNUM}-{now.strftime("%d%m%y_%H:%M:%S")}', frame, gateway.SERIALNUM, now)
                gateway.captureEvent = False

        else:
            cam.camera_cutset(1)

def loop():
    gateway.client.on_connect = gateway.on_connect
    gateway.client.on_disconnect = gateway.on_disconnect
    gateway.client.username_pw_set(gateway.config['mqtt_uname'], gateway.config['mqtt_pass'])
    gateway.client.connect(gateway.config['mqtt_host'], gateway.config['mqtt_port'])
    gateway.client.loop_start()

    io.setAlarmDefaultTime(0)

    nextLoop = millis()
    nextPing = millis()

    if camCheck := io.isCameraOn():
        Thread(target=camera, args=(), daemon=True).start()
        camErrorCount = 0

    sleep(1)

    while True:
        ms = millis()
        now = gateway.today()

        if cam.nextMotionSend is not None and cam.nextMotionSend < now: cam.nextMotionSend = None

        if ms >= nextLoop + 250:
            nextLoop += 250
            sensorData = io.readSensor()
            if sensorData:
                compareData(sensorData)
                if cam.motion_cut: 
                    camErrorCount += 1
                    if camErrorCount == 7:
                        raise Exception("[ERROR] Motion cut detected!")

            offTimeReboot = gateway.offTimeReboot()
            if gateway.triggerReboot or offTimeReboot: raise Exception("[ERROR] Reboot triggered")


        if ms >= nextPing + 14000:
            nextPing += 14000

            res = pingingGateway()
            if not res: raise Exception("[ERROR] gateway not fetched")

        if frame is not None:
            isOperated = gateway.checkOperationTime()
            if isOperated: cam.imageProcess(frame, now, ms, gateway.SERIALNUM)

        sleep(0.01)