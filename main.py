from dotenv import load_dotenv
from os import getenv
import sys

from typing import Tuple, List

import time
from time import sleep

import requests as req
from requests import Response, ConnectionError

import bluetooth  # only supported on Linux

load_dotenv()
server = getenv("SERVER_URL")
token = getenv("TOKEN")


def wait(secs: int, error: str = ""):
    error = error + " " if error and not error.endswith(" ") else error
    for s in range(secs - 1):
        print(error +
              f"Resuming in {str(secs - s).zfill(len(str(secs)))} seconds...",
              end="\r")
        sys.stdout.write('\033[2K\033[1G')
        sleep(1)
    print(error + f"Resuming in {secs} seconds.")


def handleNearby(nearby: List[Tuple[str, str, int]]):
    month, day, hour, minutes, sec = time.strftime("%m %d %H %M %S").split()
    text = f"Found {len(nearby)} devices on the {day}/{month} at {hour}:{minutes}:{sec}"
    print("- " + text, end="\r")
    sys.stdout.write('\033[2K\033[1G')

    devices = list(
        map(lambda n: ({
            "address": n[0],
            "name": n[1],
            "type": n[2]
        }), nearby))
    try:
        res = req.post(f"{server}/ping",
                       json={"devices": devices},
                       headers={"Authorization": token})
        print("| " + text)
        handleReponse(res)
    except ConnectionError:
        print("X " + text)
        wait(60, "Failed to reach server.")


def handleReponse(res: Response):
    status = res.status_code
    success = str(status).startswith("2")
    if not success:
        if str(status).startswith("4"):
            if status == 422:
                print("ERR 422 | Sent invalid data.")
                wait(60)
            elif status == 401:
                print("ERR 401 | Cannot authenticate.")
                wait(60)
            else:
                print(f"ERR {status} | Unknown error. Response body:")
                print(res.text)
                print("Terminating.")
                exit()
        elif str(status).startswith("5"):
            print(f"ERR {status} | Server error. Response body:")
            print(res.text)
            wait(60)


def getIdentity():
    found = False
    while not found:
        try:
            res = req.get(f"{server}/self", headers={"Authorization": token})
            found = True
            json = res.json()
            if res.status_code != 200:
                print("Authentication failed. Terminating.")
                exit()
            return json
        except ConnectionError:
            wait(60, "Failed to initiate connection with server.")


def main():
    print("Starting...\n")
    id = getIdentity()
    print(f"Emitting as {id['name']} [{id['id']}].")
    while True:
        print("* " + "Searching...", end="\r")
        sys.stdout.write('\033[2K\033[1G')
        nearby: List[Tuple[str, str, int]] = bluetooth.discover_devices(
            duration=8, lookup_names=True, lookup_class=True)
        handleNearby(nearby)


try:
    if __name__ == "__main__":
        main()
    else:
        print("Script should be main")
except KeyboardInterrupt:
    exit()