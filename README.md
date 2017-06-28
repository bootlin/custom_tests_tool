# Custom Test Tool

## Setup

  * Make yourself a virtualenv, or just install system wide the packages listed
in `./requirements.txt`.

```
virtualenv --python=python3 env
source env/bin/activate
pip install -r requirements.txt
```
  * That file can help you a lot not providing every argument every time you run
the script:

```
$ cat ~/.cttrc
[ctt]
server: https://my.lava.instan.ce/RPC2
username: <lava_username>
token: MyAwEsOmELAVAtOkEn
stream: /anonymous/test/
ssh_server: farm.tld
ssh_username: user-with-write-access-somewhere
api_token: my-awesome-token
rootfs_path: /root/buildroot-ci/out/
notify: my.address@my.domai.ne
```

  * `server` is the LAVA API address.
  * `username` is the LAVA username you will use to send jobs.
  * `token` is the LAVA token corresponding to the previous username.
  * `stream` is the LAVA bundle stream to store the jobs results.
  * `ssh_server` is used to upload custom files on the server running LAVA.
  * `ssh_username` is the username you will use to upload file to the server.
  * `api_token` is needed to access KernelCI's API.
  * `rootfs_path` is where you store your rootfs. It can be a path local to the
server your sending the job, as long as it actually contains valid rootfs.
  * `notify` is a comma separated list of addresses where the test results will
be sent, whatever the status of the job.

If you don't specify `notify`, the notifications will be sent to the addresses
listed in the `boards.py` file, in a per board basis.   
So be careful if you know that you will send a lot of tests not to flood those
people.

## Examples

Before any work, don't forget to reactivate your virtualenv to setup the Python
environment: `source env/bin/activate`

#### Help

`./ctt.py -h`

Will give you exhaustive help on any option.

#### Listing boards

`./ctt.py -l`

Will give you list of supported boards.

#### Sending simple job

`./ctt.py -b sun8i-h3-orangepi-pc beaglebone-black`

Will launch the default job on the OrangePi PC and Beaglebone Black. The default
job consists in running the test suite using the latest mainline kernel provided
by Kernel CI.

#### Customizing boot files

`./ctt.py -b sun8i-h3-orangepi-pc beaglebone-black --kernel ../path/to/my/kernel/zImage`

Will do quite the same but will upload a custom kernel instead of using KernelCI's one.

The same way you can use `--rootfs`, `--dtb`, `--modules` to override the
corresponding files.

If you submit jobs for multiple boards, and all your DTB files are in the same
folder, and they are named as described in the `boards.py` file (every
conditions should be met in a standard Linux work tree), you can use the
`--dtb-folder` option in order to let *ctt* guess which local file to use.

Be careful when you upload multiple time the same file name, since the storage
is made on a per-user basis: you risk to override your own previous file.   
To prevent this, just name your file differently.

#### Customizing tests

`./ctt.py -b armada-370-db -t sata`

Will send only the *sata* test on the Armada 370 DB.
`-t` or `--tests` is a list, so you can give as much tests as you want. The
tests need to be available for the given board(s) in the `boards.py` file.

Using this option will override the tests list in the `boards.py` file, so that
you have the tests you gave manually that will be made into jobs.

## Adding a new board

If you wish to add a new board to the custom test tool, it must already be in
LAVA (required), as well as being supported by kernel CI's images (optional,
you can manually provide your own files).

Then just edit the `boards.py` file. It contains just a Python dictionary, and
it's thus easy to add a new board:

```python
'beaglebone-black': { # The key must be the device type name as known to LAVA
                      # for the daily notifications to work.
                      # Otherwise, it's free to choose
    'name': 'BeagleBone Black', # A pretty name for displaying, also free
    'device_type': 'beaglebone-black', # This is the device-type as named is the
                                       # LAVA configuration
    'defconfigs': ['multi_v7_defconfig'], # This is a list of defconfigs built
                                          # by Kernel CI.
                                          # This value can be found at
                                          # https://storage.kernelci.org/mainline/master/v4.11.xxx-XXXXXX
                                          # for example.
    'dt': 'am335x-boneblack', # This is the DT name as found in the kernel,
                              # without the extension.
    'rootfs': 'rootfs_armv7.cpio.gz', # The name of the rootfs you want to use.
                                      # It must be available under the
                                      # --rootfs-path option (or rootfs_path in
                                      # the .cctrc file).
    'test_plan': 'boot', # What LAVA test to you want tu run (only boot is
                         # supported)
    'tests': [ # A list of tests to run.
        {
            'name': 'boot', # Name matching a file in the script folder of the test suite
            'defconfigs': ['multi_v7_defconfig'], # You can override the defconfigs to use, but it's not mandatory
            'template': 'generic_simple_job.jinja', # You can also override the template. 
                                                    # If not, default is generic_simple_job.jinja
            },
        # {
        #     'name': 'network',
        #     'template': 'generic_multinode_job.jinja',
        #     },
        ],
    'notify': ['tux@free-electrons.com'], # The list of people to notify if the
                                          # board begins to fail
    },
```

