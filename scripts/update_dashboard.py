import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone


USERNAME = "Bangkah"
README_FILE = "README.md"

START_MARKER = "<!-- DASHBOARD:START -->"
END_MARKER = "<!-- DASHBOARD:END -->"


def github_api(endpoint):
    token = os.environ.get("GH_TOKEN")

    if not token:
        raise RuntimeError("GH_TOKEN environment variable is not set.")

    url = f"https://api.github.com{endpoint}"

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
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
            f"GitHub API request failed: HTTP {error.code}\n{body}"
        ) from error


def get_all_repositories():
    repositories = []
    page = 1

    while True:
        data = github_api(
            f"/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&sort=updated"
        )

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repositories


def calculate_languages(repositories):
    language_bytes = {}

    for repo in repositories:
        languages_url = repo.get("languages_url")

        if not languages_url:
            continue

        try:
            request = urllib.request.Request(
                languages_url,
                headers={
                    "Authorization": f"Bearer {os.environ.get('GH_TOKEN')}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": "Bangkah-GitHub-Dashboard",
                },
            )

            with urllib.request.urlopen(request) as response:
                languages = json.load(response)

        except Exception as error:
            print(
                f"Warning: failed to fetch languages for "
                f"{repo.get('full_name')}: {error}"
            )
            continue

        for language, byte_count in languages.items():
            language_bytes[language] = (
                language_bytes.get(language, 0) + byte_count
            )

    total_bytes = sum(language_bytes.values())

    if total_bytes == 0:
        return []

    results = []

    for language, byte_count in language_bytes.items():
        percentage = (byte_count / total_bytes) * 100

        results.append(
            {
                "language": language,
                "bytes": byte_count,
                "percentage": percentage,
            }
        )

    results.sort(
        key=lambda item: item["bytes"],
        reverse=True,
    )

    return results


def format_date(date_string):
    if not date_string:
        return "-"

    try:
        date = datetime.fromisoformat(
            date_string.replace("Z", "+00:00")
        )

        return date.strftime("%Y-%m-%d")

    except Exception:
        return date_string[:10]


