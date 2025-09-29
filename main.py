import os
import re
from datetime import datetime, timedelta

# 导入功能模块
from 获取json文件 import fetch_github_file_with_history
from 删减json文件 import filter_files_by_datetime, read_json_files, filter_and_save_json
from 子弹分类 import process_all_files, process_files_by_date
from 进一步分类 import process_bullet_data
from 生成走势图.单日子弹 import plot_individual_bullet_prices, plot_all_bullets_together
from 生成走势图.三日子弹对比 import generate_three_day_comparison_charts
from 生成走势图.七日子弹对比 import generate_seven_day_comparison_charts

from cache_manager import CacheManager


def check_dependencies():
    """检查必要的依赖库是否已安装"""
    required_packages = ['requests', 'matplotlib', 'numpy']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("缺少必要的依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请使用以下命令安装:")
        print("pip install " + " ".join(missing_packages))
        return False
    return True


def create_directories():
    """创建必要的目录结构"""
    directories = [
        'price_history',
        'filtered_price_history',
        'classified_price_history',
        'bullet_data',
        'price_charts'
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"创建目录: {directory}")


def download_price_data():
    """下载价格数据 - 使用缓存管理器优化下载流程"""
    print("=" * 50)
    print("步骤1: 下载价格数据")
    print("=" * 50)

    # 初始化缓存管理器
    cache_manager = CacheManager()

    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # 设置目标日期范围：2025-09-13 到昨天
    target_start_date = "2025-09-13"
    target_end_date = yesterday

    print(f"检查缓存状态: {target_start_date} 到 {target_end_date}")

    # 检查目标日期范围内的下载状态
    all_downloaded, missing_dates = cache_manager.check_date_range_status(
        target_start_date, target_end_date
    )

    if all_downloaded:
        print("✓ 目标日期范围内的数据已全部下载完成")
    else:
        print(f"发现 {len(missing_dates)} 个缺失的日期: {missing_dates}")

        # 尝试下载缺失的数据
        if missing_dates:
            print("开始下载缺失的数据...")
            try:
                # 使用环境变量中的token
                github_token = os.getenv('GITHUB_TOKEN')
                fetch_github_file_with_history(
                    owner="orzice",
                    repo="DeltaForcePrice",
                    filepath="price.json",
                    output_dir="price_history",
                    start_date=missing_dates[0],
                    end_date=missing_dates[-1],
                    github_token=github_token,  # 添加token参数
                    request_delay=0  # 添加请求间隔
                )
                print("✓ 缺失数据下载完成")
                # 将昨天之前的数据标记为已下载
                updated_count = cache_manager.mark_range_as_downloaded(target_start_date, target_end_date)
                print(f"✓ 已将 {updated_count} 个日期的下载状态置为 True")

            except Exception as e:
                print(f"✗ 下载缺失数据失败: {e}")

    # 下载今天的数据（保持下载状态为 False）
    print(f"\n下载今天的数据: {today}")
    try:
        fetch_github_file_with_history(
            owner="orzice",
            repo="DeltaForcePrice",
            filepath="price.json",
            output_dir="price_history",
            start_date=today,
            end_date=today
        )
        print("✓ 今天的数据下载完成")
        # 注意：今天的数据下载状态保持为 False
        return True
    except Exception as e:
        print(f"✗ 下载今天数据失败: {e}")
        return False


