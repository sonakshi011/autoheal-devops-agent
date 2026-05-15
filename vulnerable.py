import os


def run_cmd(user_input):
    # SECURITY RISK: Command Injection
    os.system("echo " + user_input)
