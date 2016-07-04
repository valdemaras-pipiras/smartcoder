from nxtools import *


class AudioTrack():
    def __init__(self, **kwargs):
        self.data = kwargs

    def __getitem__(self, key):
        return self.data["key"]

    @property
    def id(self):
        return self["index"]


def guess_aspect (w, h):
    if 0 in [w, h]:
        return 0
    valid_aspects = [(16, 9), (4, 3), (2.35, 1)]
    ratio = float(w) / float(h)
    return "%s/%s" % min(valid_aspects, key=lambda x:abs((float(x[0])/x[1])-ratio))


def probe(source_path):
    logging.debug("Probing {}".format(get_base_name(friendly_name))
    probe_result = ffprobe(self.input_path)
    meta = {
        "audio_tracks" : []
        }

    format_info = probe_result["format"]

    for stream in probe_result["streams"]:
        if stream["codec_type"] == "video":
            # Frame rate detection
            fps_n, fps_d = [float(e) for e in stream["r_frame_rate"].split("/")]
            meta["frame_rate"] = fps_n / fps_d

            # Aspect ratio detection
            try:
                dar_n, dar_d = [float(e) for e in stream["display_aspect_ratio"].split(":")]
            if not (dar_n and dar_d):
                raise Exception
            except:
                dar_n, dar_d = float(stream["width"]), float(stream["height"])

            meta["aspect_ratio"] = dar_n / dar_d
            meta["guess_aspect_ratio"] = guess_aspect(dar_n, dar_d)

            try:
                source_vdur = float(stream["duration"])
            except:
                source_vdur = False

            meta["video_codec"] = stream["codec_name"]
            meta["pixel_format"] = stream["pix_fmt"]
            meta["width"] = stream["width"]
            meta["height"] = stream["height"]
            meta["video_index"] = stream["index"]

        elif stream["codec_type"] == "audio":
            meta[audio_tracks].append(AudioTrack(**stream))

    meta["duration"] = float(format_info["duration"]) or source_vdur
    meta["num_frames"] = meta["duration"] * meta["frame_rate"]
    return meta


def get_output_format(job):
    settings = job.parent.settings

    #
    # ffprobe
    #

    meta = probe(job.source_path)

    #TODO: error handling

    #TODO: create audio mapping

    #TODO: read source TC


    #
    # filter chain
    #

    filter_array = []
    if settings["logo_4_3"] and settings["logo_16_9"]:
        filter_array.append(
                "movie={}[watermark];[watermark]scale={}:{}[watermark]".format(
                    settings["logo"],
                    settings["width"],
                    settings["height"]
                    )
                )

        if settings["deinterlace"]:
            #TODO: Deinterlace here
        filter_array.append("[in]null[out]")
    else:
        filter_array.append("[in]null[out]")

    if False:
        #TODO: handle True, False, "auto"
        filter_array.append("[out]colorlevels=rimin=0.0625:gimin=0.0625:bimin=0.0625:rimax=0.9375:gimax=0.9375:bimax=0.9375[out]")

    filter_array.append("[out]scale={}:{}[out]".format(settings["width"], settings["height"]))
    if settings.get("logo", False):
        filter_array.append("[out][watermark]overlay=0:0[out]")

    #TODO: timecode burn in

    filters = ";".join(filter_array)


    #
    # output format
    #

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

    #TODO: if container == m3u8, append hls params

    result.extend([
            ["c:a", "libfdk_aac"],
            ["b:a", settings["audio_bitrate"]],
            ["ar", settings["audio_sample_rate"]]
        ])

    return result
