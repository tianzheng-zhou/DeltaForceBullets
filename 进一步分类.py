import json
import os
import glob
from datetime import datetime


def process_bullet_data():
    # 创建子弹数据文件夹
    bullet_data_dir = "bullet_data"
    if not os.path.exists(bullet_data_dir):
        os.makedirs(bullet_data_dir)
        print(f"创建文件夹: {bullet_data_dir}")

    # 获取所有价格历史文件
    price_files = glob.glob("classified_price_history/filtered_price__*.json")
    price_files.sort()  # 按时间排序

    # 存储所有子弹的基本信息和价格历史
    bullet_data = {}

    # 处理每个价格文件
    for file_path in price_files:
        try:
            # 从文件名提取时间戳
            filename = os.path.basename(file_path)
            # 提取日期和时间部分
            time_str = filename.replace("filtered_price__", "").replace("_ 更新价格.json", "")
            # 将下划线替换为冒号以符合ISO格式
            time_str = time_str.replace("_", ":")
            timestamp = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").isoformat()

            # 读取价格数据
            with open(file_path, 'r', encoding='utf-8') as f:
                price_data = json.load(f)

            # 处理每个子弹
            for bullet in price_data:
                name = bullet["name"]
                price = bullet["price"]

                # 如果是第一次遇到这个子弹，初始化数据结构
                if name not in bullet_data:
                    bullet_data[name] = {
                        "basic_info": {
                            "name": bullet["name"],
                            "level": bullet["level"],
                            "type": bullet["type"]
                        },
                        "price_history": []
                    }

                # 添加价格历史记录
                bullet_data[name]["price_history"].append({
                    "timestamp": timestamp,
                    "price": price
                })

        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")

    # 为每个子弹创建单独的JSON文件
    for bullet_name, data in bullet_data.items():
        # 创建安全的文件名（替换特殊字符）
        safe_filename = bullet_name.replace("/", "_").replace("\\", "_").replace(":", "_")
        bullet_file_path = os.path.join(bullet_data_dir, f"{safe_filename}.json")

        # 写入JSON文件
        with open(bullet_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"创建子弹文件: {bullet_file_path}")

    print(f"\n处理完成！共创建了 {len(bullet_data)} 个子弹数据文件。")

    # 显示统计信息
    print("\n统计信息:")
    for bullet_name, data in bullet_data.items():
        price_count = len(data["price_history"])
        print(f"{bullet_name}: {price_count} 条价格记录")


if __name__ == "__main__":
    process_bullet_data()