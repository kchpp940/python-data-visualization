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

Data science is one of the hottest topic of the year and data visualization is a core skillset needed to properly communicate your results and discoveries. **Take this course** to get good at a wide variety of modern Python-based visualization libraries.

<!-- DATASET_METADATA_START -->
---

## Datasets

This repository includes three datasets used throughout the course exercises. All dataset metadata is centralized in [src/dataset_metadata.py](src/dataset_metadata.py) for easy reference in notebooks, Dash apps, and documentation.

> **Note:** The row counts, column counts, and missing-value statistics below are computed from the actual data files at generation time. Re-run `python -m src.dataset_metadata --write-readme` to refresh.

### Quick Usage in Notebooks

```python
import sys; sys.path.insert(0, '..')
from src.dataset_metadata import notebook_init

# Load data and print summary
df, meta = notebook_init("epa_fuel_economy")
```

### Available Datasets

| Dataset | File | Rows | Columns | Missing Values | Chapters |
|---------|------|------|---------|----------------|----------|
| Amazon Books | `AmazonBooks.xlsx` | 600 | 7 | 0 (0.00%) | Ch6 |
| EPA Fuel Economy (Full) | `EPA_fuel_economy.csv` | 24,210 | 14 | 470 (0.14%) | Ch3, Ch4, Ch5 |
| EPA Fuel Economy (Summary) | `EPA_fuel_economy_summary.csv` | 24,210 | 16 | 461 (0.12%) | Ch6, Ch7 |

---

### Amazon Books

**File:** `AmazonBooks.xlsx` (Excel (XLSX))  
**Rows:** 600 | **Columns:** 7  
**Missing values:** 0 (0.00%)  

Top 50 selling books on Amazon from 2009-2019, including user ratings, review counts, prices, and genre classifications.

#### Fields

| Field | Type | Description | Missing |
|-------|------|-------------|---------|
| `Name` | object | Book title | - |
| `Author` | object | Book author name | - |
| `User Rating` | float64 | Average user rating (out of 5) | - |
| `Reviews` | int64 | Number of user reviews | - |
| `Price` | int64 | Book price in USD | - |
| `Year` | int64 | Year the book appeared in the top 50 | - |
| `Genre` | object | Book genre: 'Fiction' or 'Non Fiction' | - |

#### Usage by Chapter

| Chapter | Exercises | Purpose | Key Fields |
|---------|-----------|---------|------------|
| 6 | 2, 3 | Altair: categorical data visualization, heatmaps, multi-panel charts | `Genre`, `User Rating`, `Year`, `Reviews`, `Price` |

#### Notes

- Complete dataset with no missing values — excellent for teaching basic visualization without data cleaning
- Genre is binary: Fiction / Non Fiction
- Prices range from $0 to ~$100

---

### EPA Fuel Economy (Full)

**File:** `EPA_fuel_economy.csv` (CSV)  
**Rows:** 24,210 | **Columns:** 14  
**Missing values:** 470 (0.14%)  

US Environmental Protection Agency (EPA) vehicle fuel economy data spanning 2000-2020. Contains detailed technical specifications and fuel efficiency metrics for various makes and models.

#### Fields

| Field | Type | Description | Missing |
|-------|------|-------------|---------|
| `make` | object | Vehicle manufacturer brand (e.g., Acura, BMW, Toyota) | - |
| `model` | object | Specific vehicle model name | - |
| `year` | int64 | Model year (2000-2020) | - |
| `cylinders` | float64 | Number of engine cylinders | 231 |
| `trany` | object | Transmission type with gear count (e.g., 'Automatic 4-spd') | 9 |
| `displ` | float64 | Engine displacement in liters | 230 |
| `VClass` | object | Vehicle class (e.g., 'Two Seaters', 'Compact Cars') | - |
| `co2` | int64 | CO2 emissions in grams per mile (-1 indicates unavailable) | - |
| `barrels08` | float64 | Annual petroleum consumption in barrels | - |
| `fuelCost08` | int64 | Estimated annual fuel cost in USD | - |
| `fuelType` | object | Fuel type (e.g., 'Premium', 'Regular', 'Diesel') | - |
| `highway08` | int64 | Highway MPG | - |
| `city08` | int64 | City MPG | - |
| `comb08` | int64 | Combined (city+highway) MPG | - |

#### Usage by Chapter

| Chapter | Exercises | Purpose | Key Fields |
|---------|-----------|---------|------------|
| 3 | 1, 2, 3 | Matplotlib basics: histograms, scatter plots, bar charts, and custom styling | `fuelCost08`, `comb08`, `make`, `year`, `displ` |
| 4 | 1, 2 | Pandas visualization: built-in plotting methods, time series analysis | `year`, `fuelCost08`, `comb08`, `highway08`, `city08` |
| 5 | 1, 2, 3, 4 | Seaborn: statistical visualizations, distribution plots, regression analysis | `displ`, `comb08`, `cylinders`, `fuelType`, `VClass` |

#### Notes

- co2 = -1 indicates emissions data not available
- Most missing values in 'cylinders' and 'displ' are from electric vehicles

---

### EPA Fuel Economy (Summary)

**File:** `EPA_fuel_economy_summary.csv` (CSV)  
**Rows:** 24,210 | **Columns:** 16  
**Missing values:** 461 (0.12%)  

Simplified version of EPA fuel economy data with aggregated categorical fields for easier visualization. Derived from the full EPA dataset.

#### Fields

| Field | Type | Description | Missing |
|-------|------|-------------|---------|
| `make` | object | Vehicle manufacturer brand | - |
| `model` | object | Specific vehicle model name | - |
| `year` | int64 | Model year (2000-2020) | - |
| `transmission` | object | Simplified transmission: 'Automatic' or 'Manual' | - |
| `drive` | object | Drive type: '2WD' or '4WD' | - |
| `date_range` | object | Year range group (e.g., '2000-2010') | - |
| `fuel_type_summary` | object | Fuel category: 'Gas', 'Diesel', 'Electric', 'Other' | - |
| `class_summary` | object | Vehicle category: 'Car', 'SUV', 'Pickup', 'Wagon', 'Other' | - |
| `cylinders` | float64 | Number of engine cylinders | 231 |
| `displ` | float64 | Engine displacement in liters | 230 |
| `co2` | int64 | CO2 emissions in grams per mile | - |
| `barrels08` | float64 | Annual petroleum consumption in barrels | - |
| `fuelCost08` | int64 | Estimated annual fuel cost in USD | - |
| `highway08` | int64 | Highway MPG | - |
| `city08` | int64 | City MPG | - |
| `comb08` | int64 | Combined (city+highway) MPG | - |

#### Usage by Chapter

| Chapter | Exercises | Purpose | Key Fields |
|---------|-----------|---------|------------|
| 6 | 1, 2, 3 | Altair: declarative statistical visualizations, interactive charts | `fuelCost08`, `displ`, `class_summary`, `transmission`, `year` |
| 7 | 1, 2, 3, 4 | Plotly: interactive plotting, dashboards, and Dash applications | `fuelCost08`, `displ`, `year`, `transmission`, `drive`, `class_summary` |

#### Notes

- Aggregated fields simplify faceting and coloring in visualizations
- Used in Dash full app for vehicle comparison features

---

## Interactive Dataset Explorer

Launch the Dash application to browse datasets interactively:

```bash
cd code
python dash_full_app.py
```

Then navigate to the "📊 数据集信息" tab to explore:
- Field descriptions and data types
- Missing value statistics
- Chapter usage examples
- Dataset notes and special considerations

<!-- DATASET_METADATA_END -->

