import hikload.hikvisionapi as hikvisionapi
import uuid
import logging

logger = logging.getLogger('hikload')


class _search():
    def __init__(self, parent):
        self.parent = parent.parent

    def profile(self):
        """
        The ContentMgmt/search/profile schema is used to define the types of searches a RaCM device
        supports. A device with a search profile of ‘Basic’ only performs searches with one timespan per search
        request (see “/ISAPI/ContentMgmt/search”). Devices that support the ‘Full’ search profile must outline
        their parameter limits, as described in the following schema
        """
        return hikvisionapi.getXML(self.parent, "ContentMgmt/search/profile")

    def getRaw(self, data: dict):
        return hikvisionapi.postXML(self.parent, "ContentMgmt/search", data=data)

    def get(self, data: dict):
        # TODO: This is a hack, since the server likes to return a limited number of results
        result = hikvisionapi.postXML(
            self.parent, "ContentMgmt/search", data=data)
        if result['CMSearchResult']['responseStatusStrg'] == "NO MATCHES":
            return result
        original = result
        while result['CMSearchResult']['responseStatusStrg'] == "MORE":
            if len(result['CMSearchResult']['matchList']) > 0:
                logger.debug("Using %s as starttime and %s as endtime for the new search" % (
                    result['CMSearchResult']['matchList']['searchMatchItem'][-1]
                          ['timeSpan']['startTime'],
                    data['CMSearchDescription']
                    ['timeSpanList']['timeSpan']['endTime']
                ))
                # Create another UUID for the search
                data['CMSearchDescription']['searchID'] = str(uuid.uuid4())
                # Set the new search's start time to the end time of the last
                data['CMSearchDescription']['timeSpanList']['timeSpan']['startTime'] = (
                    result['CMSearchResult']['matchList']['searchMatchItem'][-1]
                    ['timeSpan']['startTime']
                )
                result = hikvisionapi.postXML(
                    self.parent, "ContentMgmt/search", data=data)
                for i in result['CMSearchResult']['matchList']['searchMatchItem']:
                    original['CMSearchResult']['matchList']['searchMatchItem'].append(
                        i)
            else:
                logger.error(
                    "Server did not return any results, but says that there are MORE?")
        original['CMSearchResult']['numOfMatches'] = len(
            original['CMSearchResult']['matchList']['searchMatchItem'])
        original['CMSearchResult']['responseStatusStrg'] = "OK"
        return original

    def download(self, data: dict):
        result = hikvisionapi.getXML(self.parent, "ContentMgmt/download",
                                     data=data, rawResponse=True)
        return result

    def get_download_capabilities(self):
        result = hikvisionapi.getXML(
            self.parent, "ContentMgmt/download/capabilities")
        return result

    def downloadURI(self, playbackURI):
        dictdata = hikvisionapi.xml2dict(b"""<downloadRequest version="1.0"
            xmlns="http://www.isapi.org/ver20/XMLSchema">
        <playbackURI></playbackURI>
        </downloadRequest>
        """)
        dictdata['downloadRequest']['playbackURI'] = playbackURI
        return self.download(dictdata)

    def getPastRecordingsForID(self, ChannelID, startTime="", endTime=""):
        dictdata = hikvisionapi.xml2dict(b"""<CMSearchDescription version="1.0"
            xmlns="http://www.isapi.org/ver20/XMLSchema">
            <searchID></searchID>
            <trackIDList>
                <trackID></trackID>
            </trackIDList>
            <timeSpanList>
                <timeSpan>
                    <startTime></startTime>
                    <endTime></endTime>
                </timeSpan>
            </timeSpanList>
            <maxResults>64</maxResults>
            </CMSearchDescription>""")
        dictdata['CMSearchDescription']['searchID'] = str(uuid.uuid4())
        dictdata['CMSearchDescription']['trackIDList']['trackID'] = str(
            ChannelID)
        (dictdata['CMSearchDescription']['timeSpanList']
         ['timeSpan']['startTime']) = str(startTime)
        (dictdata['CMSearchDescription']['timeSpanList']
         ['timeSpan']['endTime']) = str(endTime)
        return self.get(dictdata)

    def getAllRecordingsForID(self, ChannelID):
        dictdata = hikvisionapi.xml2dict(b"""<CMSearchDescription version="1.0"
            xmlns="http://www.isapi.org/ver20/XMLSchema">
            <searchID></searchID>
            <trackIDList>
            <trackID></trackID>
            </trackIDList>
            <timeSpanList>
                <timeSpan>
                    <startTime>2000-01-01T00:00:00Z</startTime>
                    <endTime>2037-10-10T23:59:59Z</endTime>
                </timeSpan>
            </timeSpanList>
            <maxResults>64</maxResults>
            </CMSearchDescription>""")
        dictdata['CMSearchDescription']['searchID'] = str(uuid.uuid4())
        dictdata['CMSearchDescription']['trackIDList']['trackID'] = str(
            ChannelID)
        return self.get(dictdata)


class _ContentMgmt():
    def __init__(self, parent):
        self.parent = parent
        self.search = _search(self)
