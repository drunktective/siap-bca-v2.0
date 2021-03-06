import paho.mqtt.client as mqtt
import datetime as dt
import subprocess, requests, time, sys, os
from src.camera_setup import activateMotion

version = os.getenv('VERSION')
SERIALNUM = os.getenv('DEVICE_NUMBER')
client = mqtt.Client(f'SIAP-{SERIALNUM}')

config = {
    'mqtt_host': "147.139.139.55",
    'mqtt_port': 5883,
    'mqtt_uname': "macuser",
    'mqtt_pass': "mac57588"
}

alarmForceOff = False
isConnected = False
operationalTime = None
triggerReboot = False
captureEvent = False

def today():
    return dt.datetime.now()

def setAlarmOff(state):
    global alarmForceOff
    alarmForceOff = state

def setOperationalTime(raw):
    global operationalTime

    splitted = raw.split(',')

    operationalTime = [dt.time(int(splitted[0]), int(splitted[1])), dt.time(int(splitted[2]), int(splitted[3])), int(splitted[4])]

    print(f'[OPERATE] {operationalTime}')

def checkOperationTime():
    if isConnected:
        currentTime = today()

        on, off, duration, now = operationalTime[0], operationalTime[1], operationalTime[2], currentTime.time()

        if (duration >= 2): 
            if on > off:
                if now > on or now < off:
                    return True
            elif on < off:
                if now > on and now < off:
                    return True
            elif now == on:
                return True

    return False

def offTimeReboot():
    currentTime = today()
    off, now = operationalTime[1].strftime("%H:%M"), currentTime.time().strftime("%H:%M")

    if now == off:
        return True

    return False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        def on_message(client, userdata, msg):
            global triggerReboot, alarmForceOff, isConnected, captureEvent

            topic = msg.topic.replace(f'siap/{SERIALNUM}/', '')
            payload = msg.payload.decode("utf-8")

            if topic == 'alarm':
                if payload == 'OFF': 
                    print('[ALARM] Alarm force off')
                    setAlarmOff(True)
                elif payload == 'ON':
                    print('[ALARM] Alarm reset')
                    setAlarmOff(False)

            elif topic == 'time':
                setOperationalTime(payload)
                checkOperationTime()

                print("[GATEWAY] synced to SIAP!")
                isConnected = True

            elif topic == 'version' and payload == 'check':
                with open('.ver', 'r') as file:
                    version = file.read().rstrip('\n')
                    file.close()

                print(f'[VERSION] machine version: {version}')
                client.publish(f'siap/{SERIALNUM}/version', version)

            elif topic == 'logs' and payload != '0':
                log = {'log': makeLog(payload, 'load').stdout.decode('utf-8')}
                # url = 'http://192.168.50.143:3000'
                # requests.post(url, data=log)
                print(f'[LOGS] sent {payload} last log')
                client.publish(f'siap/{SERIALNUM}/logs', '0')

            elif topic == 'reboot' and payload == '1':
                time.sleep(0.2)
                client.publish(f'siap/{SERIALNUM}/reboot', '0')
                time.sleep(1)
                triggerReboot = True

            elif topic == 'update':
                error_update = subprocess.run(["git", "pull"], check=True, stderr=subprocess.PIPE).stderr.decode("UTF-8")
                if error_update:
                    print(f'[UPDATE] error: {error_update}')
                    client.publish(f'siap/{SERIALNUM}/update', 'update_error')
                
                else:
                    client.publish(f'siap/{SERIALNUM}/update', '0')
                    time.sleep(1)
                    triggerReboot = True

            elif topic == 'capture' and not captureEvent:
                captureEvent = True

            elif topic == 'reset':
                activateMotion()

        client.subscribe(f'siap/{SERIALNUM}/#')
        client.on_message = on_message
        client.publish(f'siap/{SERIALNUM}/ping', 'rt')

    else:
        print(f'[GATEWAY] Failed to connect error code: {rc}')

def on_disconnect(client, userdata,  rc):
    print("[GATEWAY] disconnected from SIAP!")

    global isConnected
    isConnected = False

def reboot(pinout, error):
    pinout
    print(error)
    time.sleep(1)

def makeLog(n, s):
    if s == 'reboot': 
        command = f'journalctl -n {n} > .machine-logs && cp .machine-logs ../Desktop/logs.txt'
        # && sudo cp .machine-logs /boot/.machine-logs'
        res = subprocess.run(command, shell=True)
    
    if s == 'load': 
        command = f'journalctl -n {n} > ../Desktop/logs.txt'
        res = subprocess.run(command, shell=True, stdout=subprocess.PIPE)

    return res