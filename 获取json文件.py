import requests
import json
from datetime import datetime, timedelta
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import warnings
import urllib3  # 添加这行导入


def fetch_github_file_with_history(owner, repo, filepath, output_dir="downloaded_files",
                                 start_date=None, end_date=None):
    """
    从GitHub抓取文件及其历史版本

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

    # 获取完整的commit历史（处理分页）
    commits = []
    page = 1
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

        commits.extend(page_commits)
        print(f"已获取第 {page} 页，共 {len(page_commits)} 条commit记录")
        page += 1


    if not commits:
        print("未获取到任何commit历史")
        return

    # 保存commit历史信息
    history_file = os.path.join(output_dir, f"{os.path.basename(filepath)}_history.json")
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(commits, f, indent=2, ensure_ascii=False)

    print(f"已保存commit历史到: {history_file}")

    # 下载每个历史版本的文件
    downloaded_count = 0
    for i, commit in enumerate(commits):
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
            print(f"文件已存在，跳过下载: {filename}")
            continue

        # 获取特定commit版本的文件内容
        file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{commit_sha}/{filepath}"
        file_response = requests.get(file_url, verify=False)

        if file_response.status_code == 200:
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_response.text)
            print(f"已下载版本: {filename}")
            downloaded_count += 1  # 增加下载计数
        else:
            print(f"无法下载commit {commit_sha} 的文件版本")

        # 添加延迟避免触发API限制
        import time
        time.sleep(1)  # 1秒延迟

    print(f"已完成下载，共下载了 {downloaded_count} 个符合条件的版本")
    print(f"文件和历史版本已保存到目录: {output_dir}")


if __name__ == "__main__":
    # 示例：下载2023年1月1日到2023年12月31日之间的版本
    fetch_github_file_with_history(
        owner="orzice",
        repo="DeltaForcePrice",
        filepath="price.json",
        output_dir="price_history",
        start_date="2025-09-26",
        end_date="2025-09-26"
    )
