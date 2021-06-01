import hikvisionapi
import hikvisionapi.System
import hikvisionapi.Streaming as Streaming
from hikvisionapi.RTSPutils import downloadRTSPOnlyFrames
from datetime import datetime
import re
import os
import logging

server = hikvisionapi.HikvisionServer("192.168.10.239", "admin", "cosica.123")
# Download a frame for every 10 frames in the video
modulo = 10

channelList = hikvisionapi.Streaming.getChannels(server)

logging.getLogger().setLevel(logging.INFO)

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
        starttime = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
        endtime = datetime.now().replace(
            hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"

        recordings = Streaming.getPastRecordingsForID(server, cid, starttime,
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
            name = re.sub(r'[-T\:Z]', '', recording['timeSpan']['startTime'])
            name = name + "_%06d.mkv"

            logging.info("Started downloading %s" % name)
            downloadRTSPOnlyFrames(url=url,
                                   videoName=name,
                                   modulo=modulo,
                                   debug=True,
                                   force=True)
            logging.info("Finished downloading %s" % name)
