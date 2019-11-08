from addondev import testing
import unittest

# Testing specific imports
from codequick import youtube
import codequick
from addon import main as addon

# Check witch version of codequick we are running
framework_version = codequick.__dict__.get("__version__", (0, 9, 0))


class Tester(unittest.TestCase):
    def test_root(self):
        data = addon.root.test()
        self.assertGreaterEqual(len(data), 16)

    def test_root_audio(self):
        with testing.mock_setting("defaultview", 1):
            data = addon.root.test()
        self.assertGreaterEqual(len(data), 16)

    def test_youtube_channel(self):
        data = youtube.Playlist.test("UCDjGU4DP3b-eGxrsipCvoVQ")
        self.assertGreaterEqual(len(data), 50)

    def test_recent_videos(self):
        data = addon.content_lister.test(url="/explore/?post_types=video")
        self.assertGreaterEqual(len(data), 10)

    def test_recent_videos_next(self):
        data = addon.content_lister.test(url="/explore/?post_types=video&sf_paged=2")
        self.assertGreaterEqual(len(data), 10)

    def test_recent_audio(self):
        data = addon.content_lister.test(url="/explore/?post_types=segment")
        self.assertGreaterEqual(len(data), 10)

    def test_recent_audio_next(self):
        data = addon.content_lister.test(url="/explore/?post_types=segment&sf_paged=2")
        self.assertGreaterEqual(len(data), 10)

    def test_content_lister_video(self):
        data = addon.content_lister.test(url="/explore/?post_types=video&_sft_topic=space")
        self.assertGreaterEqual(len(data), 10)

    def test_content_lister_video_alt(self):
        data = addon.content_lister.test(
            url="/explore/?post_types=video&_sft_topic=space",
            alt_url="/explore/?post_types=segment&_sft_topic=space"
        )
        self.assertGreaterEqual(len(data), 10)

    def test_content_lister_video_next(self):
        data = addon.content_lister.test(url="/explore/?post_types=video&_sft_topic=space&sf_paged=2")
        self.assertGreaterEqual(len(data), 10)

    def test_content_lister_audio(self):
        data = addon.content_lister.test(url="/explore/?post_types=segment&_sft_topic=space")
        self.assertGreaterEqual(len(data), 10)

    def test_content_lister_audio_alt(self):
        data = addon.content_lister.test(
            url="/explore/?post_types=segment&_sft_topic=space",
            alt_url="/explore/?post_types=video&_sft_topic=space"
        )
        self.assertGreaterEqual(len(data), 10)

    def test_content_lister_audio_next(self):
        data = addon.content_lister.test(url="/explore/?post_types=segment&_sft_topic=space&sf_paged=2")
        self.assertGreaterEqual(len(data), 10)
