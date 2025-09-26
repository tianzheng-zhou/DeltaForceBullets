import json
import os
import glob
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np


def calculate_price_volatility(prices):
    """计算价格波动指标：最高10%价格与最低10%价格的比例值-1"""
    if len(prices) < 10:
        # 如果数据点太少，使用最高价和最低价
        top_10_price = max(prices)
        bottom_10_price = min(prices)
    else:
        # 计算最高10%价格和最低10%价格
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        top_10_index = int(n * 0.9)  # 最高10%的位置
        bottom_10_index = int(n * 0.1)  # 最低10%的位置

        top_10_price = sorted_prices[top_10_index]
        bottom_10_price = sorted_prices[bottom_10_index]

    # 计算比例值-1，转换为百分比
    if bottom_10_price > 0:
        volatility_ratio = (top_10_price / bottom_10_price) - 1
        volatility_percentage = volatility_ratio * 100
    else:
        volatility_percentage = 0

    return volatility_percentage


def plot_individual_bullet_prices():
    """绘制每个子弹的详细价格图表"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 获取所有子弹数据文件
    bullet_files = glob.glob("bullet_data/*.json")

    if not bullet_files:
        print("在bullet_data文件夹中没有找到任何子弹数据文件")
        return

    print(f"找到 {len(bullet_files)} 个子弹数据文件")

    # 创建图表输出文件夹
    output_dir = "price_charts"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 创建单个子弹的详细图表
    print("创建单个子弹的详细图表...")
    for file_path in bullet_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            bullet_name = data["basic_info"]["name"]
            level = data["basic_info"]["level"]
            price_history = data["price_history"]

            if price_history:
                # 创建单个子弹的图表
                plt.figure(figsize=(12, 6))

                timestamps = [datetime.fromisoformat(entry["timestamp"]) for entry in price_history]
                prices = [entry["price"] for entry in price_history]

                plt.plot(timestamps, prices, linewidth=2, marker='o', markersize=3,
                         color='blue', label=bullet_name)

                plt.title(f'{bullet_name} 价格走势 (等级{level})')
                plt.xlabel('时间')
                plt.ylabel('价格')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))

                # 添加统计信息（移动到右上角）
                min_price = min(prices)
                max_price = max(prices)
                avg_price = np.mean(prices)
                price_range = max_price - min_price

                # 计算价格波动指标
                volatility_percentage = calculate_price_volatility(prices)

                stats_text = f'最低价: {min_price}\n最高价: {max_price}\n平均价: {avg_price:.0f}\n价格范围: {price_range}\n价格波动: {volatility_percentage:.1f}%'
                plt.figtext(0.98, 0.98, stats_text, fontsize=10,
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"),
                            horizontalalignment='right', verticalalignment='top')

                plt.tight_layout()

                # 保存单个子弹图表
                safe_bullet_name = bullet_name.replace("/", "_").replace("\\", "_").replace(":", "_")
                single_chart_filename = os.path.join(output_dir, f"{safe_bullet_name}_价格走势.png")
                plt.savefig(single_chart_filename, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"已创建图表: {safe_bullet_name}_价格走势.png (波动率: {volatility_percentage:.1f}%)")

        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")

    print(f"\n所有单个子弹图表已保存到 {output_dir} 文件夹")


def plot_all_bullets_together():
    """绘制所有子弹在一个图表中（按等级分组）"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 获取所有子弹数据文件
    bullet_files = glob.glob("bullet_data/*.json")

    if not bullet_files:
        print("在bullet_data文件夹中没有找到任何子弹数据文件")
        return

    # 按等级分组
    level_3_data = []
    level_4_data = []
    level_5_data = []

    for file_path in bullet_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            bullet_name = data["basic_info"]["name"]
            level = data["basic_info"]["level"]
            price_history = data["price_history"]

            if price_history:
                timestamps = [datetime.fromisoformat(entry["timestamp"]) for entry in price_history]
                prices = [entry["price"] for entry in price_history]

                bullet_info = {
                    "name": bullet_name,
                    "timestamps": timestamps,
                    "prices": prices
                }

                if level == 3:
                    level_3_data.append(bullet_info)
                elif level == 4:
                    level_4_data.append(bullet_info)
                elif level == 5:
                    level_5_data.append(bullet_info)

        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")

    # 创建综合图表
    fig, axes = plt.subplots(3, 1, figsize=(16, 15))
    fig.suptitle('所有子弹价格走势图（按等级分组）', fontsize=16, fontweight='bold')

    # 等级3子弹
    ax1 = axes[0]
    for i, bullet in enumerate(level_3_data):
        ax1.plot(bullet["timestamps"], bullet["prices"],
                 label=bullet["name"], linewidth=1.5, alpha=0.7)

    ax1.set_title('等级3子弹价格走势')
    ax1.set_ylabel('价格')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    # 等级4子弹
    ax2 = axes[1]
    for i, bullet in enumerate(level_4_data):
        ax2.plot(bullet["timestamps"], bullet["prices"],
                 label=bullet["name"], linewidth=1.5, alpha=0.7)

    ax2.set_title('等级4子弹价格走势')
    ax2.set_ylabel('价格')
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    # 等级5子弹
    ax3 = axes[2]
    for i, bullet in enumerate(level_5_data):
        ax3.plot(bullet["timestamps"], bullet["prices"],
                 label=bullet["name"], linewidth=1.5, alpha=0.7)

    ax3.set_title('等级5子弹价格走势')
    ax3.set_xlabel('时间')
    ax3.set_ylabel('价格')
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    plt.tight_layout()

    # 保存综合图表
    output_dir = "price_charts"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.savefig(os.path.join(output_dir, "所有子弹价格走势.png"), dpi=300, bbox_inches='tight')
    plt.close()

    print("综合图表已创建")


if __name__ == "__main__":
    print("开始生成子弹价格图表...")

    # 生成单个子弹的详细图表
    plot_individual_bullet_prices()

    # 生成综合图表
    plot_all_bullets_together()

    print("\n图表生成完成！")
    print("请查看 price_charts 文件夹中的图表文件")