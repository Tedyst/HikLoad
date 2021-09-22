import collections
import hikvisionapi
from datetime import datetime, timedelta, timezone
from hikvisionapi.utils import create_folder_and_chdir
import re
import os
import logging
import argparse


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
    parser.add_argument('--videoformat', dest="videoformat", default="mkv",
                        help='specify video format (default: mkv)')
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
    args = parser.parse_args()
    return args


def main(args):
    server = hikvisionapi.HikvisionServer(
        args.server, args.username, args.password)

    channelList = server.Streaming.getChannels()
    FORMAT = "[%(name)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT)
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    logging.debug("ContentMgmt profile: %s" %
                  server.ContentMgmt.search.profile())

    if args.downloads:
        create_folder_and_chdir(args.downloads)
    original_path = os.path.abspath(os.getcwd())

    logging.debug(channelList)
    channels = []
    for channel in channelList['StreamingChannelList']['StreamingChannel']:
        if (int(channel['id']) % 10 == 1) and (args.cameras is None or channel['id'] in args.cameras):
            channels.append(channel['id'])
    logging.info("Found channels %s" % channels)

    for channel in channelList['StreamingChannelList']['StreamingChannel']:
        cname = channel['channelName']
        cid = channel['id']
        # The channel is a primary channel and is allowed to be used for recording
        if (int(cid) % 10 == 1) and (args.cameras is None or channel['id'] in args.cameras):
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

            if args.allrecordings:
                recordings = server.ContentMgmt.search.getAllRecordingsForID(
                    cid)
                logging.info("There are %s recordings in total for channel %s" %
                             (server.ContentMgmt.search.getAllRecordingsForID(cid)['CMSearchResult']['numOfMatches'], cid))
            else:
                recordings = server.ContentMgmt.search.getPastRecordingsForID(
                    cid, starttime.isoformat() + "Z", endtime.isoformat() + "Z")
                logging.info("Found %s recordings for channel %s" %
                             (recordings['CMSearchResult']['numOfMatches'], cid))

            # If we didn't have any recordings for this channel, skip it
            if int(recordings['CMSearchResult']['numOfMatches']) == 0:
                if args.folders:
                    os.chdir(original_path)
                continue

            # This loops from every recording
            recordinglist = recordings['CMSearchResult']['matchList']
            for recording in recordinglist['searchMatchItem']:
                try:
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
                    # This line appends the camera id and the extension to the filename
                    if args.folders:
                        name = "%s.%s" % (name, args.videoformat)
                    else:
                        name = "%s-%s.%s" % (name, cid, args.videoformat)

                    if not args.skipdownload:
                        logging.info("Started downloading %s" % name)
                        logging.debug(
                            "Files to download: (url: %r, name: %r)" % (url, name))
                        if args.frames:
                            url = url.replace(server.host, server.address(
                                protocol=False, credentials=True))
                            hikvisionapi.downloadRTSPOnlyFrames(
                                url, name, debug=args.debug, force=args.force, modulo=args.frames, skipSeconds=args.skipseconds, seconds=args.seconds)
                        if args.ffmpeg:
                            try:
                                url = url.replace(server.host, server.address(
                                    protocol=False, credentials=True))
                                hikvisionapi.downloadRTSP(
                                    url, name, debug=args.debug, force=args.force, skipSeconds=args.skipseconds, seconds=args.seconds)
                            except:
                                logging.error(
                                    "Could not download %s. Try to remove --fmpeg." % name)
                        else:
                            r = server.ContentMgmt.search.downloadURI(url)
                            open(name, 'wb').write(r.content)
                            hikvisionapi.processSavedVideo(
                                name, debug=args.debug, skipSeconds=args.skipseconds, seconds=args.seconds, fileFormat=args.videoformat)
                        logging.info("Finished downloading %s" % name)
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
