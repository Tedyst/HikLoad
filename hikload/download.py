import argparse
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import List
from io import StringIO
import sys

import ffmpeg
import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

import hikload.hikvisionapi as hikvisionapi
from hikload.hikvisionapi.classes import HikvisionException

from hikload.video import concat_channel_videos, cut_video

if sys.version_info < (3, 9):
    # This is a workaround for Python 3.8 and below not having the BooleanOptionalAction
    argparse.BooleanOptionalAction = "store_true"


class Recording():
    def __init__(self, cid, cname, url, startTime, endTime=None):
        self.cid = cid
        self.cname = cname
        self.url = url
        self.startTime = startTime
        self.endTime = endTime

        if self.endTime is not None:
            start = datetime.strptime(
                self.startTime, "%Y-%m-%dT%H:%M:%SZ")
            end = datetime.strptime(
                self.endTime, "%Y-%m-%dT%H:%M:%SZ")
            self.duration =  end - start
        else:
            self.duration = None

    def __str__(self) -> str:
        return "{}-{}".format(self.cname, self.startTime)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download Recordings from a HikVision server, from a range interval')
    parser.add_argument('--server', type=str, dest="server",
                        help='the hikvision server\'s address')
    parser.add_argument('--username', type=str, dest="username",
                        help='the username')
    parser.add_argument('--password', type=str, dest="password",
                        help='the password')
    parser.add_argument('--starttime', type=lambda s: datetime.fromisoformat(s),
                        default=datetime.now().replace(
                            hour=0, minute=0, second=0, microsecond=0).isoformat(),
                        help='the start time in ISO format (default: today at 00:00:00, local time)')
    parser.add_argument('--endtime', type=lambda s: datetime.fromisoformat(s),
                        default=datetime.now().replace(
                            hour=23, minute=59, second=59, microsecond=0).isoformat(),
                        help='the start time in ISO format (default: today at 23:59:59, local time)')
    parser.add_argument('--folders', type=str, dest="folders", choices=['onepercamera', 'oneperday', 'onepermonth', 'oneperyear'],
                        help='create a separate folder per camera/duration (default: disabled)')
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction, dest="debug",
                        help='enable debug mode (default: false)')
    parser.add_argument('--videoformat', dest="videoformat", default="mp4", choices=['mkv', 'mp4', 'avi'],
                        help='specify video format (default: mp4)')
    parser.add_argument('--downloads', dest="downloads", default=os.path.join(os.getcwd(), "Downloads"),
                        help='the downloads folder (default: "Downloads")')
    parser.add_argument('--frames', dest="frames", type=int,
                        help='save a frame for every X frames in the video (default: false)')
    parser.add_argument('--force', dest="force", action=argparse.BooleanOptionalAction,
                        help='force saving of files (default: false)')
    parser.add_argument('--skipseconds', dest="skipseconds", type=int,
                        help='skip first X seconds for each video (default: 0)')
    parser.add_argument('--seconds', dest="seconds", type=int,
                        help='save only X seconds for each video (default: inf)')
    parser.add_argument('--days', dest="days", type=int,
                        help='download videos for the last X days (ignores --endtime and --starttime)')
    parser.add_argument('--skipdownload', dest="skipdownload", action=argparse.BooleanOptionalAction,
                        help='do not download anything')
    parser.add_argument('--allrecordings', dest="allrecordings", action=argparse.BooleanOptionalAction,
                        help='download all recordings saved')
    parser.add_argument('--cameras', dest="cameras", type=lambda s: s.split(","),
                        help='camera IDs to search (example: --cameras=201,301)')
    parser.add_argument('--localtimefilenames', dest="localtimefilenames", action=argparse.BooleanOptionalAction,
                        help='save filenames using date in local time instead of UTC')
    parser.add_argument('--yesterday', dest="yesterday", action=argparse.BooleanOptionalAction,
                        help='download yesterday\'s videos')
    parser.add_argument('--ffmpeg', dest="ffmpeg", action=argparse.BooleanOptionalAction,
                        help='enable ffmpeg and disable downloading directly from server')
    parser.add_argument('--forcetranscoding', dest="forcetranscoding", action=argparse.BooleanOptionalAction,
                        help='force transcoding if downloading directly from server')
    parser.add_argument('--photos', dest="photos", action=argparse.BooleanOptionalAction,
                        help='enable experimental downloading of saved photos')
    parser.add_argument('--mock', dest="mock", action=argparse.BooleanOptionalAction,
                        help='enable mock mode  WARNING! This will not download anything from the server')
    parser.add_argument('--videoname', dest="videoname", type=str, default="",
                        help='name of the downloaded video(s). Does not suppress --localtimefilenames')
    parser.add_argument('--concat', dest="concat", action=argparse.BooleanOptionalAction,
                        help='enable concatenating downloaded vides into one file (channel-wise)')
    parser.add_argument('--trim', dest="trim", action=argparse.BooleanOptionalAction,
                        help='enable triming of the concatenated video. Does work only with --concat enabled')
    parser.add_argument('--httptimeout', dest="httptimeout", type=int,
                        help='HTTP requests will time out after a given seconds of server inactivity while waiting for an answer')
    parser.add_argument('--ui', dest="ui", action=argparse.BooleanOptionalAction,
                        # If running under PyInstaller, use the UI
                        default=bool(getattr(sys, 'frozen', False)),
                        help='enable UI interface WARNING! Requires Qt5 to be installed')
    parser.add_argument('--skipexisting', dest="skipexisting", action=argparse.BooleanOptionalAction,
                        help='Skip dowloading files those already exist in the destination dir. Won\'t skip files that need preprocessing')
    args = parser.parse_args()
    return args


