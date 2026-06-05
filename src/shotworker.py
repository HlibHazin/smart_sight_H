import os
import time

from pydub import AudioSegment
from pydub.playback import play


AUDIO_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..",
    "resources/9mm-pistol-shoot-short-reverb-7152-short.mp3"
)


class ShotWorker:
    def __init__(self):
        self.make_shot = False
        self.state_updated = False
        self.stop_shot_worker = False

    def shot_worker(self):
        song = AudioSegment.from_mp3(AUDIO_PATH)
        while not self.stop_shot_worker:
            if self.make_shot:
                play(song)
                self.make_shot = False
                self.state_updated = True
            else:
                time.sleep(1e-4)

    def do_shot(self):
        print('do shot')
        self.make_shot = True
        self.state_updated = True
