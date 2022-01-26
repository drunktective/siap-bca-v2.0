import subprocess, requests, time, sys, os

def load_env():
    from dotenv import load_dotenv
    env = '.env'
    try:
        with open(f'/boot/{env}', 'r') as file:
            file.read()

        return load_dotenv(f'/boot/{env}')

    except:
        return load_dotenv(env)

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
        # cloud_version = getCloudVersion(os.getenv('CLOUD_HOST'), {'x-siap-token': 'xxx'})
        # print(f'[VERSION] cloud version: {cloud_version}')

        # local_version = getLocalVersion('.ver', 'r')
        # print(f'[VERSION] local version: {local_version}')

        # if cloud_version != local_version:
        #     subprocess.run("git pull", shell=True)
        #     time.sleep(1)
        #     up = getLocalVersion('.ver', 'w')

        load_env()
        exec(main())
        gateway.makeLog(2000, 'reboot')
        
        threading.Thread(target=camera, args=(), daemon=True).start()
        events.run_until_complete(loop())

    except RuntimeError as r:
        sys.exit(r)

    except Exception as e:
        gateway.reboot(io.close(), events.close(), e)

    except KeyboardInterrupt:
        sys.exit("[ERROR] Keyboard Interrupted")