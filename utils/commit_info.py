from git import Repo

def get_latest_commit_info(repo_path=".") -> tuple[str, str, str, str]:
    repo = Repo(repo_path)
    commit = repo.head.commit
    
    diff = commit.diff(commit.parents[0])

    lines = []

    for item in diff.iter_change_type('D'):
        lines.append(f"\u001b[2;32m\u001b[1;32m+ {item.b_path}\u001b[0m")
    for item in diff.iter_change_type('M'):
        lines.append(f"\u001b[2;33m\u001b[1;33m± {item.b_path}\u001b[0m")
    for item in diff.iter_change_type('A'):
        lines.append(f"\u001b[2;31m\u001b[1;31m- {item.a_path}\u001b[0m")
    for item in diff.iter_change_type('R'):
        lines.append(f"\u001b[2;36mR {item.b_path} -> {item.a_path}\u001b[0m")

    commit_summary = "```ansi\n" + "\n".join(lines) + "\n```"
    
    return commit.hexsha[:10], commit.message.strip(), commit.author.name, commit_summary