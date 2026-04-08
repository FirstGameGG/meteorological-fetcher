import ssl
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from data_processing import build_monthly_weather_dataframe, merge_oni_labels, to_excel
from ui_components import render_region_selector
from weather_fetcher import REGION_COLORS, fetch_oni_data, fetch_stations_parallel, load_stations

MIN_STATION_THRESHOLD = 3

# Bypass macOS Python SSL certificate verification issue globally.
if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context


def validate_date_range(start_date: date, end_date: date):
    if start_date > end_date:
        st.error("วันที่เริ่มต้นต้องไม่มากกว่าวันที่สิ้นสุด")
        return False, end_date

    today = date.today()
    if start_date > today:
        st.error("วันที่เริ่มต้นต้องไม่เป็นวันในอนาคต")
        return False, end_date

    query_end_date = end_date
    if end_date > today:
        st.warning("วันที่สิ้นสุดครอบคลุมวันในอนาคต ระบบจะใช้ข้อมูลถึงวันปัจจุบันแทน")
        query_end_date = today

    return True, query_end_date


# --- App setup ---
st.set_page_config(page_title="Thailand Meteorological Analyzer", page_icon="☁️", layout="wide")

# Load custom CSS (Bank of Thailand Design System)
style_path = Path(".streamlit/style.css")
if style_path.exists():
    css_content = style_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
else:
    st.warning("ไม่พบไฟล์สไตล์ .streamlit/style.css ระบบจะใช้ธีมเริ่มต้นของ Streamlit")

# --- Header layout with Bank of Thailand styling ---
header_container = st.container()

with header_container:
    header_col1, header_col2 = st.columns([6, 1])
    
    with header_col1:
        st.title("ระบบรวบรวมและวิเคราะห์ข้อมูลอุตุนิยมวิทยา")
        st.header("ประเทศไทย")
        st.markdown(
            "ระบบอัตโนมัติสำหรับสืบค้นข้อมูลจากสถานีตรวจอากาศกรมอุตุนิยมวิทยาโดยใช้ Meteostat API "
            "พร้อมผนวกรวมดัชนีชี้วัดปรากฏการณ์เอลนีโญ-ลานีญา (ONI) จาก NOAA ผ่านกระบวนการทำความสะอาดข้อมูล "
            "(Data Cleaning) และแสดงผลในรูปแบบ Visualizations เพื่อสนับสนุนการตัดสินใจ"
        )
    
    with header_col2:
        logo_col1, logo_col2 = st.columns(2)
        with logo_col1:
            st.image("assets/TMD.png", use_container_width=True)
        with logo_col2:
            st.image("assets/NOAA.png", use_container_width=True)

# --- Station data loading ---
try:
    all_stations = load_stations()
except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลสถานี: {e}")
    st.stop()

# --- User inputs ---
with st.container():
    st.markdown("### กำหนดภูมิภาคและช่วงเวลาการสืบค้นข้อมูล")
    selected_regions = render_region_selector(REGION_COLORS)

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "วันที่เริ่มต้น",
            value=date(2005, 1, 1),
            min_value=date(1950, 1, 1),
            max_value=date.today(),
        )
    with col2:
        end_date = st.date_input("วันที่สิ้นสุด", date.today())

wmo_stations = {k: v for k, v in all_stations.items() if v["region"] in selected_regions}

