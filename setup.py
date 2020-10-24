import pathlib
import re

from setuptools import setup


here = pathlib.Path(__file__).parent
fname = here / "async_timeout" / "__init__.py"


with fname.open() as fp:
    try:
        version = re.findall(r'^__version__ = "([^"]+)"$', fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError("Unable to determine version.")


def read(name):
    fname = here / name
    with fname.open() as f:
        return f.read()


install_requires = [
    "typing_extensions>=3.6.5",
]


setup(
    name="async-timeout",
    version=version,
    description=("Timeout context manager for asyncio programs"),
    long_description="\n\n".join([read("README.rst"), read("CHANGES.rst")]),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP",
        "Framework :: AsyncIO",
    ],
    author="Andrew Svetlov",
    author_email="andrew.svetlov@gmail.com",
    url="https://github.com/aio-libs/async_timeout/",
    license="Apache 2",
    packages=["async_timeout"],
    python_requires=">=3.6",
    install_requires=install_requires,
    include_package_data=True,
)
