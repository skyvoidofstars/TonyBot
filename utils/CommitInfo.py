from git import Repo
from utils.ANSI import Colors

def get_latest_commit_info(repo_path='.') -> tuple[str, str, str]:
    repo = Repo(repo_path)
    commit = repo.head.commit
    
    output_lines = []

    parent_commit = commit.parents[0]
    diff_items = commit.diff(parent_commit, create_patch=True)

    commit_file_stats = commit.stats.files

    path_display_width = 60

    for d_item in diff_items:
        current_path = d_item.b_path or d_item.a_path 
        
        is_binary = d_item.diff is None and (d_item.a_blob is not None or d_item.b_blob is not None)
        stats_column_str: str
        
        if is_binary:
            old_size = d_item.a_blob.size if d_item.a_blob else 0
            new_size = d_item.b_blob.size if d_item.b_blob else 0
            
            if d_item.change_type == 'A':
                old_size = 0
            elif d_item.change_type == 'D':
                new_size = 0
            
            stats_column_str = f'Bin {old_size} -> {new_size} bytes'
            
        else:
            stats = commit_file_stats.get(current_path)
            
            if stats:
                insertions = stats.get('insertions', 0)
                deletions = stats.get('deletions', 0)
                total_lines_changed = insertions + deletions 

                plus_symbols = '+' * (insertions // 10)
                minus_symbols = '-' * (deletions // 10)
                
                stats_column_str = f'{str(total_lines_changed).rjust(6)} {Colors.GREEN}{plus_symbols}{Colors.RED}{minus_symbols}{Colors.END}'
            else:
                stats_column_str = 'Mode/Other'
        
        display_path_str = current_path
        if d_item.renamed_file and d_item.a_path and d_item.b_path:
           display_path_str = f'{d_item.b_path} (renomeado)'

        if len(display_path_str) > path_display_width:
            formatted_display_path = '...' + display_path_str[-(path_display_width-3):]
        else:
            formatted_display_path = display_path_str.ljust(path_display_width)
        
        match True:
            case d_item.new_file:
                output_lines.append(f'{Colors.RED}D {formatted_display_path}{Colors.END} | {stats_column_str}')
            case d_item.deleted_file:
                output_lines.append(f'{Colors.GREEN}A {formatted_display_path}{Colors.END} | {stats_column_str}')
            case d_item.renamed_file:
                output_lines.append(f'{Colors.CYAN}R {formatted_display_path}{Colors.END} | {stats_column_str}')
            case _:
                output_lines.append(f'{Colors.YELLOW}M {formatted_display_path}{Colors.END} | {stats_column_str}')

    output_lines.sort() 
    
    commit_summary = f'```ansi\n{'\n'.join(output_lines)}```'
    
    return commit.hexsha[:10], commit.message, commit_summary