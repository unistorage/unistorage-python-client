import urllib
from urlparse import urljoin

import requests
import decorator


@decorator.decorator  # Saves function name, signature and docstring -- needed for Sphinx docs
def pluck_resource_uri(method, *args, **kwargs):
    response = method(*args, **kwargs)
    return response['resource_uri']


class UnistorageError(Exception):
    """Client raises this when it receives error from Unistorage API.

    :param status_code: Response HTTP status code.
    :param msg: Error message.
    """
    def __init__(self, status_code, msg):
        self.status_code = status_code
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class UnistorageClient(object):
    """Class that provides interface to the Unistorage API.
    Built on top of the Python `requests <http://docs.python-requests.org/>`_ library.

    :param url: Unistorage API root URL.
    :param token: Access token.

    .. code-block:: python

        unistorage = UnistorageClient(
            'http://localhost:5000/', 'dc363e85965d461b81a4f78df45f636f')

    .. note::

        * All described methods can raise :class:`UnistorageError`.
        * All resource URIs returned by methods are relative.
    """
    def __init__(self, url, token):
        self.url = url
        self.token = token

    def _request(self, method, url, **kwargs):
        """Sends request by specified `method` to the relative `url`; adds Token header.
        `kwargs` has the same meaning as in the requests library.
        """
        kwargs.setdefault('headers', {})
        kwargs['headers'].update({'Token': self.token})
        response = requests.request(method, urljoin(self.url, url), **kwargs)
        
        status_code = response.status_code
        if 200 <= status_code < 300:
            return response.json
        elif status_code >= 400:
            msg = response.json and response.json.get('msg') or response.content
            raise UnistorageError(status_code, msg)

    def get(self, url, data=None):
        """Sends a GET request. Returns response dictionary.
        
        :param url: Relative URL.
        :param data: Dictionary to be sent in the query string.
        """
        return self._request('get', url, params=data)
    
    def post(self, url, data=None, files=None):
        """Sends a POST request. Returns response dictionary.
        
        :param url: Relative URL.
        :param data: Dictionary to be sent in the body of request.
        :param files: Dictionary of the files for multipart encoding upload.
            It passed directly to the `requests <http://docs.python-requests.org/>`_ library.
            See requests documentation for details:
            http://docs.python-requests.org/en/latest/user/quickstart/#post-a-multipart-encoded-file

        .. code-block:: python

            file = open('/path/to/file.doc')
            unistorage.post('/', data={'type_id': 'news_thumbnails'}, files={'file': file})
        """
        return self._request('post', url, data=data, files=files)

    @pluck_resource_uri
    def upload_file(self, file_name, file_content, type_id=None):
        """Uploads file to the Unisorage. Returns resource URI of the uploaded file.
        
        :param file_name: File name.
        :param file_content: File-like object to be uploaded.
        :param type_id: Type identifier for the `file`.

        .. code-block:: python

            file = open('/path/to/file.doc')
            file_uri = unistorage.upload_file('file.doc', file, type_id='resume')
            print unistorage.get(file_uri)
        """
        data = type_id and {'type_id': type_id} or None
        files = {'file': (file_name, file_content)}
        return self.post('/', data=data, files=files)

    @pluck_resource_uri
    def create_template(self, applicable_for, actions):
        """Creates template. Returns resource URI of the created template.
        
        :param applicable_for: Files type for that template can be applied.
        :param actions: List of tuples, each of which contains two elements:
            action name and action arguments.

        .. code-block:: python

            resize = ('resize', {'mode': 'keep', 'w': 50})
            grayscale = ('grayscale', {})
            template_uri = unistorage.create_template('image', [resize, grayscale])
            print unistorage.get(template_uri)
        """
        encoded_actions = \
            [urllib.urlencode(dict(args, action=action)) for action, args in actions]
        return self.post('/template/', data={
            'applicable_for': applicable_for,
            'action[]': encoded_actions
        })

    @pluck_resource_uri
    def apply_action(self, uri, action_name, action_args):
        """Applies action to the file with specified URI. Returns resource URI of the resulting file.

        :param action_name: Action name.
        :param action_args: Dictionary of action arguments.
        """
        data = {'action': action_name}
        data.update(action_args)
        return self.get(uri, data=data)

    @pluck_resource_uri
    def apply_template(self, uri, template):
        """Applies template to the file with specified URI. Returns resource URI of the resulting file.

        :param template: Template URI.
        """
        return self.get(uri, data={'template': template})

    @pluck_resource_uri
    def create_archive(self, archive_name, files):
        """Creates archive. Returns resource URI of created archive.

        :param archive_name: Archive name.
        :param files: URIs of the files to be included in the archive.

        .. code-block:: python

            archive_uri = unistorage.create_archive('images.zip', [file1_uri, file2_uri])
            print unistorage.get(template_uri)
        """
        return self.post('/zip/', data={
            'file': files,
            'filename': archive_name
        })
