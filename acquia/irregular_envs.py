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

import subprocess
import json
import os
from dotenv import load_dotenv

# Load API key and secret from .env file
load_dotenv()

ACQUIA_API_KEY = os.getenv("ACQUIA_API_KEY")
ACQUIA_API_SECRET = os.getenv("ACQUIA_API_SECRET")


def run_acquia_command(command):
    """Run an Acquia CLI command and return the output"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=3600)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}\n{e.stderr}")
        return None


def authenticate():
    """Authenticate using the Acquia API key and secret"""
    login_command = [
        "acli", "auth:login",
        "--key", ACQUIA_API_KEY,
        "--secret", ACQUIA_API_SECRET,
        "--no-interaction"
    ]
    return run_acquia_command(login_command)


def get_applications():
    """Get a list of applications from Acquia"""
    command = ["acli", "api:application:list"]
    output = run_acquia_command(command)
    return json.loads(output) if output else []


def get_environments(application_uuid):
    """Get a list of environments for a specific application"""
    command = ["acli", "api:application:environment-list", application_uuid]
    output = run_acquia_command(command)
    return json.loads(output) if output else []


def main():
    """Main entry point of the script"""
    # Authenticate
    print("Authenticating...")
    if authenticate():
        print("Authenticated successfully!")

        # Get applications
        applications = get_applications()
        if applications:
            print(f"Found {len(applications)} applications.\n")
            for app in applications:
                environments = get_environments(app.get("uuid"))

                # Collect environment names
                environment_names = [env.get("name") for env in environments]

                # Check if "stage" or "prod" is not in the environment list
                if "stage" not in environment_names or "prod" not in environment_names:
                    print(f"Application: {app['name']} ({app['uuid']})")
                    print(f"Environments: {', '.join([f"{env.get('label')} ({env.get('name')})" for env in environments])}\n")
                else:
                    print(f"Skipping application: {app['name']}. Environments match.")
        else:
            print("No applications found or failed to fetch applications.")
    else:
        print("Authentication failed.")


if __name__ == "__main__":
    main()
