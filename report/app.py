#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Florent Jacquet <florent.jacquet@free-electrons.com>
#

import sys
import ruamel.yaml
from xmlrpc import client
from flask import Flask, render_template
from datetime import datetime


hostname = "farm"

username = "my-user"
token = "my-awesome-token"

with open("credentials", "r") as f:
    username = f.readline().strip()
    token = f.readline().strip()

server = client.ServerProxy("http://%s:%s@%s/RPC2" % (username, token, hostname))

print(server.system.listMethods())

tests_list = set()

app = Flask(__name__)

@app.route("/")
def index():
    with open("cache.html", 'r') as f:
        html = f.read()
    return html

@app.route("/refresh")
def generate():
    """
    devices = {
        "device_name": {
            "test_name": [
                {
                    "job_id": 4000,
                    "job_name": "bleh",
                    "result": "pass",
                    },
                {
                    "job_id": 4001,
                    "job_name": "bleh--2",
                    "result": "fail",
                    }
            ]
            }
        }
    """
    start_time = datetime.now()
    devices = {}
    for device in [i[0] for i in server.scheduler.all_devices()]:
        devices[device] = {}
        for job in server.scheduler.get_last_n_runned_jobs_for_device(device, 20):
            j_id = job["id"]
            job_name = job['description']
            print('.', end='', flush=True)
            try:
                f = server.results.get_testsuite_results_yaml(j_id, '1_custom-tests')
                result = ruamel.yaml.load(f, Loader=ruamel.yaml.RoundTripLoader)
                res_dict = {
                        "job_id": result[0]['job'],
                        "job_name": job_name.split("--"),
                        "result": result[0]['result'],
                        }
                try:
                    devices[device][result[0]['name']].append(res_dict)
                except:
                    devices[device][result[0]['name']] = [res_dict]
                tests_list.add(result[0]['name'])
            except: pass
    html = render_template("index.jinja", devices=devices, tests=tests_list,
            datetime=datetime, start_time=start_time)
    with open("cache.html", 'w') as f:
        f.write(html)
    return html


def main():
    app.run(debug=True, host="0.0.0.0")

if __name__ == "__main__":
    main()