# --- Execute processing ---
if st.button("ประมวลผลและทำความสะอาดข้อมูล", type="primary", use_container_width=True):
    if not selected_regions:
        st.error("กรุณาเลือกข้อมูลอย่างน้อย 1 ภูมิภาค")
        st.stop()

    if not wmo_stations:
        st.error("ไม่พบสถานีอุตุนิยมวิทยาในภูมิภาคที่เลือก")
        st.stop()

    is_valid_date_range, query_end_date = validate_date_range(start_date, end_date)
    if not is_valid_date_range:
        st.stop()

    progress_bar = st.progress(0)
    status_text = st.empty()

    total_stations = len(wmo_stations)
    all_weather_data, fetched_stations, failed_stations, station_results = fetch_stations_parallel(
        wmo_stations, start_date, query_end_date, progress_bar, status_text
    )

    status_text.text("กำลังดำเนินการวิเคราะห์สภาพอากาศและประมวลผลดัชนี ONI...")

    success_count = len(fetched_stations)
    timeout_count = sum(1 for x in failed_stations if x["reason"] == "timeout")
    empty_count = sum(1 for x in failed_stations if x["reason"] == "empty")
    exception_count = sum(1 for x in failed_stations if x["reason"] == "exception")
    fallback_success_count = sum(1 for x in fetched_stations if x.get("source") == "fallback")

    st.info(
        f"สรุปผลการสืบค้นข้อมูลสถานี: สำเร็จ {success_count}/{total_stations} แห่ง | "
        f"เรียกข้อมูลสำรอง (Fallback) สำเร็จ {fallback_success_count} แห่ง | "
        f"ไม่มีข้อมูล {empty_count} | หมดเวลา (Timeout) {timeout_count} | ข้อผิดพลาดอื่น {exception_count}"
    )

    with st.expander("รายละเอียดบันทึกการสืบค้นข้อมูลรายสถานี"):
        st.dataframe(pd.DataFrame(station_results), use_container_width=True)

    if all_weather_data:
        try:
            df_monthly = build_monthly_weather_dataframe(all_weather_data)
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"เกิดข้อผิดพลาดระหว่างเตรียมข้อมูลสภาพอากาศ: {e}")
            st.stop()

        try:
            df_oni = fetch_oni_data()
            df_monthly = merge_oni_labels(df_monthly, df_oni)
        except Exception as e:
            st.warning(f"ไม่สามารถดึงข้อมูล ONI ได้ในขณะนี้: {e}")

        status_text.markdown("เสร็จสิ้นกระบวนการ!")
        progress_bar.empty()

        if success_count < MIN_STATION_THRESHOLD:
            st.warning(
                f"สืบค้นข้อมูลได้เพียง {success_count} สถานี ซึ่งอาจไม่เพียงพอสำหรับเป็นตัวแทนของทั้งภูมิภาค"
            )

        st.success("การประมวลผลข้อมูลเสร็จสมบูรณ์ ข้อมูลทั้งหมดไร้ Missing Values!")

        st.markdown("### แผนที่แสดงพิกัดสถานีอุตุนิยมวิทยาที่สมบูรณ์")
        if fetched_stations:
            df_stations = pd.DataFrame(fetched_stations)
            fig_map = px.scatter_mapbox(
                df_stations,
                lat="ละติจูด",
                lon="ลองจิจูด",
                color="ภูมิภาค",
                category_orders={"ภูมิภาค": list(REGION_COLORS.keys())},
                color_discrete_map=REGION_COLORS,
                hover_name="ชื่อสถานี",
                hover_data={
                    "ภูมิภาค": True,
                    "ที่อยู่": True,
                    "รหัสสถานี (WMO)": True,
                    "ละติจูด": True,
                    "ลองจิจูด": True,
                    "แหล่งข้อมูล": True,
                },
                zoom=4.5,
                height=600,
            )
            fig_map.update_layout(mapbox_style="open-street-map")
            fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig_map, use_container_width=True)

        st.markdown("### สถิติภูมิอากาศและดัชนี ONI รายเดือน")
        try:
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            fig.add_trace(
                go.Scatter(
                    x=df_monthly["year_month"],
                    y=df_monthly["prcp_sum"],
                    name="ปริมาณฝน (mm)",
                    fill="tozeroy",
                    mode="lines",
                    line=dict(color="rgba(0, 150, 255, 0.7)", width=2),
                ),
                secondary_y=False,
            )

            fig.add_trace(
                go.Scatter(
                    x=df_monthly["year_month"],
                    y=df_monthly["temp_mean"],
                    name="อุณหภูมิเฉลี่ย (°C)",
                    mode="lines",
                    line=dict(color="orange", width=2),
                ),
                secondary_y=True,
            )

            if "ONI_Index" in df_monthly.columns:
                if "ONI_Label" not in df_monthly.columns:
                    df_monthly["ONI_Label"] = "ไม่สามารถจัดประเภทได้"

                fig.add_trace(
                    go.Scatter(
                        x=df_monthly["year_month"],
                        y=df_monthly["ONI_Index"],
                        name="ดัชนี ONI",
                        mode="lines",
                        line=dict(color="red", width=2, dash="dot"),
                        customdata=df_monthly[["ONI_Label"]].values,
                        hovertemplate=(
                            "เดือน: %{x}<br>"
                            "ดัชนี ONI: %{y:.2f}<br>"
                            "ผลการจัดประเภท: %{customdata[0]}<extra></extra>"
                        ),
                    ),
                    secondary_y=True,
                )

            fig.update_layout(
                title="สถิติสภาพอากาศรายเดือนเทียบดัชนี ONI",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            fig.update_yaxes(title_text="ปริมาณฝน (mm)", secondary_y=False)
            fig.update_yaxes(title_text="อุณหภูมิ / ดัชนี ONI", secondary_y=True)

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการวาดกราฟ: {e}")

        st.markdown("### ตารางสรุปผลข้อมูลรายเดือน")
        st.dataframe(df_monthly, use_container_width=True)

        st.markdown("### พจนานุกรมข้อมูล (Data Dictionary)")
        with st.expander("คลิกเพื่อดูคำอธิบายตัวแปรในชุดข้อมูล", expanded=False):
            st.markdown(
                """
            | ชื่อตัวแปร (Field) | คำอธิบาย (Description) | หน่วย (Unit) |
            | --- | --- | --- |
            | **year_month** | ปีและเดือนของข้อมูล | YYYY-MM |
            | **temp_mean** | อุณหภูมิเฉลี่ยประจำเดือน | องศาเซลเซียส (°C) |
            | **tmax_max** | อุณหภูมิสูงสุดที่บันทึกได้ในเดือนนั้น | องศาเซลเซียส (°C) |
            | **tmin_min** | อุณหภูมิต่ำสุดที่บันทึกได้ในเดือนนั้น | องศาเซลเซียส (°C) |
            | **rhum_mean** | ความชื้นสัมพัทธ์เฉลี่ย | เปอร์เซ็นต์ (%) |
            | **wspd_mean** | ความเร็วลมเฉลี่ย | กิโลเมตรต่อชั่วโมง (km/h) |
            | **pres_mean** | ความกดอากาศเฉลี่ยที่ระดับน้ำทะเล | เฮกโตปาสคาล (hPa) |
            | **prcp_sum** | ปริมาณน้ำฝนสะสมรวมในเดือนนั้น | มิลลิเมตร (mm) |
            | **rainy_days** | จำนวนวันที่ฝนตก (ปริมาณฝน > 0.5 mm) | วัน (days) |
            | **ONI_Index** | ดัชนี Oceanic Niño Index ชี้วัดความรุนแรงปรากฏการณ์เอลนีโญ/ลานีญา | - |
            """
            )

        st.markdown("### ส่งออกข้อมูล (รวมดัชนี ONI)")
        col_down1, col_down2, _ = st.columns([1, 1, 2])

        with col_down1:
            csv_data = df_monthly.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="ส่งออกเป็น CSV",
                data=csv_data,
                file_name=f"thailand_weather_monthly_with_oni_{start_date.year}_to_{end_date.year}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )

        with col_down2:
            excel_data = to_excel(df_monthly)
            st.download_button(
                label="ส่งออกเป็น Excel",
                data=excel_data,
                file_name=f"thailand_weather_monthly_with_oni_{start_date.year}_to_{end_date.year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
    else:
        progress_bar.empty()
        status_text.empty()
        st.error("ไม่พบข้อมูลสภาพอากาศในช่วงเวลาที่ระบุ หรือล้มเหลวในการเชื่อมต่อกับทุกสถานี")
        if failed_stations:
            preview = pd.DataFrame(failed_stations)
            st.markdown("### ตัวอย่างรายละเอียดข้อผิดพลาด (10 รายการแรก)")
            st.dataframe(preview.head(10), use_container_width=True)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.9em;'>"
    "เว็บไซต์นี้ไม่ใช่เว็บไซต์อย่างเป็นทางการของหน่วยงานรัฐ (Disclaimer: This is not an official website)"
    "</div>",
    unsafe_allow_html=True,
)
