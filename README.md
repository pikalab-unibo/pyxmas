# PyXMas

Explainable Multi-Agent Systems in Python, based on [Spade](https://spade-mas.readthedocs.io)

## For users

This project is a work in progress, not yet intended for general purpose usage.

## For developers

### Relevant features

- All your project code into a single main package (`pyxmas/`)
- All your project tests into a single test package (`test/`)
- Unit testing support via [`unittest`](https://docs.python.org/3/library/unittest.html)
- Automatic testing on all branches via GitHub Actions
- Semi-automatic versioning via Git
- Packaging support via [`setuptools`](https://setuptools.pypa.io/en/latest/setuptools.html)
- Automatic release on [PyPi](https://pypi.org/) via GitHub Actions
- Docker image support via `Dockerfile`
- Automatic release on [DockerHub](https://hub.docker.com/) via GitHub Actions
- Support for semi-automatic development environment management via [Pyenv](https://github.com/pyenv/pyenv)
- Automatic dependencies updates via [Renovate](https://docs.renovatebot.com/)
- Automatic conversion of `TODO` comments into GitHub issues via the `alstr/todo-to-issue-action`

### Project structure 

Overview:
```bash
<root directory>
├── pyxmas/                 # main package
│   ├── __init__.py         # python package marker
│   └── __main__.py         # application entry point
├── test/                   # test package (should contain unit tests)
├── .github/                # configuration of GitHub CI
│   ├── scripts/            # contains bash script to be used in CI
│   │   └── retry.sh        # script automating timed retry of release operations
│   └── workflows/          # configuration of GitHub Workflows
│       ├── check.yml       # runs tests on multiple OS and versions of Python
│       ├── deploy.yml      # if check succeeds, and the current branch is one of {main, master, develop}, triggers automatic releas on PyPi
│       └── dockerify.yml   # if deploy succeeds, builds a Docker image and pushes it on DockerHub 
├── MANIFEST.in             # file stating what to include/exclude in releases 
├── LICENSE                 # license file (Apache 2.0 by default)
├── pyproject.toml          # declares build dependencies
├── renovate.json           # configuration of Renovate bot, for automatic dependency updates
├── requirements.txt        # declares development dependencies
├── setup.py                # configuration of the package to be released on Pypi
└── Dockerfile              # configuration of the Docker image to be realsed on Dockerhub
```

### How to do stuff

#### Run your code as an application

This will execute the file `pyxmas/__main__.py`:
```bash
python -m pyxmas 
```

#### Run unit tests

```bash
python -m unittest discover -s test -t .
```

> Tests are automatically run in CI, on all pushes on all branches.
> There, tests are executed on Linux and on multiple Python versions (from `3.8` to `3.9`).

Notice that the testing environment __requires__:
- Docker to be installed in the testing environment
- Docker Compose to be installed in the testing environment (this is commonly included in Docker)
- the Docker daemon to be up and running

#### Restore dev dependencies

```bash
pip install -r requirements.txt
```

#### Release a new version on PyPi

> This paragraph is more understandable if the reader has some background about:
> - [GitFlow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
> - [Conventional Commit](https://www.conventionalcommits.org/)
> - [Semantic Versioning](https://semver.org)

GitHub actions automatically release a new version of `pyxmas` on PyPi whenever commits are pushed on the `main` or `master` branches.

The PyPi package is here: https://pypi.org/project/pyxmas/

Version numbers are computed automatically as [semantic versioning](https://semver.org/) strings of the form `Major.Minor.Patch` where `Major`, `Minor`, and `Patch` are non-negative integers.
