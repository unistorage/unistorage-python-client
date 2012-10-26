def is_image(mimetype):
    return mimetype.startswith('image')


def is_video(mimetype):
    return mimetype.startswith('video') or mimetype == 'application/ogg'


def is_document(mimetype):
    return mimetype in (
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.oasis.opendocument.text', 'application/pdf', 'application/vnd.pdf',
        'application/x-pdf', 'application/rtf', 'application/x-rtf', 'text/richtext',
        'text/plain', 'text/html')
