#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Florent Jacquet <florent.jacquet@free-electrons.com>
#

import json
import os

from xmlrpc import client
from pprint import pprint
from datetime import datetime, timedelta

import configparser

import smtplib
from email.mime.text import MIMEText

hostname = "lava.tld"
username = "my-user"
token = "my-awesome-token"

config = configparser.ConfigParser()
config.read("notifications.conf")
kwargs = dict(config["mail"])

JOB_STATUS = {
        0: "Submitted",
        1: "Running",
        2: "Complete",
        3: "Incomplete",
        4: "Canceled",
        5: "Canceling",
        }

def main():
    hostname = config.get("lava", "hostname")
    username = config.get("lava", "user")
    token = config.get("lava", "token")

    ctt_root_location = os.path.abspath(os.path.dirname(
        os.path.realpath(__file__)))
    with open(os.path.join(ctt_root_location, "ci_tests.json")) as f:
        boards = json.load(f)

    server = client.ServerProxy("http://%s:%s@%s/RPC2" % (username, token, hostname))
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=24)

    # Get the results
    complete_tests = server.results.make_custom_query("testjob",
            "testjob__end_time__gt__%s,"
            "testjob__end_time__lt__%s,"
            "testcase__result__exact__Test passed,"
            "testjob__submitter__exact__custom-tests,"
            "testsuite__name__exact__1_custom-tests"
            % (start_date, end_date))
    incomplete_tests = server.results.make_custom_query("testjob",
            "testjob__end_time__gt__%s,"
            "testjob__end_time__lt__%s,"
            "testjob__submitter__exact__custom-tests,"
            "testjob__status__exact__Incomplete"
            % (start_date, end_date))
    failed_tests = server.results.make_custom_query("testjob",
            "testjob__end_time__gt__%s,"
            "testjob__end_time__lt__%s,"
            "testcase__result__exact__Test failed,"
            "testjob__submitter__exact__custom-tests,"
            "testsuite__name__exact__1_custom-tests"
            % (start_date, end_date))

    # Define how to process the jobs lists
    def append_job(j, test_status):
        d = j["description"].split("--")
        # pprint(j)
        job_report = "".join([
            '{:<10}'.format(d[1][:7] + '..' if len(d[1]) > 7 else d[1]), # tree
            '{:<10}'.format(d[2][:7] + '..' if len(d[2]) > 7 else d[2]), # branch
            '{:<25}'.format(d[0][:22] + '..' if len(d[0]) > 22 else d[0]), # device
            '{:<30}'.format(d[3][:27] + '..' if len(d[3]) > 27 else d[3]), # defconfig
            '{:<12}'.format(d[4][:9] + '..' if len(d[4]) > 9 else d[4]), # test
            '{:<12}'.format(test_status + '..' if len(test_status) > 9 else test_status), # test status
            '{:<12}'.format(JOB_STATUS[j["status"]]), # job status
            "http://lava.free-electrons.com/scheduler/job/%s" % j["id"], # link
            ])
        board = boards.get(j["requested_device_type_id"], None)
        if board:
            for email in board.get("notify", []):
                if email in mail_list.keys():
                    mail_list[email].append(job_report)
                else:
                    mail_list[email] = [job_report]

    # Process the jobs
    mail_list = {}
    for j in failed_tests:
        append_job(j, "failed")
    for j in incomplete_tests:
        append_job(j, "unknown")
    for j in complete_tests:
        append_job(j, "OK")

    # Now send the emails
    server = smtplib.SMTP(kwargs["server"], kwargs["port"])
    server.ehlo()
    server.starttls()
    server.login(kwargs["login"], kwargs["password"])
    for user,job_list in mail_list.items():
        msg_list = []
        msg_list.append("".join([
            '{:<10}'.format("tree"),
            '{:<10}'.format("branch"),
            '{:<25}'.format("device"),
            '{:<30}'.format("defconfig"),
            '{:<12}'.format("test"),
            '{:<12}'.format("test status"),
            '{:<12}'.format("job status"),
            "link",
            ])
        )
        msg_list += job_list
        print("\nMessage to %s:" % user)
        print('\n'.join(msg_list))
        msg = MIMEText(
                "The following jobs failed during the last 24 hours:\n"
                "\n" + '\n'.join(msg_list))
        msg['Subject'] = "CI summary"
        msg['From'] = kwargs["mail"]
        msg['To'] = user
        server.sendmail(kwargs["mail"], [user], msg.as_string())
    server.quit()
    return

if __name__ == "__main__":
    main()

