# HikLoad

A short Python script that downloads video recordings from the day that this script is run from a Hikvision DVR.

## Using with docker

```bash
docker pull tedyst/hikload:latest
```

If you are using docker, you could use the environment variables:

```docker
ENV server "192.168.1.69"
ENV cameras "101 201"
ENV user "admin"
```

## Modifying the config

You can modify ./config.py as follows:

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

## Using your own script

```python
from hikload.util import getList, downloadRTSP

list = getList(ElementTree)
for i in list:
    downloadRTSP(i[0],i[1],i[2])
```