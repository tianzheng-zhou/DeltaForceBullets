import os
import json
import re
from datetime import datetime


def get_bullet_level(bullet_name):
    """
    根据三角洲游戏实际设定判断子弹等级
    基于游戏内实际数据，不使用关键词提取
    """
    # 基于三角洲游戏实际设定的子弹等级映射
    bullet_levels = {
        # 5级子弹（最高穿透）

        "12.7x55mm PS12B": 5,
        "5.45x39mm BS": 5,
        "5.56x45mm M995": 5,
        "5.7x28mm SS190": 5,
        "5.8x42mm DVC12": 5,
        "6.8x51mm Hybrid": 5,
        "7.62x39mm AP": 5,
        "7.62x51mm M62": 5,
        "7.62x54R BT": 5,
        "9x39mm BP": 5,
        "4.6x30mm AP SX": 5,

        # 4级子弹（中等穿透）
        "9x19mm PBP": 4,
        ".45 ACP AP": 4,
        "12.7x55mm PD12双头弹": 4,
        "5.45x39mm BT": 4,
        "5.56x45mm M855A1": 4,
        "5.7x28mm SS193": 4,
        "5.8x42mm DBP10": 4,
        "6.8x51mm FMJ": 4,
        "7.62x39mm BP": 4,
        "7.62x51mm M80": 4,
        "7.62x54R LPS": 4,
        "9x39mm SP6": 4,
        "4.6x30mm FMJ SX": 4,
        "12.7x55mm PS12": 4,

        # 3级子弹（基础穿透）
        "9x19mm AP6.3": 3,
        "12.7x55mm PS12A": 3,
        ".45 ACP RIP": 3,
        ".45 ACP FMJ": 3,
        "5.45x39mm PS": 3,
        "5.7x28mm R37.F": 3,
        "5.7x28mm L191": 3,
        "5.8x42mm DVP88": 3,
        "7.62x39mm PS": 3,
        "7.62x51mm BPZ": 3,
        "7.62x54R T46M": 3,
        "9x19mm RIP": 3,
        "9x39mm SP5": 3,
        "4.6x30mm Subsonic SX": 3,
        "5.56x45mm M855": 3
    }

    # 直接返回映射表中的等级
    return bullet_levels.get(bullet_name, 3)  # 默认3级


def get_bullet_type(bullet_name):
    """
    提取子弹种类（口径信息）
    """
    # 如果是.45 ACP子弹，只提取.45
    if '.45 ACP' in bullet_name:
        return '.45'

    # 匹配口径模式，如 5.56x45mm, 7.62x39mm 等
    pattern = r'([\d.]+x\d+mm|[\d.]+mm)'
    match = re.search(pattern, bullet_name)

    if match:
        return match.group(1)

    # 如果无法匹配，返回原始名称的前部分
    return bullet_name.split()[0] if ' ' in bullet_name else bullet_name


def process_bullet_data(bullet_item):
    """
    处理单个子弹数据，添加等级和种类属性
    """
    name = bullet_item['name']
    price = bullet_item['price']

    bullet_level = get_bullet_level(name)
    bullet_type = get_bullet_type(name)

    return {
        'name': name,
        'price': price,
        'level': bullet_level,
        'type': bullet_type
    }


def process_all_files():
    """
    处理filtered_price_history文件夹中的所有文件
    """
    input_folder = 'filtered_price_history'
    output_folder = 'classified_price_history'

    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 获取所有JSON文件
    json_files = [f for f in os.listdir(input_folder) if f.endswith('.json')]

    print(f"找到 {len(json_files)} 个文件需要处理")

    for filename in json_files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        try:
            # 读取原始数据
            with open(input_path, 'r', encoding='utf-8') as f:
                original_data = json.load(f)

            # 处理每个子弹数据
            processed_data = [process_bullet_data(item) for item in original_data]

            # 保存处理后的数据
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)

            print(f"已处理: {filename}")

        except Exception as e:
            print(f"处理文件 {filename} 时出错: {e}")

    print("所有文件处理完成！")


def preview_sample():
    """
    预览处理后的样本数据
    """
    sample_file = 'filtered_price_history/filtered_price__2025-09-26 01_00_04_ 更新价格.json'

    if os.path.exists(sample_file):
        with open(sample_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)

        # 处理前几个样本
        sample_count = min(5, len(original_data))
        print("样本处理预览:")
        print("-" * 60)

        for i in range(sample_count):
            original_item = original_data[i]
            processed_item = process_bullet_data(original_item)
            print(f"名称: {processed_item['name']}")
            print(f"价格: {processed_item['price']}")
            print(f"等级: {processed_item['level']}")
            print(f"种类: {processed_item['type']}")
            print("-" * 30)


def process_files_by_date(target_dates=None):
    """
    按日期处理filtered_price_history文件夹中的文件

    Args:
        target_dates: 需要处理的日期列表，格式为["2025-09-13", "2025-09-14"]，如果为None则处理所有文件
    """
    input_folder = 'filtered_price_history'
    output_folder = 'classified_price_history'

    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 获取所有JSON文件
    all_json_files = [f for f in os.listdir(input_folder) if f.endswith('.json')]

    # 如果指定了目标日期，筛选对应的文件
    if target_dates:
        target_files = []
        for filename in all_json_files:
            # 从文件名提取日期
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            if date_match:
                file_date = date_match.group(1)
                if file_date in target_dates:
                    target_files.append(filename)
        json_files = target_files
        print(f"找到 {len(json_files)} 个需要处理的文件（目标日期: {target_dates}）")
    else:
        json_files = all_json_files
        print(f"找到 {len(json_files)} 个文件需要处理")

    processed_count = 0
    for filename in json_files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        try:
            # 检查输出文件是否已存在（避免重复处理）
            if os.path.exists(output_path):
                print(f"文件已存在，跳过: {filename}")
                continue

            # 读取原始数据
            with open(input_path, 'r', encoding='utf-8') as f:
                original_data = json.load(f)

            # 处理每个子弹数据
            processed_data = [process_bullet_data(item) for item in original_data]

            # 保存处理后的数据
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)

            print(f"已处理: {filename}")
            processed_count += 1

        except Exception as e:
            print(f"处理文件 {filename} 时出错: {e}")

    print(f"处理完成！共处理了 {processed_count} 个文件")
    return processed_count


if __name__ == "__main__":
    print("子弹数据分类处理工具")
    print("=" * 50)

    # 预览样本
    preview_sample()

    print("\n开始处理所有文件...")
    # 使用新的按日期处理函数，不指定日期则处理所有文件
    process_files_by_date()

    print("\n处理完成！处理后的文件保存在 'classified_price_history' 文件夹中")