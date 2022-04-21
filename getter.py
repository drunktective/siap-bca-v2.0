import subprocess, requests, time, sys 
from os import getenv, system, path, _exit, EX_OK

def load_env(env):
    from dotenv import load_dotenv
    try:
        with open(f'/boot/{env}', 'r') as file:
            file.read()
            file.close()
            env = '/boot/.env'
            return load_dotenv(env)

    except:
        return load_dotenv(env)

def envCheck(env_file):
    return path.exists(env_file)

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
    from dotenv import load_dotenv, find_dotenv

    try:
        load_env('.env')
        if envCheck('/media/bcafile/env.txt'): system('cp /media/bcafile/env.txt .env')
        if not envCheck('.env'): raise RuntimeError("[ERROR] Env not found on any local system!")

        cloud_version = getCloudVersion(getenv('CLOUD_HOST'), {'x-siap-token': 'rpi_mqtt_0d4d0dd01d8b8bffe77304d419f1ed594e5c9416d02c9757c8b03e02d37600e4:_'})
        print(f'[VERSION] cloud version: {cloud_version}')

        local_version = getLocalVersion('.ver', 'r')
        print(f'[VERSION] local version: {local_version}')

        if cloud_version != local_version:
            subprocess.run("git pull", shell=True)
            time.sleep(1)
            up = getLocalVersion('.ver', 'w')
            
        exec(main())
        gateway.makeLog(2000, 'reboot')
        loop()

    except RuntimeError as r:
        print(r)
        _exit(EX_OK)

    except Exception as e:
        gateway.reboot(io.close(), e)
        _exit(EX_OK)

    except KeyboardInterrupt:
        print("[ERROR] Keyboard Interrupted")
        _exit(EX_OK)