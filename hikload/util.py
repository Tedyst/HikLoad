import os
import xml.dom.minidom as minidom
from xml.etree import ElementTree
import subprocess
import xmltodict
import ffmpeg
from hikload.config import getConfig


class ResponseObject(object):
    def __init__(self):
        self.camera = ""
        self.arguments = ""
        self.name = ""
    pass


def getXmlString(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")


def findRec(node, element, result):
    for item in node.getChildren():
        result.append(item)
        findRec(item, element, result)
    return result


def downloadRTSP(response):
    """Downloads an RTSP livestream to a specific location.
    name, camera are optional
    """
    if(response.name != None and response.camera != None):
        if exists(response.name, response.camera) is True:
            return
    else:
        response.name = response.url
        response.camera = ""
    print("Trying to download from: " + response.url)
    stream = ffmpeg.output(ffmpeg.input(response.url), response.camera + response.name + ".mp4", reorder_queue_size="0",
                           timeout=0, stimeout=100, rtsp_flags="listen", rtsp_transport="tcp")
    return ffmpeg.run(stream, capture_stdout=False, capture_stderr=False)


def chdir(newpath):
    """Changes current directory to downloadPath"""
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    os.chdir(newpath)


def exists(name, camera):
    """Returns true if file already exists"""
    f = camera + name + ".mp4"
    if os.path.isfile(f):
        return True
    return False


def getList(response):
    """Returns a list of [url, name, camera] from a response"""
    obj = xmltodict.parse(getXmlString(response))
    ret = []
    try:
        for i in obj["ns0:CMSearchResult"]["ns0:matchList"]["ns0:searchMatchItem"]:
            url = i["ns0:mediaSegmentDescriptor"]["ns0:playbackURI"].replace(
                "rtsp://", "rtsp://" + getConfig('user') + ":" + getConfig(
                    "password") + "@")
            response = ResponseObject()
            response.camera = url.split('/')[5]
            response.arguments = url.split('?')[1]
            response.name = response.arguments.split('&')[2]
            response.name = response.name.replace("name=", "")
            ret.append(response)
    except:
        print("Could not get a list of videos from the server.")
        print("Maybe the server is down or maybe the user/password is incorrect?")
    return ret
