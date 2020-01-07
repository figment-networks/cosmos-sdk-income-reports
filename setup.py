import os
import setuptools

_locals = {}
with open(os.path.join('lib', "_version.py")) as fp:
    exec(fp.read(), None, _locals)
version = _locals["__version__"]

long_description = """
"""

setuptools.setup(
    name='cosmos-sdk-income-reports',
    version=version,
    description="",
    license="MIT",
    long_description=long_description,
    author="Figment Networks Inc.",
    author_email="contact@figment.network",
    url="https://github.com/figment-networks/cosmos-sdk-income-reports",
    install_requires=[
        "requests>=2.22.0,<3.0",
    ],
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "cosmos-sdk-income-reports = lib.cli:main"
        ]
    },
    classifiers=[
    ],
)
