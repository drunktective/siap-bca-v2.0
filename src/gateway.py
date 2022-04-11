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

        if (duration >= 2) and (
            on > off
            and (now > on or now < off)
            or on <= off
            and on < off
            and now > on
            and now < off
            or on <= off
            and on >= off
            and now == on
        ):
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

            if topic == 'time':
                setOperationalTime(payload)
                checkOperationTime()

                print("[GATEWAY] synced to SIAP!")
                isConnected = True

            if topic == 'version' and payload == 'check':
                with open('.ver', 'r') as file:
                    version = file.read().rstrip('\n')
                    file.close()

                print(f'[VERSION] machine version: {version}')
                client.publish(f'siap/{SERIALNUM}/version', version)

            if topic == 'logs' and payload != '0':
                log = {'log': makeLog(payload, 'load').stdout.decode('utf-8')}
                url = 'http://192.168.50.143:3000'
                requests.post(url, data=log)
                print(f'[LOGS] sent {payload} last log')
                client.publish(f'siap/{SERIALNUM}/logs', '0')

            if topic == 'reboot' and payload == '1':
                time.sleep(0.2)
                client.publish(f'siap/{SERIALNUM}/reboot', '0')
                time.sleep(1)
                triggerReboot = True

            if topic == 'update' and payload == 'yes':
                res = subprocess.run("git pull", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
                print(res)
                client.publish(f'siap/{SERIALNUM}/update', '0')
                time.sleep(1)
                triggerReboot = True

            if topic == 'capture' and not captureEvent:
                captureEvent = True

            if topic == 'reset':
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
    sys.exit("[REBOOT] rebooting...")

def makeLog(n, s):
    if s == 'reboot': 
        command = f'journalctl -n {n} > .machine-logs && sudo cp .machine-logs /boot/.machine-logs'
        res = subprocess.run(command, shell=True)
    
    if s == 'load': 
        command = f'journalctl -n {n}'
        res = subprocess.run(command, shell=True, stdout=subprocess.PIPE)

    return res