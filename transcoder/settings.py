#
# settings.py
#
# function get_settings(**kwargs)
# Creates transcoder setting dict. Accepts custom params loaded from config file
#

def get_settings(**kwargs):
    return {
            # Frame settings

            "width" : int(kwargs.get("width", 720)),
            "height" : int(kwargs.get("height", 576)),
            "frame_rate" : int(kwargs.get("frame_rate", 25)),
            "pixel_format" : kwargs.get("pixel_format", "yuv420p"),
            "expand_levels" : kwargs.get("expand_levels", "auto"),  # Expand levels from broadcast to full (pc) using levels
            "deinterlace" : kwargs.get("deinterlace", True),

            # Burn-in options

            # Both logos must be specified in order to enable watermarking
            "logo_4_3" : kwargs.get("logo_4_3", False),
            "logo_16_9" : kwargs.get("logo_16_9", False),

            "tc_show" : kwargs.get("tc_show", True),
            "tc_font" : kwargs.get("tc_font", "support/RobotoMono-Medium.ttf"),
            "tc_size" : kwargs.get("tc_size", 24),

            # Video encoder settings

            "container" : kwargs.get("container", "mp4"),
            "video_codec" : kwargs.get("video_codec", "libx264"),
            "video_bitrate" : kwargs.get("video_bitrate", "1800k"),
            "x264_profile" : kwargs.get("x264_profile", "main"),
            "x264_preset" : kwargs.get("x264_preset", "medium"),
            "x264_level" : kwargs.get("x264_level", "4.0"),
            "gop_size" : kwargs.get("gop_size", 50),

            # Audio encoder settings

            "audio_codec" : kwargs.get("audio_codec", "libfdk_aac"),
            "audio_bitrate" : kwargs.get("audio_bitrate", "128k"),
            "audio_sample_rate" : kwargs.get("audio_sample_rate", 48000),

            # Daemon settings

            "qtime" : int(kwargs.get("qtime", 10)),
            "loop_delay" : int(kwargs.get("loop_delay", 5)),
            "source_exts" : kwargs.get("source_exts", ["mxf"])
        }
