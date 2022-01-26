from src import modbuser as mb
import time

# device = mb.instrument(25, 9600, "/dev/ttyS3")
# time.sleep(2)

# while True:
#     print(mb.read_pool(device, 8))
#     time.sleep(0.5)

sensorData = {
    'test': 1
}

print(sensorData)
sensorData['te2'] = "rrr"

time.sleep(0.5)
print(sensorData)