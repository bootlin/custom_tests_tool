# Custom Test Tool

## Setup

  * Make yourself a virtualenv, or just install system wide the packages listed
in `./requirements.txt`.

```
virtualenv --python=python3 env
source env/bin/activate
pip install -r requirements.txt
```

Note: If you have Python2 and Python3 installed in your system, you must use `pip3`
to install dependencies because this tool needs Python3's modules.

  * That file can help you a lot not providing every argument every time you run
the script:

```
$ cat ~/.cttrc
[ctt]
server: https://my.lava.instan.ce/RPC2
username: <lava_username>
token: MyAwEsOmELAVAtOkEn
ssh_server: farm.tld
ssh_username: user-with-write-access-somewhere
api_token: my-awesome-token
notify: my.address@my.domai.ne
web_ui_address: http://my.lava.instan.ce
```

  * `server` is the LAVA API address.
  * `username` is the LAVA username you will use to send jobs.
  * `token` is the LAVA token corresponding to the previous username.
  * `ssh_server` is used to upload custom files on the server running LAVA.
  * `ssh_username` is the username you will use to upload file to the server.
  * `api_token` is needed to access KernelCI's API.
  * `notify` is a comma separated list of addresses where the test results will
be sent, whatever the status of the job.
  * `web_ui_address` is the base URL of the LAVA Web UI.

## Examples

Before any work, don't forget to reactivate your virtualenv to setup the Python
environment: `source env/bin/activate`

### Help

`./ctt.py -h`

Will give you exhaustive help on any option.

### Listing boards

`./ctt.py -l`

Will give you list of supported boards.

### Sending a job

`./ctt.py -b sun8i-h3-orangepi-pc beaglebone-black -t usb --kernel
/path/to/my/kernel/zImage --dtb /path/to/dt.dtb`

Will upload a custom kernel and DT, and create the `usb` job using them.

The same way you can use `--rootfs`, `--modules` to override the corresponding
files, but they are not mandatory.

If you submit jobs for multiple boards, and all your DTB files are in the same
folder, and they are named as described in the `boards.json` file (every
conditions should be met in a standard Linux work tree), you can use the
`--dtb-folder` option in order to let *ctt* guess which local file to use.

Be careful when you upload multiple time the same file name, since the storage
is made on a per-user basis: you risk to override your own previous file.   To
prevent this, just name your file differently.

### Manually launching daily CI

You have to use the `ci_launcher.py` command to achieve that: `./ci_launcher.py
-b all`


## Adding boards, tests, daily jobs...

### A new board

If you wish to add a new board to the custom test tool, it must already be in
LAVA (required), as well as being supported by kernel CI's images (optional, you
can manually provide your own files).

Then just edit the `boards.json` file. It contains just a list of dictionaries,
and it's thus easy to add a new board:

```json
"beaglebone-black": {
    "arch": "arm",
    "dt": "am335x-boneblack",
    "rootfs": "rootfs_armv7",
    "test_plan": "boot"
    }
```

  * The key must be the device type name as known to LAVA.
  * *arch*: The architecture of the board as found in the kernel.
  * *dt*: This is the DT name as found in the kernel, without the extension.
  * *rootfs*: The name of the rootfs you want to use.
  * *test_plan*: What LAVA test to you want to run (usually boot or boot-nfs).

### A new test

Simply add its description in `tests.json`. You must specify the template and
the timeout.

```json
"boot": {
    "template": "generic_simple_job.jinja",
    "timeout": 10
}
```

  * The key must be an existing script in the `scripts` folder of the
[test\_suite](https://github.com/free-electrons/test_suite) repository, without
the extension.
  * *template*: This must be an existing template in the `./src/jobs_templates/`
folder.
  * *timeout*: The timeout of the job, in minutes.

### The daily jobs and the notifications

To add a new board/test/tree/branch/defconfig configuration to test every day,
or to subscribe to the daily notifications of a board, you have to look at the
`ci_tests.json` file, and add something like this:

```json
"beaglebone-black": {
    "configs": [
        { "tree": "mainline", "branch": "master", "defconfig": "multi_v7_defconfig" },
        { "tree": "stable", "branch": "linux-3.16.y", "defconfig": "multi_v7_defconfig" },
        { "tree": "stable", "branch": "linux-4.1.y", "defconfig": "multi_v7_defconfig" },
        { "tree": "stable", "branch": "linux-4.4.y", "defconfig": "multi_v7_defconfig" },
        { "tree": "stable", "branch": "linux-4.9.y", "defconfig": "multi_v7_defconfig" }
    ],
    "tests": [
        { "name": "mmc" },
        { "name": "network" }
    ],
    "notify": [
        "tux@domain.tld"
    ]
},

```

  * The key must be a LAVA device-type existing in `boards.json`.
  * *configs*: A list of tree/branch/defconfig used by default for the tests.
  * *tests*: A list of tests. `name` is mandatory. You can add a `config` key
there too, with the same structure as the main one, to override which
configuration should be run for this test.
  * *notify*: A list of email addresses that will get daily summaries for this
board.


