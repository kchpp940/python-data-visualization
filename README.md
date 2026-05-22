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

项目提供统一启动入口 `launcher.py`，从同一份配置（`examples_manifest.json` + `launch_schema.json`）读取示例元数据并启动各类示例：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 查看所有可用示例（从 manifest 实时读取）
python launcher.py list

# 3. 交互式选择（推荐）
python launcher.py

# 4. 或直接启动指定示例
python launcher.py run dash-full   # 启动完整 Dash 应用
python launcher.py run st-1        # 启动 Streamlit 示例
python launcher.py run nb-ch5-1    # 打开 Notebook
```

### 环境检查

启动前可单独执行环境检查，明确区分四类问题，并额外校验 README 与配置的一致性：

```bash
# 检查所有示例的环境就绪状态 + README 是否与配置漂移
python launcher.py check

# 检查指定示例（仅环境，不校验 README）
python launcher.py check dash-1
```

检查结果会按 **缺依赖 / 缺数据文件 / 缺入口脚本 / 缺启动器** 四类分别列出，并给出对应解决方法。若发现 README 与配置不一致，会提示运行 `python launcher.py generate-readme`。

### 配置文件分工

启动入口由两个 JSON 配置文件驱动，**职责分离、互不干扰**：

| 文件 | 管什么 | 什么时候改 |
|------|--------|------------|
| `examples_manifest.json` | **示例列表** — 有哪些示例、叫什么、依赖哪些包/数据 | 新增或删除一个示例时 |
| `launch_schema.json` | **类型启动规则** — 每种 `type` 用什么命令、什么参数、什么工作目录、有哪些 fallback | 改变某类示例的启动方式时（如换一个 notebook 启动器） |

新增示例**只改 `examples_manifest.json`**，不需要动 `launch_schema.json`，也不需要改 `launcher.py`。

<!-- BEGIN EXAMPLE_INVENTORY -->
### 示例清单（自动生成，勿手动编辑）

下表由 `examples_manifest.json` 自动生成，运行 `python launcher.py generate-readme` 更新。

| ID | 类型 | 标题 | 入口脚本 | 数据 | 依赖 |
|----|------|------|----------|------|------|
| `dash-1` | Dash | Dash 简单直方图 | `dash_simple_app_1.py` | EPA_fuel_economy_summary.csv | pandas, dash, plotly |
| `dash-2` | Dash | Dash 带下拉框的直方图 | `dash_simple_app_2.py` | EPA_fuel_economy_summary.csv | pandas, dash, plotly |
| `dash-full` | Dash | Dash 完整应用（Pin 对比） | `dash_full_app.py` | EPA_fuel_economy_summary.csv | pandas, dash, plotly |
| `dash-html` | Dash | Dash 纯 HTML 布局示例 | `dash_html_gen.py` | — | dash, plotly |
| `nb-ch3-1` | Notebook | 第 3 章 练习 1 | `ch3-exercise-1.ipynb` | EPA_fuel_economy.csv | pandas, numpy, matplotlib |
| `nb-ch3-2` | Notebook | 第 3 章 练习 2 | `ch3-exercise-2.ipynb` | EPA_fuel_economy.csv | pandas, numpy, matplotlib |
| `nb-ch3-3` | Notebook | 第 3 章 练习 3 | `ch3-exercise-3.ipynb` | EPA_fuel_economy.csv | pandas, numpy, matplotlib |
| `nb-ch4-1` | Notebook | 第 4 章 练习 1 | `ch4-exercise-1.ipynb` | EPA_fuel_economy.csv | pandas, numpy, matplotlib |
| `nb-ch4-2` | Notebook | 第 4 章 练习 2 | `ch4-exercise-2.ipynb` | EPA_fuel_economy.csv | pandas, numpy, matplotlib |
| `nb-ch5-1` | Notebook | 第 5 章 练习 1 | `ch5-exercise-1.ipynb` | EPA_fuel_economy_summary.csv | pandas, numpy, matplotlib, seaborn |
| `nb-ch5-2` | Notebook | 第 5 章 练习 2 | `ch5-exercise-2.ipynb` | EPA_fuel_economy_summary.csv | pandas, numpy, matplotlib, seaborn |
| `nb-ch5-3` | Notebook | 第 5 章 练习 3 | `ch5-exercise-3.ipynb` | EPA_fuel_economy_summary.csv | pandas, numpy, matplotlib, seaborn |
| `nb-ch5-4` | Notebook | 第 5 章 练习 4 | `ch5-exercise-4.ipynb` | EPA_fuel_economy_summary.csv | pandas, numpy, matplotlib, seaborn |
| `nb-ch6-1` | Notebook | 第 6 章 练习 1 | `ch6-exercise-1.ipynb` | EPA_fuel_economy_summary.csv | pandas, numpy, altair, openpyxl, vegafusion |
| `nb-ch6-2` | Notebook | 第 6 章 练习 2 | `ch6-exercise-2.ipynb` | EPA_fuel_economy_summary.csv | pandas, numpy, altair, openpyxl, vegafusion |
| `nb-ch6-3` | Notebook | 第 6 章 练习 3 | `ch6-exercise-3.ipynb` | AmazonBooks.xlsx | pandas, numpy, altair, openpyxl, vegafusion |
| `nb-ch7-1` | Notebook | 第 7 章 练习 1 | `ch7-exercise-1.ipynb` | EPA_fuel_economy_summary.csv | pandas, numpy, plotly, kaleido |
| `nb-ch7-2` | Notebook | 第 7 章 练习 2 | `ch7-exercise-2.ipynb` | EPA_fuel_economy_summary.csv | pandas, numpy, plotly, kaleido |
| `nb-ch7-3` | Notebook | 第 7 章 练习 3 | `ch7-exercise-3.ipynb` | EPA_fuel_economy_summary.csv | pandas, numpy, plotly, kaleido |
| `nb-ch7-4` | Notebook | 第 7 章 练习 4 | `ch7-exercise-4.ipynb` | EPA_fuel_economy_summary.csv | pandas, numpy, plotly, kaleido |
| `st-1` | Streamlit | Streamlit 简单示例 | `st_simple_1.py` | EPA_fuel_economy_summary.csv | pandas, streamlit, plotly |
| `st-2` | Streamlit | Streamlit 多筛选示例 | `st_simple_2.py` | EPA_fuel_economy_summary.csv | pandas, streamlit, plotly, altair |
| `st-sidebar` | Streamlit | Streamlit Sidebar 示例 | `st_simple_sidebar.py` | EPA_fuel_economy_summary.csv | pandas, streamlit, plotly, altair |
| `static-html-gen` | Static | 静态导出：Dash 页面 | `dash_html_gen.py` | — | dash, plotly |
| `static-readme-images` | Static | 静态资源：README 图片目录说明 | `images/readme.md` | — | — |
<!-- END EXAMPLE_INVENTORY -->

<!-- BEGIN ADD_EXAMPLE_TEMPLATES -->
### 新增示例（最小配置，自动生成）

每种类型的最小配置如下（由 `launch_schema.json` 自动生成）：

**Dash** (`type: dash`)

```json
"dash-your-id": {
  "type": "dash",
  "file": "dash_simple_app_1.py",
  "title": "简短标题",
  "desc": "一句话描述",
  "data_files": ["EPA_fuel_economy_summary.csv"],
  "deps": ["pandas", "dash", "plotly"]
}
```

**Notebook** (`type: notebook`)

```json
"nb-chX-Y": {
  "type": "notebook",
  "file": "ch3-exercise-1.ipynb",
  "title": "简短标题",
  "desc": "一句话描述",
  "data_files": ["EPA_fuel_economy.csv"],
  "deps": ["pandas", "numpy", "matplotlib"]
}
```

**Static** (`type: static`)

```json
"static-your-id": {
  "type": "static",
  "file": "dash_html_gen.py",
  "title": "简短标题",
  "desc": "一句话描述",
  "data_files": [],
  "deps": ["dash", "plotly"]
}
```

**Streamlit** (`type: streamlit`)

```json
"st-your-id": {
  "type": "streamlit",
  "file": "st_simple_1.py",
  "title": "简短标题",
  "desc": "一句话描述",
  "data_files": ["EPA_fuel_economy_summary.csv"],
  "deps": ["pandas", "streamlit", "plotly"]
}
```
<!-- END ADD_EXAMPLE_TEMPLATES -->

<!-- BEGIN FIELD_REFERENCE -->
#### 字段说明（自动生成）

| 字段 | 必填 | 说明 |
|------|------|------|
| `type` | ✅ | `dash` / `notebook` / `static` / `streamlit`，对应 `launch_schema.json` 中的启动规则 |
| `file` | ✅ | 脚本文件名，相对于 `code/` 目录 |
| `title` | ✅ | 显示在列表中的简短名称 |
| `desc` | ✅ | 补充说明 |
| `data_files` | ✅ | 依赖的数据文件名（空数组为无依赖），相对于 `code/data/raw/` |
| `deps` | ✅ | 需要检查的 Python 包列表（空数组为无依赖） |
<!-- END FIELD_REFERENCE -->

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

<!-- BEGIN TYPE_LAUNCH_REFERENCE -->
#### 启动命令速查（自动生成）

| 类型 | 启动命令 | 工作目录 | 启动依赖 |
|------|----------|----------|----------|
| Dash | `{python} {file}` | `code` | dash |
| Notebook | `{python} -m jupyter lab {file}` | `code` | jupyterlab, jupyter, notebook |
| Static | `{python} -m http.server 8765` | `code` | — |
| Streamlit | `{python} -m streamlit run {file}` | `code` | streamlit |
<!-- END TYPE_LAUNCH_REFERENCE -->