def create_folder_and_chdir(dir):
    path = str(dir)
    if not os.path.exists(path):
        os.makedirs(os.path.normpath(path))
        logging.debug("Created folder %s" % path)
    else:
        logging.debug("Folder %s already exists" % path)
    if os.environ.get('RUNNING_IN_DOCKER') == 'TRUE':
        os.chmod(os.path.normpath(path), 0o777)
    os.chdir(os.path.normpath(path))


def photo_download_from_channel(server: hikvisionapi.HikvisionServer, args, url, filename, cid):
    start_time = time.perf_counter()
    name = "%s.jpeg" % filename
    if args.skipexisting and os.path.exists(name) and os.path.getsize(name) > 0:
        logging.debug(f"Skipping {name} as it already exists")
        return
    logging.debug("Started downloading %s" % name)
    logging.debug(
        "Files to download: (url: %r, name: %r)" % (url, name))
    r = server.ContentMgmt.search.downloadURI(url)
    open(name, 'wb').write(r.content)
    if os.environ.get('RUNNING_IN_DOCKER') == 'TRUE':
        os.chmod(name, 0o777)
    end_time = time.perf_counter()
    run_time = end_time - start_time
    logging.info(f"Finished downloading {name} in {run_time:.2f} seconds")


def video_download_from_channel(server: hikvisionapi.HikvisionServer, args, url, filename, cid):
    start_time = time.perf_counter()
    if args.folders:
        name = "%s.%s" % (filename, args.videoformat)
    else:
        name = "%s-%s.%s" % (filename, cid, args.videoformat)
    logging.debug("Started downloading %s" % name)
    logging.debug(
        "Files to download: (url: %r, name: %r)" % (url, name))
    if args.frames:
        try:
            url = url.replace(server.host, server.address(
                protocol=False, credentials=True))
            hikvisionapi.downloadRTSPOnlyFrames(
                url, name, debug=args.debug, force=args.force, modulo=args.frames, skipSeconds=args.skipseconds, seconds=args.seconds)
        except ffmpeg.Error as e:
            logging.error(
                "Could not download %s. Try to remove --frames." % name)
            logging.error(e)
    if args.ffmpeg:
        try:
            url = url.replace(server.host, server.address(
                protocol=False, credentials=True))
            hikvisionapi.downloadRTSP(
                url, name, debug=args.debug, force=args.force, skipSeconds=args.skipseconds, seconds=args.seconds)
        except ffmpeg.Error as e:
            logging.error(
                "Could not download %s. Try to remove --fmpeg." % name)
            logging.error(e)
    else:
        if args.folders:
            temporaryname = "%s.mp4" % filename
        else:
            temporaryname = "%s-%s.mp4" % (filename, cid)
        
        if args.skipexisting and os.path.exists(temporaryname) and os.path.getsize(temporaryname) > 0:
            logging.debug(f"Skipping {temporaryname} as it already exists")
            return
        try:
            r = server.ContentMgmt.search.downloadURI(url)
        except hikvisionapi.HikvisionError as e:
            try:
                supports = server.ContentMgmt.search.get_download_capabilities()
                logging.debug(f'Device capabilities: {supports}')
                if supports['DownloadAbility']['isSupportDownloadbyFileName'] == 'false':
                    logging.error(
                        "Downloading by file name is not supported for this device.")
                    logging.error(
                        "Try to add --ffmpeg to force recording the videos.")
                    logging.error(e)
                    return
                if supports['DownloadAbility']['isSupportDownloadbyTime'] == 'false':
                    logging.error(
                        "Downloading by time is not supported for this device.")
                    logging.error(
                        "Try to add --ffmpeg to force recording the videos.")
                    logging.error(e)
                    return
            except (hikvisionapi.HikvisionError, TypeError) as e:
                logging.error(
                    "Could not get download capabilities. The device dosen't seem to support getting capabilities.")
                logging.error(
                    "Try to add --ffmpeg to force recording the videos.")
                logging.error(e)
                return
            logging.error(
                "Could not download %s. Try to add --ffmpeg." % name)
            logging.error(e)
            return
        open(temporaryname, 'wb').write(r.content)
        try:
            logging.info(args)
            hikvisionapi.processSavedVideo(
                temporaryname, debug=args.debug, skipSeconds=args.skipseconds, seconds=args.seconds,
                fileFormat=args.videoformat, forceTranscode=args.forcetranscoding)
        except ffmpeg.Error as e:
            logging.error(
                "Could not transcode %s. Try to remove --forcetranscoding." % name)
            logging.error(e)
    if os.environ.get('RUNNING_IN_DOCKER') == 'TRUE':
        os.chmod(name, 0o777)
    end_time = time.perf_counter()
    run_time = end_time - start_time
    logging.info(f"Finished downloading {name} in {run_time:.2f} seconds")


