from addondev import initializer
import os

initializer(os.path.dirname(os.path.dirname(__file__)))
import unittest
import addon
from codequick import youtube


class Tester(unittest.TestCase):
    def test_root(self):
        data = addon.root.test()
        self.assertGreaterEqual(len(data), 16)

    def test_youtube_channel(self):
        data = youtube.Playlist.test("UCDjGU4DP3b-eGxrsipCvoVQ")
        self.assertGreaterEqual(len(data), 50)

    def test_recent_videos(self):
        data = addon.content_lister.test(sfid=1183, ctype="video")
        self.assertGreaterEqual(len(data), 10)

    def test_recent_videos_next(self):
        data = addon.content_lister.test(sfid=1183, ctype="video", page_count=2)
        self.assertGreaterEqual(len(data), 10)

    def test_revent_audio(self):
        data = addon.content_lister.test(sfid=1183, ctype="segment")
        self.assertGreaterEqual(len(data), 10)

    def test_revent_audio_next(self):
        data = addon.content_lister.test(sfid=1183, ctype="segment", page_count=2)
        self.assertGreaterEqual(len(data), 10)

    def test_content_lister_video(self):
        data = addon.content_lister.test(sfid=1183, ctype="video", topic="space")
        self.assertGreaterEqual(len(data), 10)

    def test_content_lister_video_next(self):
        data = addon.content_lister.test(sfid=1183, ctype="video", topic="space", page_count=2)
        self.assertGreaterEqual(len(data), 10)

    def test_content_lister_audio(self):
        data = addon.content_lister.test(sfid=1183, ctype="segment", topic="space")
        self.assertGreaterEqual(len(data), 10)

    def test_content_lister_audio_next(self):
        data = addon.content_lister.test(sfid=1183, ctype="segment", topic="space", page_count=2)
        self.assertGreaterEqual(len(data), 10)
