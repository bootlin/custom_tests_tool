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
from collections import OrderedDict

import configparser

import smtplib
from email.mime.text import MIMEText

JOB_STATUS = {
        0: "Submitted",
        1: "Running",
        2: "Complete",
        3: "Incomplete",
        4: "Canceled",
        5: "Canceling",
        }

JOB_REPORT_STATUS = OrderedDict()
JOB_REPORT_STATUS['failed_tests'] = "The following jobs did not pass the custom tests:"
JOB_REPORT_STATUS['failed_boot'] = "The following jobs did not boot:"
JOB_REPORT_STATUS['lava_error'] = "The following jobs did not reach power up:"
JOB_REPORT_STATUS['passed_tests'] = "The following jobs have ended up without problem:"


# Get config
config = configparser.ConfigParser()
config.read("notifications.conf")

# Get board config
ctt_root_location = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
with open(os.path.join(ctt_root_location, "ci_tests.json")) as f:
    boards_config = json.load(f)

# Get LAVA API handler
lava_api = client.ServerProxy("http://%s:%s@%s/RPC2" % (
    config.get("lava", "user"),
    config.get("lava", "token"),
    config.get("lava", "hostname")), allow_none=True)

# Define a Job class to ease processing
class Job(object):
    TABLE_TITLE = "".join([
            '{:<12}'.format("tree"),
            '{:<14}'.format("branch"),
            '{:<25}'.format("device"),
            '{:<30}'.format("defconfig"),
            '{:<12}'.format("test"),
            "link",
            ])

    def __str__(self):
        return "".join([
            '{:<12}'.format(self.tree[:9] + '..' if len(self.tree) > 9 else self.tree),
            '{:<14}'.format(self.branch[:11] + '..' if len(self.branch) > 11 else self.branch),
            '{:<25}'.format(self.device[:22] + '..' if len(self.device) > 22 else self.device),
            '{:<30}'.format(self.defconfig[:27] + '..' if len(self.defconfig) > 27 else self.defconfig),
            '{:<12}'.format(self.test[:9] + '..' if len(self.test) > 9 else self.test),
            "http://lava.bootlin.com/scheduler/job/%s" % self.id,
            ])

    def __init__(self, job):
        """
        `job` is a dictionary returned by the LAVA API
        """
        self.id = job['id']
        d = job['description'].split('--')
        self.device = d[0]
        self.tree = d[1]
        self.branch = d[2]
        self.defconfig = d[3]
        self.test = d[4]

    def has_powered_up(self):
        power_up = lava_api.results.make_custom_query("testjob",
                "testjob__id__exact__%s,"
                "testcase__name__exact__pdu-reboot"
                % (self.id))
        return bool(power_up)

    def has_booted(self):
        boot = lava_api.results.make_custom_query("testjob",
                "testjob__id__exact__%s,"
                "testcase__name__exact__auto-login-action"
                % (self.id))
        return bool(boot)

    def has_passed_test(self):
        tests = lava_api.results.make_custom_query("testcase",
                "testjob__id__exact__%s,"
                "testcase__name__exact__%s"
                % (self.id, self.test))
        if not tests:
            return False
        return not bool(tests[0]['result'])


def main():
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=24)


    # mail_list is a data structure built like this:
    # mail_list = {
    #         'email.address@domain.tld': {
    #             'passed_tests': [str(Job object), str(other Job object)],
    #             'failed_tests': [str(Job object), ...],
    #             }
    #         }
    mail_list = {}

    # Get all the last jobs
    all_jobs = lava_api.results.make_custom_query("testjob",
            "testjob__end_time__gt__%s,"
            "testjob__end_time__lt__%s,"
            "testjob__submitter__exact__custom-tests"
            % (start_date, end_date), None)

    # Build mail_list
    for job in all_jobs:
        if job['requested_device_type_id'] == "dummy-ssh":
            continue
        j = Job(job)

        if j.has_passed_test():
            status = "passed_tests"
        elif j.has_booted():
            status = "failed_tests"
        elif j.has_powered_up():
            status = "failed_boot"
        else:
            status = "lava_error"

        board = boards_config.get(j.device, None)
        if board:
            for email in board.get("notify", []):
                if email not in mail_list:
                    mail_list[email] = {}
                if status not in mail_list[email]:
                    mail_list[email][status] = [Job.TABLE_TITLE]
                mail_list[email][status].append(str(j))


    # Now send the emails
    server = smtplib.SMTP(config.get("mail", "server"), config.get("mail", "port"))
    server.ehlo()
    server.starttls()
    server.login(config.get("mail", "login"), config.get("mail", "password"))
    for user,job_list in mail_list.items():

        msg_list = []
        for status,msg in JOB_REPORT_STATUS.items():
            if status in job_list:
                msg_list += [msg]
                msg_list += job_list[status]
                msg_list += [""]

        print("\nMessage to %s:" % user)
        print('\n'.join(msg_list))
        msg = MIMEText('\n'.join(msg_list))
        msg['Subject'] = "CI summary"
        msg['From'] = config.get("mail", "from")
        msg['To'] = user
        server.sendmail(config.get("mail", "from"), [user], msg.as_string())
    server.quit()
    return

if __name__ == "__main__":
    main()

