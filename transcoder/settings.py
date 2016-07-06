def get_settings(**kwargs):
    return {
            # Frame settings

            "frame_rate" : kwargs.get("frame_rate", 25),
            "pixel_format" : kwargs.get("pixel_format", "yuv420p"),
            "width" : kwargs.get("width", 720),
            "height" : kwargs.get("height", 576),
            "logo_16_9" : kwargs.get("logo", False),
            "logo_4_3" : kwargs.get("logo", False),
            "expand_levels" : kwargs.get("expand_levels", "auto"),
            "deinterlace" : kwargs.get("deinterlace", True),

            # Video encoder settings

            "container" : kwargs.get("container", "mp4"),
            "video_codec" : kwargs.get("video_codec", "libx264"),
            "video_bitrate" : kwargs.get("video_bitrate", "1800k"),
            "x264_profile" : kwargs.get("x264_profile", "main"),
            "x264_preset" : kwargs.get("x264_preset", "medium"),
            "x264_level" : kwargs.get("x264_level", "4.0"),

            # Audio encoder settings

            "audio_codec" : kwargs.get("audio_codec", "libfdk_aac"),
            "audio_bitrate" : kwargs.get("audio_bitrate", "128k"),
            "audio_sample_rate" : kwargs.get("audio_sample_rate", 48000),

            # Daemon settings

            "qtime" : int(kwargs.get("qtime", 10)),
            "loop_delay" : int(kwargs.get("loop_delay", 5)),
            "source_exts" : kwargs.get("source_exts", ["mxf"])
        }