def search_for_recordings(server: hikvisionapi.HikvisionServer, args) -> dict:
    start_time = time.perf_counter()
    channelids = []
    channels = []
    if args.cameras:
        for cid in args.cameras:
            channelids.append(cid)
            channels.append({
                'id': str(cid),
                'channelName': str(cid),
            })
    else:
        try:
            channelList = server.Streaming.getChannels()
            for channel in channelList['StreamingChannelList']['StreamingChannel']:
                if (int(channel['id']) % 10 == 1):
                    if args.photos:
                        # Force looking at the hidden 103 channel for the photos
                        channel['id'] = str(int(channel['id'])+2)
                    channelids.append(channel['id'])
                    channels.append(channel)
                logging.info("Found channels %s" % channelids)
        except HikvisionException as e:
            logging.error(
                "Could not get channel list. If you still want to continue, add the argument --cameras with the channel ids you want to download.")
            raise e

    downloadDict = {
        "num_videos": 0,
        "num_channels": 0,
        "channels": {}
    }
    for channel in channels:
        cname = channel['channelName']
        cid = channel['id']
        if args.days:
            endtime = datetime.now().replace(
                hour=23, minute=59, second=59, microsecond=0)
            starttime = endtime - timedelta(days=args.days)
        elif args.yesterday:
            endtime = datetime.now().replace(
                hour=23, minute=59, second=59, microsecond=0) - timedelta(days=1)
            starttime = endtime - timedelta(days=1)
        else:
            starttime = args.starttime
            endtime = args.endtime

        logging.debug("Using %s and %s as start and end times" %
                      (starttime.isoformat() + "Z", endtime.isoformat() + "Z"))

        try:
            if args.allrecordings:
                recordings = server.ContentMgmt.search.getAllRecordingsForID(
                    cid)
                logging.info("There are %s recordings in total for channel %s" %
                             (recordings['CMSearchResult']['numOfMatches'], cid))
            else:
               
                if args.concat:
                    # List recordings around given time to estimate true duration
                    # Would break if one recording is longer than a day. Could be solved
                    # by listing all recordings but that takes a lot of time.
                    earlier_start = starttime - timedelta(days=1)
                    later_end = endtime + timedelta(days=1)
                    recordings = server.ContentMgmt.search.getPastRecordingsForID(
                        cid, earlier_start.isoformat() + "Z", later_end.isoformat() + "Z")
                else:
                    recordings = server.ContentMgmt.search.getPastRecordingsForID(
                        cid, starttime.isoformat() + "Z", endtime.isoformat() + "Z")

                logging.info("Found %s recordings for channel %s" %
                             (recordings['CMSearchResult']['numOfMatches'], cid))
        except hikvisionapi.classes.HikvisionException as e:
            logging.error("Could not get recordings for channel %s" % cid)
            logging.error(e)
            continue
        
        # This loops from every recording
        if recordings['CMSearchResult']['numOfMatches'] != "0":
            recordinglist = recordings['CMSearchResult']['matchList']['searchMatchItem']
        else:
            recordinglist = []
        # In case there is only one recording, we need to make it a list
        if type(recordinglist) is not list:
            recordinglist = [recordinglist]
        
        # Prepare data structure for the channel
        downloadDict["channels"][cid] = {
            "num_videos": 0,
            "filenames": [],
            "duration": endtime - starttime,
            "startTime": starttime.isoformat() + "Z",
            "endTime": endtime.isoformat() + "Z",
            "minStartTime": None,
            "recordings": [],
        }

        result = []
        for i in recordinglist:

            # Check if the recoding is in the required timespan
            recording_startTime = datetime.strptime(
                i['timeSpan']['startTime'], "%Y-%m-%dT%H:%M:%SZ")
            recording_endTime = datetime.strptime(
                i['timeSpan']['endTime'], "%Y-%m-%dT%H:%M:%SZ")
            if recording_endTime < args.starttime or recording_startTime > args.endtime:
                continue
            
            rec = Recording(
                cid=cid,
                cname=cname,
                url=i['mediaSegmentDescriptor']['playbackURI'],
                startTime=i['timeSpan']['startTime'],
                endTime=i['timeSpan']['endTime'],
            )
            
            result.append(rec)
            downloadDict["channels"][cid]["num_videos"] += 1
            logging.debug("Found recording type %s on channel %s" % (
                i['mediaSegmentDescriptor']['contentType'], cid
            ))

            if not args.photos and i['mediaSegmentDescriptor']['contentType'] != 'video':
                # This recording is not a video, skip it
                continue

        # Save channel metadata
        downloadDict["channels"][cid]["recordings"].extend(result)
        if downloadDict["channels"][cid]["recordings"]:
            downloadDict["channels"][cid]["minStartTime"] = downloadDict["channels"][cid]["recordings"][0].startTime
        downloadDict["num_videos"] += downloadDict["channels"][cid]["num_videos"]
        downloadDict["num_channels"] += 1

    end_time = time.perf_counter()
    run_time = end_time - start_time
    logging.info(
        f"Found {downloadDict['num_videos']} files to download in {run_time:.2f} seconds")
    return downloadDict


