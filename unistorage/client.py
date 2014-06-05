from urlparse import urljoin

import requests
from requests.exceptions import Timeout
from models import FileFactory, Template, ZipFile


class UnistorageError(Exception):
    """Client raises this when it receives error from Unistorage API.

    :param status_code: Response HTTP status code.
    :param msg: Error message.
    """
    def __init__(self, status_code, msg):
        self.status_code = status_code
        self.msg = msg

    def __str__(self):
        return '<{0}: {1}>'.format(self.status_code, self.msg)


class UnistorageTimeout(Exception):
    """Client raises this when the request timed out.
    """
    def __str__(self):
        return 'Unistorage API request timed out.'


class UnistorageClient(object):
    """Class that provides interface to the Unistorage API.

    :param url: Unistorage API root URL.
    :param token: Access token.

    .. code-block:: python

        unistorage = UnistorageClient(
            'http://localhost:5000/', 'dc363e85965d461b81a4f78df45f636f')

    .. note::

        All methods can raise :class:`UnistorageError` and :class:`UnistorageTimeout`.
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
        try:
            response = requests.request(method, urljoin(self.url, url), **kwargs)
        except Timeout:
            raise UnistorageTimeout()
        
        status_code = response.status_code
        try:
            json = response.json()
        except:
            raise UnistorageError(
                status_code, 'Unistorage API returned invalid JSON: %s' % response.content)

        if 200 <= status_code < 300:
            return json
        elif status_code >= 400:
            msg = json and json.get('msg') or response.content
            raise UnistorageError(status_code, msg)

    def _get(self, url, data=None):
        """Sends a GET request. Returns the response dictionary.
        
        :param url: Relative URL.
        :param data: Dictionary to be sent in the query string.
        """
        return self._request('get', url, params=data)
    
    def _post(self, url, data=None, files=None, timeout=None):
        """Sends a POST request. Returns the response dictionary.
        
        :param url: Relative URL.
        :param data: Dictionary to be sent in the body of request.
        :param files: Dictionary of the files for multipart encoding upload.
        :param timeout: Integer value that define request timeout in seconds.
            It passed directly to the `requests <http://docs.python-requests.org/>`_ library.
            See requests documentation for details:
            http://docs.python-requests.org/en/latest/user/quickstart/#post-a-multipart-encoded-file
        """
        return self._request('post', url, data=data, files=files,
                             timeout=timeout)

    def get_file(self, file_uri):
        """Retrieves data from Unistorage and returns :class:`unistorage.models.File`.
        
        :param resource_uri: File URI.
        """
        file_response = self._get(file_uri)
        return FileFactory.build_from_dict(file_uri, file_response)
    
    def get_zip_file(self, zip_uri):
        """Retrieves data from Unistorage and returns :class:`unistorage.models.ZipFile`.
        
        :param resource_uri: Zip file URI.
        """
        zip_response = self._get(zip_uri)
        return ZipFile(zip_uri, zip_response)

    def upload_file(self, file_name, file_content, type_id=None, timeout=None):
        """Uploads file to the Unistorage. Returns :class:`unistorage.models.File`.
        
        :param file_name: File name.
        :param file_content: File-like object to be uploaded.
        :param type_id: Type identifier.
        :param timeout: Integer value that define request timeout in seconds.
        :rtype: :class:`unistorage.models.File`

        .. code-block:: python

            >>> file = open('/path/to//jpg.jpg')
            >>> unistorage.upload_file('jpg.jpg', file, type_id='bubu')
            <models.ImageFile object at 0x13edf10>
        """
        data = type_id and {'type_id': type_id} or None
        files = {'file': (file_name, file_content)}
        upload_response = self._post('/', data=data, files=files,
                                     timeout=timeout)
        return self.get_file(upload_response['resource_uri'])

    def create_template(self, applicable_for, actions):
        """Creates template. Returns :class:`unistorage.models.Template`.
        
        :param applicable_for: Files type for that template can be applied.
            Supported types: ``'image'``, ``'video'``, ``'doc'``.
        :param actions: List of :class:`unistorage.models.Action`.
        :rtype: :class:`unistorage.models.Template`

        .. code-block:: python

            >>> from unistorage import Action
            >>> unistorage.create_template('image', [
            ...     Action('resize', {'mode': 'keep', 'w': 50, 'h': 50}),
            ...     Action('grayscale')
            ... ])
            <models.Template object at 0x19a5910>
        """
        encoded_actions = [action.encode() for action in actions]
        response = self._post('/template/', data={
            'applicable_for': applicable_for,
            'action[]': encoded_actions
        })
        return Template(response['resource_uri'])

    def apply_action(self, file, action):
        """Applies `action` to the `file`.

        :param file: Source file.
        :type file: :class:`unistorage.models.File`
        :param action: Action to be applied.
        :type action: :class:`unistorage.models.Action`
        :rtype: :class:`unistorage.models.File`
        """
        action_response = self._get(file.resource_uri, data=action.to_dict())
        resulting_file_uri = action_response['resource_uri']
        file_response = self._get(resulting_file_uri)
        return FileFactory.build_from_dict(resulting_file_uri, file_response)

    def apply_template(self, file, template, with_low_priority=False):
        """Applies `template` to the `file`.

        :param file: Source file.
        :type file: :class:`unistorage.models.File`
        :param template: Template to be applied.
        :type template: :class:`unistorage.models.Template`
        :rtype: :class:`unistorage.models.File`
        """
        data = {'template': template.resource_uri}
        if with_low_priority:
            data['with_low_priority'] = '1'
        template_response = self._get(file.resource_uri, data=data)
        resulting_file_uri = template_response['resource_uri']
        file_response = self._get(resulting_file_uri)
        return FileFactory.build_from_dict(resulting_file_uri, file_response)

    def get_zipped(self, zip_file_name, files):
        """Creates ZIP archive.

        :param archive_name: Archive name.
        :param files: List of :class:`unistorage.models.File`.
        :rtype: :class:`unistorage.models.ZipFile`

        .. code-block:: python

            >>> with open('/path/to/file1.jpg', 'rb') as f:
            ...     file1 = unistorage.upload_file('upchk.jpg', f, type_id='qwerty')
            >>> with open('/path/to/file2.jpg', 'rb') as f:
            ...     file2 = unistorage.upload_file('upchk2.jpg', f, type_id='qwerty')
            >>> unistorage.get_zipped('files.zip', [file1, file2])
            <models.ZipFile object at 0x19ab710>
        """
        response = self._post('/zip/', data={
            'file': [file.resource_uri for file in files],
            'filename': zip_file_name
        })
        return self.get_zip_file(response['resource_uri'])
