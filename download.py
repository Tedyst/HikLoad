import hikvisionapi
from datetime import datetime, timedelta, timezone
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
    parser.add_argument('--folders', action=argparse.BooleanOptionalAction, dest="folders",
                        help='create a separate folder per camera (default: false)')
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
    args = parser.parse_args()
    return args


def main(args):
    server = hikvisionapi.HikvisionServer(
        args.server, args.username, args.password)

    channelList = server.Streaming.getChannels()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    if args.downloads:
        if not os.path.exists(args.downloads):
            os.makedirs(os.path.normpath(args.downloads))
            logging.debug("Created folder %s" % args.downloads)
        else:
            logging.debug("Folder %s already exists" % args.downloads)
        os.chdir(os.path.normpath(args.downloads))

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
            else:
                starttime = args.starttime
                endtime = args.endtime

            if not os.path.exists(cname):
                os.makedirs(os.path.normpath(cname))
                logging.debug("Created folder %s" % cname)
            else:
                logging.debug("Folder %s already exists" % cname)
            if args.folders:
                os.chdir(os.path.normpath(cname))
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
                    os.chdir("..")
                continue

            # This loops from every recording
            recordinglist = recordings['CMSearchResult']['matchList']
            for recording in recordinglist['searchMatchItem']:
                url = recording['mediaSegmentDescriptor']['playbackURI']
                url = url.replace(server.host, server.address(
                    protocol=False, credentials=True))
                # You can choose your own filename, this is just an example
                if args.localtimefilenames:
                    date = datetime.strptime(
                        recording['timeSpan']['startTime'], "%Y-%m-%dT%H:%M:%SZ")
                    delta = datetime.now(
                        timezone.utc).astimezone().tzinfo.utcoffset(datetime.now(timezone.utc).astimezone())
                    date = date - delta
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
                    logging.debug("url: %r, name: %r" % (url, name))
                    if args.frames:
                        hikvisionapi.downloadRTSPOnlyFrames(
                            url, name, debug=args.debug, force=args.force, modulo=args.frames, skipSeconds=args.skipseconds, seconds=args.seconds)
                    hikvisionapi.downloadRTSP(
                        url, name, debug=args.debug, force=args.force, skipSeconds=args.skipseconds, seconds=args.seconds)
                    logging.info("Finished downloading %s" % name)
            if args.folders:
                os.chdir("..")


if __name__ == '__main__':
    args = parse_args()
    main(args)
