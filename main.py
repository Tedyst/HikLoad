from xml.etree import ElementTree
import requests
from util import chdir, getList, getXmlString, downloadRTSP
from config import getConfig
import datetime


def main():
    search = ElementTree.fromstring("""<?xml version="1.0" encoding="utf-8"?>
    <CMSearchDescription>
        <searchID>C85AB0C7-F380-0001-E33B-A030EEB671F0</searchID>
        <trackList>
            <trackID></trackID>
        </trackList>
        <timeSpanList>
            <timeSpan>
                <startTime></startTime>
                <endTime></endTime>
            </timeSpan>
        </timeSpanList>
        <maxResults>40</maxResults>
        <searchResultPostion>0</searchResultPostion>
        <metadataList>
            <metadataDescriptor>//recordType.meta.std-cgi.com</metadataDescriptor>
        </metadataList>
    </CMSearchDescription>""")

    headers = {'Content-Type': 'application/xml'}

    serverpath = "http://" + getConfig('user') + ":" + getConfig(
        "password") + "@" + getConfig("server") + "/ISAPI/ContentMgmt/search"

    chdir(getConfig("downloadPath"))
    starttime = datetime.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    endtime = datetime.datetime.now().replace(
        hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"

    for i in getConfig("cameras"):
        print("Trying to download from camera " + i)
        search[1][0].text = i
        search[2][0][0].text = starttime
        search[2][0][1].text = endtime
        data = getXmlString(search)
        responseXML = requests.post(serverpath, data, headers).text
        response = ElementTree.fromstring(responseXML)
        l = getList(response)
        for i in l:
            downloadRTSP(i[0], i[1], i[2])


if __name__ == "__main__":
    main()
