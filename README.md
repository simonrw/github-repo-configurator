# GitHub repository configurator

Configure GitHub repositories in the way I like

## Usage

* set your github API token to the `GITHUB_ACCESS_TOKEN` environment variable
    * scopes: TODO
* run `python -m grc`

## What this tool does

* sets up all checks to be required before pull requests can be merged
* configures merge commit merging strategy
* allows github actions to create and approve pull requests
* allow auto-merge
* sets "Fork pull request workflows from outside collaborators" to "Require approval for first-time contributors who are new to GitHub"
* ...

## Installation

```bash
pip install git+ssh://github.com/simonrw/github-repo-configurator
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```
