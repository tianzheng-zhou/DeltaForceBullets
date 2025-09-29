# 三角洲子弹价格数据分析工具

[![License](https://img.shields.io/badge/License-MIT-green)](https://opensource.org/licenses/MIT)

自动化三角洲子弹数据分析工具，支持价格数据抓取、清洗分类、多维度可视化分析。

## 主要功能

给三角洲大部分子弹的数据做可视化，便于炒子弹差价赚哈夫币

也可以自己尝试做不同的可视化方式。

## 环境要求

- 你自己把需要的库装上就行了
- 作者的python版本：3.12

## 快速开始

1. 克隆仓库
2. 配置环境变量（需要github token防止下载toke限制）

   ```bash
   # Windows
   setx GITHUB_TOKEN "your_token_here"

   # Linux/MacOS
   export GITHUB_TOKEN="your_token_here"
   ```
   
3. 运行主程序main.py

   ```bash
   python main.py
   ```
   在生成图片的时候，需要的时间比较长。
   
4. 图片文件存储在price_charts中
5. 注意：如果出现前几天的数据缺失，程序可能不会重新下载，这时候可以选择清空缓存，这会使得程序重新下载并生成前几天的图片。运行cache_manager.py清空缓存，程序会要求用户确认是否清空缓存。当然，还有一种办法，可以清空特定日期的缓存，就是打开cache.json文件，找到对应日期，并把所有的true改为false，这样会使得程序重新尝试这些步骤。


## 项目结构

├── price_history/          # 原始价格数据

├── filtered_price_history/ # 筛选后数据

├── classified_price_history/ # 分类数据

├── bullet_data/            # 子弹详细数据

├── price_charts/           # 生成的可视化图表

├── cache_manager.py        # 缓存管理系统

└── main.py                 # 主程序入口

## 注意事项

源数据10分钟更新一次。

由于作者水平有限，这个项目结构有些臃肿，存储了很多中间的数据文件，而且bug多多。

而且从数据来源下载的所有文件都会存在price_history中，filtered_price_history classified_price_history bullet_data这三个文件夹存储了中间过程的数据

由于一级，二级子弹没有炒的必要，所以作者把这些子弹的数据都加入了黑名单。

如果你想要分析其他子弹的数据，可以在main.py中的name_white_list中添加你想要分析的子弹名称。但是没有.300子弹的数据。

这么说，也可以看别的什么物品的数据（doge）

注意：添加的名称必须与数据来源中的名称完全一致，包括大小写。

## 数据来源

[orzice/DeltaForcePrice: 三角洲行动API-真实游戏内交易行实时价格](https://github.com/orzice/DeltaForcePrice) 但是这个API没有.300子弹的数据
