from nxtools import *


class AudioTrack():
    def __init__(self, **kwargs):
        self.data = kwargs

    def __getitem__(self, key):
        return self.data[key]

    @property
    def id(self):
        return self["index"]


def guess_aspect (w, h):
    if 0 in [w, h]:
        return 0
    valid_aspects = [(16, 9), (4, 3), (2.35, 1)]
    ratio = float(w) / float(h)
    return "{}:{}".format(*min(valid_aspects, key=lambda x:abs((float(x[0])/x[1])-ratio)))


def probe(source_path):
    probe_result = ffprobe(source_path)
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
            meta["audio_tracks"].append(AudioTrack(**stream))

    meta["duration"] = float(format_info["duration"]) or source_vdur
    meta["num_frames"] = meta["duration"] * meta["frame_rate"]
    return meta


def get_output_format(job):
    settings = job.parent.settings

    #
    # ffprobe
    #

    logging.debug("Probing {}".format(job.base_name))
    meta = probe(job.source_path)

    #TODO: error handling

    #TODO: read source TC

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

    #TODO: timecode burn in

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
