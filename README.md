# Custom Test Tool

## Setup

  * Make yourself a virtualenv, or just install system wide the packages listed in `./requirements.txt`.
  * That file can help you a lot not providing every argument every time you run the script:

```
$ cat ~/.cttrc
[ctt]
server: https://my.lava.instan.ce/RPC2
username: <lava_username>
token: MyAwEsOmELAVAtOkEn
stream: /anonymous/test/
ssh_server: 192.168.1.3
ssh_username: user-with-write-access-somewhere
api_token: my-awesome-token
rootfs_path: /root/buildroot-ci/out/
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

## Examples

`./ctt.py -b sun8i-h3-orangepi-pc beaglebone-black --send`

Will launch the default job on the OrangePi PC and Beaglebone Black. The default
job consists in running the test suite using the latest mainline kernel provided
by Kernel CI

`./ctt.py -b sun8i-h3-orangepi-pc beaglebone-black --send --upload --kernel ../path/to/my/kernel/zImage`

Will do quite the same but will upload a custom kernel instead of using KernelCI's one.

Be careful when you upload multiple time the same file name, since the storage
is made on a per-user basis: you risk to override your own previous file.   
To prevent this, just name your file differently.

