# HikLoad

A collection of short Python scripts that utilize the ISAPI specification for Hikvision DVR/NVRs.

`downloadTodayRecordings.py` downloads video recordings from the day that this script is run
`downloadTodayRecordingsAsFrames.py` downloads video recordings from the day that this script is run and saves every 10th frame

## Modifying the config

To use your own DVR it is usually only needed to modify this specific line from the scripts. The first parameter is the IP, the second one is the username and the third is the password. 

The DVR/NVR needs to have ISAPI and RTSP enabled in System/Security and H264+ disabled for every camera.

```python
server = hikvisionapi.HikvisionServer("192.168.10.239", "admin", "password")
```
