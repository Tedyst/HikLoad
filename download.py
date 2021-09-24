import collections
import hikvisionapi
from datetime import datetime, timedelta, timezone
import re
import os
import logging
import argparse
import ffmpeg


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download Recordings from a HikVision server, from a range interval')
    parser.add_argument('server', type=str,
                        help='the hikvision server\'s address')
    parser.add_argument('username', type=str,
                        help='the username')
    parser.add_argument('password', type=str,
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
    parser.add_argument('--videoformat', dest="videoformat", default="mp4",
                        help='specify video format (default: mp4)')
    parser.add_argument('--downloads', dest="downloads", default="Downloads",
                        help='the downloads folder (default: "Downloads")')
    parser.add_argument('--frames', dest="frames", type=int,
                        help='save a frame for every X frames in the video (default: false)')
    parser.add_argument('--force', dest="force", type=int,
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
    args = parser.parse_args()
    return args


def create_folder_and_chdir(dir):
    path = str(dir)
    if not os.path.exists(path):
        os.makedirs(os.path.normpath(path))
        logging.debug("Created folder %s" % path)
    else:
        logging.debug("Folder %s already exists" % path)
    os.chdir(os.path.normpath(path))


def photo_download_from_channel(args, server, url, filename, cid):
    name = "%s.jpeg" % filename
    logging.info("Started downloading %s" % name)
    logging.debug(
        "Files to download: (url: %r, name: %r)" % (url, name))
    r = server.ContentMgmt.search.downloadURI(url)
    open(name, 'wb').write(r.content)
    logging.info("Finished downloading %s" % name)


def video_download_from_channel(args, server, url, filename, cid):
    if args.folders:
        name = "%s.%s" % (filename, args.videoformat)
    else:
        name = "%s-%s.%s" % (filename, cid, args.videoformat)
    logging.info("Started downloading %s" % name)
    logging.debug(
        "Files to download: (url: %r, name: %r)" % (url, name))
    if args.frames:
        try:
            url = url.replace(server.host, server.address(
                protocol=False, credentials=True))
            hikvisionapi.downloadRTSPOnlyFrames(
                url, name, debug=args.debug, force=args.force, modulo=args.frames, skipSeconds=args.skipseconds, seconds=args.seconds)
        except ffmpeg.Error:
            logging.error(
                "Could not download %s. Try to remove --frames." % name)
    if args.ffmpeg:
        try:
            url = url.replace(server.host, server.address(
                protocol=False, credentials=True))
            hikvisionapi.downloadRTSP(
                url, name, debug=args.debug, force=args.force, skipSeconds=args.skipseconds, seconds=args.seconds)
        except ffmpeg.Error:
            logging.error(
                "Could not download %s. Try to remove --fmpeg." % name)
    else:
        if args.folders:
            temporaryname = "%s.mp4" % filename
        else:
            temporaryname = "%s-%s.mp4" % (filename, cid)
        r = server.ContentMgmt.search.downloadURI(url)
        open(temporaryname, 'wb').write(r.content)
        try:
            hikvisionapi.processSavedVideo(
                temporaryname, debug=args.debug, skipSeconds=args.skipseconds, seconds=args.seconds,
                fileFormat=args.videoformat, forceTranscode=args.forcetranscoding)
        except ffmpeg.Error:
            logging.error(
                "Could not transcode %s. Try to remove --forcetranscoding." % name)
    logging.info("Finished downloading %s" % name)


def main(args):
    server = hikvisionapi.HikvisionServer(
        args.server, args.username, args.password)

    FORMAT = "[%(name)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT)
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    channelList = server.Streaming.getChannels()

    if args.downloads:
        create_folder_and_chdir(args.downloads)
    original_path = os.path.abspath(os.getcwd())

    logging.debug("ChannelList: %s" % channelList)
    channelids = []
    channels = []
    if args.photos:
        for channel in channelList['StreamingChannelList']['StreamingChannel']:
            if (int(channel['id']) % 10 == 1) and (args.cameras is None or channel['id'] in args.cameras):
                # Force looking at the hidden 103 channel for the photos
                channel['id'] = str(int(channel['id'])+2)
                channelids.append(channel['id'])
                channels.append(channel)
        logging.info("Found channels %s" % channelids)
    else:
        for channel in channelList['StreamingChannelList']['StreamingChannel']:
            if (int(channel['id']) % 10 == 1) and (args.cameras is None or channel['id'] in args.cameras):
                channelids.append(channel['id'])
                channels.append(channel)
        logging.info("Found channels %s" % channelids)

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
                recordings = server.ContentMgmt.search.getPastRecordingsForID(
                    cid, starttime.isoformat() + "Z", endtime.isoformat() + "Z")
                logging.info("Found %s recordings for channel %s" %
                             (recordings['CMSearchResult']['numOfMatches'], cid))
        except hikvisionapi.classes.HikvisionException:
            logging.error("Could not get recordings for channel %s" % cid)
            continue

        # If we didn't have any recordings for this channel, skip it
        if int(recordings['CMSearchResult']['numOfMatches']) == 0:
            if args.folders:
                os.chdir(original_path)
            continue

        # This loops from every recording
        recordinglist = recordings['CMSearchResult']['matchList']
        for recording in recordinglist['searchMatchItem']:
            try:
                logging.debug("Found recording type %s on channel %s" % (
                    recording['mediaSegmentDescriptor']['contentType'], cid
                ))
                if not args.photos and recording['mediaSegmentDescriptor']['contentType'] != 'video':
                    # This recording is not a video, skip it
                    continue
                url = recording['mediaSegmentDescriptor']['playbackURI']
                recording_time = datetime.strptime(
                    recording['timeSpan']['startTime'], "%Y-%m-%dT%H:%M:%SZ")
                if args.folders:
                    create_folder_and_chdir(cname)
                    if args.folders in ["oneperyear", "onepermonth", "oneperday"]:
                        create_folder_and_chdir(recording_time.year)
                        if args.folders in ["onepermonth", "oneperday"]:
                            create_folder_and_chdir(recording_time.month)
                            if args.folders in ["oneperday"]:
                                create_folder_and_chdir(recording_time.day)

                # You can choose your own filename, this is just an example
                if args.localtimefilenames:
                    date = datetime.strptime(
                        recording['timeSpan']['startTime'], "%Y-%m-%dT%H:%M:%SZ")
                    delta = datetime.now(
                        timezone.utc).astimezone().tzinfo.utcoffset(datetime.now(timezone.utc).astimezone())
                    date = date + delta
                    name = re.sub(r'[-T\:Z]', '', date.isoformat())
                else:
                    name = re.sub(r'[-T\:Z]', '', recording['timeSpan']
                                  ['startTime'])

                if not args.skipdownload:
                    if args.photos:
                        photo_download_from_channel(
                            args, server, url, name, cid)
                    else:
                        video_download_from_channel(
                            args, server, url, name, cid)

                if args.folders:
                    os.chdir(original_path)
            except TypeError as e:
                logging.error(
                    "HikVision dosen't apparently like to return correct XML data...")
                logging.error(repr(e))
                logging.error(recording)


if __name__ == '__main__':
    args = parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        logging.info("Exited by user")
        exit(0)
