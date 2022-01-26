import cv2, os, requests
import numpy as np
import datetime as dt
import urllib.request

nextMotionSend = None
startDetectMillis = 0
recorded = []
waitDetection = 1000
avg = None
capName = None

def motion_record():
    if len(recorded) == 6:
        return True

    return False

def capture_name():
    return capName

def device(loc):
    cap = cv2.VideoCapture(loc)
    return cap

def checkLocalConnection(host='http://192.168.1.64'):
    try:
        urllib.request.urlopen(host)
        return True

    except:
        return False

def captureUpload(filename, imgObject, SERIALNUM, now):
    try:
        cv2.putText(imgObject, now.strftime("%A, %d %B %Y %I:%M:%S%p"), (25, imgObject.shape[0] - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)

        cv2.putText(imgObject, SERIALNUM, (25, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        cv2.imwrite(f'captured/{filename}.jpg', imgObject)

        # requests.post(os.environ.get('UPLOAD_URL'), files={"file": open("captured/{}.jpg".format(filename), "rb")})

        print('[MOTION] Capture success')

    except:
        print('[MOTION] Error saving image')

def imageProcess(frame, currentTime, ms, SERIALNUM):
    global avg, startDetectMillis, recorded, waitDetection, nextMotionSend, capName

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

                        capName = f'{SERIALNUM}-{startDetectMillis}'
                        captureUpload(capName, horz, SERIALNUM, currentTime)

    else:
        waitDetection = 1000
        recorded = []
        startDetectMillis = 0
        capName = None