# HikLoad

A short Python script that downloads video recordings from the day that this script is run from a Hikvision DVR.

## Modifying the config

If you are using the script without Docker, you can modify ./config.py as follows:

```python
CONFIG = {
    //This is the address of the DVR
    "server": "192.168.1.69",
    //These are the cameras that you are going to download from.
    //101 means main stream of camera 1
    //201 means main stream of camera 2
    "cameras": [
        "101",
        "201"
    ],
    "user": "admin",
    "password": "",
    "downloadPath": "./Downloads/"
}
```

If you are using docker, you could use the environment variables:

```docker
ENV server = "192.168.1.69"
ENV cameras = "101 201"
ENV user = "admin"
```

## Using your own script

```python
from util import getList, downloadRTSP

list = getList(ElementTree)
for i in list:
    downloadRTSP(i[0],i[1],i[2])
```