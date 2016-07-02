from nxtools import *


def get_output_format(job):
    settings = job.parent.settings

    meta = ffprobe(job.source_path)
    duration = meta["format"].get("duration",0)
    logging.debug("source duration is {}".format(duration))
    #TODO: error handling

    #TODO: get audio tracks

    #TODO: create audio mapping

    #TODO: read source TC

    filter_array = []
    if settings.get("logo", False):
        filter_array.append(
                "movie={}[watermark];[watermark]scale={}:{}[watermark]".format(
                    settings["logo"],
                    settings["width"],
                    settings["height"]
                    )
                )
    #TODO: Deinterlace
    filter_array.append("[in]null[out]")
    if settings.get("expand_levels"):
        filter_array.append("[out]colorlevels=rimin=0.0625:gimin=0.0625:bimin=0.0625:rimax=0.9375:gimax=0.9375:bimax=0.9375[out]")
    filter_array.append("[out]scale={}:{}[out]".format(settings["width"], settings["height"]))
    if settings.get("logo", False):
        filter_array.append("[out][watermark]overlay=0:0[out]")

    #TODO: timecode burn in

    filters = ";".join(filter_array)

    result = [
            ["filter:v", filters],
            ["r", settings["frame_rate"]],
            ["pix_fmt", settings["pixel_format"]]
        ]

    result.extend([
            ["c:v", settings["video_codec"]],
            ["b:v", settings["video_bitrate"]],
            ["video_track_timescale", settings["frame_rate"]]
        ])

    if settings["video_codec"] == "libx264":
        result.extend([
                ["profile:v" , settings["x264_profile"]],
                ["level", settings["x264_level"]],
                ["preset:v", settings["x264_preset"]]
            ])

    #TODO: if container == mpeg, append buf_size

    result.extend([
            ["c:a", "libfdk_aac"],
            ["b:a", settings["audio_bitrate"]],
            ["ar", settings["audio_sample_rate"]]
        ])

    return result
