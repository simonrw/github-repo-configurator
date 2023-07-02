from __future__ import annotations
import os
import json
import re
from typing import TypedDict, Optional

import requests
import yaml


MATRIX_PLACEHOLDER_RE = re.compile(r"\$\{\{\s*matrix\.(?P<name>\w+)\s*\}\}")


class RemoteWorkflowFile(TypedDict):
    name: str
    download_url: str


class Strategy(TypedDict):
    matrix: Optional[dict[str, list[str]]]


class JobDefinition(TypedDict):
    name: str
    strategy: Optional[Strategy]


class WorkflowDefinition(TypedDict):
    jobs: dict[str, JobDefinition]


if __name__ == "__main__":
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {os.environ['GITHUB_ACCESS_TOKEN']}"
    session.headers["X-GitHub-Api-Version"] = "2022-11-28"

    owner = "simonrw"
    repo = "rynamodb"

    # get contents of workflows
    r = session.get(f"https://api.github.com/repos/{owner}/{repo}/contents/.github/workflows")
    r.raise_for_status()
    workflow_meta: list[RemoteWorkflowFile] = r.json()

    names = []
    for workflow in workflow_meta:
        name = workflow["name"]
        download_url = workflow["download_url"]

        # download the file and parse the contents
        r = requests.get(download_url)
        r.raise_for_status()
        body = r.text
        workflow_definition: WorkflowDefinition = yaml.safe_load(body)
        # print(json.dumps(workflow_definition, indent=2))
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
