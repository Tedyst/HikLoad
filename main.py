import logging
from xml.etree import ElementTree
import requests
from requests.api import get
from hikload.util import chdir, downloadRTSPOnlyFrames, getList, getXmlString, downloadRTSP, getConfig, baseXML
from datetime import datetime


def main():
    headers = {'Content-Type': 'application/xml'}
    serverpath = "http://" + getConfig("server") + "/ISAPI/ContentMgmt/search"

    if getConfig("debug"):
        logging.basicConfig(level=logging.DEBUG)

    if getConfig("downloadPath"):
        chdir(getConfig("downloadPath"))

    # TODO: Specify time in config file
    # For now we just download the files from today
    starttime = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0, day=1).isoformat() + "Z"
    endtime = datetime.now().replace(
        hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"

    # This downloads the files from every camera
    for i in getConfig("cameras"):
        logging.info("Trying to download from camera %s" % i)

        search = baseXML(starttime, endtime, i)

        response = requests.post(serverpath, getXmlString(search), headers,
                                 auth=requests.auth.HTTPBasicAuth(getConfig("user"), getConfig("password")))

        logging.debug(response.text)

        response = ElementTree.fromstring(response.text)

        skipSeconds = int(getConfig("skipFirstSeconds"))

        for stream in getList(response):
            if getConfig("skipFrames") == None or getConfig("skipFrames") == 0:
                downloadRTSP(stream, skipSeconds)
            else:
                downloadRTSPOnlyFrames(
                    stream, getConfig("skipFrames"), skipSeconds)


if __name__ == "__main__":
    main()
