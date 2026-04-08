from __future__ import annotations

from typing import Dict, List

import streamlit as st


def _map_icon(size: int = 16) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;">'
        '<path d="M3 6 9 3l6 3 6-3v15l-6 3-6-3-6 3V6Z" />'
        '<path d="M9 3v15M15 6v15" />'
        '</svg>'
    )


def render_region_selector(region_colors: Dict[str, str]) -> List[str]:
    all_regions = list(region_colors.keys())
    st.markdown(f"{_map_icon()} เลือกภูมิภาคที่ต้องการ", unsafe_allow_html=True)

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
