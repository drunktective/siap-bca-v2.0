from src import io_polls as io
from src import gateway

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

    print(f'{motion}, {outage}, {cut_alarm}, {heat}, {cut_heat}')

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