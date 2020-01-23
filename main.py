from xml.etree import ElementTree
import requests
from hikload.util import chdir, getList, getXmlString, downloadRTSP, getConfig, baseXML
import datetime


def main():
    # This is needed because Hikvision only uses XML
    search = baseXML()
    headers = {'Content-Type': 'application/xml'}
    serverpath = "http://" + getConfig("server") + "/ISAPI/ContentMgmt/search"

    chdir(getConfig("downloadPath"))

    # TODO: Specify time in config file
    # For now we just download the files from today
    starttime = datetime.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    endtime = datetime.datetime.now().replace(
        hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"

    # This downloads the files from every camera
    for i in getConfig("cameras"):
        print("Trying to download from camera " + i)

        # This is the <trackID>
        search[1][0].text = i
        # These two are the <startTime> and <endTime>
        search[2][0][0].text = starttime
        search[2][0][1].text = endtime

        response = requests.post(serverpath, getXmlString(search), headers,
                                 auth=requests.auth.HTTPBasicAuth(getConfig("user"), getConfig("password")))

        if(getConfig("debug")):
            print(response.text)
            
        response = ElementTree.fromstring(response.text)

        for stream in getList(response):
            downloadRTSP(stream)


if __name__ == "__main__":
    main()
