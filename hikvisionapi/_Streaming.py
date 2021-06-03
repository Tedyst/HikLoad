import hikvisionapi


class _Streaming():
    def __init__(self, parent):
        self.parent = parent

    def status(self):
        """
        It is used to get a device streaming status
        """
        return hikvisionapi.getXML(self.parent, "Streaming/status")

    def getChannels(self):
        """
        It is used to get the properties of streaming channels for the device
        """
        return hikvisionapi.getXML(self.parent, "Streaming/channels")

    def putChannels(self, StreamingChannelList: str):
        """
        It is used to update the properties of streaming channels for the device.
        A StreamingChannelList can be obtained from getChannels()
        """
        return hikvisionapi.putXML(self.parent, "Streaming/channels",
                                   xmldata=StreamingChannelList)

    def postChannels(self, StreamingChannelList: str):
        """
        It is used to add a streaming channel for the device.
        A StreamingChannel can be obtained from getChannels()
        """
        return hikvisionapi.postXML(self.parent, "Streaming/channels",
                                    xmldata=StreamingChannelList)

    def deleteChannels(self, StreamingChannelList):
        """
        It is used to add a streaming channel for the device.
        A StreamingChannel can be obtained from getChannels()
        """
        return hikvisionapi.deleteXMLRaw(self.parent, "Streaming/channels")

    def getChannelByID(self, ChannelID):
        """
        It is used to get the properties of a particular streaming channel for the
        device
        """
        return hikvisionapi.getXML(self.parent, "Streaming/channels/%s" % ChannelID)

    def putChannelByID(self, ChannelID, StreamingChannel):
        """
        It is used to get the properties of a particular streaming channel for the
        device
        """
        return hikvisionapi.putXML(self.parent, "Streaming/channels/%s" % ChannelID,
                                   StreamingChannel)

    def deleteChannelByID(self, ChannelID):
        """
        It is used to get the properties of a particular streaming channel for the
        device
        """
        return hikvisionapi.deleteXML(self.parent, "Streaming/channels/" + ChannelID)

    def getChannelRTSP(self, ChannelID):
        """
        Returns the RTSP link for a channel
        """
        channel = self.getChannelByID(ChannelID)
        data = hikvisionapi.xml2dict(channel)
        control = data['StreamingChannel']['Transport']['ControlProtocolList']
        if control['ControlProtocol']['streamingTransport'] != "RTSP":
            return ""
        return "rtsp://%s:554/Streaming/channels/%s" % (self.parent.address(protocol=False, credentials=True), ChannelID)

    def getPastRecordingsForID(self, ChannelID, startTime="", endTime=""):
        dictdata = hikvisionapi.xml2dict(b"""<CMSearchDescription version="1.0"
            xmlns="http://www.isapi.org/ver20/XMLSchema">
            <searchID>{812F04E0-4089-11A3-9A0C-0305E82C2906}</searchID>
            <trackIDList>
            <trackID>9</trackID>
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
        return hikvisionapi.getXML(self.parent, "ContentMgmt/search", data=dictdata)
