import json
import os
import subprocess
from queue import Queue
from bottle import route, run, Bottle, request, response, static_file, hook
from datetime import datetime, timedelta
from threading import Thread
import youtube_dl
import redis
import urllib.request, json

app = Bottle()
r = redis.StrictRedis(unix_socket_path='/tmp/redis.sock', db=0, charset="utf-8", decode_responses=True)
youtube_dl_version = "firststart"
lastCheck = datetime.now() - timedelta(minutes=17)
locked = False

class Media:
    def __init__(self, url, token, mediaType):
        self.url = url
        self.status = 0
        self.token = token
        self.expiration = None
        self.type = mediaType
        self.toQueue = False
    def setQueued(self):
        self.toQueue = False
    def updateStatus(self, status):
        self.status = status
        if status == 2:
            self.expiration = datetime.now() + timedelta(hours=6)
    def getFileName(self):
        for root, dirs, filenames in os.walk('/downloads'):
            for f in filenames:
                if(f != None and len(f) > 32 and f[0:32] == self.token):
                    return f;
    def update(self, status, expiration, toQueue):
        self.status = status
        self.expiration = expiration
        self.toQueue = toQueue
    def toJSON(self):
        if self.expiration != None and type(self.expiration) is not str:
            self.expiration = self.expiration.isoformat()
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)

def fromJSON(mediaJSON):
    if mediaJSON != None:
        myJSON = json.loads(mediaJSON)
        myMedia = Media(myJSON['url'], myJSON['token'], myJSON['type'])
        myMedia.update(myJSON['status'], myJSON['expiration'], myJSON['toQueue'])
        return myMedia
    else:
        return None

##################
# WORKERS
# |- DownloadWorker
# |- CleanerWorker
# |- QueueElaboratorWorker
# |- UpdaterWorker
##################

class DownloadWorker(Thread):
   def __init__(self, queue):
       Thread.__init__(self)
       self.queue = queue
   def run(self):
       while True:
           token = self.queue.get()
           process(token)
           self.queue.task_done()

class CleanerWorker(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        while True:
            for i in r.keys():
                if i != None:
                    media = fromJSON(r.get(i))
                if media.status == 2:
                    if datetime.now() > datetime.strptime(media.expiration, "%Y-%m-%dT%H:%M:%S.%f"):
                        os.remove('/downloads/'+media.getFileName())
                        r.delete(i)

class QueueElaboratorWorker(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        while True:
            for i in r.keys():
                if i != None and len(i) > 0:
                    media = fromJSON(r.get(i))
                if media != None and media.toQueue:
                    media.setQueued()
                    queue.put(i)
                    r.set(i, media.toJSON());

class UpdaterWorker(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        while True:
            global youtube_dl_version, lastCheck, locked
            if (datetime.now() - lastCheck) > timedelta(minutes=15):
                with urllib.request.urlopen("https://api.github.com/repos/rg3/youtube-dl/releases/latest") as url:
                    data = json.loads(url.read().decode())
                    if youtube_dl_version == "firststart":
                        youtube_dl_version = data['tag_name']
                    else:
                        if data['tag_name'] != youtube_dl_version:
                            print("[UPDATE] Got a new version!! we have to update...")
                            locked = True
                            print("[UPDATE] New incoming media have been locked, will be processed as soon as update finished")
                            youtube_dl_version = data['tag_name']
                            while True:
                                ready = True;
                                for i in r.keys():
                                    if i != None:
                                        media = fromJSON(r.get(i))
                                        if media.status == 1:
                                            ready = False;

                                if ready == True:
                                    print("[UPDATE] Ready to start to update, there aren't any media processing right now.")
                                    break;
                            command = ['/usr/local/bin/pip3', 'install', '--upgrade', 'youtube-dl']
                            call = subprocess.call(command, shell=False)
                            print("[UPDATE] Software updated")
                            locked = False;
                        lastCheck = datetime.now()
def process(token):
    global locked
    if locked == True:
        while True:
            if locked == False:
                break;
    media = fromJSON(r.get(token))
    media.updateStatus(1)
    command = ['/usr/local/bin/youtube-dl', '--restrict-filenames', '-o', '/downloads/'+token+'-%(title)s.%(ext)s']
    r.set(token, media.toJSON());
    if media.type == "mp3":
        command.append('-x')
        command.append('--audio-format=mp3')
        command.append('--audio-quality=0')
    command.append(media.url)
    call = subprocess.call(command, shell=False)
    if call == 0:
        media.updateStatus(2)
    else:
        media.updateStatus(3)

    r.set(token, media.toJSON());

queue = Queue()
for x in range(8):
   worker = DownloadWorker(queue)
   worker.daemon = True
   worker.start()

worker = CleanerWorker()
worker.daemon = True
worker.start()

worker = QueueElaboratorWorker()
worker.daemon = True
worker.start()

worker = UpdaterWorker()
worker.daemon = True
worker.start()

queue.join()
print("  ___                  _              _ _     ")
print(" |   \ _____ __ ___ _ | |___  __ _ __| | |_ _ ")
print(" | |) / _ \ V  V / ' \| / _ \/ _` / _` | | '_|")
print(" |___/\___/\_/\_/|_||_|_\___/\__,_\__,_|_|_|  ")
print("")
print("Downloaldr ProSrv (Processing Server)")
print("REL 01.03.00.01")
print("")
app.run(host='0.0.0.0', port=34567)
