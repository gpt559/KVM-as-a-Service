# Dependency Automation Plan

This plan outlines how to automate dependency updates for the KVM-as-a-Service project using GitHub-native tooling (Dependabot and Actions).

## Objective
Detect dependency updates (Python packages, Docker base images, GitHub Actions), apply them, run tests, and automatically merge if successful.

## 1. Tool Selection: GitHub Dependabot
Dependabot is the industry standard for this on GitHub. It is integrated directly into the platform and supports all ecosystems used in this project.

- **Detection**: Dependabot scans manifests (`requirements.txt`, `pyproject.toml`, `Dockerfile`, `.github/workflows`) on a schedule.
- **Update**: It creates a Pull Request with the version bump and release notes.
- **Testing**: Your existing `CI` workflow (`.github/workflows/ci.yml`) will automatically trigger on these PRs.
- **Merging**: A new "Auto-Merge" workflow will be created to merge the PRs if CI passes.

## 2. Configuration (`dependabot.yml`)

We will create `.github/dependabot.yml` with the following configuration:

| Ecosystem | Target File(s) | Schedule |
| :--- | :--- | :--- |
| **pip** | `requirements.txt`, `pyproject.toml` | Weekly |
| **docker** | `Dockerfile` | Weekly |
| **github-actions** | `.github/workflows/ci.yml` | Weekly |

*Note: We can set the schedule to `daily` if preferred, but `weekly` reduces noise.*

## 3. Auto-Merge Workflow

To fulfill the "if no issue, commit" requirement, we need to automate the merging of Dependabot PRs. GitHub does not do this by default for security reasons.

We will create a new workflow `.github/workflows/dependabot-auto-merge.yml` that:
1.  Triggers when a Pull Request is opened by Dependabot.
2.  Fetches metadata to ensure it's a minor/patch update (optional safety check) or just trusts CI.
3.  Approves the PR (GitHub requires approval for PRs in some settings).
4.  Enables GitHub's "Auto-Merge" feature for the PR.

**Prerequisites:**
You (the user) must enable "Allow auto-merge" in the repository settings:
`Settings` -> `General` -> `Pull Requests` -> `Allow auto-merge`.

## 4. Addressing "Older version of pip"

The user noted an older version of pip. This can be addressed in two ways:
1.  **Explicit Upgrade**: Add `RUN pip install --upgrade pip` in the `Dockerfile`.
2.  **Base Image Update**: Dependabot will update `FROM python:3.12-slim` to newer digests which contain newer pip versions.

We will proceed with **Option 1** as it ensures the latest pip is always used during the build, regardless of the base image age.

## 5. Implementation Steps

1.  **Create `.github/dependabot.yml`**: Define the update rules.
2.  **Create `.github/workflows/dependabot-auto-merge.yml`**: Handle the "commit/merge" logic.
3.  **Update `Dockerfile`**: Add the explicit pip upgrade command.
4.  **Update `Dockerfile`**: Move `uv` version to an argument or ensure it's tracked (Dependabot doesn't easily update `RUN pip install uv==x.x.x`, so we might move this to `requirements.txt` or just leave it for manual updates for now, as it's a build tool).

## 6. Verification
After implementation, Dependabot will run its initial scan (usually immediate or within minutes). It will likely open PRs for any outdated dependencies. The new workflow will then trigger, and if tests pass, the PRs will be merged.
