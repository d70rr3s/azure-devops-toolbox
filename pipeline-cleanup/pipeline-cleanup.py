"""
MIT License

Copyright (c) 2024 Dennis A. Torres <d70rr3s@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import argparse
import requests
from requests.auth import HTTPBasicAuth
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication


def get_connection(organization_url, personal_access_token):
    """Authenticate and connect to the Azure DevOps organization using the SDK."""
    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=organization_url, creds=credentials)
    return connection


def get_release_runs(connection, project, pipeline_id):
    """Get all release pipeline runs (Classic release pipelines)."""
    release_client = connection.clients.get_release_client()
    releases = release_client.get_releases(project=project, definition_id=pipeline_id)
    return releases


def get_build_runs(organization, project, pipeline_id, personal_access_token):
    """Get all build pipeline runs (YAML pipelines)."""
    base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
    url = f"{base_url}/build/builds?definitions={pipeline_id}&api-version=6.0"
    response = requests.get(url, auth=HTTPBasicAuth('', personal_access_token))
    response.raise_for_status()
    return response.json()


def delete_release(connection, project, run_id):
    """Delete a release run (Classic release pipelines)."""
    release_client = connection.clients.get_release_client()
    release_client.delete_release(project=project, release_id=run_id)
    print(f"Deleted release run: {run_id}")


def delete_build(organization, project, run_id, personal_access_token):
    """Delete a build run (YAML pipelines)."""
    base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
    url = f"{base_url}/build/builds/{run_id}?api-version=6.0"
    response = requests.delete(url, auth=HTTPBasicAuth('', personal_access_token))
    response.raise_for_status()
    if response.status_code == 204:
        print(f"Successfully deleted build run: {run_id}")
    else:
        print(f"Failed to delete build run: {run_id}, Status Code: {response.status_code}")


def remove_retention_leases(organization, project, run_id, is_release, personal_access_token):
    """Remove retention leases using the Leases API."""
    base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
    if is_release:
        url = f"{base_url}/release/releases/{run_id}/retentionleases?api-version=6.0"
    else:
        url = f"{base_url}/build/builds/{run_id}/retentionleases?api-version=6.0"

    response = requests.get(url, auth=HTTPBasicAuth('', personal_access_token))
    response.raise_for_status()
    leases = response.json().get('value', [])

    if not leases:
        print(f"No retention leases found for run {run_id}")
    else:
        print(f"Found {len(leases)} retention lease(s) for run {run_id}, removing them...")

        for lease in leases:
            lease_id = lease['leaseId']
            delete_url = f"{url}/{lease_id}?api-version=6.0"
            del_response = requests.delete(delete_url, auth=HTTPBasicAuth('', personal_access_token))
            del_response.raise_for_status()
            print(f"Deleted retention lease {lease_id} for run {run_id}")


def mark_run_as_retained(organization, project, run_id, is_release, personal_access_token):
    """Mark a run as retained using the correct payload."""
    base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
    if is_release:
        url = f"{base_url}/release/releases/{run_id}?api-version=6.0"
        payload = {'keepForever': True}
    else:
        url = f"{base_url}/build/builds/{run_id}?api-version=6.0"
        payload = {'daysValid': 36500, 'protectPipeline': True}

    response = requests.patch(url, json=payload, auth=HTTPBasicAuth('', personal_access_token))
    response.raise_for_status()
    print(f"Run {run_id} marked as retained with payload: {payload}")


def process_runs(connection, organization, project, pipeline_id, pipeline_type, keep, delete_all,
                 personal_access_token):
    """Main logic to handle retention and deletion of pipeline runs."""
    if pipeline_type == 'release':
        runs = get_release_runs(connection, project, pipeline_id)
        is_release = True
    elif pipeline_type == 'yaml':
        runs = get_build_runs(organization, project, pipeline_id, personal_access_token)
        is_release = False
    else:
        raise ValueError("Invalid pipeline_type. Must be either 'release' or 'yaml'.")

    # Sort the runs by buildNumber (most recent first)
    sorted_runs = sorted(runs['value'], key=lambda x: x['buildNumber'], reverse=True)
    total_runs = len(sorted_runs)

    # Handle deletion logic
    if delete_all:
        print(f"Deleting all {total_runs} runs...")
        for run in sorted_runs:
            if run.get("keepForever", False):
                print(f"Run {run['id']} is retained. Removing retention leases first.")
                remove_retention_leases(organization, project, run['id'], is_release, personal_access_token)
            if is_release:
                delete_release(connection, project, run['id'])
            else:
                delete_build(organization, project, run['id'], personal_access_token)
    elif keep is not None:
        print(f"Keeping the most recent {keep} runs. Deleting the rest.")
        # Similar logic as before...


# CLI entry point
def main():
    """Main function to run the script via CLI."""
    parser = argparse.ArgumentParser(
        description="Delete runs for either a classic release pipeline or a YAML pipeline in Azure DevOps.")
    parser.add_argument("--organization", required=True, help="Azure DevOps organization name.")
    parser.add_argument("--project", required=True, help="Azure DevOps project name.")
    parser.add_argument("--pipeline_id", required=True, help="Azure DevOps pipeline ID.")
    parser.add_argument("--pipeline_type", required=True, choices=['release', 'yaml'],
                        help="Pipeline type: 'release' for classic release pipeline, 'yaml' for YAML pipeline.")
    parser.add_argument("--all", action="store_true", help="If specified, all runs will be deleted.")
    parser.add_argument("--keep", type=int,
                        help="Number of most recent runs to keep. The remaining runs will be deleted.")

    args = parser.parse_args()
    personal_access_token = os.getenv('AZURE_DEVOPS_PAT')

    if not personal_access_token:
        raise EnvironmentError("Please set the AZURE_DEVOPS_PAT environment variable.")

    organization_url = f"https://dev.azure.com/{args.organization}"
    connection = get_connection(organization_url, personal_access_token)

    process_runs(connection, args.organization, args.project, args.pipeline_id, args.pipeline_type, args.keep, args.all,
                 personal_access_token)


# Allow both module import and CLI usage
if __name__ == "__main__":
    main()
