import os
import setuptools

# Path to directory containing setup.py
here = os.path.abspath(os.path.dirname(__file__))


def get_version():
    # Load the package's __version__.py module as a dictionary.
    about = {}
    with open(os.path.join(here, 'pytype', '__version__.py')) as f:
        exec(f.read(), about)  # pylint: disable=exec-used
    return about['__version__']


def get_install_requires():
    requires = [
        'pyyaml (>=3.11)',
        'ortools (>=7.1)',
        'humanfriendly (>=4.18)'
    ]
    return requires

def get_long_description():
    with open("README.md", "r") as fh:
        long_description = fh.read()

    return long_description


setuptools.setup(
    name="allocation",
    version="0.5",
    author="Michael Gendelman",
    author_email="genged@gmail.com",
    description="Apps to nodes allocator",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/genged/allocator",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'allocator = allocation.cli:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)