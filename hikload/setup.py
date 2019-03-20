from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='hikload',
    version='0.2dev',
    packages=['hikload', ],
    license='MIT Licence',
    author="Stoica Tedy",
    author_email="stoicatedy@gmail.com",
    description="Auto Download videos from HikVision DVR",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/Tedyst/HikLoad"
)
