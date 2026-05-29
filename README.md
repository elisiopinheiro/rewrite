[![Quality Gate Status](https://sonar.atc-github.azure.cloud.bmw/instance11/api/project_badges/measure?project=4wheels-m_clusters-4wm&metric=alert_status&token=sqb_c0bdade6d153f2f2d064c3f807c3cb8486f9eb11)](https://sonar.atc-github.azure.cloud.bmw/instance11/dashboard?id=4wheels-m_clusters-4wm) [![Coverage](https://sonar.atc-github.azure.cloud.bmw/instance11/api/project_badges/measure?project=4wheels-m_clusters-4wm&metric=coverage&token=sqb_c0bdade6d153f2f2d064c3f807c3cb8486f9eb11)](https://sonar.atc-github.azure.cloud.bmw/instance11/dashboard?id=4wheels-m_clusters-4wm) [![Bugs](https://sonar.atc-github.azure.cloud.bmw/instance11/api/project_badges/measure?project=4wheels-m_clusters-4wm&metric=bugs&token=sqb_c0bdade6d153f2f2d064c3f807c3cb8486f9eb11)](https://sonar.atc-github.azure.cloud.bmw/instance11/dashboard?id=4wheels-m_clusters-4wm) [![Maintainability Rating](https://sonar.atc-github.azure.cloud.bmw/instance11/api/project_badges/measure?project=4wheels-m_clusters-4wm&metric=sqale_rating&token=sqb_c0bdade6d153f2f2d064c3f807c3cb8486f9eb11)](https://sonar.atc-github.azure.cloud.bmw/instance11/dashboard?id=4wheels-m_clusters-4wm)

# 4Wheels Managed Clusters Database

[![Create Client library (OpenApi Generator)](https://atc-github.azure.cloud.bmw/4WHEELS-M/clusters-4wm/actions/workflows/client-lib-creation.yaml/badge.svg)](https://atc-github.azure.cloud.bmw/4WHEELS-M/clusters-4wm/actions/workflows/client-lib-creation.yaml)

## Automated processes (CI)

Upon opening a pull request or committing after opening it:
  * Pre-commit: completed in [status-checks.yaml](.github/workflows/status-checks.yaml). . It features Ruff for linting/formatting
  * Pytest: completed in [status-checks.yaml](.github/workflows/status-checks.yaml)
  * SonarQube: completed in [status-checks.yaml](.github/workflows/status-checks.yaml). Can alternatively be run manually through [on-demand-sonarqube.yaml](.github/workflows/on-demand-sonarqube.yaml)
  * Docker image build & push: completed in [build-push-images-ecr.yaml](.github/workflows/build-push-images-ecr.yaml). After the branch is merged to main, [delete-images-ecr-int.yaml](.github/workflows/delete-images-ecr-int.yaml) is triggered, which causes images related to the now merged test branch to be deleted.
  * [Client Lib](https://atc-github.azure.cloud.bmw/4WHEELS-M/clusters-4wm-client): completed in [client-lib-creation.yaml](.github/workflows/client-lib-creation.yaml). After the branch is merged to main, [client-lib-branch-cleanup.yaml](.github/workflows/client-lib-branch-cleanup.yaml) is triggered, which causes branches related to the now merged test branch to be deleted. Updates the client lib based on source code changes.

Upon merging code:
* Version bumping: in [bump-version.yaml](.github/workflows/bump-version.yaml), automated version bumping that takes into account branch name format and dir structure changes. It uses ['bump-my-version'](https://github.com/callowayproject/bump-my-version) underneath.

## API Development

`cd src`

### Poetry

Install poetry with:  
`pip3 install poetry`

Install python packages with:  
`poetry install`

Enable git pre-commit hook with:  
`poetry run pre-commit install`

### Testing locally

Run local tests with:

`poetry run pytest`

Use `-v` for verbose output and `-s` for terminal output of prints or logging messages.

In order to run integration tests, you need to generate an updated snapshot (with both the schema and the data) of the clusters-4wm database from the int environment via the use of the `clusters4wm_pg_dump.sh` script located in the `utils` folder.

### Helpful commands

Get a bash shell inside your app container:  
`docker-compose exec app /bin/bash`

See all logs:  
`docker-compose logs`

See logs for a particular service, e.g. app.  
`docker-compose logs app` 

Stop and remove containers, networks, images, and volumes.  
`docker-compose down -v`

### Flake8

In VSCode, add the following argument to the python extension settings:  
`"python.linting.flake8Args": ["--config=.flake8"]`

## Application Deployment

The docker image is built automatically on push. If you would like to build it manually, set the required environment variables:

- `PROFILE=<your_aws_profile_name>` (corresponding to the correct ECR account).
- `TAG=<tag>`: the tag associated with the version that is being deployed.
- `VAULT_ROLE_ID` and `VAULT_SECRET_ID`: you can obtain these from secrets repo with `pass isetta/Vault/VAULT_ROLE_ID`

```bash
cd src

aws ecr get-login-password --region eu-central-1 --profile $PROFILE | docker login --username AWS --password-stdin 688376064307.dkr.ecr.eu-central-1.amazonaws.com/clusters-4wm:$TAG
docker buildx build . --secret id=VAULT_ROLE_ID --secret id=VAULT_SECRET_ID --platform=linux/amd64 --tag=688376064307.dkr.ecr.eu-central-1.amazonaws.com/clusters-4wm:$TAG --push
```

Note: `docker build` and `--provenance=false` will only work for later Docker versions (`25.03+`). If needed, remove the `provenance` flag and/or replace `docker build` with `docker buildx build`.

Currently, clusters-4wm will be managed by an Argo-CD app installed into the Shared-Services Cluster (INT/PROD), so whenever a new version is created, update the appropriate `applications.yaml` file ([`int`](https://atc-github.azure.cloud.bmw/4WHEELS-M/shared-services/blob/main/aws/argocd/int/applications.yaml) or [`prod`](https://atc-github.azure.cloud.bmw/4WHEELS-M/shared-services/blob/main/aws/argocd/prod/applications.yaml)).

Using Helm, install the application into the cluster  
```bash
cd charts/clusters-4wm
helm install int . -f values-int.yaml -n clusters-4wm-int --create-namespace
helm install prod . -f values-prod.yaml -n clusters-4wm-prod --create-namespace
```


## Testing 4WM Clusters API with CI/CD integration

To test new code of 4WM Clusters API with CI/CD, change the DNS on values-test.yaml and run the following command on a k8s cluster:

```bash
helm install clusters4wm-test-$USER . -f values-test.yaml 
```

Change the CI/CD 4WM Clusters API URL env variable, to match the new DNS on values-test.yaml, the credentials are the same as the 4WM Clusters API int.

This creates a Postgres database as a Deployment on the cluster and a SVC to connect to it.

## How to Debug

In Visual Studio Code, you can use the debugger in local test and container attach modes.
See the [DEBUGGING.md](./DEBUGGING.md) for full setup and usage.

## Versioning & Tagging Process

This project automates versioning and changelog generation using [Release-Please](https://github.com/googleapis/release-please). The process relies on the [Conventional Commits format](#pull-request-titles) in your Pull Request titles to determine version bumps and generate release notes.

The workflow is as follows:

1.  When a pull request with a conventional commit title (e.g., `feat: ...`, `fix: ...`) is merged into `main`, Release-Please opens a new **Release PR**.
2.  This Release PR contains the proposed version bump and an updated `CHANGELOG.md`.
3.  When the Release PR is merged, Release-Please automatically creates a GitHub release, tags the commit with the new version, and publishes the changelog.

### Pull Request Titles: The Key to Automation

The title of a pull request is critical, as it's the **only thing** `release-please` uses to determine if a new version is needed and what that version should be. Please adhere strictly to the [🔗 Conventional Commits](https://www.conventionalcommits.org/) format.

#### How PR Titles Affect Versioning

-   **Major Release (`!`):** A `!` after the type/scope (e.g., `feat!: drop support for Python 3.7`) triggers a major version bump (e.g., `1.2.3` → `2.0.0`).
-   **Minor Release (`feat`):** A title starting with `feat:` (e.g., `feat: add user profile page`) triggers a minor version bump (e.g., `1.2.3` → `1.3.0`).
-   **Patch Release (`fix`):** A title starting with `fix:` (e.g., `fix: correct typo in error message`) triggers a patch version bump (e.g., `1.2.3` → `1.2.4`).
-   **No Release:** Titles starting with other types (`docs:`, `chore:`, `refactor:`, etc.) will be included in the next release's changelog but **will not** trigger a release on their own.

#### Format

```
type([scope])[!]: description

Examples:
feat: add user authentication
fix(auth): resolve login validation
refactor!: remove deprecated page

Note: The scope is optional but recommended for clarity.
Use ! for breaking changes.
```

**Commit Types:**

- `feat` - New features
- `fix` - Bug fixes
- `docs` - Documentation changes
- `style` - Code formatting & style changes (no logic changes)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks & non-code changes (dependencies, configs)
- `ci` - CI/CD changes
- `perf` - Performance improvements without behavior changes
- `build` - Build system changes
- `revert` - Undo a commit
