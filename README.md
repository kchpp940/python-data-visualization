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
