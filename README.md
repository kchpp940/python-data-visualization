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

启动前可单独执行环境检查，明确区分四类问题：

```bash
# 检查所有示例的环境就绪状态
python launcher.py check

# 检查指定示例
python launcher.py check dash-1
```

检查结果会按 **缺依赖 / 缺数据文件 / 缺入口脚本 / 缺启动器** 四类分别列出，并给出对应解决方法。

### 配置文件分工

启动入口由两个 JSON 配置文件驱动，**职责分离、互不干扰**：

| 文件 | 管什么 | 什么时候改 |
|------|--------|------------|
| `examples_manifest.json` | **示例列表** — 有哪些示例、叫什么、依赖哪些包/数据 | 新增或删除一个示例时 |
| `launch_schema.json` | **类型启动规则** — 每种 `type` 用什么命令、什么参数、什么工作目录、有哪些 fallback | 改变某类示例的启动方式时（如换一个 notebook 启动器） |

新增示例**只改 `examples_manifest.json`**，不需要动 `launch_schema.json`，也不需要改 `launcher.py`。

### 新增示例（最小配置）

在 `examples_manifest.json` 中追加一条记录。三种类型的最小配置如下：

**Dash 应用**

```json
"dash-your-id": {
  "type": "dash",
  "file": "your_dash_app.py",
  "title": "简短标题",
  "desc": "一句话描述",
  "data_files": ["EPA_fuel_economy_summary.csv"],
  "deps": ["pandas", "dash", "plotly"]
}
```

**Streamlit 应用**

```json
"st-your-id": {
  "type": "streamlit",
  "file": "your_streamlit_app.py",
  "title": "简短标题",
  "desc": "一句话描述",
  "data_files": ["EPA_fuel_economy_summary.csv"],
  "deps": ["pandas", "streamlit", "plotly"]
}
```

**Jupyter Notebook**

```json
"nb-chX-Y": {
  "type": "notebook",
  "file": "chX-exercise-Y.ipynb",
  "title": "第 X 章 练习 Y",
  "desc": "一句话描述",
  "data_files": ["EPA_fuel_economy.csv"],
  "deps": ["pandas", "numpy", "matplotlib"]
}
```

字段说明：

| 字段 | 必填 | 说明 |
|------|------|------|
| `type` | ✅ | `dash` / `streamlit` / `notebook` / `script`，对应 `launch_schema.json` 中的启动规则 |
| `file` | ✅ | 脚本文件名，相对于 `code/` 目录 |
| `title` | ✅ | 显示在列表中的简短名称 |
| `desc` | ✅ | 补充说明 |
| `data_files` | ✅ | 依赖的数据文件名（空数组为无依赖），相对于 `code/data/raw/` |
| `deps` | ✅ | 需要检查的 Python 包列表（空数组为无依赖） |

示例 ID 命名约定：`dash-*` / `st-*` / `nb-chX-Y`（第X章第Y题）。

### 新增启动类型（高级）

如果需要支持一种全新的示例类型（例如 `bokeh` 或 `gradio`），在 `launch_schema.json` 中追加一条类型规则：

```json
"bokeh": {
  "command": "{python}",
  "args_template": ["-m", "bokeh", "serve", "{file}"],
  "cwd": "code",
  "check_package": "bokeh",
  "fallbacks": []
}
```

然后在 `examples_manifest.json` 中使用 `"type": "bokeh"` 即可，无需修改任何 Python 代码。
