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

Example of usage
----------------
.. code-block:: python

    import time
    from pprint import pprint

    from unistorage import UnistorageClient


    # Create Unistorage client
    unistorage = UnistorageClient(
    	'http://localhost:5000/', '3932da55c30740852fd2ba22dd59a382')

    # Create template: resize and then grayscale
    template_uri = unistorage.create_template('image', [
        ('resize', {'mode': 'keep', 'w': 50}),
        ('grayscale', {})
    ])

    # Upload file
    with open('/path/to/upchk.gif', 'rb') as f:
    	file_uri = unistorage.upload_file('upchk.gif', f, type_id='qwerty')
    pprint(unistorage.get(file_uri))

    # Apply template to the file
    modified_file_uri = unistorage.apply_template(file_uri, template_uri)

    # See that template has been enqueued
    assert unistorage.get(modified_file_uri)['status'] == 'wait'

    # Wait some time
    time.sleep(5)

    response = unistorage.get(modified_file_uri)

    # See that status has changed to 'ok'
    assert response['status'] == 'ok'
    # And template was applied
    assert response['data']['extra']['width'] == 50
    pprint(response)

    # Create archive that contains both original and modified file
    archive_uri = unistorage.create_archive('images.zip', [
        file_uri,
        modified_file_uri
    ])
    pprint(unistorage.get(archive_uri))
