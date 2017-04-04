#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Florent Jacquet <florent.jacquet@free-electrons.com>
#

import sys
import json
from xmlrpc import client
from flask import Flask, render_template
from datetime import datetime


hostname = "farm"
server = client.ServerProxy("http://%s/RPC2" % (hostname))

print(server.system.listMethods())

device_type_blacklist = ['dummy-ssh']
tests_list = {
        "network": 'lava-test-shell-run',
        "mmc": '/tests/tests/mmc',
        "usb": '/tests/tests/usb',
        "sata": '/tests/tests/sata',
        "first_test": '/tests/tests/first_test',
        }


app = Flask(__name__)

@app.route("/")
def index():
    with open("cache.html", 'r') as f:
        html = f.read()
    return html

@app.route("/refresh")
def generate():
    devices = {d[0]:{t:[] for t in tests_list.keys()} for d in server.scheduler.all_devices()}
    # print(devices)
    for b in reversed(server.dashboard.bundles('/anonymous/custom-tests/')[-400:]):
        print('.', end='', flush=True)
        # print(b)
        bundle = server.dashboard.get(b["content_sha1"])
        # print("\Bundle: \n\n")
        bundle_json = json.loads(bundle['content'])
        # print(json.dumps(bundle_json, indent=4))
        for t in bundle_json["test_runs"]:
            # print(t["attributes"]["target.device_type"])
            if t["attributes"]["target.device_type"] in device_type_blacklist:
                continue
            for r in t["test_results"]:
                for test,prefix in tests_list.items():
                    if r["test_case_id"].startswith(prefix):
                        devices[t["attributes"]["target"]][test].append({
                            "job_id": b["associated_job"],
                            "job_name": b["content_filename"].split('--'),
                            "result": r["result"]
                            })
                        # print(json.dumps(bundle_json, indent=2))
    print('\n', end='')
    html = render_template("index.jinja", devices=devices, tests=tests_list, datetime=datetime)
    with open("cache.html", 'w') as f:
        f.write(html)
    return html



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