def build_dashboard(user, repositories, languages):
    public_repositories = [
        repo for repo in repositories
        if not repo.get("private", False)
    ]

    original_repositories = [
        repo for repo in repositories
        if not repo.get("fork", False)
    ]

    forked_repositories = [
        repo for repo in repositories
        if repo.get("fork", False)
    ]

    archived_repositories = [
        repo for repo in repositories
        if repo.get("archived", False)
    ]

    total_stars = sum(
        repo.get("stargazers_count", 0)
        for repo in repositories
    )

    total_forks = sum(
        repo.get("forks_count", 0)
        for repo in repositories
    )

    total_watchers = sum(
        repo.get("watchers_count", 0)
        for repo in repositories
    )

    repositories_with_stars = sum(
        1
        for repo in repositories
        if repo.get("stargazers_count", 0) > 0
    )

    repositories_with_forks = sum(
        1
        for repo in repositories
        if repo.get("forks_count", 0) > 0
    )

    top_repositories = sorted(
        repositories,
        key=lambda repo: (
            repo.get("stargazers_count", 0),
            repo.get("forks_count", 0),
        ),
        reverse=True,
    )[:10]

    active_repositories = sorted(
        repositories,
        key=lambda repo: repo.get("pushed_at") or "",
        reverse=True,
    )[:10]

    now = datetime.now(timezone.utc)

    lines = []

    lines.append("## 👤 Profile")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Username | `{user['login']}` |")
    lines.append(f"| Name | {user.get('name') or '-'} |")
    lines.append(f"| Followers | {user.get('followers', 0):,} |")
    lines.append(f"| Following | {user.get('following', 0):,} |")
    lines.append(
        f"| Account Created | {format_date(user.get('created_at'))} |"
    )
    lines.append(
        f"| Public Repositories | {user.get('public_repos', 0):,} |"
    )
    lines.append(
        f"| Public Gists | {user.get('public_gists', 0):,} |"
    )
    lines.append(
        f"| Account Type | {user.get('type', '-')} |"
    )

    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 📦 Repositories")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(
        f"| Total Repositories | {len(repositories):,} |"
    )
    lines.append(
        f"| Original Repositories | {len(original_repositories):,} |"
    )
    lines.append(
        f"| Forked Repositories | {len(forked_repositories):,} |"
    )
    lines.append(
        f"| Archived Repositories | {len(archived_repositories):,} |"
    )
    lines.append(
        f"| Public Repositories | {len(public_repositories):,} |"
    )
    lines.append(
        f"| Total Stars Received | {total_stars:,} |"
    )
    lines.append(
        f"| Total Forks Received | {total_forks:,} |"
    )
    lines.append(
        f"| Total Watchers | {total_watchers:,} |"
    )
    lines.append(
        f"| Repositories with Stars | {repositories_with_stars:,} |"
    )
    lines.append(
        f"| Repositories with Forks | {repositories_with_forks:,} |"
    )

    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## ⭐ Repository Impact")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Stars Received | {total_stars:,} |")
    lines.append(f"| Forks Received | {total_forks:,} |")
    lines.append(f"| Watchers | {total_watchers:,} |")
    lines.append(
        f"| Repositories with Stars | {repositories_with_stars:,} |"
    )
    lines.append(
        f"| Repositories with Forks | {repositories_with_forks:,} |"
    )

    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 🏆 Top Repositories")
    lines.append("")
    lines.append("| # | Repository | Stars | Forks | Issues | Updated |")
    lines.append("|---:|---|---:|---:|---:|---|")

    for index, repo in enumerate(top_repositories, start=1):
        lines.append(
            f"| {index} "
            f"| [{repo['name']}]({repo['html_url']}) "
            f"| {repo.get('stargazers_count', 0):,} "
            f"| {repo.get('forks_count', 0):,} "
            f"| {repo.get('open_issues_count', 0):,} "
            f"| {format_date(repo.get('updated_at'))} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 🔥 Most Recently Active Repositories")
    lines.append("")
    lines.append(
        "| # | Repository | Stars | Forks | Last Activity |"
    )
    lines.append("|---:|---|---:|---:|---|")

    for index, repo in enumerate(active_repositories, start=1):
        lines.append(
            f"| {index} "
            f"| [{repo['name']}]({repo['html_url']}) "
            f"| {repo.get('stargazers_count', 0):,} "
            f"| {repo.get('forks_count', 0):,} "
            f"| {format_date(repo.get('pushed_at'))} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 🧑‍💻 Languages")
    lines.append("")
    lines.append("| Language | Percentage |")
    lines.append("|---|---:|")

    for item in languages[:15]:
        lines.append(
            f"| {item['language']} | "
            f"{item['percentage']:.2f}% |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## ⚙️ Dashboard")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("|---|---|")
    lines.append(f"| GitHub Account | `@{USERNAME}` |")
    lines.append("| Data Source | GitHub REST API |")
    lines.append(
        f"| Last Synchronization | "
        f"{now.strftime('%Y-%m-%d %H:%M:%S UTC')} |"
    )
    lines.append("| Dashboard Version | 1.0 |")

    return "\n".join(lines)


def update_readme(dashboard):
    if not os.path.exists(README_FILE):
        raise RuntimeError("README.md not found.")

    with open(README_FILE, "r", encoding="utf-8") as file:
        readme = file.read()

    if START_MARKER not in readme:
        raise RuntimeError(
            f"Missing marker: {START_MARKER}"
        )

    if END_MARKER not in readme:
        raise RuntimeError(
            f"Missing marker: {END_MARKER}"
        )

    start = readme.index(START_MARKER)
    end = readme.index(END_MARKER) + len(END_MARKER)

    generated = (
        START_MARKER
        + "\n\n"
        + dashboard
        + "\n\n"
        + END_MARKER
    )

    updated_readme = (
        readme[:start]
        + generated
        + readme[end:]
    )

    with open(
        README_FILE,
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        file.write(updated_readme)


def main():
    print("========================================")
    print("   GitHub Personal Dashboard Updater")
    print("========================================")
    print()

    print(f"Fetching GitHub profile for @{USERNAME}...")
    user = github_api(f"/users/{USERNAME}")

    print(
        f"Profile loaded: "
        f"{user['login']} "
        f"({user.get('followers', 0)} followers)"
    )

    print()
    print("Fetching repositories...")

    repositories = get_all_repositories()

    print(
        f"Repositories loaded: {len(repositories)}"
    )

    print()
    print("Calculating language statistics...")

    languages = calculate_languages(repositories)

    print(
        f"Languages detected: {len(languages)}"
    )

    print()
    print("Generating dashboard...")

    dashboard = build_dashboard(
        user,
        repositories,
        languages,
    )

    print()
    print("Updating README.md...")

    update_readme(dashboard)

    print()
    print("========================================")
    print("Dashboard update completed successfully.")
    print("========================================")


if __name__ == "__main__":
    main()