def search_for_recordings_mock(args) -> dict:
    logger = logging.getLogger('hikload')
    logger.debug(f"{args=}")
    return {
        "num_videos": 5,
        "channels": {
            "Channel 1": {
                "num_videos": 5,
                "filenames": [],
                "duration": timedelta(minutes=10),
                "startTime": "2021-12-19T09:04:46Z",
                "endTime": None,
                "minStartTime": None,
                "recordings": [
                    Recording(cid=1, cname="Channel 1",
                            startTime="2021-12-19T09:04:46Z", url="https://tedyst.ro"),
                    Recording(cid=1, cname="Channel 1",
                            startTime="2021-12-19T09:04:47Z", url="https://tedyst.ro"),
                    Recording(cid=1, cname="Channel 1",
                            startTime="2021-12-19T09:04:48Z", url="https://tedyst.ro"),
                    Recording(cid=1, cname="Channel 1",
                            startTime="2021-12-19T09:04:49Z", url="https://tedyst.ro"),
                    Recording(cid=1, cname="Channel 1",
                            startTime="2021-12-19T09:04:50Z", url="https://tedyst.ro"),
                    Recording(cid=1, cname="Channel 1",
                            startTime="2021-12-19T09:04:51Z", url="https://tedyst.ro"),
                ],
            }
        }
    }


