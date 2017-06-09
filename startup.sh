#!/bin/sh
apk add --no-cache ffmpeg && \
pip3 install --upgrade -r ./requirements.txt && \
rm -rf /var/lib/apt/lists/*
echo "unixsocket /tmp/redis.sock" >> /etc/redis.conf
echo "unixsocketperm 755" >> /etc/redis.conf
redis-server /etc/redis.conf --daemonize yes
chown -R apache:apache /usr/src/app/websrv/downloadlr-wapi && chmod -R 755 /usr/src/app/websrv/downloadlr-wapi
rm -f /run/apache2/apache2.pid
rm -f /run/apache2/httpd.pid
httpd -D FOREGROUND &
python3 -u ./downloadlr-prosrv.py
exit 0
