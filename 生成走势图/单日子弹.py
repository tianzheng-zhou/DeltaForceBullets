import json
import os
import glob
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date
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


def calculate_exact_price_volatility(prices):
    """计算价格波动(精确)指标：最高价格与最低价格的比例值-1"""
    if len(prices) == 0:
        return 0

    max_price = max(prices)
    min_price = min(prices)

    # 计算比例值-1，转换为百分比
    if min_price > 0:
        volatility_ratio = (max_price / min_price) - 1
        volatility_percentage = volatility_ratio * 100
    else:
        volatility_percentage = 0

    return volatility_percentage


def filter_data_by_date(price_history, target_date):
    """根据日期筛选数据"""
    filtered_history = []
    for entry in price_history:
        entry_datetime = datetime.fromisoformat(entry["timestamp"])
        if entry_datetime.date() == target_date:
            filtered_history.append(entry)
    return filtered_history


def plot_individual_bullet_prices(target_date=None):
    """绘制每个子弹的详细价格图表"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 获取所有子弹数据文件
    bullet_files = glob.glob("../bullet_data/*.json")

    if not bullet_files:
        print("在bullet_data文件夹中没有找到任何子弹数据文件")
        return

    print(f"找到 {len(bullet_files)} 个子弹数据文件")

    # 创建图表输出文件夹结构
    base_output_dir = "../price_charts"
    if target_date:
        date_str = target_date.strftime("%Y-%m-%d")
        chart_type_dir = "单日子弹价格波动"
        output_dir = os.path.join(base_output_dir, date_str, chart_type_dir)
    else:
        output_dir = os.path.join(base_output_dir, "所有日期", "单日子弹价格波动")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 创建单个子弹的详细图表
    print("创建单个子弹的详细图表...")
    for file_path in bullet_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            bullet_name = data["basic_info"]["name"]
            level = data["basic_info"]["level"]
            price_history = data["price_history"]

            # 根据日期筛选数据
            if target_date and price_history:
                price_history = filter_data_by_date(price_history, target_date)

            if price_history:
                # 创建单个子弹的图表
                plt.figure(figsize=(12, 6))

                timestamps = [datetime.fromisoformat(entry["timestamp"]) for entry in price_history]
                prices = [entry["price"] for entry in price_history]

                plt.plot(timestamps, prices, linewidth=2, marker='o', markersize=3,
                         color='blue', label=bullet_name)

                # 添加日期信息到标题
                if target_date:
                    title_date = target_date.strftime("%Y-%m-%d")
                    plt.title(f'{bullet_name} 价格走势 (等级{level}) - {title_date}')
                else:
                    plt.title(f'{bullet_name} 价格走势 (等级{level})')

                plt.xlabel('时间')
                plt.ylabel('价格')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))

                # 添加统计信息（移动到右上角，调整位置避免遮挡）
                min_price = min(prices)
                max_price = max(prices)
                avg_price = np.mean(prices)
                price_range = max_price - min_price

                # 计算价格波动指标
                volatility_percentage = calculate_price_volatility(prices)
                exact_volatility_percentage = calculate_exact_price_volatility(prices)

                stats_text = f'最低价: {min_price}\n最高价: {max_price}\n平均价: {avg_price:.0f}\n价格范围: {price_range}\n价格波动: {volatility_percentage:.1f}%\n价格波动(精确): {exact_volatility_percentage:.1f}%'
                # 修改位置：移动到右上角但稍微向下和向左偏移，避免遮挡图表
                plt.figtext(0.95, 0.85, stats_text, fontsize=9,
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8),
                            horizontalalignment='right', verticalalignment='top')

                plt.tight_layout()

                # 保存单个子弹图表
                safe_bullet_name = bullet_name.replace("/", "_").replace("\\", "_").replace(":", "_")
                if target_date:
                    single_chart_filename = os.path.join(output_dir,
                                                         f"{safe_bullet_name}_价格走势_{target_date.strftime('%Y%m%d')}.png")
                else:
                    single_chart_filename = os.path.join(output_dir, f"{safe_bullet_name}_价格走势.png")

                plt.savefig(single_chart_filename, dpi=300, bbox_inches='tight')
                plt.close()

                if target_date:
                    print(
                        f"已创建图表: {safe_bullet_name}_价格走势_{target_date.strftime('%Y%m%d')}.png (波动率: {volatility_percentage:.1f}%, 精确波动率: {exact_volatility_percentage:.1f}%)")
                else:
                    print(
                        f"已创建图表: {safe_bullet_name}_价格走势.png (波动率: {volatility_percentage:.1f}%, 精确波动率: {exact_volatility_percentage:.1f}%)")

        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")

    print(f"\n所有单个子弹图表已保存到 {output_dir} 文件夹")


def plot_all_bullets_together(target_date=None):
    """绘制所有子弹在一个图表中（按等级分组）"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 获取所有子弹数据文件
    bullet_files = glob.glob("bullet_data/*.json")

    if not bullet_files:
        print("在bullet_data文件夹中没有找到任何子弹数据文件")
        return

    # 创建图表输出文件夹结构
    base_output_dir = "../price_charts"
    if target_date:
        date_str = target_date.strftime("%Y-%m-%d")
        chart_type_dir = "综合图表"
        output_dir = os.path.join(base_output_dir, date_str, chart_type_dir)
    else:
        output_dir = os.path.join(base_output_dir, "所有日期", "综合图表")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

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

            # 根据日期筛选数据
            if target_date and price_history:
                price_history = filter_data_by_date(price_history, target_date)

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

    # 添加日期信息到标题
    if target_date:
        title_date = target_date.strftime("%Y-%m-%d")
        fig.suptitle(f'所有子弹价格走势图（按等级分组） - {title_date}', fontsize=16, fontweight='bold')
    else:
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
    if target_date:
        plt.savefig(os.path.join(output_dir, f"所有子弹价格走势_{target_date.strftime('%Y%m%d')}.png"), dpi=300,
                    bbox_inches='tight')
    else:
        plt.savefig(os.path.join(output_dir, "所有子弹价格走势.png"), dpi=300, bbox_inches='tight')

    plt.close()

    print("综合图表已创建")


