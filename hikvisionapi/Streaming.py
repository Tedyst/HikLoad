import hikvisionapi.utils as utils


def status(server: utils.HikvisionServer):
    """
    It is used to get a device streaming status
    """
    return utils.getXML(server, "Streaming/status")


def getChannels(server: utils.HikvisionServer):
    """
    It is used to get the properties of streaming channels for the device
    """
    return utils.getXML(server, "Streaming/channels")


def putChannels(server: utils.HikvisionServer, StreamingChannelList):
    """
    It is used to update the properties of streaming channels for the device.
    A StreamingChannelList can be obtained from getChannels()
    """
    return utils.putXML(server, "Streaming/channels",
                        xmldata=StreamingChannelList)


def postChannels(server: utils.HikvisionServer, StreamingChannelList):
    """
    It is used to add a streaming channel for the device.
    A StreamingChannel can be obtained from getChannels()
    """
    return utils.postXML(server, "Streaming/channels",
                         xmldata=StreamingChannelList)


def deleteChannels(server: utils.HikvisionServer, StreamingChannelList):
    """
    It is used to add a streaming channel for the device.
    A StreamingChannel can be obtained from getChannels()
    """
    return utils.deleteXML(server, "Streaming/channels")


def getChannelByID(server: utils.HikvisionServer, ChannelID):
    """
    It is used to get the properties of a particular streaming channel for the
    device
    """
    return utils.getXML(server, "Streaming/channels/" + ChannelID)


def putChannelByID(server: utils.HikvisionServer, ChannelID, StreamingChannel):
    """
    It is used to get the properties of a particular streaming channel for the
    device
    """
    return utils.putXML(server, "Streaming/channels/" + ChannelID,
                        StreamingChannel)


def deleteChannelByID(server: utils.HikvisionServer, ChannelID):
    """
    It is used to get the properties of a particular streaming channel for the
    device
    """
    return utils.deleteXML(server, "Streaming/channels/" + ChannelID)


def getChannelRTSP(server: utils.HikvisionServer, ChannelID):
    """
    Returns the RTSP link for a channel
    """
    channel = getChannelByID(server, ChannelID)
    data = utils.xml2dict(channel)
    control = data['StreamingChannel']['Transport']['ControlProtocolList']
    if control['ControlProtocol']['streamingTransport'] != "RTSP":
        return ""
    # rtsp://admin:cosica.123@192.168.1.239:554/Streaming/channels/801
    return "rtsp://" + server.user + ":" + server.password + \
        "@" + server.host + ":554/Streaming/channels/" + ChannelID


def getPastRecordingsForID(server: utils.HikvisionServer, ChannelID,
                           startTime="", endTime=""):
    dictdata = utils.xml2dict(b"""<CMSearchDescription version="1.0"
        xmlns="http://www.isapi.org/ver20/XMLSchema">
        <searchID>{812F04E0-4089-11A3-9A0C-0305E82C2906}</searchID>
        <trackIDList>
        <trackID>9</trackID>
        <trackID>22</trackID>
        <trackID>43</trackID>
        </trackIDList>
        <timeSpanList>
        <timeSpan>
        <startTime>2013-06-10T12:00:00Z</startTime>
        <endTime>2013-06-10T13:30:00Z</endTime>
        </timeSpan>
        </timeSpanList>
        <contentTypeList>
        <contentType>video</contentType>
        </contentTypeList>
        <maxResults>100</maxResults>
        <metadataList>
        <metadataDescriptor>recordType.meta.hikvision.com/motion</metadataDescriptor>
        </metadataList>
        </CMSearchDescription>""")
    dictdata['CMSearchDescription']['trackIDList']['trackID'] = ChannelID
    (dictdata['CMSearchDescription']['timeSpanList']
             ['timeSpan']['startTime']) = startTime
    (dictdata['CMSearchDescription']['timeSpanList']
             ['timeSpan']['endTime']) = endTime
    return utils.getXML(server, "ContentMgmt/search", data=dictdata)