def filter_price_data():
    """筛选价格数据 - 使用缓存机制优化筛选流程"""
    print("\n" + "=" * 50)
    print("步骤2: 筛选价格数据")
    print("=" * 50)

    # 初始化缓存管理器
    cache_manager = CacheManager()

    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # 设置目标日期范围：2025-09-13 到昨天
    target_start_date = "2025-09-13"
    target_end_date = yesterday

    print(f"检查筛选缓存状态: {target_start_date} 到 {target_end_date}")

    # 检查目标日期范围内的筛选状态
    all_filtered, missing_filter_dates = cache_manager.check_filter_range_status(
        target_start_date, target_end_date
    )

    if all_filtered:
        print("✓ 目标日期范围内的数据已全部筛选完成")
    else:
        print(f"发现 {len(missing_filter_dates)} 个需要筛选的日期: {missing_filter_dates}")

        # 尝试筛选缺失的数据
        if missing_filter_dates:
            print("开始筛选缺失的数据...")
            try:
                # 获取需要筛选的日期对应的文件
                start_date = missing_filter_dates[0]
                end_date = missing_filter_dates[-1]

                # 使用filter_files_by_datetime函数筛选文件
                start_datetime = datetime.combine(datetime.strptime(start_date, "%Y-%m-%d").date(), datetime.min.time())
                end_datetime = datetime.combine(datetime.strptime(end_date, "%Y-%m-%d").date(), datetime.max.time())
                json_files = filter_files_by_datetime("price_history", start_datetime, end_datetime)

                if not json_files:
                    print("未找到指定日期的JSON文件，尝试查找最近的文件...")
                    # 查找最近7天内的文件
                    recent_datetime = datetime.now() - timedelta(days=7)
                    json_files = filter_files_by_datetime("price_history", recent_datetime, datetime.now())

                    if not json_files:
                        print("未找到任何可用的数据文件")
                        return False

                    # 按时间排序，获取最新的文件
                    json_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                    latest_file = json_files[0] if json_files else None

                    if latest_file:
                        print(f"使用最新数据文件: {os.path.basename(latest_file)}")
                        json_files = [latest_file]
                    else:
                        print("未找到任何可用的数据文件")
                        return False

                print(f"找到 {len(json_files)} 个符合条件的文件")

                # 使用read_json_files函数读取文件内容
                file_contents = read_json_files(json_files)

                # 定义黑名单和白名单（与删减json文件.py中一致）
                name_blacklist = [
                    "93R", ".357 Magnum JHP", ".357 Magnum HP", ".357 Magnum FMJ",
                    ".45 ACP JHP", ".45 ACP HS", ".50 AE FMJ", ".50 AE JHP",
                    ".50 AE HP", "5.45x39mm PRS", "5.45x39mm T", "5.56x45mm FMJ",
                    "5.56x45mm RRLP", "5.7x28mm SS197SR", "5.7x28mm SS198LF",
                    "5.8x42mm DBP87", "7.62x39mm T45M", "7.62x39mm LP",
                    "7.62x51mm Ultra Nosler", "9x19mm Pst", "9x19mm PSO",
                    "45-70 Govt FTX", "45-70 Govt FMJ", "45-70 Govt RN"
                ]

                name_whitelist = ["12.7x55mm PD12双头弹"]

                # 使用filter_and_save_json函数筛选并保存
                saved_count = filter_and_save_json(
                    file_contents,
                    "filtered_price_history",
                    blacklist_names=name_blacklist,
                    whitelist_names=name_whitelist
                )

                print(f"✓ 筛选完成，保存了 {saved_count} 个文件")

                # 将昨天之前的数据标记为已筛选
                updated_count = cache_manager.mark_range_as_filtered(target_start_date, target_end_date)
                print(f"✓ 已将 {updated_count} 个日期的筛选状态置为 True")

                return saved_count > 0

            except Exception as e:
                print(f"✗ 筛选数据失败: {e}")
                return False

    # 筛选今天的数据（保持筛选状态为 False）
    print(f"\n筛选今天的数据: {today}")
    try:
        # 获取今天的文件 - 修正时间范围
        today_date = datetime.now().date()
        start_datetime = datetime.combine(today_date, datetime.min.time())  # 今天00:00:00
        end_datetime = datetime.combine(today_date, datetime.max.time())  # 今天23:59:59.999999

        json_files = filter_files_by_datetime("price_history", start_datetime, end_datetime)

        if not json_files:
            print("未找到今天的数据文件，尝试使用最新可用数据...")
            # 获取最近7天的文件，使用最新的数据
            recent_datetime = datetime.now() - timedelta(days=7)
            json_files = filter_files_by_datetime("price_history", recent_datetime, datetime.now())

            if not json_files:
                print("未找到任何可用的数据文件")
                return False

            # 按时间排序，获取最新的文件
            json_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest_file = json_files[0] if json_files else None

            if latest_file:
                print(f"使用最新数据文件: {os.path.basename(latest_file)}")
                json_files = [latest_file]
            else:
                print("未找到任何可用的数据文件")
                return False

        print(f"找到 {len(json_files)} 个文件")
        # 使用read_json_files函数读取文件内容
        file_contents = read_json_files(json_files)

        # 定义黑名单和白名单
        name_blacklist = [
            "93R", ".357 Magnum JHP", ".357 Magnum HP", ".357 Magnum FMJ",
            ".45 ACP JHP", ".45 ACP HS", ".50 AE FMJ", ".50 AE JHP",
            ".50 AE HP", "5.45x39mm PRS", "5.45x39mm T", "5.56x45mm FMJ",
            "5.56x45mm RRLP", "5.7x28mm SS197SR", "5.7x28mm SS198LF",
            "5.8x42mm DBP87", "7.62x39mm T45M", "7.62x39mm LP",
            "7.62x51mm Ultra Nosler", "9x19mm Pst", "9x19mm PSO",
            "45-70 Govt FTX", "45-70 Govt FMJ", "45-70 Govt RN"
        ]

        name_whitelist = ["12.7x55mm PD12双头弹"]

        # 使用filter_and_save_json函数筛选并保存
        saved_count = filter_and_save_json(
            file_contents,
            "filtered_price_history",
            blacklist_names=name_blacklist,
            whitelist_names=name_whitelist
        )

        print(f"✓ 数据筛选完成，保存了 {saved_count} 个文件")
        # 注意：今天的数据筛选状态保持为 False
        return saved_count > 0

    except Exception as e:
        print(f"✗ 筛选数据失败: {e}")
        return False


