import os
import xml.dom.minidom as minidom
from xml.etree import ElementTree
import xmltodict
import ffmpeg
from .config import CONFIG
import re


class ResponseObject(object):
    def __init__(self):
        self.camera = ""
        self.name = ""
    pass


def getConfig(text):
    try:
        if text == "cameras":
            return os.environ["cameras"].split(' ')
        if os.environ[text]:
            return os.environ[text]
    except Exception:
        pass
    return CONFIG[text]


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
    if(response.name is not None and response.camera is not None):
        if exists(response.name, response.camera) is True:
            return
    else:
        response.name = response.url
        response.camera = ""
    print("Trying to download from: " + response.url)
    stream = ffmpeg.output(ffmpeg.input(response.url),
                           response.camera + response.name + ".mp4",
                           reorder_queue_size="0",
                           timeout=0, stimeout=100,
                           rtsp_flags="listen", rtsp_transport="tcp")
    if config.CONFIG["debug"] == True:
        return ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
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
    """Returns a list of ResponseObject from a response"""
    obj = xmltodict.parse(getXmlString(response))
    ret = []
    try:
        response = ResponseObject()

        # Good luck trying to fix this if this ever breaks
        vid = obj["ns0:CMSearchResult"]["ns0:matchList"]["ns0:searchMatchItem"]
        for i in vid:
            # This adds the user/password after rtsp://
            url = i["ns0:mediaSegmentDescriptor"]["ns0:playbackURI"].replace(
                "rtsp://", "rtsp://" + getConfig('user') + ":" + getConfig(
                    "password") + "@", 1)

            # set the url and replace the ip returned by the server by the one configured
            # in case of ip forwarding
            response.url = re.sub("\\d+\.\\d+\.\\d+\.\\d+", getConfig("server"), url, 1)
            # This gets the camera ID
            response.camera = url.split('/')[5]
            # This gets the "name" argument from the url
            arguments = url.split('?')[1]
            response.name = arguments.split('&')[2].replace("name=", "")

            ret.append(response)
    except Exception:
        raise
    return ret
