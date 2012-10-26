import unittest

from unistorage.models import (FileFactory, TemporaryFile, PendingFile,
                               ImageFile, VideoFile, DocFile)


class TestFileFactory(unittest.TestCase):
    def get_ok_response(self):
        return {
            'status': 'ok',
            'data': {
                'extra': {'width': 100, 'height': 100},
                'mimetype': 'image/jpeg',
                'name': 'some.jpeg',
                'size': 211258,
                'uri': 'http://127.0.0.1/503dd7c48149954c99f41a29'
            },
            'ttl': 604800
        }

    def get_just_uri_response(self):
        return {
            'status': 'just_uri',
            'data': {
                'uri': 'http://127.0.0.1/503dd7c48149954c99f41a29'
            },
            'ttl': 15
        }

    def get_wait_response(self):
        return {
            'status': 'wait',
            'ttl': 5
        }

    def test_just_uri(self):
        response = self.get_just_uri_response()
        result = FileFactory.build_from_dict(None, response)
        self.assertIs(type(result), TemporaryFile)

    def test_wait(self):
        response = self.get_wait_response()
        result = FileFactory.build_from_dict(None, response)
        self.assertIs(type(result), PendingFile)

    def test_ok(self):
        response = self.get_ok_response()
        result = FileFactory.build_from_dict(None, response)
        self.assertIs(type(result), ImageFile)

        response = self.get_ok_response()
        response['data']['mimetype'] = 'video/ogg'
        response['data']['extra']['codec'] = 'codec'
        result = FileFactory.build_from_dict(None, response)
        self.assertIs(type(result), VideoFile)

        response = self.get_ok_response()
        response['data']['mimetype'] = 'application/pdf'
        result = FileFactory.build_from_dict(None, response)
        self.assertIs(type(result), DocFile)
