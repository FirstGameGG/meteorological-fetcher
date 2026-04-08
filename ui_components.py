from __future__ import annotations

from typing import Dict, List

import streamlit as st


def render_region_selector(region_colors: Dict[str, str]) -> List[str]:
    all_regions = list(region_colors.keys())
    st.markdown("เลือกภูมิภาคที่ต้องการ")

    region_cols = st.columns(3)
    region_selected_map = {}
    for idx, region in enumerate(all_regions):
        with region_cols[idx % 3]:
            swatch_col, checkbox_col = st.columns([1, 8])
            with swatch_col:
                st.markdown(
                    f"<div style='margin-top: 8px; width: 14px; height: 14px; border-radius: 3px; background-color: {region_colors[region]};'></div>",
                    unsafe_allow_html=True,
                )
            with checkbox_col:
                region_selected_map[region] = st.checkbox(
                    region,
                    value=True,
                    key=f"region_selector_{region}",
                )

    return [region for region in all_regions if region_selected_map.get(region, False)]
