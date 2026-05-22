# Python Data Visualization course
Code and examples from our [**Python Data Visualization course**](https://training.talkpython.fm/courses/python-data-visualization).

[![](./readme_resources/python-data-visualization.jpg)](https://training.talkpython.fm/courses/python-data-visualization)

Have you ever been confused by all the different python plotting libraries? Have you tried to make a "simple" plot and gotten stuck and been unable to move forward? Do you want to make sophisticated, interactive data visualizations in python? If you answer yes, to any of these questions, then this course is for you.

## What's this course about and how is it different?

The python data visualization landscape has many different libraries. They are all powerful and useful but it can be confusing to determine what works best for you. This course is unique because you will learn about many of the most popular python visualization libraries. You will start by learning how to use each library to build simple visualizations. You will also explore more complex usage and identify the scenarios where each library shines.

By the end of this course, you will have a basic working knowledge of how to visualize data in python using multiple libraries. You will also learn which library is best for you and your coding style. Along the way, you'll learn general visualization concepts to make your plots more effective.

In addition to the overview material, we will cover some of the more complex, interactive visualization dashboard technologies.

## What topics are covered

In this course, you will:

- Review the python visualization landscape
- Explore core visualization concepts
- Use matplotlib to build and customize visualizations
- Build and customize simple plots with pandas
- Learn about seaborn and use it for statistical visualizations
- Create visualizations using Altair
- Generate interactive plots using the Plotly library
- Design interactive dashboards using Streamlit
- Construct highly custom and flexible dashboards using Plotly's Dash framework

View the full [**course outline**](https://training.talkpython.fm/courses/python-data-visualization#course_outline).

## Who is this course for?

Developers and Data Analysts that have some experience with python but have not developed a competency in a python visualization library. This course is also helpful for those that feel restricted by their current plotting tools and wish to explore other options.

**Note**: All software used during this course, including editors, Python language, etc., are 100% free and open source. You won't have to buy anything to take the course.

## Take the course

Data sciense is one of the hottest topic of the year and data visualization is a core skillset needed to properly communicate your results and discoveries. **Take this course** to get good at a wide variety of modern Python-based visualization libraries.

---

## 快速开始

### 一键运行示例

项目提供统一启动入口 `launcher.py`，自动检查依赖并启动各类示例：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 查看所有可用示例
python launcher.py list

# 3. 交互式选择（推荐）
python launcher.py

# 4. 或直接启动指定示例
python launcher.py run dash-full   # 启动完整 Dash 应用
python launcher.py run st-1        # 启动 Streamlit 示例
python launcher.py run nb-ch5      # 打开 Notebook
```

### 环境检查

启动前可单独执行环境检查，明确区分三类问题：

```bash
# 检查所有示例的环境就绪状态
python launcher.py check

# 检查指定示例
python launcher.py check dash-1
```

检查结果会按 **缺依赖 / 缺数据文件 / 缺入口脚本** 三类分别列出，并给出对应解决方法。

### 示例清单维护

所有示例注册在 `examples_manifest.json`，**新增示例无需修改 launcher.py**，只需在此文件追加一条记录：

```json
"your-example-id": {
  "type": "dash | streamlit | notebook",
  "file": "script_file.py",
  "title": "简短标题",
  "desc": "一句话描述",
  "data_files": ["data_file.csv"],
  "deps": ["pandas", "plotly"]
}
```

字段说明：

| 字段 | 必填 | 说明 |
|------|------|------|
| `type` | ✅ | `dash` / `streamlit` / `notebook`，决定启动命令 |
| `file` | ✅ | 脚本文件名，相对于 `code/` 目录 |
| `title` | ✅ | 显示在列表中的简短名称 |
| `desc` | ✅ | 补充说明 |
| `data_files` | ✅ | 依赖的数据文件名（空数组为无依赖），相对于 `code/data/raw/` |
| `deps` | ✅ | 需要检查的 Python 包列表（空数组为无依赖） |

示例 ID 命名约定：`dash-*` / `st-*` / `nb-chX-Y`（第X章第Y题）。

---

<!-- DATASET_INFO_START -->
## 数据集说明

> 本区块由 `DatasetService 自动生成，请勿手动编辑。

### Amazon 畅销书排行榜

- **来源**: Kaggle - Amazon Top 50 Bestselling Books
- **文件**: `AmazonBooks.xlsx`
- **行数**: 600
- **列数**: 7
- **标签**: 图书, 电商, 评分

Amazon 图书畅销榜数据，包含书名、作者、评分、评论数、价格、年份和 genre 分类。

#### 字段说明

| 字段名 | 显示名称 | 类型 | 单位 | 说明 | 缺失值 |
|--------|----------|------|------|------|--------|
| `Name` | 书名 | `str` | - | 图书名称 | 0 |
| `Author` | 作者 | `str` | - | 图书作者 | 0 |
| `User Rating` | 用户评分 | `float` | 星 | Amazon 用户平均评分 | 0 |
| `Reviews` | 评论数 | `int` | - | 用户评论数量 | 0 |
| `Price` | 价格 | `float` | $ | 图书售价 | 0 |
| `Year` | 年份 | `int` | - | 上榜年份 | 0 |
| `Genre` | 分类 | `str` | - | 图书类别（小说/非小说） | 0 |


---

### EPA 燃油经济性数据集（完整版）

- **来源**: https://www.fueleconomy.gov/
- **文件**: `EPA_fuel_economy.csv`
- **行数**: 24,210
- **列数**: 14
- **标签**: 燃油经济, 汽车, 环境, 原始数据

美国环保署发布的完整车辆燃油经济性测试数据，包含更详细的传动系统和燃油类型信息。

#### 字段说明

| 字段名 | 显示名称 | 类型 | 单位 | 说明 | 缺失值 |
|--------|----------|------|------|------|--------|
| `make` | 品牌 | `str` | - | 车辆制造商 | 0 |
| `model` | 型号 | `str` | - | 车型名称 | 0 |
| `year` | 年份 | `int` | - | 生产年份 | 0 |
| `cylinders` | 气缸数 | `int` | - | 发动机气缸数量 | 231 (0.95%) |
| `trany` | 变速箱 | `str` | - | 变速器类型（原始字段名） | 9 (0.04%) |
| `displ` | 排量 | `float` | L | 发动机排量（升） | 230 (0.95%) |
| `VClass` | 车型分类 | `str` | - | EPA 车型分类 | 0 |
| `co2` | CO2 排放 | `float` | g/mi | 二氧化碳排放量 | 0 |
| `barrels08` | 年耗油量 | `float` | 桶/年 | 年度燃油消耗（桶） | 0 |
| `fuelCost08` | 年燃油成本 | `float` | $ | 年度预计燃油成本 | 0 |
| `fuelType` | 燃料类型 | `str` | - | 使用的燃料类型 | 0 |
| `highway08` | 高速油耗 | `int` | MPG | 高速工况燃油经济性 | 0 |
| `city08` | 城市油耗 | `int` | MPG | 城市工况燃油经济性 | 0 |
| `comb08` | 综合油耗 | `int` | MPG | 综合工况燃油经济性 | 0 |


---

### EPA 燃油经济性数据集（摘要版）

- **来源**: https://www.fueleconomy.gov/
- **文件**: `EPA_fuel_economy_summary.csv`
- **行数**: 24,210
- **列数**: 16
- **标签**: 燃油经济, 汽车, 环境

美国环保署发布的车辆燃油经济性测试数据摘要，包含各车型的油耗、排放、成本等指标。

#### 字段说明

| 字段名 | 显示名称 | 类型 | 单位 | 说明 | 缺失值 |
|--------|----------|------|------|------|--------|
| `make` | 品牌 | `str` | - | 车辆制造商 | 0 |
| `model` | 型号 | `str` | - | 车型名称 | 0 |
| `year` | 年份 | `int` | - | 生产年份 | 0 |
| `transmission` | 变速箱 | `str` | - | 变速器类型 | 0 |
| `drive` | 驱动方式 | `str` | - | 驱动轮配置（前驱/后驱/四驱） | 0 |
| `date_range` | 日期范围 | `str` | - | 数据覆盖的时间范围 | 0 |
| `fuel_type_summary` | 燃料类型 | `str` | - | 使用的燃料类型摘要 | 0 |
| `class_summary` | 车型分类 | `str` | - | EPA 车型分类摘要 | 0 |
| `cylinders` | 气缸数 | `int` | - | 发动机气缸数量 | 231 (0.95%) |
| `displ` | 排量 | `float` | L | 发动机排量（升） | 230 (0.95%) |
| `co2` | CO2 排放 | `float` | g/mi | 二氧化碳排放量 | 0 |
| `barrels08` | 年耗油量 | `float` | 桶/年 | 年度燃油消耗（桶） | 0 |
| `fuelCost08` | 年燃油成本 | `float` | $ | 年度预计燃油成本 | 0 |
| `highway08` | 高速油耗 | `int` | MPG | 高速工况燃油经济性 | 0 |
| `city08` | 城市油耗 | `int` | MPG | 城市工况燃油经济性 | 0 |
| `comb08` | 综合油耗 | `int` | MPG | 综合工况燃油经济性 | 0 |


---

<!-- DATASET_INFO_END -->
