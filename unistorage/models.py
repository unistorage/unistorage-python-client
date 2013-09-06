import urllib

import decorator

from filetypes import is_image, is_video, is_document


class Action(dict):
    """
    Class that represents action.

    :param name: Action name;
    :param with_low_priority: Whether action has low priority;
    :param args: Dictionary contains arguments of the action.

    .. code-block:: python

        >>> action = Action('resize', {'mode': 'crop', 'w': 100, 'h': 100})
        >>> action.to_dict()
        {'action': 'resize', 'h': 100, 'mode': 'crop', 'w': 100}
        >>> action.encode()
        'action=resize&h=100&mode=crop&w=100'
    """
    def __init__(self, name, *args, **kwargs):
        super(Action, self).__init__(*args)
        self.name = name
        self.with_low_priority = kwargs.get('with_low_priority', False)

    def encode(self):
        """Returns URL-encoded representation of this action."""
        data = self.to_dict()
        if self.with_low_priority:
            data['with_low_priority'] = 1
        return urllib.urlencode(data)

    def to_dict(self):
        """Returns dictionary that contains both action arguments and action name.
        It can be URL-encoded and used to call the Unistorage API.
        """
        return dict(self, action=self.name)


class Template(object):
    """Represents template.

    :param resource_uri: File resource URI.

    .. attribute:: resource_uri

        Resource URI.
    """
    def __init__(self, resource_uri):
        self.resource_uri = resource_uri


class File(object):
    """Base file class.

    :param resource_uri: File resource URI.
    :param response: File data (Unistorage API response).

    .. attribute:: resource_uri

        Resource URI.

    .. attribute:: ttl

        TTL.
    """
    def __init__(self, resource_uri, response):
        self.resource_uri = resource_uri
        self.ttl = response['ttl']

    def __str__(self):
        return self.resource_uri


class PendingFile(File):
    """Represents pending file (pending files have status ``'wait'``)."""
    def __init__(self, resource_uri, response):
        super(PendingFile, self).__init__(resource_uri, response)


class TemporaryFile(File):
    """Represents temporary file (temporary files have status ``'just_uri'``).

    .. attribute:: url

        URL of the binary content.
    """
    def __init__(self, resource_uri, response):
        super(TemporaryFile, self).__init__(resource_uri, response)
        data = response['data']
        self.url = data['url']


class ZipFile(File):
    """Represents ZIP archive.

    .. attribute:: url

        URL of the binary content.
    """
    def __init__(self, resource_uri, response):
        super(ZipFile, self).__init__(resource_uri, response)
        data = response['data']
        self.url = data['url']


class RegularFile(File):
    """Represents regular file (regular files have status ``'ok'``).

    .. attribute:: url
            
        URL of the binary content.

    .. attribute:: mimetype

        MIME type.

    .. attribute:: size

        Size in bytes.

    .. attribute:: name

        Name.
    """
    def __init__(self, resource_uri, response):
        super(RegularFile, self).__init__(resource_uri, response)
        data = response['data']
        self.url = data['url']
        self.mimetype = data['mimetype']
        self.size = data['size']
        self.name = data['name']

    def apply_template(self, unistorage, template, with_low_priority=False):
        """Applies template to this file.

        :param unistorage: Unistorage client
        :type unistorage: :class:`unistorage.client.UnistorageClient`
        :param template: Template to be applied.
        :type template: :class:`unistorage.models.Template`
        :type with_low_priority: :class:`bool`
        :rtype: :class:`unistorage.models.File`
        """
        return unistorage.apply_template(self, template,
                                         with_low_priority=with_low_priority)


@decorator.decorator
def action(method, self, unistorage, *args, **kwargs):
    with_low_priority = kwargs.pop('with_low_priority', False)
    action_name, action_args = method(self, unistorage, *args, **kwargs)
    action = Action(action_name, action_args, with_low_priority=with_low_priority)
    return unistorage.apply_action(self, action)


class Watermarkable(object):
    @action
    def watermark(self, unistorage, watermark, corner, w, h, w_pad, h_pad, **kwargs):
        """:rtype: :class:`File`"""
        return 'watermark', {
            'watermark': watermark.resource_uri,
            'corner': corner,
            'w': w,
            'h': h,
            'w_pad': w_pad,
            'h_pad': h_pad,
        }


class ImageFile(RegularFile, Watermarkable):
    """Represents image file.

    .. attribute:: width
            
        Image width.

    .. attribute:: height

        Image height.

    .. attribute:: orientation

        EXIF orientation (number from 1 to 8).
    """
    def __init__(self, resource_uri, response):
        super(ImageFile, self).__init__(resource_uri, response)
        extra = response['data']['extra']
        self.width = extra['width']
        self.height = extra['height']
        self.orientation = extra['orientation']

    @action
    def convert(self, unistorage, to, **kwargs):
        """:rtype: :class:`File`"""
        return 'convert', {'to': to}

    @action
    def resize(self, unistorage, mode, w, h, **kwargs):
        """:rtype: :class:`File`"""
        return 'resize', {'mode': mode, 'w': w, 'h': h}
    
    @action
    def grayscale(self, unistorage, **kwargs):
        """:rtype: :class:`File`"""
        return 'grayscale', {}
    
    @action
    def rotate(self, unistorage, angle, **kwargs):
        """:rtype: :class:`File`"""
        return 'rotate', {'angle': angle}


class VideoFile(RegularFile, Watermarkable):
    """Represents video file.

    .. attribute:: width
            
        Video width.

    .. attribute:: height

        Video height.

    .. attribute:: codec

        Video codec.
    """
    def __init__(self, resource_uri, response):
        super(VideoFile, self).__init__(resource_uri, response)
        extra = response['data']['extra']
        self.width = extra['video']['width']
        self.height = extra['video']['height']
        self.codec = extra['video']['codec']

    @action
    def convert(self, unistorage, to, vcodec=None, acodec=None, **kwargs):
        """:rtype: :class:`File`"""
        args = {'to': to}
        if vcodec:
            args['vcodec'] = vcodec
        if acodec:
            args['acodec'] = acodec
        return 'convert', args

    @action
    def extract_audio(self, unistorage, to, **kwargs):
        """:rtype: :class:`File`"""
        return 'extract_audio', {'to': to}

    @action
    def capture_frame(self, unistorage, to, position, **kwargs):
        """:rtype: :class:`File`"""
        return 'capture_frame', {'to': to, 'position': position}


class DocFile(RegularFile):
    """Represents document file."""
    @action
    def convert(self, unistorage, to, **kwargs):
        """:rtype: :class:`File`"""
        return 'convert', {'to': to}


class AudioFile(RegularFile):
    """Represents audio file."""
    @action
    def convert(self, unistorage, to, **kwargs):
        """:rtype: :class:`File`"""
        return 'convert', {'to': to}


class FileFactory(object):
    unistorage_type_map = {
        'unknown': RegularFile,
        'image': ImageFile,
        'video': VideoFile,
        'audio': AudioFile,
        'doc': DocFile
    }

    @classmethod
    def build_from_dict(cls, resource_uri, file_data):
        file_class = None

        status = file_data['status']
        if status == 'ok':
            unistorage_type = file_data['data']['unistorage_type']
            file_class = cls.unistorage_type_map[unistorage_type]

        elif status == 'just_uri':
            file_class = TemporaryFile

        elif status == 'wait':
            file_class = PendingFile

        return file_class(resource_uri, file_data)
