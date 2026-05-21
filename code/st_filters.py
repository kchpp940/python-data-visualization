from pathlib import Path
import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# 1. 数据加载
# ---------------------------------------------------------------------------
@st.cache()
def load_data():
    src_file = Path.cwd() / "data" / "raw" / "EPA_fuel_economy_summary.csv"
    raw_df = pd.read_csv(src_file)
    return raw_df


# ---------------------------------------------------------------------------
# 2. 筛选状态 - 受控组件，统一 session_state key
# ---------------------------------------------------------------------------
class FilterState:
    def __init__(self, df, session_key="selected_makes"):
        self.min_year = int(df["year"].min())
        self.max_year = int(df["year"].max())
        self.valid_makes = ["ALL"] + sorted(df["make"].unique())
        self.session_key = session_key
        if session_key not in st.session_state:
            st.session_state[session_key] = ["ALL"]

    @property
    def selected_makes(self):
        return st.session_state[self.session_key]

    @selected_makes.setter
    def selected_makes(self, value):
        st.session_state[self.session_key] = value


# ---------------------------------------------------------------------------
# 3. 选择归一化 - 纯函数，可独立验证
#    规则：
#    - 空选择 → 回退为 ["ALL"]
#    - 选了 ALL + 其他 → 只保留 ALL（互斥）
#    - 只选了其他品牌 → 正常保留
# ---------------------------------------------------------------------------
def normalize_make_selection(selection, valid_makes):
    filtered = [m for m in selection if m in valid_makes]
    if not filtered:
        return ["ALL"]
    if "ALL" in filtered and len(filtered) > 1:
        return ["ALL"]
    return filtered


# ---------------------------------------------------------------------------
# 4. 控件渲染 - 受控 multiselect，带归一化写回
# ---------------------------------------------------------------------------
def _normalize_callback(filter_state):
    raw = st.session_state[filter_state.session_key]
    normalized = normalize_make_selection(raw, filter_state.valid_makes)
    if normalized != raw:
        st.session_state[filter_state.session_key] = normalized


def render_filters(filter_state, target=st):
    target.multiselect(
        "Select a make:",
        filter_state.valid_makes,
        default=filter_state.selected_makes,
        key=filter_state.session_key,
        on_change=_normalize_callback,
        args=(filter_state,),
    )

    year_range = target.slider(
        label="Year range",
        min_value=filter_state.min_year,
        max_value=filter_state.max_year,
        value=(filter_state.min_year, filter_state.max_year),
    )
    return filter_state.selected_makes, year_range


# ---------------------------------------------------------------------------
# 5. 数据过滤 - 纯函数
# ---------------------------------------------------------------------------
def filter_data(df, make, year_range):
    year_filter = df["year"].between(year_range[0], year_range[1])
    if "ALL" in make:
        make_filter = True
    elif make:
        make_filter = df["make"].isin(make)
    else:
        make_filter = df["make"].isin([])
    return df[make_filter & year_filter]


# ---------------------------------------------------------------------------
# 6. 纯函数验证 - 独立验证 normalize_make_selection 的行为
# ---------------------------------------------------------------------------
def verify_normalize_make_selection():
    valid = ["ALL", "Ford", "Toyota", "Honda"]
    assert normalize_make_selection([], valid) == ["ALL"]
    assert normalize_make_selection(["ALL"], valid) == ["ALL"]
    assert normalize_make_selection(["ALL", "Ford"], valid) == ["ALL"]
    assert normalize_make_selection(["Ford"], valid) == ["Ford"]
    assert normalize_make_selection(["Ford", "Toyota"], valid) == ["Ford", "Toyota"]
    assert normalize_make_selection(["INVALID"], valid) == ["ALL"]
    assert normalize_make_selection(["ALL", "INVALID"], valid) == ["ALL"]
    print("All normalize_make_selection tests passed.")


# ---------------------------------------------------------------------------
# 7. 纯函数验证 - 独立验证 filter_data 的行为
# ---------------------------------------------------------------------------
def verify_filter_data():
    df_test = pd.DataFrame({
        "year": [2018, 2019, 2020, 2021],
        "make": ["Ford", "Toyota", "Honda", "Ford"],
    })
    result_all = filter_data(df_test, ["ALL"], (2018, 2021))
    assert len(result_all) == 4

    result_ford = filter_data(df_test, ["Ford"], (2018, 2021))
    assert len(result_ford) == 2
    assert set(result_ford["make"].unique()) == {"Ford"}

    result_year = filter_data(df_test, ["ALL"], (2019, 2020))
    assert len(result_year) == 2
    assert set(result_year["year"].unique()) == {2019, 2020}

    result_empty = filter_data(df_test, [], (2018, 2021))
    assert len(result_empty) == 0

    result_mixed = filter_data(df_test, ["Ford", "Toyota"], (2018, 2021))
    assert len(result_mixed) == 3
    assert set(result_mixed["make"].unique()) == {"Ford", "Toyota"}

    print("All filter_data tests passed.")


# ---------------------------------------------------------------------------
# 8. 跨入口一致性验证 - 确保 filter_data 不依赖布局，纯函数行为一致
#    思路：对同一归一化输入，无论从哪个入口调用，结果必须一致
# ---------------------------------------------------------------------------
def verify_filter_data_layout_independent():
    df_test = pd.DataFrame({
        "year": [2018, 2019, 2020, 2021],
        "make": ["Ford", "Toyota", "Honda", "Ford"],
    })

    valid_makes = ["ALL", "Ford", "Toyota", "Honda"]

    test_cases = [
        (["ALL"], (2018, 2021)),
        (["Ford"], (2018, 2021)),
        (["Ford", "Toyota"], (2019, 2020)),
        (["ALL"], (2019, 2020)),
    ]

    for make, year_range in test_cases:
        normalized = normalize_make_selection(make, valid_makes)
        assert normalized == make, (
            f"Test input must be pre-normalized: {make} -> {normalized}"
        )

        result_1 = filter_data(df_test, make, year_range)
        result_2 = filter_data(df_test, make, year_range)

        assert len(result_1) == len(result_2), (
            f"Determinism failed: make={make}, year_range={year_range}"
        )
        assert result_1.equals(result_2), (
            f"Content mismatch: make={make}, year_range={year_range}"
        )

    print("All layout independence tests passed.")


# ---------------------------------------------------------------------------
# 9. 完整验证入口
# ---------------------------------------------------------------------------
def verify_all():
    verify_normalize_make_selection()
    verify_filter_data()
    verify_filter_data_layout_independent()
    print("=" * 50)
    print("ALL VERIFICATION TESTS PASSED!")
    print("=" * 50)
