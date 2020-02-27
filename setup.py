import os
import setuptools

_locals = {}
with open(os.path.join('csir', '_version.py')) as fp:
    exec(fp.read(), None, _locals)
version = _locals['__version__']

project_root = os.path.dirname(os.path.realpath(__file__))
requirements_path = os.path.join(project_root, 'requirements.txt')
with open(requirements_path) as f: install_requires = f.read().splitlines()

with open(os.path.join(project_root, 'README.md')) as f: readme = f.read()

setuptools.setup(
    name='cosmos-sdk-income-reports',
    version=version,
    description='Cosmos-SDK Income Reports',
    long_description=readme,
    long_description_content_type="text/markdown",
    license='Apache License 2.0',
    author='Figment Networks Inc.',
    author_email='contact@figment.network',
    url='https://github.com/figment-networks/cosmos-sdk-income-reports',
    install_requires=install_requires,
    python_requires='>=3.6',
    packages=setuptools.find_packages(),
    entry_points={'console_scripts': ['cosmos-sdk-income-reports = csir.cli.__main__:main']},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
