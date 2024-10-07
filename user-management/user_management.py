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

import requests
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()


def get_user_descriptor(connection, user_email):
    """Get the user descriptor by email (with pagination)"""
    graph_client = connection.clients.get_graph_client()

    try:
        continuation_token = None
        while True:
            # Query users with pagination token
            users = graph_client.list_users(continuation_token=continuation_token)

            for user in users.graph_users:
                if str.lower(user.principal_name) == user_email or str.lower(user.mail_address) == user_email:
                    return user.descriptor

            # Check if there's more data to fetch
            continuation_token = users.continuation_token
            if not continuation_token:
                break

        print(f"No user found with email: {user_email}")
        return None

    except Exception as err:
        print(f"An error occurred while retrieving user descriptor: {err}")
        return None


def get_user_memberships(connection, user_descriptor):
    """Get all memberships (teams/groups) for a specific user"""
    graph_client = connection.clients.get_graph_client()

    try:
        memberships = graph_client.list_memberships(subject_descriptor=user_descriptor)

        if memberships:
            print(f"Found {len(memberships)} memberships for this user.")
            return memberships
        else:
            print("No memberships found for this user.")
            return []

    except Exception as err:
        print(f"An error occurred while retrieving user memberships: {err}")
        return []


def get_team_details(connection, container_descriptor):
    """Get a team details using a container descriptor"""
    graph_client = connection.clients.get_graph_client()

    try:
        team = graph_client.get_group(container_descriptor)
        return team

    except Exception as err:
        print(f"An error occurred while retrieving team details: {err}")
        return None


def remove_user_from_team(organization, user_descriptor, team_descriptor, personal_access_token):
    """Remove a user from a specific team"""
    try:
        base_url = f"https://vssps.dev.azure.com/{organization}/_apis"
        url = f"{base_url}/graph/memberships/{user_descriptor}/{team_descriptor}?api-version=7.2-preview.1"
        response = requests.delete(url, auth=HTTPBasicAuth('', personal_access_token))
        response.raise_for_status()
        if response.status_code == 200:
            print(f"Successfully removed user from team: {team_descriptor}")

    except Exception as err:
        print(f"An error occurred while removing user from team: {err}")


def get_connection(organization_url, personal_access_token):
    """Authenticate and connect to the Azure DevOps organization using the SDK."""
    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=organization_url, creds=credentials)
    return connection


# CLI entry point
def main():
    """Main function to run the script via CLI."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Azure DevOps User Management Tool")
    parser.add_argument("--organization", required=True, help="Azure DevOps organization name.")
    parser.add_argument("--user_email", required=True, help="The email address of the user.")
    args = parser.parse_args()

    personal_access_token = os.getenv('AZURE_DEVOPS_PAT')
    if not personal_access_token:
        raise EnvironmentError("Please set the AZURE_DEVOPS_PAT environment variable.")

    organization_url = f"https://dev.azure.com/{args.organization}"
    connection = get_connection(organization_url, personal_access_token)

    print(f"Fetching data for user: {args.user_email}")
    user_descriptor = get_user_descriptor(connection, args.user_email)
    if user_descriptor:
        print(f"User descriptor found: {user_descriptor}")
        memberships = get_user_memberships(connection, user_descriptor)

        if memberships:
            teams = []
            for membership in memberships:
                container_descriptor = membership.container_descriptor
                team = get_team_details(connection, container_descriptor)
                if team:
                    teams.append(dict(descriptor=container_descriptor, details=team))
                    print(f"User is a member of team: {team.principal_name}")

            # Ask the user if they want to remove the user from all teams or individually
            all_teams_response = input("Do you want to remove the user from ALL teams? (yes/no): ").strip().lower()
            if all_teams_response == 'yes':
                # Remove the user from all teams
                for team in teams:
                    remove_user_from_team(args.organization, user_descriptor, team['descriptor'], personal_access_token)
            else:
                # Iterate through each team and ask if they should be removed individually
                for team in teams:
                    team_response = input(
                        f"Do you want to remove the user from {team['details'].principal_name}? (yes/no): ").strip().lower()
                    if team_response == 'yes':
                        remove_user_from_team(args.organization, user_descriptor, team['descriptor'], personal_access_token)
                    else:
                        print(f"Skipping removal from {team['details'].principal_name}.")


if __name__ == "__main__":
    main()
