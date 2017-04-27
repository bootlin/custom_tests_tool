#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Florent Jacquet <florent.jacquet@free-electrons.com>
#


from xmlrpc import client
from pprint import pprint
from datetime import datetime, timedelta

import configparser

import smtplib
from email.mime.text import MIMEText


hostname = "farm"

username = "my-user"
token = "my-awesome-token"

config = configparser.ConfigParser()
config.read("notifications.conf")
kwargs = dict(config["mail"])


def main():
    username = config.get("lava", "user")
    token = config.get("lava", "token")

    server = client.ServerProxy("http://%s:%s@%s/RPC2" % (username, token, hostname))
    end_date = datetime.now().replace(hour=11, minute=0, second=0,
            microsecond=0)
    start_date = end_date - timedelta(hours=24)
    job_list = []
    job_list.append("".join([
        '{:<10}'.format("tree"),
        '{:<35}'.format("device"),
        '{:<20}'.format("defconfig"),
        '{:<14}'.format("test"),
        "link",
        ])
    )
    for j in server.results.query("testjob",
            "testjob__end_time__gt__%s,"
            "testjob__end_time__lt__%s,"
            "testcase__result__exact__Test failed,"
            "testjob__submitter__exact__custom-tests,"
            "testsuite__name__exact__1_custom-tests"
            % (start_date, end_date)):
        d = j["description"].split("--")
        job_list.append("".join([
            '{:<10}'.format(d[0]),
            '{:<35}'.format(d[1]),
            '{:<20}'.format(d[2]),
            '{:<14}'.format(d[3]),
            "http://farm/scheduler/job/%s" % j["id"],
            ])
        )
        # job_list.append("    link: http://farm/scheduler/job/%s" % j["id"])

    msg = MIMEText(
            "The following devices failed one of there job during the last 24 hours:\n"
            "At least one of them is yours.\n"
            "\n" + '\n'.join(job_list))
    print(msg)
    user = "guy@libskia.so"
    msg['Subject'] = "Custom tests summary"
    msg['To'] = user
    msg['From'] = kwargs["mail"]
    server = smtplib.SMTP(kwargs["server"], kwargs["port"])
    server.ehlo()
    server.starttls()
    server.login(kwargs["login"], kwargs["password"])
    server.sendmail(kwargs["mail"], [user], msg.as_string())
    server.quit()
    return

if __name__ == "__main__":
    main()

