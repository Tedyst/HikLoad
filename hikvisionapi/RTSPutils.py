from operator import mod
import ffmpeg
import os
import logging


def downloadRTSP(url: str, videoName: str, seconds: int = 9999999, debug: bool = False, force: bool = False, skipSeconds: bool = 0):
    """Downloads an RTSP livestream from url to videoName.

    Parameters:
        url (str): the RTSP link to a stream
        videoName (str): the filename of the downloaded stream
        seconds (int): the maximum number of seconds that should be recorded (default is 999999)
        debug (bool): Enables debug logging (default is False)
        force (bool): Forces saving of file (default is False)
        skipSeconds (int): the number of seconds that should be skipped when downloading (default is 0)
    """
    logging.info("Starting download from: " + url)
    stream = ffmpeg.output(ffmpeg.input(url),
                           videoName,
                           vcodec="copy",
                           acodec="copy",
                           reorder_queue_size=0,
                           timeout=10,
                           stimeout=10,
                           rtsp_flags="listen",
                           rtsp_transport="tcp",
                           ss=skipSeconds
                           )
    if os.path.exists(videoName):
        logging.debug(
            "The file %s exists, should have been downloaded from %s" % (videoName, url))
        if force is False:
            raise Exception("File already exists")
        os.remove(videoName)
    if debug:
        return ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
    return ffmpeg.run(stream, capture_stdout=False, capture_stderr=False)


def downloadRTSPOnlyFrames(url: str, videoName: str, modulo: int, seconds: int = 9999999, debug: bool = False, force: bool = False, skipSeconds: int = 0):
    """Downloads an image for every `modulo` frame from an url and saves it to videoName.

    Parameters:
        url (str): The RTSP link to a stream
        videoName (str): The filename of the downloaded stream
                         should be in the format `{name}_%06d.jpg`
        modulo (int): 
        seconds (int): The maximum number of seconds that should be recorded (default is 9999999)
        debug (bool): Enables debug logging (default is False)
        force (bool): Forces saving of file (default is False)
        skipSeconds (int): The number of seconds that should be skipped when downloading (default is 0)
    """
    if videoName % 1 == videoName % 2:
        raise Exception("videoName cannot be formatted correctly")
    if modulo <= 0:
        raise Exception("modulo is not valid")
    logging.info("Trying to download from %s" % url)
    stream = ffmpeg.output(ffmpeg.input(url),
                           videoName,
                           reorder_queue_size=100,
                           timeout=1, stimeout=1,
                           rtsp_flags="listen",
                           rtsp_transport="tcp",
                           vf="select=not(mod(n\,%s))" % (modulo),
                           vsync="vfr",
                           ss=skipSeconds
                           )
    if debug:
        return ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
    return ffmpeg.run(stream, capture_stdout=False, capture_stderr=False)
