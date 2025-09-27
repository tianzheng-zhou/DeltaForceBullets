import json
import os
import glob
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date, timedelta
import numpy as np
from collections import defaultdict




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


def filter_data_by_date(price_history, target_date):
    """根据日期筛选数据"""
    filtered_history = []
    for entry in price_history:
        entry_datetime = datetime.fromisoformat(entry["timestamp"])
        if entry_datetime.date() == target_date:
            filtered_history.append(entry)
    return filtered_history


def calculate_price_volatility(prices):
    """计算价格波动指标：最高5%价格与最低5%价格的比例值-1"""
    if len(prices) < 10:
        # 如果数据点太少，使用最高价和最低价
        top_5_price = max(prices)
        bottom_5_price = min(prices)
    else:
        # 计算最高5%价格和最低5%价格
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        top_5_index = int(n * 0.95)  # 最高5%的位置
        bottom_5_index = int(n * 0.05)  # 最低5%的位置

        top_5_price = sorted_prices[top_5_index]
        bottom_5_price = sorted_prices[bottom_5_index]

    # 计算比例值-1，转换为百分比
    if bottom_5_price > 0:
        volatility_ratio = (top_5_price / bottom_5_price) - 1
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


def calculate_daily_statistics(prices):
    """计算每日统计信息"""
    if not prices:
        return {
            'min_price': 0,
            'max_price': 0,
            'avg_price': 0,
            'price_range': 0,
            'volatility': 0,
            'exact_volatility': 0
        }

    min_price = min(prices)
    max_price = max(prices)
    avg_price = np.mean(prices)
    price_range = max_price - min_price

    # 计算价格波动（使用5%阈值的波动率计算）
    volatility = calculate_price_volatility(prices)

    # 计算精确价格波动（最高价/最低价 - 1）
    if min_price > 0:
        exact_volatility = ((max_price / min_price) - 1) * 100
    else:
        exact_volatility = 0

    return {
        'min_price': min_price,
        'max_price': max_price,
        'avg_price': avg_price,
        'price_range': price_range,
        'volatility': volatility,
        'exact_volatility': exact_volatility
    }

