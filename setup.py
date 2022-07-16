import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="hikload",
    version="1.1.4",
    description="Download videos from a HikVision DVR/NVR",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Tedyst/HikLoad",
    author="Stoica Tedy",
    author_email="stoicatedy@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=["certifi==2022.6.15; python_full_version >= '3.6.0'", "charset-normalizer==2.1.0; python_full_version >= '3.6.0'", 'ffmpeg-python==0.2.0', "future==0.18.2; python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'", "idna==3.3; python_version >= '3.5'", 'lxml==4.9.1', 'pefile==2022.5.30', 'pyqt5==5.15.7', 'pyqt5-qt5==5.15.2', "pyqt5-sip==12.11.0; python_version >= '3.7'", 'pywin32-ctypes==0.2.0', 'requests==2.28.1', 'tqdm==4.64.0', "urllib3==1.26.10; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4, 3.5' and python_version < '4'", 'xmler==0.2.0'
],
    entry_points={
        "console_scripts": [
            "hikload=hikload.__main__:main",
            "hikload-qt=hikload.__main__:main_ui",
        ]
    },
)