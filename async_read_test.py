import subprocess

with open("text.txt", "w") as file:
    command = "python3 printloop.py"
    subprocess.call(command.split(), stdout=file)