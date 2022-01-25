import cv2, asyncio

cam = cv2.VideoCapture("rtsp://admin:mac57588@192.168.1.64:554/1")

ret, frame = cam.read()

while True:
    ret, frame = cam.read()
    if not ret:
        print("failed to grab frame")
        break

    img_name = '../captured/opencv_frame_1.png'
    cv2.imwrite(img_name, frame)
    print("{} written!".format(img_name))
    break

cam.release()