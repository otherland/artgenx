import requests

def create_project_to_cloudflare(api_token, account_identifier, repo_name):
    base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_identifier}/pages/projects"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}",
        "X-Auth-Email": "YOUR_CLOUDFLARE_EMAIL",  # Replace with your Cloudflare email
    }

    data = {
        "build_config": {
            "build_command": "hugo",
            "destination_dir": "public",
            "root_dir": "",
        },
        'source': {'type': 'github', 'config': {'owner': 'otherland', 'repo_name': repo_name, 'production_branch': 'master', 'pr_comments_enabled': True, 'deployments_enabled': True, 'production_deployments_enabled': True, 'preview_deployment_setting': 'all', 'preview_branch_includes': ['*'], 'preview_branch_excludes': []}},
        "name": repo_name,
        "production_branch": "master"
    }

    try:
        response = requests.post(base_url, headers=headers, json=data)
        response_data = response.json()

        if response.status_code == 200:
            print("Project creation successful!")
            print(f"{response_data}")
        else:
            print(f"Project creation failed: {response_data}")
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")

def deploy_project_to_cloudflare(api_token, account_identifier, project_name):
    base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_identifier}/pages/projects/{project_name}/deployments"

    headers = {
        "Content-Type": "multipart/form-data",
        "Authorization": f"Bearer {api_token}",
    }

    data = {
        'branch' : 'master'
    }

    try:
        response = requests.post(base_url, headers=headers, data=data)
        response_data = response.json()

        if response.status_code == 200:
            print("Deployment initiated successfully!")
        else:
            print(f"Deployment initiation failed: {response_data}")
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")

def deploy_project(project_name):
    # Set your Cloudflare API Token, Account ID, and Project Name here
    CLOUDFLARE_API = "uTdfhnltZNz-nVmsz62nrzeRpracplXHEehju9ee"
    CLOUDFLARE_ACCOUNT_ID = "1d0a91a3fb595e00f275d0cd1215a636"

    create_project_to_cloudflare(CLOUDFLARE_API, CLOUDFLARE_ACCOUNT_ID, project_name)
    deploy_project_to_cloudflare(CLOUDFLARE_API, CLOUDFLARE_ACCOUNT_ID, project_name)
