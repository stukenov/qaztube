import unittest
import os
from videos.models import generate_uid, get_video_path, get_processed_video_path, get_hls_path, get_thumbnail_path

class TestModelFunctions(unittest.TestCase):
    def test_generate_uid(self):
        uid = generate_uid()
        self.assertEqual(len(uid), 6)
        self.assertTrue(uid.isalnum())
        self.assertTrue(uid.islower())

    def test_get_video_path(self):
        class MockVideo:
            def __init__(self):
                self.uid = 'abc123'
        
        mock_video = MockVideo()
        path = get_video_path(mock_video, 'test.mp4')
        self.assertEqual(path, 'videos/a/b/c/1/2/3/video.mp4')

    def test_get_processed_video_path(self):
        class MockVideo:
            def __init__(self):
                self.uid = 'abc123'
        
        mock_video = MockVideo()
        path = get_processed_video_path(mock_video, 'test.mp4')
        self.assertEqual(path, 'videos/a/b/c/1/2/3/processed.mp4')

    def test_get_hls_path(self):
        class MockVideo:
            def __init__(self):
                self.uid = 'abc123'
        
        mock_video = MockVideo()
        path = get_hls_path(mock_video, 'test.m3u8')
        self.assertEqual(path, 'videos/a/b/c/1/2/3/master.m3u8')

    def test_get_thumbnail_path(self):
        class MockVideo:
            def __init__(self):
                self.uid = 'abc123'
        
        mock_video = MockVideo()
        path = get_thumbnail_path(mock_video, 'test.jpg')
        self.assertEqual(path, 'videos/a/b/c/1/2/3/thumbnail.jpg')

if __name__ == '__main__':
    unittest.main() 