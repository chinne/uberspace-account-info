import csv
import getpass
import json
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup


class UberspaceWebRequest:
    def __init__(self, username: str, password: str):
        self.session = requests.Session()
        self.url = "https://dashboard.uberspace.de/login"
        self.username = username
        self.password = password
        self.data = {}

    def get_account_info(self):
        data = self._request_data()
        response = self.session.post(self.url, data=data)
        response = self.session.get(
            "https://uberspace.de/dashboard/accountinfo?format=json", data=data
        )
        return json.loads(response.content.decode("utf-8"))

    def _get_csrf_token(self):
        response = self.session.get(self.url)
        soup = BeautifulSoup(response.content, features="html.parser")
        csrf_token = soup.select_one("[name=_csrf_token]").get("value")
        return csrf_token

    def _request_data(self):
        csrf_token = self._get_csrf_token()
        data = {
            "_csrf_token": csrf_token,
            "login": self.username,
            "password": self.password,
            "submit": "login",
        }
        return data

    def get_data(self):
        data = self.get_account_info()
        self.data = {
            "guthaben": data["current_amount"],
            "wunschpreis": data["price"],
            "domains_webserver": data["domains"]["web"],
            "domains_mailserver": data["domains"]["mail"],
            "hostname": data["host"]["fqdn"],
            "ipv4": data["host"]["ipv4"],
            "username": data["login"],
        }


def main():
    infos = []
    username = (
        json.loads(os.getenv("1UBERSPACE_USERNAME"))
        if os.getenv("1UBERSPACE_USERNAME")
        else None
    )
    password = (
        json.loads(os.getenv("1UBERSPACE_PASSWORD"))
        if os.getenv("1UBERSPACE_PASSWORD")
        else None
    )

    if username is None:
        print("type in username")
        username = input()
        username = [username]

    if password is None:
        print("type in password")
        password = getpass.getpass()
        password = [password]

    for user, pw in zip(username, password):
        uberspace = UberspaceWebRequest(user, pw)
        uberspace.get_data()
        infos.append(uberspace.data)
    header = [
        "guthaben",
        "wunschpreis",
        "domains_webserver",
        "domains_mailserver",
        "hostname",
        "ipv4",
        "username",
    ]
    try:
        with open(
            "output" + str(datetime.today()) + ".csv",
            mode="w",
            encoding="utf8",
            newline="",
        ) as output_to_csv:
            dict_csv_writer = csv.DictWriter(
                output_to_csv, fieldnames=header, dialect="excel"
            )
            dict_csv_writer.writeheader()
            dict_csv_writer.writerows(infos)
        print("\nData exported to csv succesfully and sample data")
    except IOError as io:
        print("\n", io)


if __name__ == "__main__":
    main()
