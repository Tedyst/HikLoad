import os
import xml.dom.minidom as minidom
from xml.etree import ElementTree
import xmltodict
import ffmpeg
from hikload.config import CONFIG
import re
from hikload.classes import *
import logging


FILE_NAME_FRAMES = "img_{response.camera}_{response.starttime}_%06d.jpg"
FILE_NAME_NORMAL = "{response.camera}_{response.name}.mkv"


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


def downloadRTSP(response: ResponseObject, skipSeconds: int = 0):
    """Downloads an RTSP livestream to a specific location.
    name, camera are optional
    """
    filename = FILE_NAME_NORMAL.format(response=response)
    if not validResponse(response):
        raise InvalidResponseException
    # If the video exists, return
    if os.path.isfile(filename):
        return
    logging.info("Trying to download from the url %s" % response.url)
    stream = ffmpeg.output(ffmpeg.input(response.url),
                           filename,
                           vcodec="copy",
                           acodec="copy",
                           reorder_queue_size=0,
                           timeout=10,
                           stimeout=10,
                           rtsp_flags="listen",
                           rtsp_transport="tcp",
                           ss=skipSeconds
                           )
    if getConfig("debug"):
        return ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
    return ffmpeg.run(stream, capture_stdout=False, capture_stderr=False)


def downloadRTSPOnlyFrames(response: ResponseObject, modulo: int, skipSeconds: int = 0):
    """Downloads an image for every `modulo` frame from a response.
    """
    filename = FILE_NAME_FRAMES.format(response=response)
    if not validResponse(response):
        raise InvalidResponseException
    # If the first frame exists, return
    if os.path.isfile(filename % 1):
        return
    logging.info("Trying to download from %s" % response.url)
    stream = ffmpeg.output(ffmpeg.input(response.url),
                           filename,
                           reorder_queue_size=100,
                           timeout=1, stimeout=1,
                           rtsp_flags="listen",
                           rtsp_transport="tcp",
                           vf="select=not(mod(n\,%s))" % (modulo),
                           vsync="vfr",
                           ss=skipSeconds
                           )
    if getConfig("debug"):
        return ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
    return ffmpeg.run(stream, capture_stdout=False, capture_stderr=False)


def chdir(newpath):
    """Changes current directory to downloadPath"""
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    os.chdir(newpath)


def getList(response):
    """Returns a list of ResponseObject from a response of the DVR/NVR"""
    obj = xmltodict.parse(getXmlString(response))
    ret = []
    # Good luck trying to fix this if this ever breaks
    if "ns0:CMSearchResult" not in obj:
        logging.error("Got the response: %s" % obj)
        return []
    searchResult = obj["ns0:CMSearchResult"]
    if searchResult["ns0:numOfMatches"] == "0":
        logging.info("No videos found for this camera")
        return []
    vid = searchResult["ns0:matchList"]["ns0:searchMatchItem"]
    for i in vid:
        url = i["ns0:mediaSegmentDescriptor"]["ns0:playbackURI"].replace(
            "rtsp://", "rtsp://" + getConfig('user') + ":" + getConfig(
                "password") + "@", 1)

        response = ResponseObject(
            url.split('/')[5],
            url.split('?')[1].split('&')[2].replace("name=", ""),
            url.split("starttime=")[1].split("&")[0],
            url.split("endtime=")[1].split("&")[0],
        )

        # set the url and replace the ip returned by the server by the one configured
        # in case of ip forwarding
        response.url = re.sub("\\d+\.\\d+\.\\d+\.\\d+",
                              getConfig("server"), url, 1)

        ret.append(response)
    return ret


def baseXML(starttime: str, endtime: str, trackid: str) -> ElementTree:
    return ElementTree.fromstring("""<?xml version="1.0" encoding="utf-8"?>
    <CMSearchDescription>
        <searchID>C85AB0C7-F380-0001-E33B-A030EEB671F0</searchID>
        <trackList>
            <trackID>{trackid}</trackID>
        </trackList>
        <timeSpanList>
            <timeSpan>
                <startTime>{starttime}</startTime>
                <endTime>{endtime}</endTime>
            </timeSpan>
        </timeSpanList>
        <maxResults>40</maxResults>
        <searchResultPostion>0</searchResultPostion>
        <metadataList>
            <metadataDescriptor>//recordType.meta.std-cgi.com</metadataDescriptor>
        </metadataList>
    </CMSearchDescription>""".format(starttime=starttime, endtime=endtime, trackid=trackid))


def validResponse(response: ResponseObject):
    if response.url is None:
        return False
    if response.camera is None:
        return False
    if response.name is None:
        return False
    return True
