from __future__ import annotations

from typing import Any, Dict, List, Tuple

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


def _build_station_options(
    stations: Dict[str, Dict[str, Any]], selected_regions: List[str]
) -> List[Tuple[str, Dict[str, Any]]]:
    station_items = [(station_id, payload) for station_id, payload in stations.items() if payload["region"] in selected_regions]
    station_items.sort(key=lambda item: (item[1]["region"], item[1]["name"], item[0]))
    return station_items


def render_station_selector(stations: Dict[str, Dict[str, Any]], selected_regions: List[str]) -> List[str]:
    st.markdown("เลือกสถานีตรวจอากาศรายสถานี")

    if not selected_regions:
        st.info("โปรดเลือกภูมิภาคก่อน เพื่อแสดงรายชื่อสถานีที่เกี่ยวข้อง")
        return []

    station_items = _build_station_options(stations, selected_regions)
    if not station_items:
        st.warning("ไม่พบสถานีที่ตรงกับภูมิภาคที่เลือก")
        return []

    station_ids = [station_id for station_id, _ in station_items]
    station_label_map = {
        station_id: f"{payload['name']} ({station_id}) · {payload['region']}"
        for station_id, payload in station_items
    }

    select_all = st.checkbox(
        "เลือกสถานีทั้งหมดในภูมิภาคที่เลือก",
        value=True,
        key="station_selector_select_all",
    )

    if select_all:
        selected_station_ids = station_ids
        st.caption(f"เลือกทั้งหมด {len(station_ids)} สถานี")
        st.multiselect(
            "รายการสถานีที่เลือก",
            options=station_ids,
            default=station_ids,
            format_func=lambda station_id: station_label_map[station_id],
            disabled=True,
        )
    else:
        manual_selection_key = "station_selector_manual_ids"
        previous_selection = st.session_state.get(manual_selection_key, station_ids)
        filtered_previous_selection = [station_id for station_id in previous_selection if station_id in station_ids]
        if not filtered_previous_selection:
            filtered_previous_selection = station_ids

        st.session_state[manual_selection_key] = filtered_previous_selection

        selected_station_ids = st.multiselect(
            "รายการสถานีที่เลือก",
            options=station_ids,
            format_func=lambda station_id: station_label_map[station_id],
            key=manual_selection_key,
        )
        st.caption(f"เลือกแล้ว {len(selected_station_ids)} / {len(station_ids)} สถานี")

    if selected_station_ids:
        with st.expander(f"ดูชื่อเต็มสถานีที่เลือก ({len(selected_station_ids)} สถานี)", expanded=False):
            st.markdown(
                "\n".join([f"- {station_label_map[station_id]}" for station_id in selected_station_ids])
            )

    return selected_station_ids
