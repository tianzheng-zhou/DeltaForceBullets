import requests
import json
from datetime import datetime, timedelta
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import warnings
import urllib3
import time


def fetch_github_file_with_history(owner, repo, filepath, output_dir="downloaded_files",
                                   start_date=None, end_date=None):
    """
    从GitHub抓取文件及其历史版本（优化版：增量获取历史，但重新下载所有应下载的文件）

    Args:
        owner: GitHub仓库所有者
        repo: 仓库名称
        filepath: 文件路径
        output_dir: 输出目录
        start_date: 筛选开始日期(格式:YYYY-MM-DD)
        end_date: 筛选结束日期(格式:YYYY-MM-DD)
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 创建带重试机制的session
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    # 检查本地是否已有历史记录文件
    history_file = os.path.join(output_dir, f"{os.path.basename(filepath)}_history.json")
    existing_commits = []
    last_known_commit_sha = None

    if os.path.exists(history_file):
        print("检测到本地已有历史记录文件，将只获取新增的commit...")
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                existing_commits = json.load(f)
            if existing_commits:
                last_known_commit_sha = existing_commits[0]['sha']  # 最新的commit在列表开头
                print(f"最后一个已知的commit: {last_known_commit_sha[:8]}...")
        except Exception as e:
            print(f"读取本地历史记录失败: {str(e)}，将重新获取完整历史")

    # 获取commit历史（增量获取）
    commits = []
    page = 1
    found_last_known = False

    while True:
        commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?path={filepath}&page={page}&per_page=100"
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
                commits_response = session.get(commits_url, verify=False)
            commits_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {str(e)}")
            break

        if commits_response.status_code != 200:
            print(f"无法获取commit历史: {commits_response.status_code}")
            break

        page_commits = commits_response.json()
        if not page_commits:
            break  # 没有更多数据了

        # 检查是否找到了最后一个已知的commit
        for commit in page_commits:
            if last_known_commit_sha and commit['sha'] == last_known_commit_sha:
                found_last_known = True
                print(f"在第{page}页找到了最后一个已知的commit，停止获取更多历史")
                break

        # 如果是增量更新，只添加新的commit
        if last_known_commit_sha and found_last_known:
            # 只添加在最后一个已知commit之前的commit
            new_commits = []
            for commit in page_commits:
                if commit['sha'] == last_known_commit_sha:
                    break
                new_commits.append(commit)
            commits.extend(new_commits)
            print(f"已获取第 {page} 页，共 {len(new_commits)} 条新增commit记录")
            break
        else:
            commits.extend(page_commits)
            print(f"已获取第 {page} 页，共 {len(page_commits)} 条commit记录")

        page += 1

        # 添加延迟避免触发API限制
        time.sleep(0.5)

    if not commits and not existing_commits:
        print("未获取到任何commit历史")
        return

    # 合并新旧commit历史（新的在前，旧的在后）
    if commits:
        all_commits = commits + existing_commits
        print(f"合并后的commit总数: {len(all_commits)} (新增: {len(commits)}, 已有: {len(existing_commits)})")
    else:
        all_commits = existing_commits
        print("没有新增的commit，使用本地历史记录")

    # 保存完整的commit历史信息
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(all_commits, f, indent=2, ensure_ascii=False)
    print(f"已更新commit历史到: {history_file}")

    # 下载所有应该下载的文件（包括之前可能因为各种原因没下载的）
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0

    print(f"开始处理 {len(all_commits)} 个commit，检查并下载缺失的文件...")

    for i, commit in enumerate(all_commits):
        commit_sha = commit['sha']
        commit_date_str = commit['commit']['committer']['date']
        commit_date_utc = datetime.strptime(commit_date_str, "%Y-%m-%dT%H:%M:%SZ")
        # 转换为北京时间 (UTC+8)
        commit_date_bj = commit_date_utc + timedelta(hours=8)

        # 日期筛选条件（使用北京时间）
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            if commit_date_bj.date() < start.date():
                continue
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            if commit_date_bj.date() > end.date():
                continue

        # 生成文件名（使用提交信息而不是commit sha）
        commit_message = commit['commit']['message'].strip()
        # 移除文件名中的非法字符
        safe_message = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in commit_message)
        safe_message = safe_message[:50]  # 限制长度
        filename = f"price_{safe_message}.json"
        file_path = os.path.join(output_dir, filename)

        # 检查文件是否已存在
        if os.path.exists(file_path):
            print(f"[{i + 1}/{len(all_commits)}] 文件已存在，跳过: {filename}")
            skipped_count += 1
            continue

        # 获取特定commit版本的文件内容
        file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{commit_sha}/{filepath}"
        try:
            file_response = requests.get(file_url, verify=False, timeout=30)
        except requests.exceptions.RequestException as e:
            print(f"[{i + 1}/{len(all_commits)}] 下载文件失败: {str(e)}")
            failed_count += 1
            continue

        if file_response.status_code == 200:
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_response.text)
            print(f"[{i + 1}/{len(all_commits)}] 已下载文件: {filename}")
            downloaded_count += 1
        else:
            print(
                f"[{i + 1}/{len(all_commits)}] 无法下载commit {commit_sha} 的文件版本 (状态码: {file_response.status_code})")
            failed_count += 1

        # 添加延迟避免触发API限制
        time.sleep(1)

    print(f"文件处理完成:")
    print(f"  - 新增下载: {downloaded_count} 个文件")
    print(f"  - 跳过已存在: {skipped_count} 个文件")
    print(f"  - 下载失败: {failed_count} 个文件")
    print(f"文件和历史版本已保存到目录: {output_dir}")


if __name__ == "__main__":
    fetch_github_file_with_history(
        owner="orzice",
        repo="DeltaForcePrice",
        filepath="price.json",
        output_dir="price_history",
        start_date="2025-09-25",
        end_date="2025-09-26"
    )
