import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional


class CacheManager:
    """缓存管理器 - 纯粹的接口提供者，不包含文件验证逻辑

==========使用示例==========
# 初始化缓存管理器
cache_manager = CacheManager()

# 其他程序决定如何验证文件并更新缓存
def process_date(date_str):
    # 1. 检查缓存状态
    if cache_manager.is_date_fully_processed(date_str):
        print(f"日期 {date_str} 已完全处理，跳过")
        return

    # 2. 执行处理步骤（由调用程序决定验证逻辑）
    if not cache_manager.get_date_status(date_str)["download_complete"]:
        # 执行下载逻辑
        download_success = download_price_data(date_str)
        # 更新缓存状态
        cache_manager.update_step_status(date_str, "download", download_success)

    # 3. 类似处理其他步骤...

    # 4. 生成图片
    missing_images = cache_manager.get_missing_images(date_str)
    for image_type in missing_images:
        generate_success = generate_image(date_str, image_type)
        cache_manager.update_image_status(date_str, image_type, generate_success)



    """

    def __init__(self, cache_file: str = "cache.json"):
        """
        初始化缓存管理器

        Args:
            cache_file: 缓存文件路径
        """
        self.cache_file = cache_file
        self.cache_data = self._load_cache()

        # 定义支持的图片类型（可扩展）
        self.image_types = {
            "individual_bullet": "单个子弹价格走势图",
            "all_bullets_together": "所有子弹综合走势图",
            "price_comparison": "价格对比图",
            "trend_analysis": "趋势分析图"
        }

    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_cache(self) -> bool:
        """保存缓存数据"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def add_image_type(self, image_type: str, description: str) -> None:
        """添加新的图片类型支持"""
        self.image_types[image_type] = description
        print(f"✓ 添加图片类型: {image_type} - {description}")

    def get_date_status(self, date_str: str) -> Dict:
        """获取指定日期的完整处理状态"""
        default_status = {
            "download_complete": False,
            "filter_complete": False,
            "classification_complete": False,
            "further_classification_complete": False,
            "files_verified": False,
            "images_generated": {},  # 记录每种图片的生成状态
            "last_updated": None
        }

        # 初始化图片生成状态
        for image_type in self.image_types:
            default_status["images_generated"][image_type] = False

        status = self.cache_data.get(date_str, default_status)

        # 确保新的图片类型有对应的状态记录
        for image_type in self.image_types:
            if image_type not in status["images_generated"]:
                status["images_generated"][image_type] = False

        return status

    def set_date_status(self, date_str: str, status_data: Dict) -> bool:
        """
        设置指定日期的完整状态

        Args:
            date_str: 日期字符串
            status_data: 完整的状态数据

        Returns:
            保存是否成功
        """
        self.cache_data[date_str] = status_data
        self.cache_data[date_str]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._save_cache()

    def update_step_status(self, date_str: str, step_name: str, status: bool = True) -> bool:
        """
        更新指定步骤的状态

        该方法允许调用程序更新特定日期中某个处理步骤的完成状态。
        支持更新基本处理步骤和图片生成状态。

        Args:
            date_str (str): 日期字符串，格式为 "YYYY-MM-DD"
            step_name (str): 步骤名称，可以是基本步骤或图片类型
                            - 基本步骤: "download", "filter", "classification",
                                      "further_classification", "files_verified"
                            - 图片步骤: "image_{image_type}" 格式，如 "image_individual_bullet"
            status (bool): 步骤状态，True表示完成，False表示未完成，默认为True

        Returns:
            bool: 缓存保存是否成功

        Example:
             # 更新下载步骤状态为完成
             cache_manager.update_step_status("2024-01-15", "download", True)
            True

             # 更新单个子弹图片生成状态为完成
             cache_manager.update_step_status("2024-01-15", "image_individual_bullet", True)
            True
        """
        if date_str not in self.cache_data:
            self.cache_data[date_str] = self.get_date_status(date_str)

        step_mapping = {
            "download": "download_complete",
            "filter": "filter_complete",
            "classification": "classification_complete",
            "further_classification": "further_classification_complete",
            "files_verified": "files_verified"
        }

        if step_name in step_mapping:
            self.cache_data[date_str][step_mapping[step_name]] = status
        elif step_name.startswith("image_"):
            # 处理图片生成状态更新
            image_type = step_name.replace("image_", "")
            if image_type in self.image_types:
                self.cache_data[date_str]["images_generated"][image_type] = status

        self.cache_data[date_str]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._save_cache()

    def update_image_status(self, date_str: str, image_type: str, status: bool = True) -> bool:
        """更新指定图片类型的生成状态"""
        return self.update_step_status(date_str, f"image_{image_type}", status)

    def is_date_fully_processed(self, date_str: str, required_images: Optional[List[str]] = None) -> bool:
        """检查指定日期是否已完全处理（包括指定的图片类型）"""
        status = self.get_date_status(date_str)

        # 检查基本处理步骤
        basic_steps_complete = all([
            status["download_complete"],
            status["filter_complete"],
            status["classification_complete"],
            status["further_classification_complete"],
            status["files_verified"]
        ])

        if not basic_steps_complete:
            return False

        # 检查图片生成状态
        if required_images is None:
            required_images = list(self.image_types.keys())

        for image_type in required_images:
            if not status["images_generated"].get(image_type, False):
                return False

        return True

    def get_missing_images(self, date_str: str, required_types: Optional[List[str]] = None) -> List[str]:
        """获取指定日期缺失的图片类型"""
        if required_types is None:
            required_types = list(self.image_types.keys())

        status = self.get_date_status(date_str)
        missing_images = []

        for image_type in required_types:
            if not status["images_generated"].get(image_type, False):
                missing_images.append(image_type)

        return missing_images

    def get_incomplete_dates(self, days_back: int = 7, required_images: Optional[List[str]] = None) -> List[str]:
        """获取最近几天中未完全处理的日期"""
        incomplete_dates = []
        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if not self.is_date_fully_processed(date, required_images):
                incomplete_dates.append(date)
        return incomplete_dates

    def get_processing_summary(self, date_str: str) -> Dict:
        """获取指定日期的处理摘要"""
        status = self.get_date_status(date_str)
        summary = {
            "date": date_str,
            "basic_steps_complete": all([
                status["download_complete"],
                status["filter_complete"],
                status["classification_complete"],
                status["further_classification_complete"],
                status["files_verified"]
            ]),
            "images_status": {},
            "missing_images": [],
            "last_updated": status["last_updated"]
        }

        for image_type, description in self.image_types.items():
            generated = status["images_generated"].get(image_type, False)
            summary["images_status"][f"{image_type} ({description})"] = "✓" if generated else "✗"
            if not generated:
                summary["missing_images"].append(image_type)

        return summary

    def cleanup_old_cache(self, days_to_keep: int = 30) -> bool:
        """清理超过指定天数的旧缓存"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")

        dates_to_remove = []
        for date_str in self.cache_data.keys():
            if date_str < cutoff_date:
                dates_to_remove.append(date_str)

        for date_str in dates_to_remove:
            del self.cache_data[date_str]

        return self._save_cache()

    def export_cache_report(self, output_file: str = "cache_report.json") -> bool:
        """导出缓存报告"""
        report = {
            "cache_info": {
                "total_dates": len(self.cache_data),
                "image_types": self.image_types,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "dates_status": {}
        }

        for date_str, status in self.cache_data.items():
            report["dates_status"][date_str] = self.get_processing_summary(date_str)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def get_all_dates(self) -> List[str]:
        """获取缓存中所有的日期"""
        return list(self.cache_data.keys())

    def delete_date_cache(self, date_str: str) -> bool:
        """删除指定日期的缓存"""
        if date_str in self.cache_data:
            del self.cache_data[date_str]
            return self._save_cache()
        return False

    def clear_cache(self) -> bool:
        """清空所有缓存"""
        self.cache_data = {}
        return self._save_cache()

    def get_download_status(self, date_str):
        """获取指定日期的下载状态"""
        # 获取缓存数据，如果不存在则使用默认值
        status_data = self.cache_data.get(date_str, {})

        # 确保返回的字典包含downloaded键
        return {
            "downloaded": status_data.get("downloaded", False),
            "last_checked": status_data.get("last_checked", None)
        }

    def set_download_status(self, date_str, downloaded=True):
        """设置指定日期的下载状态"""
        self.cache_data[date_str] = {
            "downloaded": downloaded,
            "last_checked": datetime.now().isoformat()
        }
        self._save_cache()

    def check_date_range_status(self, start_date, end_date):
        """检查日期范围内的下载状态"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        current_date = start
        all_downloaded = True
        missing_dates = []

        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            status = self.get_download_status(date_str)

            if not status["downloaded"]:
                all_downloaded = False
                missing_dates.append(date_str)

            current_date += timedelta(days=1)

        return all_downloaded, missing_dates

    def mark_range_as_downloaded(self, start_date, end_date):
        """将日期范围内的所有日期标记为已下载（除了今天）"""
        today = datetime.now().strftime("%Y-%m-%d")
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        current_date = start
        updated_count = 0

        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            # 不标记今天为已下载
            if date_str != today:
                status = self.get_download_status(date_str)
                if not status["downloaded"]:
                    self.set_download_status(date_str, True)
                    updated_count += 1

            current_date += timedelta(days=1)

        return updated_count

    def get_filter_status(self, date_str):
        """获取指定日期的筛选状态"""
        # 获取缓存数据，如果不存在则使用默认值
        status_data = self.cache_data.get(date_str, {})

        # 确保返回的字典包含filtered键
        return {
            "filtered": status_data.get("filtered", False),
            "last_filtered": status_data.get("last_filtered", None)
        }

    def set_filter_status(self, date_str, filtered=True):
        """设置指定日期的筛选状态"""
        if date_str not in self.cache_data:
            self.cache_data[date_str] = {}
        self.cache_data[date_str]["filtered"] = filtered
        self.cache_data[date_str]["last_filtered"] = datetime.now().isoformat()
        return self._save_cache()

    def check_filter_range_status(self, start_date, end_date):
        """检查日期范围内的筛选状态"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        current_date = start
        all_filtered = True
        missing_filter_dates = []

        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            status = self.get_filter_status(date_str)

            if not status["filtered"]:
                all_filtered = False
                missing_filter_dates.append(date_str)

            current_date += timedelta(days=1)

        return all_filtered, missing_filter_dates

    def mark_range_as_filtered(self, start_date, end_date):
        """将日期范围内的所有日期标记为已筛选（除了今天）"""
        today = datetime.now().strftime("%Y-%m-%d")
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        current_date = start
        updated_count = 0

        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            # 不标记今天为已筛选
            if date_str != today:
                status = self.get_filter_status(date_str)
                if not status["filtered"]:
                    self.set_filter_status(date_str, True)
                    updated_count += 1

            current_date += timedelta(days=1)

        return updated_count

    def get_chart_status(self, date_str, chart_type):
        """获取指定日期和图表类型的生成状态"""
        # 获取缓存数据，如果不存在则使用默认值
        status_data = self.cache_data.get(date_str, {})

        # 确保返回的字典包含chart_type键
        return {
            "generated": status_data.get(f"chart_{chart_type}_generated", False),
            "last_generated": status_data.get(f"chart_{chart_type}_last_generated", None)
        }

    def set_chart_status(self, date_str, chart_type, generated=True):
        """设置指定日期和图表类型的生成状态"""
        if date_str not in self.cache_data:
            self.cache_data[date_str] = {}

        self.cache_data[date_str][f"chart_{chart_type}_generated"] = generated
        self.cache_data[date_str][f"chart_{chart_type}_last_generated"] = datetime.now().isoformat()
        return self._save_cache()

    def check_chart_range_status(self, start_date, end_date, chart_type):
        """检查日期范围内指定图表类型的生成状态"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        current_date = start
        all_generated = True
        missing_dates = []

        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            status = self.get_chart_status(date_str, chart_type)

            if not status["generated"]:
                all_generated = False
                missing_dates.append(date_str)

            current_date += timedelta(days=1)

        return all_generated, missing_dates

    def mark_range_as_charts_generated(self, start_date, end_date, chart_type):
        """将日期范围内的所有日期标记为指定图表类型已生成（除了今天）"""
        today = datetime.now().strftime("%Y-%m-%d")
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        current_date = start
        updated_count = 0

        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            # 不标记今天为已生成
            if date_str != today:
                status = self.get_chart_status(date_str, chart_type)
                if not status["generated"]:
                    self.set_chart_status(date_str, chart_type, True)
                    updated_count += 1

            current_date += timedelta(days=1)

        return updated_count

    def get_missing_charts(self, date_str, required_chart_types=None):
        """获取指定日期缺失的图表类型"""
        if required_chart_types is None:
            required_chart_types = ["single_day", "three_day", "seven_day"]

        missing_charts = []
        for chart_type in required_chart_types:
            status = self.get_chart_status(date_str, chart_type)
            if not status["generated"]:
                missing_charts.append(chart_type)

        return missing_charts

    def is_date_charts_complete(self, date_str, required_chart_types=None):
        """检查指定日期的所有图表是否已生成"""
        if required_chart_types is None:
            required_chart_types = ["single_day", "three_day", "seven_day"]

        for chart_type in required_chart_types:
            status = self.get_chart_status(date_str, chart_type)
            if not status["generated"]:
                return False

        return True


if __name__ == "__main__":
    cache_manager = CacheManager()
    delete = input("是否确认清空缓存？(y/n)")
    if delete == "y":
        cache_manager.clear_cache()
        print("缓存已清空")
