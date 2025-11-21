#!/usr/bin/env python3
import os
import json
import subprocess

# Read the release notes
with open('RELEASE_NOTES_v1.0.0.md', 'r') as f:
    release_notes = f.read()

# Create release data
release_data = {
    "tag_name": "v1.0.0",
    "target_commitish": "main",
    "name": "v1.0.0 - Stable Release: AI Day Trading Bot",
    "body": release_notes,
    "draft": False,
    "prerelease": False
}

# Get the repo info
repo_info = subprocess.check_output(['git', 'remote', 'get-url', 'origin']).decode().strip()
# Extract owner/repo from git@github.com:owner/repo.git or https://github.com/owner/repo.git
if 'github.com' in repo_info:
    if repo_info.startswith('git@'):
        repo_path = repo_info.split(':')[1].replace('.git', '')
    else:
        repo_path = repo_info.split('github.com/')[1].replace('.git', '')
    
    owner, repo = repo_path.split('/')
    
    print(f"Creating release for {owner}/{repo}...")
    print(f"Tag: {release_data['tag_name']}")
    print(f"Title: {release_data['name']}")
    
    # Use curl to create the release via GitHub API
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    
    # Save to temp file
    with open('/tmp/release_data.json', 'w') as f:
        json.dump(release_data, f)
    
    print(f"\nAPI URL: {api_url}")
    print("\nTo create the release, run:")
    print(f"curl -X POST -H 'Accept: application/vnd.github+json' \\")
    print(f"  -H 'Authorization: Bearer YOUR_GITHUB_TOKEN' \\")
    print(f"  {api_url} \\")
    print(f"  -d @/tmp/release_data.json")
    print("\nOr visit: https://github.com/{owner}/{repo}/releases/new?tag=v1.0.0")
else:
    print("Could not determine GitHub repository")
