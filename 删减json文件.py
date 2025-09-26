import os
import re
import json
from datetime import datetime, timedelta


def extract_datetime_from_filename(filename):
    """从文件名中提取日期时间信息

    Args:
        filename: 文件名，格式如"price__2025-09-26 00_00_09_ 更新价格.json"

    Returns:
        datetime对象或None: 成功提取则返回datetime对象，否则返回None
    """
    # 使用正则表达式匹配日期时间部分
    match = re.search(r'price__(\d{4}-\d{2}-\d{2} \d{2}_\d{2}_\d{2})_ 更新价格\.json', filename)
    if match:
        datetime_str = match.group(1)
        # 将字符串转换为datetime对象
        try:
            return datetime.strptime(datetime_str, '%Y-%m-%d %H_%M_%S')
        except ValueError:
            return None
    return None


def filter_files_by_datetime(directory, start_datetime=None, end_datetime=None):
    """根据日期时间筛选price_history目录下的JSON文件

    Args:
        directory: 要搜索的目录路径
        start_datetime: 起始日期时间(包含)，datetime对象
        end_datetime: 结束日期时间(包含)，datetime对象

    Returns:
        list: 符合条件的文件路径列表
    """
    filtered_files = []

    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        # 检查是否为JSON文件且符合命名格式
        if filename.endswith('.json') and 'price__' in filename and '_ 更新价格' in filename:
            # 提取日期时间
            file_datetime = extract_datetime_from_filename(filename)
            if file_datetime:
                # 检查是否在指定的日期时间范围内
                if ((start_datetime is None or file_datetime >= start_datetime) and
                        (end_datetime is None or file_datetime <= end_datetime)):
                    filtered_files.append({
                        'path': os.path.join(directory, filename),
                        'datetime': file_datetime,
                        'filename': filename
                    })

    # 按日期时间排序
    filtered_files.sort(key=lambda x: x['datetime'])
    return [file['path'] for file in filtered_files]


def read_json_files(file_paths):
    """读取多个JSON文件并返回内容

    Args:
        file_paths: JSON文件路径列表

    Returns:
        list: 包含每个JSON文件内容的列表
    """
    json_contents = []
    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                json_contents.append({
                    'file_path': path,
                    'content': content,
                    'status': 'success'
                })
        except Exception as e:
            json_contents.append({
                'file_path': path,
                'error': str(e),
                'status': 'error'
            })
    return json_contents


def filter_and_save_json(json_contents, output_dir, blacklist_names=None, whitelist_names=None):
    """筛选JSON内容并保存到指定目录

    Args:
        json_contents: read_json_files()返回的内容列表
        output_dir: 输出目录路径
        blacklist_names: 需要过滤的名称列表(可选)
        whitelist_names: 需要保留的名称列表(可选)

    Returns:
        int: 成功保存的文件数量
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    saved_count = 0

    for item in json_contents:
        if item['status'] != 'success':
            print(f"跳过无效文件: {item['file_path']}")
            continue

        filtered_content = []
        for entry in item['content']:
            if 'name' in entry and isinstance(entry['name'], str):
                # 白名单条目直接添加，不检查其他条件
                if whitelist_names is not None and entry['name'] in whitelist_names:
                    filtered_content.append(entry)
                    continue

                # 非白名单条目需要检查其他条件
                if (len(entry['name']) > 0 and
                        (entry['name'][0].isdigit() or entry['name'][0] == '.') and
                        not any('\u4e00' <= char <= '\u9fff' for char in entry['name'])):
                    # 不在黑名单中的才添加
                    if blacklist_names is None or entry['name'] not in blacklist_names:
                        filtered_content.append(entry)

        print(f"文件 {item['file_path']} 找到 {len(filtered_content)} 条符合条件的记录")

        if filtered_content:
            # 从原文件名生成新文件名
            basename = os.path.basename(item['file_path'])
            new_filename = f"filtered_{basename}"
            new_path = os.path.join(output_dir, new_filename)

            try:
                with open(new_path, 'w', encoding='utf-8') as f:
                    json.dump(filtered_content, f, ensure_ascii=False, indent=2)
                saved_count += 1
            except Exception as e:
                print(f"保存文件失败: {new_path}, 错误: {str(e)}")

    return saved_count


if __name__ == '__main__':
    # 示例用法
    price_history_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'price_history')

    # 示例：获取最近7天的文件
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # 筛选文件
    print(f'筛选{start_date}至{end_date}之间的JSON文件...')
    json_files = filter_files_by_datetime(price_history_dir, start_date, end_date)  # 确保这行代码存在

    # 确保添加这行代码
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filtered_price_history')
    print(f"输出目录: {output_dir}")

    # 定义需要过滤的名称黑名单
    name_blacklist = ["93R", ".357 Magnum JHP", ".357 Magnum HP",
                      ".357 Magnum FMJ",
                      ".45 ACP JHP",
                      ".45 ACP HS",
                      ".50 AE FMJ",
                      ".50 AE JHP",
                      ".50 AE HP",
                      "5.45x39mm PRS",
                      "5.45x39mm T",
                      "5.56x45mm FMJ",
                      "5.56x45mm RRLP",
                      "5.7x28mm SS197SR",
                      "5.7x28mm SS198LF",
                      "5.8x42mm DBP87",
                      "7.62x39mm T45M",
                      "7.62x39mm LP",
                      "7.62x51mm Ultra Nosler",
                      "9x19mm Pst",
                      "9x19mm PSO",
                      "45-70 Govt FTX",
                      "45-70 Govt FMJ",
                      "45-70 Govt RN",
                      ".50 AE FMJ",
                      ]

    # 定义需要保留的白名单
    name_whitelist = ["12.7x55mm PD12双头弹"]  # 示例白名单

    if json_files:
        print(f'找到{len(json_files)}个符合条件的文件：')
        for file_path in json_files:
            print(f'  {file_path}')

        # 读取文件内容
        print('\n读取文件内容...')
        file_contents = read_json_files(json_files)

        # 处理文件内容（这里仅打印成功/失败状态）
        for item in file_contents:
            if item['status'] == 'success':
                print(f'成功读取：{item["file_path"]}')
            else:
                print(f'读取失败：{item["file_path"]}，错误：{item["error"]}')

        # 修改调用，添加白名单参数
        saved_count = filter_and_save_json(file_contents, output_dir,
                                         blacklist_names=name_blacklist,
                                         whitelist_names=name_whitelist)
        print(f"实际保存了 {saved_count} 个文件")
    else:
        print('未找到符合条件的JSON文件')
