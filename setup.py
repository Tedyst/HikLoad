import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="hikload",
    version="1.1.2",
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
    package_data={'hikload': ['MainWindow.ui', 'Startup.ui']},
    packages=find_packages(),
    include_package_data=True,
    install_requires=["tqdm", "ffmpeg-python", "lxml", "requests", "xmler", "PyQt5", "PyQt5-sip"],
    entry_points={
        "console_scripts": [
            "hikload=hikload.__main__:main",
            "hikload-qt=hikload.__main__:main_ui",
        ]
    },
)