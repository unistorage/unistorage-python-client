Installation
------------
Project hosted on `Github <https://github.com/unistorage/unistorage-python-client>`_ and
can be installed via pip:

.. code-block:: shell

    pip install git+git://github.com/unistorage/unistorage-python-client.git

API
---
.. automodule:: unistorage.client
    :members:

Models
------
.. autoclass:: unistorage.models.Action
    :members:

.. automodule:: unistorage.models
    :members:
    :inherited-members:
    :show-inheritance:
    :exclude-members: Action

Example of usage
----------------
.. code-block:: python

    >>> from unistorage import UnistorageClient, Action
    >>> 
    >>> unistorage = UnistorageClient(
    ...     'http://localhost:5000/', '01234567890123456789012345678901')

    >>> with open('/path/to/image.jpg', 'rb') as f:
    ...     image_file = unistorage.upload_file('upchk.jpg', f, type_id='qwerty')

    >>> image_file
    <models.ImageFile object at 0x28adad0>

    >>> with open('/path/to/document.doc', 'rb') as f:
    ...     doc_file = unistorage.upload_file('upchk.doc', f)

    >>> doc_file
    <models.DocFile object at 0x28aac10>

    >>> unistorage.get_zipped('archive.zip', [image_file, doc_file])
    <models.ZipFile object at 0x28b76d0>

    >>> image_file.resize(unistorage, 'crop', 50, 50)
    <models.TemporaryFile object at 0x28aadd0>

    >>> doc_file.convert(unistorage, 'txt')
    <models.PendingFile object at 0x15f0ad0>

    >>> template = unistorage.create_template('image', [
    ...     Action('resize', {'mode': 'keep', 'w': 50, 'h': 50}),
    ...     Action('grayscale')
    ... ])
    <models.Template object at 0x2c13090>

    >>> resized_grayscaled_image = image_file.apply_template(unistorage, template)
    >>> resized_grayscaled_image
    <models.PendingFile object at 0x28adf10>