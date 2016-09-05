#!/bin/bash
cd /opt/transcoder

PATH=/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH
screen -AdmS transcoder -t transcoder python "./transcoder.py"

