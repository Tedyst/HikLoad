import ffmpeg
import os
import logging

from datetime import datetime

logger = logging.getLogger('hikload')

def concat_channel_videos(channel_metadata: dict, cid, args):
    # Create temporary text file as the FFmpeg requires it
    with open("tmp_list.txt", "w") as fl:

        audio_codec = True
        for filename in channel_metadata["filenames"]:
            fl.write("file '{}'\n".format(filename))
            
            # Find out if the file has audio stream 
            has_audio = False
            probe = ffmpeg.probe(filename)
            for stream in probe["streams"]:
                if stream["codec_type"].lower() == "audio":
                    has_audio = True
                    break
            audio_codec = audio_codec and has_audio
    
    if args.videoname != "":
        outname = "{}-{}.{}".format(
            args.videoname,
            cid,
            args.videoformat
        )
    else:
        outname = "{}-{}.{}".format(
            channel_metadata["startTime"].replace("-", "").replace(":", "").replace("Z", "").replace("T", ""),
            cid,
            args.videoformat
        )

    try:
        (
            ffmpeg
            .input('tmp_list.txt', f='concat', safe=0)
            .output(outname, codec='copy')
            .overwrite_output()
            .run()
        )
    except ffmpeg._run.Error:
        # The FFmpeg thrown error while running
        # This could be because of unsupported audio codec (or the audio is missing)
        # Try to cocatenate without the audio stream
        (
            ffmpeg
            .input('tmp_list.txt', f='concat', safe=0)
            .output(outname, vcodec='copy')
            .overwrite_output()
            .run()
        )

    # Clean up after yourself
    os.remove("tmp_list.txt")
    for filename in channel_metadata["filenames"]:
        os.remove(filename)

    logging.debug("Recordings of the channel {} concatenated into video {}".format(cid, outname))
    return outname


def cut_video(video_name, channel_metadata: dict):
    # Cut videos to required duration
    starttime = datetime.strptime(
        channel_metadata["startTime"], "%Y-%m-%dT%H:%M:%SZ")
    minstarttime = datetime.strptime(
        channel_metadata["minStartTime"], "%Y-%m-%dT%H:%M:%SZ")
    trim_start =  starttime - minstarttime 
    
    outname = video_name.replace(".", "_cut.")
    (
        ffmpeg
        .input(video_name, ss=trim_start, t=channel_metadata["duration"])
        .output(outname, codec='copy')
        .overwrite_output()
        .global_args('-loglevel', 'error')
        .run()
    )

    # Clean up after yourself
    os.remove(video_name)

    logging.debug("Video {} trimed into video".format(video_name, outname))
    return outname
