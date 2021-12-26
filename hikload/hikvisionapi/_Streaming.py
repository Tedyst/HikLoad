import hikload.hikvisionapi as hikvisionapi
import uuid


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
        return hikvisionapi.deleteXML(self.parent, "Streaming/channels/%s" % ChannelID)

    def getChannelRTSP(self, ChannelID):
        """
        Returns the RTSP link for a channel
        """
        channel = self.getChannelByID(ChannelID)
        data = hikvisionapi.xml2dict(channel)
        control = data['StreamingChannel']['Transport']['ControlProtocolList']
        if control['ControlProtocol']['streamingTransport'] != "RTSP":
            raise hikvisionapi.HikvisionException(
                "Cannot get RTSP link for this ChannelID")
        return "rtsp://%s:554/Streaming/channels/%s" % (self.parent.address(protocol=False, credentials=True), ChannelID)
