import json
import os
import urllib.request
import urllib.error

USERNAME = "Bangkah"
TOKEN = os.environ.get("GH_TOKEN")


def github_api(endpoint):
    """Fetch data from GitHub REST API."""

    if not TOKEN:
        raise RuntimeError("GH_TOKEN environment variable is not set.")

    url = f"https://api.github.com{endpoint}"

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Bangkah-GitHub-Dashboard",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")

        raise RuntimeError(
            f"GitHub API request failed: "
            f"HTTP {error.code}\n{body}"
        ) from error


def main():
    print("========================================")
    print("   GitHub Personal Dashboard Updater")
    print("========================================")
    print()

    print(f"Fetching GitHub profile for @{USERNAME}...")

    user = github_api(f"/users/{USERNAME}")

    print()
    print("=== PROFILE ===")
    print(f"Username:      {user['login']}")
    print(f"Name:          {user.get('name') or '-'}")
    print(f"Followers:     {user['followers']}")
    print(f"Following:     {user['following']}")
    print(f"Public repos:  {user['public_repos']}")
    print(f"Public gists:  {user['public_gists']}")
    print(f"Account type:  {user['type']}")
    print(f"Created:       {user['created_at']}")
    print(f"Updated:       {user['updated_at']}")

    print()
    print("GitHub API connection successful.")
    print("Dashboard updater finished successfully.")


if __name__ == "__main__":
    main()
