import cv2, os, requests

def device(loc):
    cap = cv2.VideoCapture(loc)
    return cap

def captureUpload(filename, imgObject, SERIALNUM, now):
    try:
        cv2.putText(imgObject, now.strftime("%A, %d %B %Y %I:%M:%S%p"), (25, imgObject.shape[0] - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)

        cv2.putText(imgObject, SERIALNUM, (25, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        cv2.imwrite(f'captured/{filename}.jpg', imgObject)

        # requests.post(os.environ.get('UPLOAD_URL'), files={"file": open("captured/{}.jpg".format(filename), "rb")})

        print('[MOTION] Capture success')

    except:
        print('[MOTION] Error saving image')