def download_recording(server: hikvisionapi.HikvisionServer, args, recordingobj: Recording, original_path):
    filename = None
    try:
        logger = logging.getLogger('hikload')
        if args.mock:
            logger.info("Mocking download of %s" % recordingobj.url)
            time.sleep(1)
            return
        os.chdir(original_path)
        recording_time = datetime.strptime(
            recordingobj.startTime, "%Y-%m-%dT%H:%M:%SZ")
        filepath = ""
        if args.folders:
            create_folder_and_chdir(recordingobj.cname)
            filepath = os.path.join(filepath, recordingobj.cname)
            if args.folders in ["oneperyear", "onepermonth", "oneperday"]:
                create_folder_and_chdir(recording_time.year)
                filepath = os.path.join(filepath, str(recording_time.year))
                if args.folders in ["onepermonth", "oneperday"]:
                    month_folder = f"{recording_time.month:02d}"
                    create_folder_and_chdir(month_folder)
                    filepath = os.path.join(filepath, month_folder)
                    if args.folders in ["oneperday"]:
                        day_folder = f"{recording_time.day:02d}"
                        create_folder_and_chdir(day_folder)
                        filepath = os.path.join(filepath, day_folder)

        # You can choose your own filename, this is just an example
        if args.localtimefilenames:
            date = datetime.strptime(
                recordingobj.startTime, "%Y-%m-%dT%H:%M:%SZ")
            delta = datetime.now(
                timezone.utc).astimezone().tzinfo.utcoffset(datetime.now(timezone.utc).astimezone())
            date = date + delta
            name = re.sub(r'[-T\:Z]', '', date.isoformat())
        elif args.videoname != "":
            name = args.videoname + "_" + re.sub(r'[-T\:Z]', '', recordingobj.startTime)
        else:
            name = re.sub(r'[-T\:Z]', '', recordingobj.startTime)

        if not args.skipdownload:
            if args.photos:
                photo_download_from_channel(
                    server, args, recordingobj.url, name, recordingobj.cid)
            else:
                video_download_from_channel(
                    server, args, recordingobj.url, name, recordingobj.cid)
        else:
            logging.debug("Skipping download of %s" % recordingobj.url)

        if args.folders:
            os.chdir(original_path)
        
        if args.folders:
            filename = "%s.%s" % (name, args.videoformat)
        else:
            filename = "%s-%s.%s" % (name, recordingobj.cid, args.videoformat)
        os.path.join(filepath, filename)
    except TypeError as e:
        logging.error(
            "HikVision dosen't apparently like to return correct XML data...")
        logging.error(repr(e))
        logging.error(recordingobj)

    return filename


def download_recordings(server: hikvisionapi.HikvisionServer, args, downloadDict: dict):
    logger = logging.getLogger('hikload')
    if args.downloads:
        create_folder_and_chdir(args.downloads)
    original_path = os.path.abspath(os.getcwd())

    logger.info("Downloading recordings...")
    with tqdm.tqdm(total=downloadDict["num_videos"]) as progress_bar:
        for cid, channel_metadata in downloadDict["channels"].items():
            try:
                for recordingobj in channel_metadata["recordings"]:
                    filename = download_recording(server, args, recordingobj, original_path)
                    downloadDict["channels"][cid]["filenames"].append(filename)
                    progress_bar.update()
            except TypeError:
                # Value (channel_metadata) is not subscriptible
                pass
    return downloadDict


def process_recordings_with_ffmpeg(args, downloadDict: dict):
    logger = logging.getLogger('hikload')
    # Check for max duration of the video and if it's too long, promt user
    max_duration = timedelta(seconds=0)
    for cid, channel_metadata in downloadDict["channels"].items():
        if not isinstance(channel_metadata, dict):
            continue
        max_duration = max (max_duration, channel_metadata["duration"])

    if args.downloads:
        create_folder_and_chdir(args.downloads)

    logger.info("Concatenating videos..")
    with tqdm.tqdm(total=downloadDict["num_channels"]) as progress_bar:
        for cid, channel_metadata in downloadDict["channels"].items():
            if not isinstance(channel_metadata, dict):
                continue

            concat_filename = concat_channel_videos(channel_metadata, cid, args)

            if args.trim:
                cut_filename = cut_video(concat_filename, channel_metadata)
                logger.info("Trimmed video saved as %s" % cut_filename)

            progress_bar.update()


def run(args):
    if args.server == "" or args.server == None:
        raise HikvisionException(
            "No server specified! You need to specify a server with --server")
    if args.username == "" or args.username == None:
        raise HikvisionException(
            "No username specified! You need to specify a username with --username")
    if args.password == "" or args.password == None:
        raise HikvisionException(
            "No password specified! You need to specify a password with --password")

    server = hikvisionapi.HikvisionServer(
        args.server, args.username, args.password, httptimeout=args.httptimeout)

    FORMAT = "[%(name)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger('hikload')
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    with logging_redirect_tqdm():
        server.test_connection()
        if args.mock:
            downloadDict = search_for_recordings_mock(args)
            args.skipdownload = True
        else:
            downloadDict = search_for_recordings(server, args)

        downloadDict = download_recordings(server, args, downloadDict)

        if args.concat:
            process_recordings_with_ffmpeg(args, downloadDict)       

