from cryptography.fernet import Fernet
import subprocess
import requests
import argparse
import logging
import yaml
import os
import re

def getToken():
    key = bytes(os.getenv('KEY'), 'utf-8')
    encrypted = bytes(os.getenv('SECRET_TELEGRAM'), 'utf-8')
    return Fernet(key).decrypt(encrypted).decode()

def encrypt(text, key=None):
    if key is None:
        key = bytes(os.getenv('KEY'), 'utf-8')
    else:
        key = bytes(key, 'utf-8')
    return Fernet(key).encrypt(text.encode()).decode()

def decrypt(value, key=None):
    if key is None:
        key = bytes(os.getenv('KEY'), 'utf-8')
    else:
        key = bytes(key, 'utf-8')
    if os.getenv(f'SECRET_{value.upper()}'):
        encrypted = bytes(os.getenv(f'SECRET_{value.upper()}'), 'utf-8')
    else:
        encrypted = bytes(value, 'utf-8')
    return Fernet(key).decrypt(encrypted).decode()

def getNgrokConfig():
    cmd = 'ps -fCngrok --no-headers'
    proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = [i.decode().strip() if i else None for i in proc.communicate()]
    regex = re.search(r'.*--config ([^ ]*)', stdout)
    return regex.group(1)

def getNgrokIP():
    config = loadYaml(getNgrokConfig())
    return config['web_addr']
    
def loadYaml(file):
    try:
        with open(file, 'r') as stream:
            yamlData = yaml.safe_load(stream)
        return yamlData
    except Exception as e:
        raise e

def callTelegramAPI(method, params, apiMethod='POST', files=None):
    url = 'https://api.telegram.org/bot{}/{}'.format(getToken(), method)
    if apiMethod == 'POST':
        if files:
            response = requests.post(url=url, params=params, files=files)
        else:
            response = requests.post(url=url, params=params)
        return response
    elif apiMethod == 'GET':
        response = requests.get(url=url, params=params)
    else:
        raise Exception(f'apiMethod-{apiMethod} is not in valid methods (GET, POST)')
    return response

def getTelegramFilePath(fileId):
    method = 'getFile'
    response = callTelegramAPI(method, {'file_id': fileId})
    if response.status_code == 200:
        filePath = response.json()['result']['file_path']
        response = requests.get(url=f'https://api.telegram.org/file/bot{getToken()}/{filePath}')
        print(response)
        if response.status_code == 200:
            savePath = f'files/{os.path.basename(filePath)}'
            with open(savePath, 'wb') as file:
                file.write(response.content)
                print(f'saved {filePath} to {savePath}')
        else:
            raise Exception(f'fail to call telegram/file/{filePath}')
    else:
        raise Exception(f'fail to call telegram/{method}')
    pass

def customLogger(app):
    # print(__name__, __file__)
    logger = logging.getLogger(app)
    logger.setLevel(level=logging.INFO)
    file_handler = logging.FileHandler(filename=app.replace('.py', '.log'), mode='a', encoding='utf-8')
    logger.addHandler(file_handler)
    return logger

if __name__ == '__main__':
    mainParser = argparse.ArgumentParser()
    choices = ['decrypt', 'encrypt', 'getFile']
    arg_template = {
        'required': True,
        'type': str
    }
    mainParser.add_argument('--action', choices=choices, help='cryptography utility', **arg_template)
    mainParser.add_argument('--value', help='argument', **arg_template)
    mainParser.add_argument('--key', help='argument', type=str)
    args = mainParser.parse_args()
    if args.action == 'encrypt':
        if args.key:
            print(encrypt(args.value, args.key))
        else:
            print(encrypt(args.value))
    elif args.action == 'decrypt':
        if args.key:
            print(decrypt(args.value, args.key))
        else:
            print(decrypt(args.value))
    elif args.action == 'getFile':
        getTelegramFilePath(args.value)