def classify_bullet_data():
    """分类子弹数据 - 使用子弹分类.py中的函数"""
    print("\n" + "=" * 50)
    print("步骤3: 子弹分类")
    print("=" * 50)

    try:
        # 初始化缓存管理器
        cache_manager = CacheManager()

        # 获取今天和昨天的日期
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # 检查昨天之前的数据是否已分类
        target_start_date = datetime.strptime("2025-09-13", "%Y-%m-%d").date()
        target_end_date = yesterday

        # 检查classified_price_history文件夹中的文件来确定实际需要分类的日期
        classified_folder = 'classified_price_history'
        if not os.path.exists(classified_folder):
            os.makedirs(classified_folder)

        # 获取已存在的分类文件
        existing_files = [f for f in os.listdir(classified_folder) if f.endswith('.json')]

        # 提取已存在的日期
        existing_dates = set()
        for filename in existing_files:
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            if date_match:
                existing_dates.add(date_match.group(1))

        # 获取需要分类的日期 - 基于文件存在性而不是缓存
        missing_classify_dates = []
        current_date = target_start_date
        while current_date <= target_end_date:
            date_str = current_date.strftime("%Y-%m-%d")

            # 如果该日期的文件不存在，则需要分类
            if date_str not in existing_dates:
                missing_classify_dates.append(date_str)

            current_date += timedelta(days=1)

        print(f"发现 {len(missing_classify_dates)} 个需要分类的日期: {missing_classify_dates}")

        # 如果有需要分类的数据，执行分类
        if missing_classify_dates:
            print("开始分类缺失的数据...")
            try:
                # 使用process_files_by_date函数按日期处理
                from 子弹分类 import process_files_by_date
                processed_count = process_files_by_date(missing_classify_dates)

                if processed_count > 0:
                    print(f"✓ 子弹分类完成，处理了 {processed_count} 个文件")

                    # 将昨天之前的数据标记为已分类 - 使用与缓存文件一致的数据结构
                    updated_count = 0
                    for date_str in missing_classify_dates:
                        if datetime.strptime(date_str, "%Y-%m-%d").date() <= yesterday:
                            # 直接更新缓存数据
                            if date_str not in cache_manager.cache_data:
                                cache_manager.cache_data[date_str] = {}

                            cache_manager.cache_data[date_str]["classification_complete"] = True
                            cache_manager.cache_data[date_str]["last_updated"] = datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S")
                            updated_count += 1

                    # 保存缓存
                    cache_manager._save_cache()
                    print(f"✓ 已将 {updated_count} 个日期的分类状态置为 True")
                    return True
                else:
                    print("✗ 没有文件被处理，分类失败")
                    return False

            except Exception as e:
                print(f"✗ 子弹分类失败: {e}")
                return False
        else:
            print("✓ 所有历史数据已分类完成，跳过")

        # 分类今天的数据（保持分类状态为 False）
        print(f"\n分类今天的数据: {today}")
        try:
            # 检查今天的数据是否已存在
            today_str = today.strftime("%Y-%m-%d")
            today_file = os.path.join('classified_price_history', f"{today_str}_classified.json")

            if os.path.exists(today_file):
                print(f"✓ 今天的数据已存在，跳过处理")
                return True  # 今天的数据已存在，返回True表示成功跳过

            # 使用process_files_by_date函数处理今天的数据
            from 子弹分类 import process_files_by_date
            processed_count = process_files_by_date([today_str])

            # 修改判断逻辑，0个文件也视为成功（可能数据没有变化）
            print(f"✓ 今天的数据处理完成，共处理 {processed_count} 个文件")
            return True

        except Exception as e:
            print(f"✗ 今天的数据分类失败: {e}")
            return False

    except Exception as e:
        print(f"✗ 子弹分类失败: {e}")
        return False


def further_classify_data():
    """进一步分类数据 - 使用进一步分类.py中的函数"""
    print("\n" + "=" * 50)
    print("步骤4: 进一步分类")
    print("=" * 50)

    try:
        # 使用process_bullet_data函数进一步分类
        process_bullet_data()
        print("✓ 进一步分类完成")
        return True
    except Exception as e:
        print(f"✗ 进一步分类失败: {e}")
        return False


