import json
import os
import glob
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date, timedelta
import numpy as np
from collections import defaultdict

import json
import os
import glob
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date, timedelta
import numpy as np
from collections import defaultdict

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_available_dates():
    """获取所有可用的日期"""
    # 获取所有子弹数据文件 - 使用绝对路径
    bullet_data_dir = os.path.join(PROJECT_ROOT, "bullet_data")
    # 使用os.listdir获取所有文件，然后筛选JSON文件
    all_files = os.listdir(bullet_data_dir)
    bullet_files = [os.path.join(bullet_data_dir, f) for f in all_files
                   if f.endswith('.json') and os.path.isfile(os.path.join(bullet_data_dir, f))]

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


def plot_seven_day_comparison(bullet_name, dates, bullet_data):
    """绘制七日子弹对比图"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 创建图表 - 使用2个子图（删除波动率折线图）
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

    # 彩虹颜色方案：第一天紫色，最后一天红色，中间使用彩虹过渡色
    rainbow_colors = ['purple', 'blue', 'cyan', 'green', 'yellow', 'orange', 'red']

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

            # 为7天数据分配彩虹颜色
            if len(dates) == 7:
                # 使用彩虹颜色：第一天紫色，最后一天红色
                color = rainbow_colors[i]
            else:
                # 如果天数不是7天，循环使用彩虹颜色
                color = rainbow_colors[i % len(rainbow_colors)]

            label = f"{date_obj.strftime('%m-%d')} (波动: {stats['volatility']:.1f}%)"
            ax1.plot(time_points, prices, linewidth=2, marker='o', markersize=2,
                     color=color, label=label, alpha=0.8)

    # 设置价格走势图属性
    ax1.set_title(f'{bullet_name} - 七日期价格对比', fontsize=14, fontweight='bold')
    ax1.set_ylabel('价格')
    ax1.set_xlabel('时间 (0-24点)')
    ax1.legend(loc='upper right', fontsize=8)  # 缩小图例字体以适应更多日期
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1440)  # 0点到24点
    ax1.set_xticks(range(0, 1441, 120))  # 每2小时一个刻度
    ax1.set_xticklabels([f'{i // 60:02d}:00' for i in range(0, 1441, 120)])

    # 绘制统计信息对比图 - 最小价、最大价、平均价
    if daily_stats:
        dates_str = [date_obj.strftime('%m-%d') for date_obj in dates if date_obj in bullet_data]

        # 创建统计对比数据
        min_prices = [stats['min_price'] for stats in daily_stats]
        max_prices = [stats['max_price'] for stats in daily_stats]
        avg_prices = [stats['avg_price'] for stats in daily_stats]
        volatilities = [stats['volatility'] for stats in daily_stats]
        exact_volatilities = [stats['exact_volatility'] for stats in daily_stats]

        # 绘制最小价、最大价、平均价对比，使用对应的彩虹颜色
        x_pos = np.arange(len(dates_str))
        width = 0.25

        # 使用彩虹颜色对应的浅色版本
        bar_colors = ['lavender', 'lightblue', 'lightcyan', 'lightgreen', 'lightyellow', 'peachpuff', 'lightcoral']

        for i in range(len(dates_str)):
            color_idx = i % len(rainbow_colors)
            ax2.bar(x_pos[i] - width, min_prices[i], width,
                    alpha=0.7, color=bar_colors[color_idx],
                    label=f'{dates_str[i]}最低价' if i == 0 else "")
            ax2.bar(x_pos[i], avg_prices[i], width,
                    alpha=0.7, color=bar_colors[color_idx],
                    label=f'{dates_str[i]}平均价' if i == 0 else "")
            ax2.bar(x_pos[i] + width, max_prices[i], width,
                    alpha=0.7, color=bar_colors[color_idx],
                    label=f'{dates_str[i]}最高价' if i == 0 else "")

        # 在柱状图上添加数值标签
        for i, (min_p, avg_p, max_p) in enumerate(zip(min_prices, avg_prices, max_prices)):
            ax2.text(i - width, min_p + 5, f'{min_p:.0f}', ha='center', va='bottom', fontsize=7)
            ax2.text(i, avg_p + 5, f'{avg_p:.0f}', ha='center', va='bottom', fontsize=7)
            ax2.text(i + width, max_p + 5, f'{max_p:.0f}', ha='center', va='bottom', fontsize=7)

        ax2.set_title('每日价格统计对比', fontsize=12)
        ax2.set_xlabel('日期')
        ax2.set_ylabel('价格')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(dates_str, rotation=45)  # 旋转标签以避免重叠

        # 简化图例
        ax2.legend(['最低价', '平均价', '最高价'], fontsize=8)
        ax2.grid(True, alpha=0.3)

        # 添加波动率统计信息到第二个子图（替代原来的第三个子图）
        volatility_text = "价格波动率统计:\n"
        for i, date_str in enumerate(dates_str):
            volatility_text += f"{date_str}: {volatilities[i]:.1f}%\n"

        exact_volatility_text = "精确价格波动率:\n"
        for i, date_str in enumerate(dates_str):
            exact_volatility_text += f"{date_str}: {exact_volatilities[i]:.1f}%\n"

        # 在第二个子图的右侧添加波动率信息
        ax2.text(0.98, 0.98, volatility_text,
                 transform=ax2.transAxes, fontsize=9,
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"),
                 verticalalignment='top', horizontalalignment='right')

        ax2.text(0.98, 0.70, exact_volatility_text,
                 transform=ax2.transAxes, fontsize=9,
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcyan"),
                 verticalalignment='top', horizontalalignment='right')

        # 添加总体统计信息到第二个子图
        total_stats_text = f"7日统计汇总:\n"
        total_stats_text += f"平均波动率: {np.mean(volatilities):.1f}%\n"
        total_stats_text += f"最大波动率: {max(volatilities):.1f}% ({dates_str[volatilities.index(max(volatilities))]})\n"
        total_stats_text += f"最小波动率: {min(volatilities):.1f}% ({dates_str[volatilities.index(min(volatilities))]})"

        ax2.text(0.02, 0.98, total_stats_text,
                 transform=ax2.transAxes, fontsize=9,
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen"),
                 verticalalignment='top')

        # 添加颜色说明到第一个子图
        color_explanation = "颜色说明:\n"
        for i, date_str in enumerate(dates_str):
            if i < len(rainbow_colors):
                color_explanation += f"{date_str}: {rainbow_colors[i]}\n"

        ax1.text(0.98, 0.02, color_explanation,
                 transform=ax1.transAxes, fontsize=8,
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="white"),
                 verticalalignment='bottom', horizontalalignment='right')

    plt.tight_layout()
    return fig


def generate_seven_day_comparison_charts(days_back=7, specific_dates=None):
    """生成七日子弹对比图表"""
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

    # 创建输出目录 - 放在对应日期的文件夹下 - 使用绝对路径
    base_output_dir = os.path.join(PROJECT_ROOT, "price_charts")
    target_date_str = target_date_folder.strftime("%Y-%m-%d")
    output_dir = os.path.join(base_output_dir, target_date_str, "七日子弹对比")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 获取所有子弹数据文件 - 使用绝对路径
    bullet_data_dir = os.path.join(PROJECT_ROOT, "bullet_data")
    # 使用os.listdir获取所有文件，然后筛选JSON文件
    all_files = os.listdir(bullet_data_dir)
    bullet_files = [os.path.join(bullet_data_dir, f) for f in all_files
                   if f.endswith('.json') and os.path.isfile(os.path.join(bullet_data_dir, f))]

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

            # 如果至少有两天有数据，则生成对比图
            if len(bullet_data_by_date) >= 2:
                print(f"生成 {bullet_name} 的七日对比图...")

                # 绘制对比图
                fig = plot_seven_day_comparison(bullet_name, dates_to_compare, bullet_data_by_date)

                # 保存图表
                safe_bullet_name = bullet_name.replace("/", "_").replace("\\", "_").replace(":", "_")
                date_range = "_".join([d.strftime('%Y%m%d') for d in dates_to_compare])
                filename = os.path.join(output_dir, f"{safe_bullet_name}_七日对比_{date_range}.png")

                fig.savefig(filename, dpi=300, bbox_inches='tight')
                plt.close(fig)

                print(f"已保存: {filename}")
            else:
                print(f"{bullet_name} 在对比日期中数据不足，跳过")

        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")

    print(f"\n所有七日子弹对比图表已保存到 {output_dir} 文件夹")


def main(target_date=None, comparison_mode=None):
    """主函数
    Args:
        target_date (str): 要对比的目标日期，格式为 'YYYY-MM-DD'
        comparison_mode (str): 对比模式，'recent' 对比最近7天，'specific' 指定日期与前六天对比
    """
    print("七日子弹对比图生成工具")
    print("=" * 50)

    # 获取所有可用日期
    available_dates = get_available_dates()
    if not available_dates:
        print("没有找到任何可用的数据日期")
        return

    print(f"可用的日期: {[d.strftime('%Y-%m-%d') for d in available_dates]}")

    # 如果提供了参数，使用参数模式
    if target_date is not None and comparison_mode is not None:
        if comparison_mode == 'recent':
            # 对比最近7天
            generate_seven_day_comparison_charts(days_back=7)
            return
        elif comparison_mode == 'specific':
            # 指定一个日期，与前六天对比
            try:
                target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()

                if target_date_obj not in available_dates:
                    print(f"警告: 日期 {target_date_obj} 没有可用数据")
                    return

                # 找到目标日期在可用日期列表中的位置
                target_index = available_dates.index(target_date_obj)

                # 获取前六天的日期（如果存在）
                dates_to_compare = []
                for i in range(6, -1, -1):  # 从目标日期往前推6天
                    check_index = target_index - i
                    if check_index >= 0:
                        dates_to_compare.append(available_dates[check_index])

                if len(dates_to_compare) < 2:
                    print(f"警告: 日期 {target_date_obj} 之前的数据不足，无法进行七日对比")
                    print(f"可用的对比日期: {[d.strftime('%Y-%m-%d') for d in dates_to_compare]}")
                    return

                print(f"对比日期: {[d.strftime('%Y-%m-%d') for d in dates_to_compare]}")

                # 生成对比图表
                generate_seven_day_comparison_charts(specific_dates=dates_to_compare)
                return

            except ValueError:
                print("日期格式错误，请使用 YYYY-MM-DD 格式")
                return
        else:
            print("无效的对比模式，使用交互式模式")

    # 交互式模式
    print("请选择对比方式:")
    print("1. 对比最近7天")
    print("2. 指定一个日期，与前六天对比")

    choice = input("请输入选择 (1 或 2): ").strip()

    if choice == "1":
        # 对比最近7天
        generate_seven_day_comparison_charts(days_back=7)

    elif choice == "2":
        # 指定一个日期，与前六天对比
        try:
            date_input = input("请输入要对比的日期 (格式: YYYY-MM-DD): ").strip()
            target_date = datetime.strptime(date_input, "%Y-%m-%d").date()

            if target_date not in available_dates:
                print(f"警告: 日期 {target_date} 没有可用数据")
                return

            # 找到目标日期在可用日期列表中的位置
            target_index = available_dates.index(target_date)

            # 获取前六天的日期（如果存在）
            dates_to_compare = []
            for i in range(6, -1, -1):  # 从目标日期往前推6天
                check_index = target_index - i
                if check_index >= 0:
                    dates_to_compare.append(available_dates[check_index])

            if len(dates_to_compare) < 2:
                print(f"警告: 日期 {target_date} 之前的数据不足，无法进行七日对比")
                print(f"可用的对比日期: {[d.strftime('%Y-%m-%d') for d in dates_to_compare]}")
                return

            print(f"对比日期: {[d.strftime('%Y-%m-%d') for d in dates_to_compare]}")

            # 生成对比图表
            generate_seven_day_comparison_charts(specific_dates=dates_to_compare)

        except ValueError:
            print("日期格式错误，请使用 YYYY-MM-DD 格式")

    else:
        print("无效选择，使用默认设置（对比最近7天）")
        generate_seven_day_comparison_charts(days_back=7)


if __name__ == "__main__":
    # 保留原有的调用方式，同时支持参数调用
    main()
