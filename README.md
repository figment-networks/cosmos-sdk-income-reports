# Cosmos-SDK Income Reports

Library & CLI for calculating income reports from Cosmos-SDK-based networks.

Current explicit support:
- Cosmos
- Terra
- Kava

Made with :heart: by<br/>
<a href='https://figment.network'><img alt='Figment Networks' src='http://figment-public-assets.s3.ca-central-1.amazonaws.com/figment-inline.svg' height='32px' align='bottom' /></a>


## Dependencies

- Python 3.6+
- Access to Cosmos-SDK 0.37+ LCD/REST server


## Installation

```
pip install cosmos-sdk-income-reports
```


## Usage

See:

```
cosmos-sdk-income-reports --help
```


## Development

- Install [pyenv](https://github.com/pyenv/pyenv#installation):
    ```
    curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
    ```
    (**Note:** Don't forget to follow instructions to add to bash profile afterwards)

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

- Run directly or install locally:
    ```
    python -m cli --help
    pip install -e . && cosmos-sdk-income-reports --help
    ```

- Build release:
    ```
    python setup.py sdist bdist_wheel --bdist-dir ~/.tmp-bdistwheel
    ```
