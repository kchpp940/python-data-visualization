import sys
sys.path.insert(0, '.')

from st_filters import (
    load_data, apply_filters, is_empty, FilterState,
    _normalize_multiselect, _sync_filter_state, _ensure_filter_defaults
)
import streamlit as st

# 1. 验证 _normalize_multiselect 互斥逻辑
assert _normalize_multiselect(['ALL']) == ['ALL']
assert _normalize_multiselect(['ALL', 'Chevrolet']) == ['ALL']
assert _normalize_multiselect(['Chevrolet', 'ALL', 'Ford']) == ['ALL']
assert _normalize_multiselect(['Chevrolet', 'Ford']) == ['Chevrolet', 'Ford']
assert _normalize_multiselect([]) == ['ALL']
print('✓ _normalize_multiselect 互斥逻辑正确')

# 2. 验证受控状态同步
st.session_state["filter_makes"] = ["ALL", "Chevrolet", "Ford"]
_sync_filter_state("filter_makes")
assert st.session_state["filter_makes"] == ["ALL"], f"Expected ['ALL'], got {st.session_state['filter_makes']}"
print('✓ _sync_filter_state 受控同步正确（ALL + 具体值 → 仅 ALL）')

st.session_state["filter_makes"] = ["Chevrolet", "Ford"]
_sync_filter_state("filter_makes")
assert st.session_state["filter_makes"] == ["Chevrolet", "Ford"]
print('✓ _sync_filter_state 受控同步正确（仅具体值保持不变）')

st.session_state["filter_makes"] = []
_sync_filter_state("filter_makes")
assert st.session_state["filter_makes"] == ["ALL"]
print('✓ _sync_filter_state 受控同步正确（空 → ALL）')

# 3. 验证默认值初始化
st.session_state.clear()
options = {"min_year": 2000, "max_year": 2020}
_ensure_filter_defaults(options)
assert st.session_state["filter_makes"] == ["ALL"]
assert st.session_state["filter_transmissions"] == ["ALL"]
assert st.session_state["filter_fuel_types"] == ["ALL"]
assert st.session_state["filter_year_range"] == (2000, 2020)
print('✓ _ensure_filter_defaults 统一默认值正确')

# 4. 验证已存在值不被覆盖
st.session_state["filter_makes"] = ["Chevrolet"]
_ensure_filter_defaults(options)
assert st.session_state["filter_makes"] == ["Chevrolet"], "已有值不应被覆盖"
print('✓ _ensure_filter_defaults 已有值不被覆盖')

# 5. 验证数据过滤
df = load_data()
state = FilterState(["ALL"], (2010,2015), ["ALL"], ["ALL"])
result = apply_filters(df, state)
print(f'✓ ALL过滤: {len(result)} 行')

print('\n全部验证通过!')
