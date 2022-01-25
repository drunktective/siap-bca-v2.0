from src import io_polls as io
from src import gateway
from src import camera_setup as cam

import threading

import cv2
import asyncio
import json
import time

events = asyncio.get_event_loop()
timeoutAlarmForceOff = None
timeoutGateway = None

temp = {}

def gatewayRestart():
    raise Exception("[ERROR] gateway not connected")

def millis():
    return round(time.time() * 1000)

def alarmForceOffTask():
    global timeoutAlarmForceOff

    io.setAlarm(False)
    timeoutAlarmForceOff = None
    gateway.setAlarmOff(True)

def compareData(sensorData):
    global temp, timeoutAlarmForceOff

    motion, outage, cut_alarm, heat, cut_heat = sensorData['motion'], sensorData['outage'], sensorData['cut_alarm'], sensorData['heat'], sensorData['cut_heat']

    # print(f'{motion}, {outage}, {cut_alarm}, {heat}, {cut_heat}')

    isOperated = gateway.checkOperationTime()

    if not motion or outage or cut_alarm or heat or cut_heat:
        if not gateway.alarmForceOff:
            if (not motion or heat or cut_heat) and isOperated and timeoutAlarmForceOff is None:
                print("[VANDAL] Vandal detected on operational time!")
                io.setAlarm(True)
                timeoutAlarmForceOff = events.call_later(360, alarmForceOffTask)

            elif (heat or cut_heat) and not isOperated and timeoutAlarmForceOff is None:
                print("[VANDAL] Heat problem!")
                io.setAlarm(True)
                timeoutAlarmForceOff = events.call_later(360, alarmForceOffTask)

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
            timeoutGateway = events.call_later(20, gatewayRestart)
            return True

    return False

nextMotionSend = None
startDetectMillis = 0
recorded = []
waitDetection = 1000
avg = None

import numpy as np
import datetime as dt

def imageProcess(frame, currentTime, ms, SERIALNUM):
    global avg, startDetectMillis, recorded, waitDetection, nextMotionSend

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if avg is None:
        avg = gray.copy().astype("float")
        return 
    
    cv2.accumulateWeighted(gray, avg, 0.05)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        frame = cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)

        area = np.sum([cv2.contourArea(c) for c in contours])
        
        if area > 3500 and nextMotionSend is None: 
            if startDetectMillis == 0: startDetectMillis = ms

            else:
                if ms - startDetectMillis > waitDetection and len(recorded) < 6:
                    waitDetection += 1000
                    recorded.append(cv2.resize(frame, (640, 400)))

                    if len(recorded) == 6:
                        nextMotionSend = currentTime + dt.timedelta(minutes=30)

                        v1 = np.vstack((recorded[0], recorded[2], recorded[4]))
                        v2 = np.vstack((recorded[1], recorded[3], recorded[5]))
                        horz = np.hstack((v1, v2))

                        cam.captureUpload(f'{SERIALNUM}-{startDetectMillis}', horz, SERIALNUM, currentTime)

                        # captureUpload('{}-{}'.format(SERIALNUM, startDetectMillis), horz)

    else:
        waitDetection = 1000
        recorded = []
        startDetectMillis = 0

def camera():
    while True:
        ms = millis()
        now = gateway.today()
        _, frame = io.camera.read()

        if gateway.captureEvent:
            cam.captureUpload(f'manual-{gateway.SERIALNUM}-{now.strftime("%d%m%y_%H:%M:%S")}', frame, gateway.SERIALNUM, now)
            gateway.captureEvent = False
        
        isOperated = gateway.checkOperationTime()
        if isOperated: imageProcess(frame, now, ms, gateway.SERIALNUM)

async def loop():
    gateway.client.on_connect = gateway.on_connect
    gateway.client.on_disconnect = gateway.on_disconnect
    gateway.client.username_pw_set(gateway.config['mqtt_uname'], gateway.config['mqtt_pass'])
    gateway.client.connect(gateway.config['mqtt_host'], gateway.config['mqtt_port'])
    gateway.client.loop_start()

    nextLoop = millis()
    nextPing = millis()

    await asyncio.sleep(1)

    while True:
        ms = millis()
        now = gateway.today()

        global nextMotionSend
        if nextMotionSend is not None and nextMotionSend < now:
            print("y")
            nextMotionSend = None

        if ms >= nextLoop + 250:
            nextLoop += 250
            
            sensorData = io.readSensor()
            if sensorData:
                compareData(sensorData)

            offTimeReboot = gateway.offTimeReboot()
            if gateway.triggerReboot or offTimeReboot:
                raise Exception("[ERROR] Reboot triggered")


        if ms >= nextPing + 14000:
            nextPing += 14000

            res = pingingGateway()

            if not res:
                raise Exception("[ERROR] gateway not fetched")

        await asyncio.sleep(0.01)