import pandas as pd
import plotly.graph_objects as go
import streamlit as st


DATA_URL = (
    "https://raw.githubusercontent.com/enchan1220-prog/contents/"
    "main/population_ts_yearly_gender.zip"
)
AGES = [f"{age}세" for age in range(100)] + ["100세 이상"]

st.set_page_config(page_title="洞네 人口新聞", page_icon="📰", layout="wide")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;700;900&display=swap');
    .stApp { background: #f5f3ed; color: #181818; }
    html, body, [class*="st-"], h1, h2, h3 {
        font-family: 'Noto Serif KR', Georgia, serif;
    }
    .block-container { max-width: 1160px; padding-top: 2.5rem; }
    .masthead { text-align: center; border-top: 5px solid #181818;
        border-bottom: 3px double #181818; padding: 20px 0 16px; }
    .masthead .edition { font-size: 12px; letter-spacing: 3px; }
    .masthead h1 { font-size: clamp(32px, 6vw, 60px); font-weight: 900;
        letter-spacing: 6px; margin: 8px 0; padding: 0; color: #181818; }
    .masthead p { font-size: 14px; margin: 8px 0 0; }
    .stSelectbox [data-baseweb="select"] > div {
        background: #fffefa; color: #181818; border-color: #777; border-radius: 0;
    }
    [data-testid="stMetric"] { border-top: 1px solid #181818; padding-top: 10px; }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"],
    [data-testid="stWidgetLabel"], [data-testid="stCaptionContainer"] {
        color: #181818;
    }
    </style>
    <div class="masthead">
      <div class="edition">地域統計 · 人口特輯</div>
      <h1>동네별 人口 피라미드</h1>
      <p>우리 고장의 世代를 읽다 — 邑·面·洞 男女 年齡別 人口誌</p>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_latest_population():
    """압축 CSV를 직접 읽고, 데이터에 존재하는 최신 연도만 보관한다."""
    try:
        frame = pd.read_csv(DATA_URL, compression="zip", encoding="utf-8-sig")
    except UnicodeDecodeError:
        frame = pd.read_csv(DATA_URL, compression="zip", encoding="cp949")

    frame.columns = frame.columns.str.strip()
    required = ["연도", "시도", "시군구", "동"] + [
        f"{sex}_{age}" for sex in ("남", "여") for age in AGES
    ]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError("필수 열이 없습니다: " + ", ".join(missing[:8]))

    years = pd.to_numeric(frame["연도"], errors="coerce")
    if years.notna().sum() == 0:
        raise ValueError("연도 열에 유효한 연도가 없습니다.")
    latest_year = int(years.max())
    frame = frame.loc[years.eq(latest_year), required].copy()
    for column in ("시도", "시군구", "동"):
        frame[column] = frame[column].fillna("").astype(str).str.strip()
    frame = frame.loc[frame["시도"].ne("") & frame["동"].ne("")]
    if frame.empty:
        raise ValueError("최신 연도의 읍·면·동 자료가 없습니다.")
    return frame, latest_year


try:
    with st.spinner("人口 原簿를 불러오는 중입니다…"):
        population, year = load_latest_population()
except Exception as exc:
    st.error("人口 자료를 불러오지 못하였습니다. 원본 CSV 주소와 공개 여부를 확인하여 주십시오.")
    with st.expander("연결 오류 詳細"):
        st.code(str(exc), language="text")
        st.write(DATA_URL)
    st.stop()

st.caption(f"資料年度 {year}年 · 원본에 수록된 가장 최신 연도 · 單位: 명")

col1, col2, col3 = st.columns(3)
with col1:
    province = st.selectbox("一. 시도 選擇", sorted(population["시도"].unique()))
province_rows = population.loc[population["시도"].eq(province)]
with col2:
    district = st.selectbox(
        "二. 시군구 選擇",
        sorted(province_rows["시군구"].unique()),
        format_func=lambda value: value or "시군구 구분 없음",
    )
district_rows = province_rows.loc[province_rows["시군구"].eq(district)]
with col3:
    town = st.selectbox("三. 읍·면·동 選擇", sorted(district_rows["동"].unique()))
selected = district_rows.loc[district_rows["동"].eq(town)]


def age_counts(sex):
    columns = [f"{sex}_{age}" for age in AGES]
    values = selected[columns].astype(str).apply(
        lambda series: pd.to_numeric(
            series.str.replace(",", "", regex=False).str.strip(), errors="coerce"
        )
    )
    if values.isna().any().any() or values.lt(0).any().any():
        raise ValueError("연령별 인구에 결측값 또는 유효하지 않은 수치가 있습니다.")
    return values.sum(axis=0).to_numpy()


try:
    male, female = age_counts("남"), age_counts("여")
except ValueError as exc:
    st.error(str(exc))
    st.stop()

place = " ".join(part for part in (province, district, town) if part)
st.subheader(f"{town}의 人口 構成")
st.caption(place)
total_male, total_female = int(male.sum()), int(female.sum())
m1, m2, m3 = st.columns(3)
m1.metric("總人口", f"{total_male + total_female:,}명")
m2.metric("男子", f"{total_male:,}명")
m3.metric("女子", f"{total_female:,}명")

fig = go.Figure()
for name, counts, sign, color in (
    ("男子", male, -1, "#333333"),
    ("女子", female, 1, "#b9b9b9"),
):
    fig.add_trace(go.Bar(
        name=name,
        y=AGES,
        x=sign * counts,
        orientation="h",
        marker=dict(color=color, line=dict(color="#181818", width=0.4)),
        customdata=counts,
        hovertemplate=f"{name} · %{{y}}<br>%{{customdata:,.0f}}명<extra></extra>",
    ))

limit = max(float(male.max()), float(female.max()), 1) * 1.12
ticks = [-limit, -limit / 2, 0, limit / 2, limit]
fig.update_layout(
    height=1500,
    barmode="relative",
    bargap=0.16,
    paper_bgcolor="#f5f3ed",
    plot_bgcolor="#f5f3ed",
    font=dict(family="Noto Serif KR, Georgia, serif", color="#181818"),
    margin=dict(l=90, r=35, t=60, b=60),
    legend=dict(orientation="h", x=0.5, xanchor="center", y=1.04),
    xaxis=dict(
        title="← 男子 · 人口(명) · 女子 →",
        range=[-limit, limit],
        tickmode="array",
        tickvals=ticks,
        ticktext=[f"{abs(value):,.0f}" for value in ticks],
        zeroline=True,
        zerolinecolor="#181818",
        gridcolor="#d6d3cd",
        fixedrange=True,
    ),
    # Plotly 범주축은 categoryarray의 첫 항목을 아래쪽에 배치한다.
    # 순서를 명시하고 범위도 고정하여 0세 → 100세 이상을 보장한다.
    yaxis=dict(
        title="年齡",
        type="category",
        categoryorder="array",
        categoryarray=AGES,
        tickmode="array",
        tickvals=AGES,
        ticktext=AGES,
        range=[-0.5, len(AGES) - 0.5],
        tickfont=dict(size=10),
        fixedrange=True,
    ),
)

# 차트 설정 검증: 축 반전이나 인구 크기순 정렬을 사용하지 않는다.
assert list(fig.layout.yaxis.categoryarray) == AGES
assert fig.layout.yaxis.ticktext[0] == "0세"
assert fig.layout.yaxis.ticktext[-1] == "100세 이상"
assert fig.layout.yaxis.range[0] < fig.layout.yaxis.range[1]

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
st.caption("圖表 解說 | 맨 아래는 0세, 맨 위는 100세 이상. 좌측은 男子, 우측은 女子이며 양쪽 눈금은 실제 인구수입니다.")
st.divider()
st.caption(f"資料: 제공된 전국 읍·면·동 연령별 인구 CSV · {year}年 | 地域의 오늘을 기록하다")