def get_available_dates():
    """获取所有可用的日期"""
    bullet_files = glob.glob("../bullet_data/*.json")
    dates_set = set()

    for file_path in bullet_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            price_history = data["price_history"]
            for entry in price_history:
                entry_datetime = datetime.fromisoformat(entry["timestamp"])
                dates_set.add(entry_datetime.date())
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")

    return sorted(list(dates_set))


def generate_charts_for_date(target_date=None):
    """为指定日期生成所有图表（适合自动化调用）"""
    print("开始生成子弹价格图表...")

    if target_date:
        print(f"生成 {target_date.strftime('%Y-%m-%d')} 的图表...")
        plot_individual_bullet_prices(target_date)
        plot_all_bullets_together(target_date)
    else:
        # 生成所有可用日期的图表，每个日期单独创建文件夹
        available_dates = get_available_dates()
        print(f"为 {len(available_dates)} 个可用日期生成图表...")

        for date_obj in available_dates:
            print(f"\n生成 {date_obj.strftime('%Y-%m-%d')} 的图表...")
            plot_individual_bullet_prices(date_obj)
            plot_all_bullets_together(date_obj)

    print("\n图表生成完成！")
    print("请查看 price_charts 文件夹中的图表文件")


def main(target_date=None):
    """主函数，接受参数传入而不是命令行接口"""
    available_dates = get_available_dates()

    if not available_dates:
        print("没有找到任何可用的数据日期")
        return

    print(f"可用的日期: {[d.strftime('%Y-%m-%d') for d in available_dates]}")

    if target_date:
        # 如果传入的是字符串，转换为日期对象
        if isinstance(target_date, str):
            try:
                target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                print("日期格式错误，请使用 YYYY-MM-DD 格式")
                return

        # 检查日期是否可用
        if target_date in available_dates:
            generate_charts_for_date(target_date)
        else:
            print(f"日期 {target_date} 没有可用数据")
    else:
        # 默认生成所有日期的图表
        generate_charts_for_date()


if __name__ == "__main__":

    # main(date.today())

    main()
