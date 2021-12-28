import subprocess, requests, time, sys, os

from dotenv import load_dotenv
load_dotenv('/boot/.env')

def getCloudVersion(host, header):
    version = requests.get(host, headers=header)
    if version.status_code != 200: raise RuntimeError("[ERROR] version not fetched")
    return version.text.rstrip('\n')

def getLocalVersion(filename, state):
    content = None
    with open(filename, state) as file:
        if state == 'w': file.write(cloud_version)
        elif state == 'r': content = file.read().rstrip('\n')
        else: raise RuntimeError("[ERROR] file state wrong")
        file.close()

    if content is not None: return content
    return True

def main():
    with open('main.py', 'r') as file:
        sketch = file.read()
        file.close()

    return sketch

if __name__ == "__main__":
    try:
        executed = False
        time.sleep(1)

        # cloud_version = getCloudVersion(os.getenv('CLOUD_HOST'), {'x-siap-token': 'xxx'})
        # print(f'[VERSION] cloud version: {cloud_version}')

        # local_version = getLocalVersion('.ver', 'r')
        # print(f'[VERSION] local version: {local_version}')

        # if cloud_version != local_version:
        #     subprocess.run("git pull", shell=True)
        #     time.sleep(1)
        #     up = getLocalVersion('.ver', 'w')

        exec(main())
        executed = True
        
        gateway.makeLog(2000, 'reboot')
        events.run_until_complete(loop())

    except RuntimeError as r:
        sys.exit(r)

    except Exception as e:
        gateway.reboot(io.close(), events.close(), e)

    except KeyboardInterrupt:
        sys.exit("[ERROR] Keyboard Interrupted")