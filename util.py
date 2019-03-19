import os
import xml.dom.minidom as minidom
from xml.etree import ElementTree
import subprocess
import xmltodict


def getXmlString(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")


def findRec(node, element, result):
    print(node)
    for item in node.getChildren():
        result.append(item)
        findRec(item, element, result)
    return result


def initVlc():
    subprocess.call([
        "killall",
        "-9",
        "vlc"
    ])
    # I'm sorry


def download(url, name, camera):
    print("Trying to download from: " + url)
    name = exists(name, camera)
    if name is None:
        return
    subprocess.call([
        "vlc",
        url,
        "-I dummy",
        "--sout",
        '#transcode{vcodec=mp4v,vb=10240,acodec=mp4a,ab=128}:standard{mux=mp4,dst="' +
        name + '\",access=file}"',
        "--rtsp-tcp",
        "--rtsp-frame-buffer-size",
        "100000000",
        "--sout-mux-caching",
        "500000",
        "--network-caching",
        "100000",
        'vlc://quit'
    ])


def folder():
    newpath = r'./Downloads/'
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    os.chdir(newpath)


def exists(name, camera):
    f = camera + "_" + name + ".mp4"
    if os.path.isfile(f):
        return None
    else:
        return f


def getList(response):
    obj = xmltodict.parse(getXmlString(response))
    for i in obj["ns0:CMSearchResult"]["ns0:matchList"]["ns0:searchMatchItem"]:
        url = i["ns0:mediaSegmentDescriptor"]["ns0:playbackURI"].replace(
            "rtsp://", "rtsp://admin:cosica123@")
        camera = url.split('/')[5]
        arguments = url.split('?')[1]
        name = arguments.split('&')[2]
        name = name.replace("name=", "")
        download(url, name, camera)
