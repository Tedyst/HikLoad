# HikLoad

A collection of short Python scripts that utilize the ISAPI specification for Hikvision DVR/NVRs/Cameras.

To use your own DVR it is usually only needed to change the arguments for the script. The first parameter is the IP, the second one is the username and the third is the password. Here are all of the possible parameters:

```
usage: download.py [-h] [--starttime STARTTIME] [--endtime ENDTIME] [--folders | --no-folders] [--debug | --no-debug] [--videoformat VIDEOFORMAT] [--downloads DOWNLOADS]
                   [--frames FRAMES] [--force FORCE] [--skipseconds SKIPSECONDS] [--seconds SECONDS]
                   server username password

Download Recordings from a HikVision server, from a range interval

positional arguments:
  server                the hikvision server's address
  username              the username
  password              the password

optional arguments:
  -h, --help            show this help message and exit
  --starttime STARTTIME
                        the start time in ISO format (default: today at 00:00:00, local time)
  --endtime ENDTIME     the start time in ISO format (default: today at 23:59:59, local time)
  --folders, --no-folders
                        create a separate folder per camera (default: false)
  --debug, --no-debug   enable debug mode (default: false)
  --videoformat VIDEOFORMAT
                        specify video format (default: mkv)
  --downloads DOWNLOADS
                        the downloads folder (default: "Downloads")
  --frames FRAMES       save a frame for every X frames in the video (default: false)
  --force FORCE         force saving of files (default: false)
  --skipseconds SKIPSECONDS
                        skip first X seconds for each video (default: 0)
  --seconds SECONDS     save only X seconds for each video (default: inf)
```

The DVR/NVR needs to have ISAPI and RTSP enabled in System/Security and H264+ disabled for every camera.

## Installing Dependencies

Due to [common problems](https://github.com/kkroening/ffmpeg-python/issues/174#issuecomment-561546739) found while installing the dependencies needed by this project, it is recommended to use a python virtualenv. Here is how to setup one:

```bash
pip install virtualenv
virtualenv venv
source venv/bin/activate # On Linux/Mac OS
venv\Scripts\activate    # On Windows
pip install -r requirements.txt
```

And everytime you restart the terminal and want to use the virtualenv, you need to run these commands:

```bash
source venv/bin/activate # On Linux/Mac OS
venv\Scripts\activate    # On Windows
```

## Running the script

If you want to use the default arguments, you can specify only the required arguments:

```bash
python download.py 192.168.10.239 username password
```

For more advanced users, you can specify optional arguments like the start and end time for the video search:

```bash
python download.py 192.168.10.239 username password --starttime 2021-09-19T03:00:00+03:00 --endtime 2021-09-20T04:00:00+00:00
```
