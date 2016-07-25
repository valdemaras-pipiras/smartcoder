#
# probe.py
#
# function probe(source_path):
# Analyzes source file using ffprobe and extracts its metadata
#

from nxtools import *

__all__ = ["probe"]

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

    if not probe_result:
        return False

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
            if "timecode" in stream:
                meta["timecode"] = stream["timecode"]
            else:
                meta["timecode"] = "00:00:00:00"

        elif stream["codec_type"] == "audio":
            meta["audio_tracks"].append(AudioTrack(**stream))

    if meta["timecode"] == "00:00:00:00" and format_info.get("timecode", "00:00:00:00") != "00:00:00:00":
        meta["timecode"] = format_info["timecode"]

    meta["duration"] = float(format_info["duration"]) or source_vdur
    meta["num_frames"] = meta["duration"] * meta["frame_rate"]
    return meta
