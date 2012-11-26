from setuptools import setup


setup(
    name='unistorage',
    version='0.0.1',
    description='Python client for the Unistorage API',
    url='https://github.com/unistorage/unistorage-python-client',

    author='Anton Romanovich',
    author_email='anthony.romanovich@gmail.com',

    packages=['unistorage'],
    install_requires=['requests>=0.14.1', 'decorator>=3.4.0'],
)
