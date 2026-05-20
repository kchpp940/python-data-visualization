RESET_TRIGGERS = frozenset([
    "year-slider.value",
    "transmission-list.value",
    "reset.n_clicks",
])


def build_filter_signature(year_range, transmission_list):
    if year_range is None or transmission_list is None:
        return None
    return f"{year_range[0]}-{year_range[1]}|{'|'.join(sorted(transmission_list))}"


def filter_dataframe(df, year_range, transmission_list):
    return df[df["year"].between(year_range[0], year_range[1])
               & df["transmission"].isin(transmission_list)]


def extract_valid_indices(selectedData, filtered_df):
    if not selectedData or not selectedData.get("points"):
        return []
    indices = []
    for point in selectedData["points"]:
        customdata = point.get("customdata")
        if customdata and customdata[0] in filtered_df.index:
            indices.append(customdata[0])
    return indices


def map_indices_to_positions(indices, filtered_df):
    point_index_map = {idx: pos for pos, idx in enumerate(filtered_df.index)}
    return [point_index_map[i] for i in indices if i in point_index_map]


def build_selection_state(signature, selected_indices):
    return {
        "filter_signature": signature,
        "selected_indices": selected_indices,
    }


def build_default_state(min_year, max_year, transmission_types):
    return build_selection_state(
        build_filter_signature((min_year, max_year), transmission_types),
        [],
    )


def resolve_selection_update(df, triggered, year_range, transmission_list,
                              selectedData, state):
    state = state or build_default_state(
        df["year"].min(), df["year"].max(), df["transmission"].unique()
    )

    if triggered & RESET_TRIGGERS:
        return build_selection_state(
            build_filter_signature(year_range, transmission_list) or state.get("filter_signature"),
            [],
        ), None

    signature = build_filter_signature(year_range, transmission_list)
    filtered_df = filter_dataframe(df, year_range, transmission_list)
    new_indices = extract_valid_indices(selectedData, filtered_df)

    if set(new_indices) != set(state.get("selected_indices", [])):
        return build_selection_state(
            signature or state.get("filter_signature"),
            new_indices,
        ), None

    return state, None


def resolve_selection_render(df, year_range, transmission_list, state):
    state = state or {}
    filtered_df = filter_dataframe(df, year_range, transmission_list)

    current_sig = build_filter_signature(year_range, transmission_list)
    stored_sig = state.get("filter_signature")
    stored_indices = state.get("selected_indices") or []

    if current_sig != stored_sig or not stored_indices:
        return filtered_df.head(10), [], "No points selected - showing top 10 only"

    valid_indices = [i for i in stored_indices if i in filtered_df.index]
    if not valid_indices:
        return filtered_df.head(10), [], "No points selected - showing top 10 only"

    selected_point_indices = map_indices_to_positions(valid_indices, filtered_df)
    return df.loc[valid_indices], selected_point_indices, f"Showing {len(valid_indices)} selected points:"
