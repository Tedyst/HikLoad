# HikLoad

A collection of short Python scripts that utilize the ISAPI specification for Hikvision DVR/NVRs/Cameras.

To use your own DVR it is usually only needed to change the arguments for the script. The first parameter is the IP, the second one is the username and the third is the password. Here are all of the possible parameters:

```
usage: hikload [-h] [--starttime STARTTIME] [--endtime ENDTIME] [--folders {onepercamera,oneperday,onepermonth,oneperyear}] [--debug | --no-debug]
               [--videoformat VIDEOFORMAT] [--downloads DOWNLOADS] [--frames FRAMES] [--force FORCE] [--skipseconds SKIPSECONDS] [--seconds SECONDS] [--days DAYS]
               [--skipdownload | --no-skipdownload] [--allrecordings | --no-allrecordings] [--cameras CAMERAS] [--localtimefilenames | --no-localtimefilenames]
               [--yesterday | --no-yesterday] [--ffmpeg | --no-ffmpeg] [--forcetranscoding | --no-forcetranscoding] [--photos | --no-photos] [--mock | --no-mock]
               server username password

Download Recordings from a HikVision server, from a range interval

positional arguments:
  server                the hikvision server's address
  username              the username
  password              the password

options:
  -h, --help            show this help message and exit
  --starttime STARTTIME
                        the start time in ISO format (default: today at 00:00:00, local time)
  --endtime ENDTIME     the start time in ISO format (default: today at 23:59:59, local time)
  --folders {onepercamera,oneperday,onepermonth,oneperyear}
                        create a separate folder per camera/duration (default: disabled)
  --debug, --no-debug   enable debug mode (default: false)
  --videoformat VIDEOFORMAT
                        specify video format (default: mp4)
  --downloads DOWNLOADS
                        the downloads folder (default: "Downloads")
  --frames FRAMES       save a frame for every X frames in the video (default: false)
  --force FORCE         force saving of files (default: false)
  --skipseconds SKIPSECONDS
                        skip first X seconds for each video (default: 0)
  --seconds SECONDS     save only X seconds for each video (default: inf)
  --days DAYS           download videos for the last X days (ignores --endtime and --starttime)
  --skipdownload, --no-skipdownload
                        do not download anything
  --allrecordings, --no-allrecordings
                        download all recordings saved
  --cameras CAMERAS     camera IDs to search (example: --cameras=201,301)
  --localtimefilenames, --no-localtimefilenames
                        save filenames using date in local time instead of UTC
  --yesterday, --no-yesterday
                        download yesterday's videos
  --ffmpeg, --no-ffmpeg
                        enable ffmpeg and disable downloading directly from server
  --forcetranscoding, --no-forcetranscoding
                        force transcoding if downloading directly from server
  --photos, --no-photos
                        enable experimental downloading of saved photos
  --mock, --no-mock     enable mock mode WARNING! This will not download anything from the server
```

The DVR/NVR needs to have ISAPI and RTSP enabled in System/Security and H264+ disabled for every camera.

## Running the script

You can install the script from [PyPi](https://pypi.org/project/hikload/), run the script directly from the source, or use the Docker image:

```bash
docker pull ghcr.io/tedyst/hikload
docker run -v $(pwd)/Downloads:/app/Downloads ghcr.io/tedyst/hikload 192.168.10.239 admin password
```

If you decide to use the PyPi package, there will be a command called `hikload` in your PATH:
```bash
pip install hikload
hikload -h
```

To run the script from source, you can use this command from the root directory of the project:
```bash
python -m hikload -h
```

If you want to use the default arguments, you can specify only the required arguments:

```bash
hikload 192.168.10.239 username password
```

For more advanced users, you can specify optional arguments like the start and end time for the video search:

```bash
hikload 192.168.10.239 username password --starttime 2021-09-19T03:00:00+03:00 --endtime 2021-09-20T04:00:00+00:00
```

Or just specify the cameras that you want to search(be sure to use the HikVision format - 101 for first camera, 201 for the second one...):

```bash
hikload 192.168.10.239 username password --cameras=201,301
```

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