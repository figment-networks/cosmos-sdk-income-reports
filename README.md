# Cosmos-SDK Income Reports

Library & CLI for calculating income reports from Cosmos-SDK-based networks.

Current explicit support:
- Cosmos
- Kava
- Terra

Made with :heart: by<br/>
<a href='https://figment.network'><img alt='Figment Networks' src='http://figment-public-assets.s3.ca-central-1.amazonaws.com/figment-inline.svg' height='32px' align='bottom' /></a>


## Overview

This code is not recommended for newer and in-experienced users. It will require prior Python knowledge and knowledge of Cosmos-SDK-based networks and infrastructure.

## Dependencies

- Python 3.6+ + pip
- Access to Cosmos-SDK 0.37+ LCD/REST server


## Installation & Usage

*Note:* Not deployed to PyPI yet. Please clone this repo and see 'Development' instructions instead.

```
pip install cosmos-sdk-income-reports
cosmos-sdk-income-reports --help
```


## Development

- Install [pyenv](https://github.com/pyenv/pyenv#installation)

- Install Python 3.6+:
    ```
    pyenv update
    pyenv install 3.8.2
    ```

- Create & pin virtualenv:
    ```
    pyenv virtualenv 3.8.2 cosmos-sdk-income-reports
    echo cosmos-sdk-income-reports > .python-version
    ```

- Install Python requirements & confirm:
    ```
    pip install --upgrade pip
    python setup.py install
    ```

- Run:
    ```
    python -u -m csir.cli --help
    ```

- Build release:
    ```
    python setup.py sdist bdist_wheel --bdist-dir ~/.tmp-bdistwheel
    ```
