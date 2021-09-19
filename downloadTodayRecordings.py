import hikvisionapi
from datetime import datetime, timezone
import re
import os
import logging

server = hikvisionapi.HikvisionServer("192.168.10.239", "admin", "password")

channelList = server.Streaming.getChannels()

logging.getLogger().setLevel(logging.INFO)
# If you want to see the debug messages, you can uncomment the following line.
# logging.getLogger().setLevel(logging.DEBUG)

if not os.path.exists("Downloads"):
    logging.debug("Created folder Downloads")
    os.makedirs("Downloads")
else:
    logging.debug("Folder already exists")
os.chdir("Downloads")

logging.debug(channelList)

for channel in channelList['StreamingChannelList']['StreamingChannel']:
    cid = channel['id']
    # The channel is a primary channel
    if (int(cid) % 10 == 1):
        # This makes sure that we only get today's recordings
        starttime = datetime.now().astimezone().replace(
            hour=0, minute=0, second=0).isoformat()
        endtime = datetime.now().astimezone().replace(
            hour=23, minute=59, second=59).isoformat()
        logging.debug("Using %s and %s as start and end times" %
                      (starttime, endtime))

        recordings = server.Streaming.getPastRecordingsForID(cid, starttime,
                                                             endtime)

        # If we didn't have any recordings for this channel today
        if int(recordings['CMSearchResult']['numOfMatches']) == 0:
            logging.info("Could not find any videos for camera %s" % cid)
            continue

        # This loops from every recording
        recordinglist = recordings['CMSearchResult']['matchList']
        for recording in recordinglist['searchMatchItem']:
            url = recording['mediaSegmentDescriptor']['playbackURI']
            url = url.replace(server.host, server.address(
                protocol=False, credentials=True))
            # You can choose your own filename, this is just an example
            # This line strips the timezone from the time retuned by the server
            name = re.sub(r'[-T\:Z]', '', recording['timeSpan']
                          ['startTime'])
            # This line appends the camera id and the extension to the filename
            name = "%s-%s.mkv" % (name, cid)

            logging.info("Started downloading %s" % name)
            hikvisionapi.downloadRTSP(url,
                                      name,
                                      force=False)
            logging.info("Finished downloading %s" % name)
