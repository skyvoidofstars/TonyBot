from git import Repo
from utils.ANSI import Colors


def get_latest_commit_info(repo_path='.') -> tuple[str, str, str, str]:
    repo = Repo(repo_path)
    commit = repo.head.commit

    diff = commit.diff(commit.parents[0])

    lines = []

    for item in diff.iter_change_type('D'):
        lines.append(f'{Colors.GREEN}- {item.b_path}{Colors.END}')
    for item in diff.iter_change_type('M'):
        lines.append(f'{Colors.YELLOW}± {item.b_path}{Colors.END}')
    for item in diff.iter_change_type('A'):
        lines.append(f'{Colors.RED}- {item.a_path}{Colors.END}')
    for item in diff.iter_change_type('R'):
        lines.append(f'{Colors.CYAN}{item.b_path} -> {item.a_path}{Colors.END}')

    commit_summary = '```ansi\n' + '\n'.join(lines) + '\n```'

    return commit.hexsha[:10], commit.message.strip(), commit_summary
