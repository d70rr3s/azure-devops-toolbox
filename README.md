
# Azure DevOps Toolbox

Azure DevOps Toolbox is a Python-based toolset designed to automate various tasks and workflows in Azure DevOps. This toolbox helps streamline processes, manage pipelines, and handle other DevOps-related activities efficiently.

Currently, it includes the following features:

- **Pipeline Cleanup**: A tool to manage and delete retained pipeline runs in Azure DevOps.
- **User Management**: A tool to manage Azure DevOps user memberships.

## Features

### 1. Pipeline Cleanup

The `pipeline-cleanup` tool allows you to delete pipeline runs from both classic release pipelines and YAML-based pipelines in Azure DevOps. You can retain a specific number of recent runs or delete all runs based on your requirements.

#### Usage

You can run `pipeline-cleanup` via the command line after setting up your Azure DevOps Personal Access Token (PAT).

##### Command Line Interface (CLI)

```bash
pipeline-cleanup --organization <organization_name> --project <project_name> --pipeline_id <pipeline_id> --pipeline_type <release|yaml> [--all | --keep <N>]
```

#### Parameters:
- `--organization`: Your Azure DevOps organization name.
- `--project`: The project name within the Azure DevOps organization.
- `--pipeline_id`: The ID of the pipeline whose runs you want to manage.
- `--pipeline_type`: Specify whether the pipeline is a `release` or `yaml` pipeline.
- `--all`: If specified, all runs will be deleted.
- `--keep <N>`: The number of most recent pipeline runs to keep. All older runs will be deleted.

#### Example:

```bash
pipeline-cleanup --organization myOrg --project myProject --pipeline_id 1234 --pipeline_type yaml --keep 5
```

In the example above, the tool will retain the most recent 5 pipeline runs and delete the rest.

### 2. User Management

The `user-management` tool allows you to retrieve a user's memberships (teams/groups) in Azure DevOps by their email address.

#### Usage:

```bash
user-management --organization <organization_name> --user_email <user_email>
```

#### Parameters:
- `--organization`: Your Azure DevOps organization name.
- `--user_email`: The email address of the user whose memberships you want to retrieve.

#### Example:

```bash
user-management --organization myOrg --user_email user@example.com
```

This example retrieves all team memberships associated with the specified user email.

## Installation

### Prerequisites

- Python 3.6 or higher
- `pip` for Python package management
- Azure DevOps Personal Access Token (PAT) with appropriate permissions

### Setting up

1. Clone the repository:

    ```bash
    git clone https://github.com/d70rr3s/azure-devops-toolbox.git
    cd azure-devops-toolbox
    ```

2. Install the required dependencies:

    ```bash
    pip install -e .
    ```

3. Set up your Azure DevOps Personal Access Token (PAT) as an environment variable:

    ```bash
    export AZURE_DEVOPS_PAT='your_personal_access_token'
    ```

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.

## Contributions

Contributions, issues, and feature requests are welcome! Feel free to submit a pull request or open an issue on the [GitHub repository](https://github.com/d70rr3s/azure-devops-toolbox).

## Author

- **Dennis A. Torres** - [d70rr3s](https://github.com/d70rr3s)

---

**Note**: This toolbox is actively under development. More features will be added over time to help automate Azure DevOps workflows.
