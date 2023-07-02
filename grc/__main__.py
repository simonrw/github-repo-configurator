from __future__ import annotations
import os
import json
import re
from typing import TypedDict, Optional

import requests
import yaml


MATRIX_PLACEHOLDER_RE = re.compile(r"\$\{\{\s*matrix\.(?P<name>\w+)\s*\}\}")


class RemoteWorkflowFile(TypedDict):
    download_url: str


class Strategy(TypedDict):
    matrix: Optional[dict[str, list[str]]]


class JobDefinition(TypedDict):
    name: str
    strategy: Optional[Strategy]


class WorkflowDefinition(TypedDict):
    jobs: dict[str, JobDefinition]


class GitHubClient:
    def __init__(self, token: str):
        session = requests.Session()
        session.headers["Authorization"] = f"Bearer {token}"
        session.headers["X-GitHub-Api-Version"] = "2022-11-28"
        self.session = session

    def get_workflow_metas(self, owner: str, repo: str) -> list[RemoteWorkflowFile]:
        r = self.session.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/.github/workflows"
        )
        r.raise_for_status()
        return r.json()

    def get_workflow_file_contents(self, meta: RemoteWorkflowFile) -> dict:
        download_url = meta["download_url"]

        # download the file and parse the contents
        r = requests.get(download_url)
        r.raise_for_status()
        body = r.text
        return yaml.safe_load(body)


if __name__ == "__main__":
    owner = "simonrw"
    repo = "rynamodb"

    token = os.environ["GITHUB_ACCESS_TOKEN"]
    client = GitHubClient(token)
    workflow_meta = client.get_workflow_metas(owner, repo)

    names = []
    for workflow in workflow_meta:
        workflow_definition = client.get_workflow_file_contents(workflow)
        for job in workflow_definition["jobs"].values():
            # first parse the job strategy matrix
            matrix = job.get("strategy", {}).get("matrix", {})
            job_name = job["name"]

            matrix_match = MATRIX_PLACEHOLDER_RE.search(job_name)
            if matrix_match:
                assert matrix is not None

                matrix_name = matrix_match.group("name")
                for matrix_value in matrix[matrix_name]:
                    substituted_job_name = MATRIX_PLACEHOLDER_RE.sub(matrix_value, job_name)
                    names.append(substituted_job_name)
            else:
                names.append(job_name)

    for name in names:
        print(name)
