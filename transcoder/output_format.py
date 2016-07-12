#
# output_format.py
#
# function get_output_format(job)
# Creates list of ffmpeg params (as list of tuples) for given job
#

from nxtools import *
from .probe import *

__all__ = ["get_output_format"]

def get_output_format(job):
    settings = job.parent.settings

    #
    # ffprobe
    #

    logging.debug("Probing {}".format(job.base_name))
    meta = probe(job.source_path)
    if not meta:
        return False

    #
    # filter chain
    #

    filter_array = []
    if settings["logo_4_3"] and settings["logo_16_9"]:
        logo_path = {
                "16:9" : settings["logo_16_9"],
                "4:3" : settings["logo_4_3"]
            }[meta.get("guess_aspect_ratio","16:9")]
        logging.debug("Adding logo {}".format(logo_path))
        filter_array.append(
                "movie={}[watermark];[watermark]scale={}:{}[watermark]".format(
                    logo_path,
                    settings["width"],
                    settings["height"]
                    )
                )

    if settings["deinterlace"]:
        filter_array.append("[in]yadif=0:-1:0[out]")
    else:
        filter_array.append("[in]null[out]")

    if False:
        #TODO: handle True, False, "auto"
        filter_array.append("[out]colorlevels=rimin=0.0625:gimin=0.0625:bimin=0.0625:rimax=0.9375:gimax=0.9375:bimax=0.9375[out]")

    filter_array.append("[out]scale={}:{}[out]".format(settings["width"], settings["height"]))
    if settings["logo_4_3"] and settings["logo_16_9"]:
        filter_array.append("[out][watermark]overlay=0:0[out]")

    if settings["tc_show"]:
        #x = (w-tw)/2: y=h-(3*lh)
        x="(w*0.1)"
        y="h-(h*0.05)-lh"

        filter_array.append("[out]drawtext=fontfile={font}: timecode='{tc}': r={r}: \
                x={x}: y={y}: fontcolor=white: fontsize={font_size}: box=1: boxborderw=8: boxcolor=0x00000000@1[out]".format(
                    tc=meta["timecode"].replace(":","\:"),
                    r=meta["frame_rate"],
                    font=settings["tc_font"],
                    font_size=settings["tc_size"],
                    x=x,
                    y=y
                    )
                )

    filters = ";".join(filter_array)

    #
    # output format
    #

    result = [
            ["filter:v", filters],
            ["r", settings["frame_rate"]],
            ["pix_fmt", settings["pixel_format"]],
            ["aspect", meta["guess_aspect_ratio"]]
        ]

    result.extend([
            ["c:v", settings["video_codec"]],
            ["b:v", settings["video_bitrate"]],
            ["video_track_timescale", settings["frame_rate"]]
        ])

    #TODO: Add gop size
    if settings["video_codec"] == "libx264":
        result.extend([
                ["profile:v" , settings["x264_profile"]],
                ["level", settings["x264_level"]],
                ["preset:v", settings["x264_preset"]]
            ])

    atracks = meta["audio_tracks"]
    audio_layout_map = ""
    for stream in atracks:
        audio_layout_map += stream["codec_type"].upper()[0]
        if stream["codec_type"] == "audio":
            audio_layout_map += str(stream["channels"])
        audio_layout_map += " "
    audio_layout_map = audio_layout_map.strip()

    logging.debug("Audio layout map is: {}".format(audio_layout_map))
    if atracks:
        if atracks[0]["channels"] > 1:
            # Take first two channels of the first track
            result.extend([
                    ["map", "0:{}".format(meta["video_index"])],
                    ["map", "0:{}".format(atracks[0].id)],
                    ["filter:a", "pan=stereo:c0=c0:c1=c1"]
                ])

        elif len(meta["audio_tracks"]) > 1:
            # merge first two (mono) tracks
            result.extend([
                    ["filter_complex", "[0:{}][0:{}]amerge=inputs=2[aout]".format(atracks[0].id, atracks[1].id)],
                    ["map", "0:{}".format(meta["video_index"])],
                    ["map", "[aout]"],
                ])

        else:
            # ONLY one mono track present (asi). keep original layout layout
            logging.warning("Unexpected audio layout {} in file {}".format(row, job.base_name ))

        result.extend([
                ["c:a", "libfdk_aac"],
                ["b:a", settings["audio_bitrate"]],
                ["ar", settings["audio_sample_rate"]]
            ])
    else:
        # no audio track in source file
        result.append(["an"])

    # clear original metadata
    result.append(["movflags", "frag_keyframe+empty_moov"])
    result.append(["map_metadata", "-1"])
    return result
