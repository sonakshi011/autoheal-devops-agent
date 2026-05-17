import subprocess

def dangerous():
    subprocess.call("ls -la", shell=True)