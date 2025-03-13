import os


for k in os.environ:
    print(f'{k}: {os.environ[k]}')

project_root = os.environ['PYTHONPATH']
environ_pwd = os.environ['PWD']