def plot_three_day_comparison(bullet_name, dates, bullet_data):
    """绘制三日子弹对比图"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 创建图表 - 现在只有2个子图（取消价格波动率折线图）
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

    # 颜色列表（按照要求：红色为最后一天，橙色为倒数第二天，蓝色为最早的一天）
    colors = ['blue', 'orange', 'red', 'green', 'purple']

    # 存储每日统计信息
    daily_stats = []

    # 绘制价格走势图
    for i, date_obj in enumerate(dates):
        if date_obj in bullet_data:
            price_history = bullet_data[date_obj]
            prices = [entry["price"] for entry in price_history]

            # 提取时间信息（只保留小时和分钟，忽略日期）
            time_points = []
            for entry in price_history:
                entry_datetime = datetime.fromisoformat(entry["timestamp"])
                # 创建只包含时间的时间对象（忽略日期部分）
                time_only = entry_datetime.time()
                # 转换为分钟数（从0点开始）
                minutes_from_midnight = time_only.hour * 60 + time_only.minute
                time_points.append(minutes_from_midnight)

            # 计算统计信息
            stats = calculate_daily_statistics(prices)
            daily_stats.append(stats)

            # 绘制价格线（使用时间点作为x轴）
            if len(dates) == 3:
                if i == 0:  # 最早的一天
                    color = 'blue'
                elif i == 1:  # 倒数第二天
                    color = 'orange'
                else:  # 最后一天 (i == 2)
                    color = 'red'
            else:
                color = colors[i % len(colors)]

            label = f"{date_obj.strftime('%m-%d')} (波动: {stats['volatility']:.1f}%)"
            ax1.plot(time_points, prices, linewidth=2, marker='o', markersize=3,
                     color=color, label=label, alpha=0.8)

    # 设置价格走势图属性
    ax1.set_title(f'{bullet_name} - 三日期价格对比', fontsize=14, fontweight='bold')
    ax1.set_ylabel('价格')
    ax1.set_xlabel('时间 (0-24点)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1440)  # 0点到24点
    ax1.set_xticks(range(0, 1441, 120))  # 每2小时一个刻度
    ax1.set_xticklabels([f'{i // 60:02d}:00' for i in range(0, 1441, 120)])

    # 绘制统计信息对比图
    if daily_stats:
        dates_str = [date_obj.strftime('%m-%d') for date_obj in dates if date_obj in bullet_data]

        # 创建统计对比数据
        min_prices = [stats['min_price'] for stats in daily_stats]
        max_prices = [stats['max_price'] for stats in daily_stats]
        avg_prices = [stats['avg_price'] for stats in daily_stats]
        volatilities = [stats['volatility'] for stats in daily_stats]
        exact_volatilities = [stats['exact_volatility'] for stats in daily_stats]

        # 绘制最小价、最大价、平均价对比
        x_pos = np.arange(len(dates_str))
        width = 0.25

        ax2.bar(x_pos - width, min_prices, width, label='最低价', alpha=0.7, color='lightcoral')
        ax2.bar(x_pos, avg_prices, width, label='平均价', alpha=0.7, color='lightblue')
        ax2.bar(x_pos + width, max_prices, width, label='最高价', alpha=0.7, color='lightgreen')

        # 在柱状图上添加数值标签
        for i, (min_p, avg_p, max_p) in enumerate(zip(min_prices, avg_prices, max_prices)):
            ax2.text(i - width, min_p + 5, f'{min_p:.0f}', ha='center', va='bottom', fontsize=8)
            ax2.text(i, avg_p + 5, f'{avg_p:.0f}', ha='center', va='bottom', fontsize=8)
            ax2.text(i + width, max_p + 5, f'{max_p:.0f}', ha='center', va='bottom', fontsize=8)

        ax2.set_title('每日价格统计对比', fontsize=12)
        ax2.set_xlabel('日期')
        ax2.set_ylabel('价格')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(dates_str)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 添加波动率信息到图表（保留在第二个子图中）
        volatility_text = "\n".join([f"{dates_str[i]}: {volatilities[i]:.1f}%"
                                     for i in range(len(volatilities))])
        exact_volatility_text = "\n".join([f"{dates_str[i]}: {exact_volatilities[i]:.1f}%"
                                           for i in range(len(exact_volatilities))])

        ax2.text(0.02, 0.98, f'价格波动率:\n{volatility_text}',
                 transform=ax2.transAxes, fontsize=10,
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"),
                 verticalalignment='top')

        ax2.text(0.02, 0.70, f'精确价格波动率:\n{exact_volatility_text}',
                 transform=ax2.transAxes, fontsize=10,
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcyan"),
                 verticalalignment='top')

    plt.tight_layout()
    return fig


def generate_three_day_comparison_charts(days_back=3, specific_dates=None):
    """生成三日子弹对比图表"""
    # 获取所有可用日期
    available_dates = get_available_dates()

    if not available_dates:
        print("没有找到任何可用的数据日期")
        return

    print(f"可用的日期: {[d.strftime('%Y-%m-%d') for d in available_dates]}")

    # 确定要对比的日期
    if specific_dates:
        # 使用指定的日期
        dates_to_compare = specific_dates
        # 获取对比日期中的最后一天作为目标文件夹
        target_date_folder = dates_to_compare[-1]
    else:
        # 使用最近N天
        if len(available_dates) >= days_back:
            dates_to_compare = available_dates[-days_back:]
            # 获取对比日期中的最后一天作为目标文件夹
            target_date_folder = dates_to_compare[-1]
        else:
            dates_to_compare = available_dates
            target_date_folder = dates_to_compare[-1]
            print(f"可用日期不足{days_back}天，使用所有{len(available_dates)}天数据进行对比")

    print(f"对比日期: {[d.strftime('%Y-%m-%d') for d in dates_to_compare]}")
    print(f"目标文件夹日期: {target_date_folder.strftime('%Y-%m-%d')}")

    # 创建输出目录 - 放在对应日期的文件夹下
    base_output_dir = "../price_charts"
    target_date_str = target_date_folder.strftime("%Y-%m-%d")
    output_dir = os.path.join(base_output_dir, target_date_str, "三日子弹对比")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 获取所有子弹数据
    bullet_files = glob.glob("../bullet_data/*.json")

    if not bullet_files:
        print("在bullet_data文件夹中没有找到任何子弹数据文件")
        return

    print(f"处理 {len(bullet_files)} 个子弹数据文件...")

    # 为每个子弹生成对比图
    for file_path in bullet_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            bullet_name = data["basic_info"]["name"]
            level = data["basic_info"]["level"]
            price_history = data["price_history"]

            # 按日期组织数据
            bullet_data_by_date = {}
            for date_obj in dates_to_compare:
                filtered_data = filter_data_by_date(price_history, date_obj)
                if filtered_data:  # 只包含有数据的日期
                    bullet_data_by_date[date_obj] = filtered_data

            # 如果至少有两个日期有数据，则生成对比图
            if len(bullet_data_by_date) >= 2:
                print(f"生成 {bullet_name} 的三日对比图...")

                # 绘制对比图
                fig = plot_three_day_comparison(bullet_name, dates_to_compare, bullet_data_by_date)

                # 保存图表
                safe_bullet_name = bullet_name.replace("/", "_").replace("\\", "_").replace(":", "_")
                date_range = "_".join([d.strftime('%Y%m%d') for d in dates_to_compare])
                filename = os.path.join(output_dir, f"{safe_bullet_name}_三日对比_{date_range}.png")

                fig.savefig(filename, dpi=300, bbox_inches='tight')
                plt.close(fig)

                print(f"已保存: {filename}")
            else:
                print(f"{bullet_name} 在对比日期中数据不足，跳过")

        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")

    print(f"\n所有三日子弹对比图表已保存到 {output_dir} 文件夹")


def main():
    """主函数"""
    print("三日子弹对比图生成工具")
    print("=" * 50)

    # 获取用户输入
    print("请选择对比方式:")
    print("1. 对比最近3天")
    print("2. 指定具体日期对比")

    choice = input("请输入选择 (1 或 2): ").strip()

    if choice == "1":
        # 对比最近3天
        generate_three_day_comparison_charts(days_back=3)

    elif choice == "2":
        # 指定具体日期对比
        available_dates = get_available_dates()
        print(f"可用的日期: {[d.strftime('%Y-%m-%d') for d in available_dates]}")

        dates_input = input("请输入要对比的日期 (格式: YYYY-MM-DD, 多个日期用逗号分隔): ").strip()

        try:
            specific_dates = []
            for date_str in dates_input.split(','):
                date_obj = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
                if date_obj in available_dates:
                    specific_dates.append(date_obj)
                else:
                    print(f"警告: 日期 {date_str} 没有可用数据")

            if len(specific_dates) >= 2:
                # 确保日期按顺序排列
                specific_dates.sort()
                generate_three_day_comparison_charts(specific_dates=specific_dates)
            else:
                print("需要至少指定2个有数据的日期进行对比")

        except ValueError:
            print("日期格式错误，请使用 YYYY-MM-DD 格式")

    else:
        print("无效选择，使用默认设置（对比最近3天）")
        generate_three_day_comparison_charts(days_back=3)


if __name__ == "__main__":
    main()