def generate_charts():
    """生成图表 - 使用独立的缓存标签为每种图表类型"""
    print("\n" + "=" * 50)
    print("步骤5: 生成图表")
    print("=" * 50)

    try:
        # 初始化缓存管理器
        cache_manager = CacheManager()

        # 获取最近7天的日期（包括今天）
        today = datetime.now().date()
        dates_to_process = []
        for i in range(7):
            date_obj = today - timedelta(days=i)
            dates_to_process.append(date_obj)

        # 定义三种图表类型及其对应的生成函数
        chart_types = {
            "single_day": {
                "name": "单日子弹价格走势图",
                "function": plot_individual_bullet_prices
            },
            "three_day": {
                "name": "三日子弹对比图",
                "function": generate_three_day_comparison_charts
            },
            "seven_day": {
                "name": "七日子弹对比图",
                "function": generate_seven_day_comparison_charts
            }
        }

        # 为每个日期生成缺失的图表
        total_generated = 0
        for date_obj in dates_to_process:
            date_str = date_obj.strftime("%Y-%m-%d")
            print(f"\n处理日期: {date_str}")

            # 检查该日期缺失的图表类型
            missing_charts = cache_manager.get_missing_charts(date_str)

            if not missing_charts:
                print(f"  ✓ 所有图表已生成，跳过")
                continue

            # 生成缺失的图表
            for chart_type in missing_charts:
                if chart_type in chart_types:
                    chart_info = chart_types[chart_type]
                    print(f"  生成 {chart_info['name']}...")

                    try:
                        # 调用对应的图表生成函数
                        if chart_type == "single_day":
                            # 单日子弹价格走势图只需要日期参数
                            chart_info['function'](date_obj)
                        elif chart_type == "three_day":
                            # 三日子弹对比图需要指定对比日期
                            chart_info['function'](specific_dates=[date_obj - timedelta(days=2),
                                                                   date_obj - timedelta(days=1),
                                                                   date_obj])
                        elif chart_type == "seven_day":
                            # 七日子弹对比图需要指定对比日期
                            chart_info['function'](specific_dates=[date_obj - timedelta(days=6),
                                                                   date_obj - timedelta(days=5),
                                                                   date_obj - timedelta(days=4),
                                                                   date_obj - timedelta(days=3),
                                                                   date_obj - timedelta(days=2),
                                                                   date_obj - timedelta(days=1),
                                                                   date_obj])

                        # 更新缓存状态（如果是今天，不标记为已生成）
                        if date_obj != today:
                            cache_manager.set_chart_status(date_str, chart_type, True)
                            print(f"  ✓ {chart_info['name']} 生成完成")
                        else:
                            print(f"  ✓ {chart_info['name']} 生成完成（今天数据不标记缓存）")

                        total_generated += 1

                    except Exception as e:
                        print(f"  ✗ 生成 {chart_info['name']} 失败: {e}")

            # 如果是昨天或更早的日期，检查是否所有图表都已生成
            if date_obj < today:
                if cache_manager.is_date_charts_complete(date_str):
                    print(f"  ✓ 日期 {date_str} 的所有图表已完全生成")

        print(f"\n✓ 图表生成完成，共生成 {total_generated} 个图表")
        return True

    except Exception as e:
        print(f"✗ 图表生成失败: {e}")
        return False


def main():
    """主程序"""
    print("三角洲炒股数据分析工具")
    print("=" * 60)

    # 检查依赖
    if not check_dependencies():
        return

    # 创建目录
    create_directories()

    # 执行所有步骤
    steps = [
        ("下载价格数据", download_price_data),
        ("筛选价格数据", filter_price_data),
        ("子弹分类", classify_bullet_data),
        ("进一步分类", further_classify_data),
        ("生成图表", generate_charts)
    ]

    successful_steps = 0

    for step_name, step_function in steps:
        if step_function():
            successful_steps += 1
        else:
            print(f"步骤 '{step_name}' 失败，继续执行后续步骤...")

    print("\n" + "=" * 60)
    print(f"程序执行完成！成功步骤: {successful_steps}/{len(steps)}")

    if successful_steps == len(steps):
        print("✓ 所有步骤均成功完成！")
        print("\n生成的文件结构:")
        print("  - price_history/: 原始价格数据")
        print("  - filtered_price_history/: 筛选后的价格数据")
        print("  - classified_price_history/: 分类后的子弹数据")
        print("  - bullet_data/: 每个子弹的详细数据")
        print("  - price_charts/: 价格走势图表")
    else:
        print("⚠ 部分步骤失败，请检查错误信息")


if __name__ == "__main__":
    main()
