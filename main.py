import os
from datetime import datetime, timedelta

# 导入功能模块
from 获取json文件 import fetch_github_file_with_history
from 删减json文件 import filter_files_by_datetime, read_json_files, filter_and_save_json
from 子弹分类 import process_all_files
from 进一步分类 import process_bullet_data
from 生成走势图.单日子弹 import plot_individual_bullet_prices, plot_all_bullets_together


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
    """下载价格数据 - 使用获取json文件.py中的函数"""
    print("=" * 50)
    print("步骤1: 下载价格数据")
    print("=" * 50)

    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        fetch_github_file_with_history(
            owner="orzice",
            repo="DeltaForcePrice",
            filepath="price.json",
            output_dir="price_history",
            start_date=today,
            end_date=today
        )
        print("✓ 价格数据下载完成")
        return True
    except Exception as e:
        print(f"✗ 下载价格数据失败: {e}")
        return False


def filter_price_data():
    """筛选价格数据 - 使用删减json文件.py中的函数"""
    print("\n" + "=" * 50)
    print("步骤2: 筛选价格数据")
    print("=" * 50)

    try:
        # 获取最近1天的文件
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)

        # 使用filter_files_by_datetime函数筛选文件
        json_files = filter_files_by_datetime("price_history", start_date, end_date)

        if not json_files:
            print("未找到符合条件的JSON文件")
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
        return saved_count > 0

    except Exception as e:
        print(f"✗ 筛选价格数据失败: {e}")
        return False


def classify_bullet_data():
    """分类子弹数据 - 使用子弹分类.py中的函数"""
    print("\n" + "=" * 50)
    print("步骤3: 子弹分类")
    print("=" * 50)

    try:
        # 使用process_all_files函数处理所有文件
        process_all_files()
        print("✓ 子弹分类完成")
        return True
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
    """生成图表 - 使用生成图表.py中的函数"""
    print("\n" + "=" * 50)
    print("步骤5: 生成图表")
    print("=" * 50)

    try:
        # 使用plot_individual_bullet_prices函数生成单个子弹图表
        plot_individual_bullet_prices()

        # 使用plot_all_bullets_together函数生成综合图表
        plot_all_bullets_together()

        print("✓ 图表生成完成")
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