from __future__ import annotations
import os
import json
import re
from typing import Any, TypedDict, Optional

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


class Repository(TypedDict):
    default_branch: str


class Check(TypedDict):
    context: str


class SetBranchProtectionPayload(TypedDict):
    strict: bool
    checks: list[Check]


class GitHubClientFactory:
    def __init__(self, token: str):
        session = requests.Session()
        session.headers["Authorization"] = f"Bearer {token}"
        session.headers["X-GitHub-Api-Version"] = "2022-11-28"
        session.headers["Accept"] = "application/vnd.github+json"
        self.session = session

    def repo(self, owner: str, repo: str) -> GitHubClient:
        return GitHubClient(self.session, owner, repo)


class GitHubClient:
    def __init__(self, session: requests.Session, owner: str, repo: str):
        self.session = session
        self.owner = owner
        self.repo = repo

    def get_repository(self) -> Repository:
        r = self.session.get(self._url(""))
        self._check_for_errors(r)
        return r.json()

    def get_workflow_metas(self) -> list[RemoteWorkflowFile]:
        r = self.session.get(self._url("/contents/.github/workflows"))
        self._check_for_errors(r)
        return r.json()

    def get_workflow_file_contents(self, meta: RemoteWorkflowFile) -> dict:
        download_url = meta["download_url"]

        # download the file and parse the contents
        r = requests.get(download_url)
        self._check_for_errors(r)
        body = r.text
        return yaml.safe_load(body)

    def get_branch_protection(self, branch: str) -> dict:
        r = self.session.get(self._url(f"/branches/{branch}/protection"))
        self._check_for_errors(r)
        return r.json()

    def get_default_branch(self) -> str:
        return self.get_repository()["default_branch"]

    def set_branch_protection(self, checks: list[str]):
        branch_name = self.get_default_branch()
        payload: SetBranchProtectionPayload = {
            "strict": False,
            "checks": [{"context": check} for check in checks],
        }
        r = self.session.patch(
            self._url(f"/branches/{branch_name}/protection/required_status_checks"),
            json=payload,
        )
        self._check_for_errors(r)

    def _check_for_errors(self, response: requests.Response):
        if response.status_code >= 300:
            breakpoint()

    def _url(self, stub: str) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}{stub}"


def jprint(o: Any):
    print(json.dumps(o, indent=2))


if __name__ == "__main__":
    owner = "simonrw"
    repo = "rynamodb"

    token = os.environ["GITHUB_ACCESS_TOKEN"]
    client = GitHubClientFactory(token).repo(owner, repo)

    workflow_meta = client.get_workflow_metas()

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

    client.set_branch_protection(names)
