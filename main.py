import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components


DATA_URL = (
    "https://raw.githubusercontent.com/first2022-cyber/contents/"
    "main/population_ts_yearly_gender.zip"
)
AGES = [f"{age}세" for age in range(100)] + ["100세 이상"]

st.set_page_config(page_title="동네 人口新聞", page_icon="📰", layout="wide")
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
    [data-testid="stMetric"] {
        border: 1px solid #777; border-top: 3px double #181818;
        padding: 16px; background: #fffefa;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"],
    [data-testid="stWidgetLabel"], [data-testid="stCaptionContainer"] {
        color: #181818;
    }
    </style>
    <div class="masthead">
      <div class="edition">地域統計 · 人口特輯</div>
      <h1>동네별 人口 피라미드</h1>
      <p>우리 고장의 世代를 살피다 ― 邑·面·洞 男女 年齡別 人口誌</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# HTML 컴포넌트에서 실행한 JS가 장식 레이어를 만든다.
# 재실행할 때 같은 레이어를 재사용하여 효과가 중첩되지 않게 한다.
components.html(
    """
    <script>
    (() => {
      let doc;
      try {
        doc = window.parent.document;
      } catch (_) {
        return; // 상위 문서 접근이 제한되면 통계 화면은 그대로 표시한다.
      }
      const host = doc.querySelector('.stApp');
      if (!host) return;
      const previous = doc.getElementById('newspaper-ink');
      if (previous?.dataset.version === '2') return;
      previous?.remove();

      const layer = doc.createElement('div');
      layer.id = 'newspaper-ink';
      layer.dataset.version = '2';
      layer.setAttribute('aria-hidden', 'true');
      layer.setAttribute('inert', '');
      const style = doc.createElement('style');
      style.textContent = `
        #newspaper-ink {
          position: fixed; inset: 0; z-index: 999;
          overflow: hidden; pointer-events: none !important;
          user-select: none; contain: strict;
        }
        #newspaper-ink * { pointer-events: none !important; }
        #newspaper-ink .ink-drop {
          position: absolute; top: -24px;
          width: var(--size); height: var(--size);
          border-radius: 43% 57% 61% 39%;
          background: #181818;
          box-shadow: 3px -4px 0 -2px #333, -4px 3px 0 -2px #555;
          animation: newspaper-ink-fall var(--duration) linear infinite;
          animation-delay: var(--delay);
        }
        @keyframes newspaper-ink-fall {
          0% { transform: translate3d(0, -25px, 0) rotate(0deg); opacity: 0; }
          12% { opacity: .48; }
          85% { opacity: .3; }
          100% {
            transform: translate3d(var(--drift), 105vh, 0) rotate(240deg);
            opacity: 0;
          }
        }
        #newspaper-ink .ink-brush {
          position: absolute; width: var(--width); height: var(--height);
          transform-origin: left center;
          border-radius: 65% 14% 55% 24%;
          background:
            repeating-linear-gradient(177deg, transparent 0 3px, #181818 4px 6px,
              transparent 7px 9px),
            linear-gradient(90deg, #080808 0%, #181818 65%, transparent 100%);
          clip-path: polygon(0 25%, 13% 11%, 45% 17%, 91% 0, 75% 23%,
            100% 30%, 82% 47%, 96% 60%, 69% 66%, 83% 88%, 30% 81%, 0 100%);
          animation: newspaper-ink-brush var(--duration) cubic-bezier(.16,.85,.3,1) infinite;
          animation-delay: var(--delay);
          opacity: 0;
        }
        @keyframes newspaper-ink-brush {
          0% { transform: rotate(var(--angle)) scale(.02, .55); opacity: 0; }
          7% { opacity: var(--ink-opacity); }
          17% { transform: rotate(var(--angle)) scale(1, 1.15); opacity: var(--ink-opacity); }
          29% { transform: translateX(var(--sweep)) rotate(var(--angle)) scale(1.06, 1); opacity: var(--ink-opacity); }
          66%, 100% { transform: translateX(var(--sweep)) rotate(var(--angle)) scale(1.1, .9); opacity: 0; }
        }
        #newspaper-ink.ink-paused * { animation-play-state: paused; }
        @media (prefers-reduced-motion: reduce) {
          #newspaper-ink { display: none; }
          #newspaper-ink * { animation: none !important; }
        }
        @media (max-width: 640px) {
          #newspaper-ink .ink-brush { height: calc(var(--height) * .65); }
        }
      `;
      layer.appendChild(style);

      // 먹방울은 지면 전체에 흩날리고, 한 주기마다 자리를 바꾼다.
      const scatterDrop = drop => {
        drop.style.left = `${Math.random() * 100}%`;
        drop.style.setProperty('--size', `${2 + Math.random() * 8}px`);
        drop.style.setProperty('--drift', `${Math.random() * 180 - 90}px`);
      };
      for (let i = 0; i < 28; i++) {
        const drop = doc.createElement('span');
        drop.className = 'ink-drop';
        scatterDrop(drop);
        drop.style.setProperty('--duration', `${6 + Math.random() * 8}s`);
        drop.style.setProperty('--delay', `${-Math.random() * 14}s`);
        drop.addEventListener('animationiteration', () => scatterDrop(drop));
        layer.appendChild(drop);
      }
      // 여러 붓의 주기를 엇갈리게 하고, 매번 위치·방향·농담을 새로 뽑는다.
      const randomizeBrush = brush => {
        const fromRight = Math.random() > .5;
        brush.style.left = fromRight ? 'auto' : `${Math.random() * 38 - 5}vw`;
        brush.style.right = fromRight ? `${Math.random() * 38 - 5}vw` : 'auto';
        brush.style.top = `${8 + Math.random() * 84}%`;
        brush.style.transformOrigin = fromRight ? 'right center' : 'left center';
        brush.style.setProperty('--width', `${30 + Math.random() * 38}vw`);
        brush.style.setProperty('--height', `${28 + Math.random() * 68}px`);
        brush.style.setProperty('--angle', `${Math.random() * 66 - 33}deg`);
        brush.style.setProperty('--ink-opacity', `${.38 + Math.random() * .3}`);
        brush.style.setProperty('--sweep', `${(fromRight ? -1 : 1) * (8 + Math.random() * 32)}px`);
      };
      for (let i = 0; i < 5; i++) {
          const brush = doc.createElement('span');
          brush.className = 'ink-brush';
          randomizeBrush(brush);
          brush.style.setProperty('--duration', `${2.6 + Math.random() * 2}s`);
          brush.style.setProperty('--delay', `${-Math.random() * 4.6}s`);
          brush.addEventListener('animationiteration', () => randomizeBrush(brush));
          layer.appendChild(brush);
      }
      host.appendChild(layer);

      // 비활성 탭에서는 애니메이션을 쉬고, 화면을 떠나면 감시도 해제한다.
      const pause = () => layer.classList.toggle('ink-paused', doc.hidden);
      doc.addEventListener('visibilitychange', pause);
      pause();
      const observer = new window.parent.MutationObserver(() => {
        if (!layer.isConnected) {
          doc.removeEventListener('visibilitychange', pause);
          observer.disconnect();
        }
      });
      observer.observe(doc.body, {childList: true, subtree: true});
    })();
    </script>
    """,
    height=0,
    scrolling=False,
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
        raise ValueError("資料에 필요한 項目이 없읍니다: " + ", ".join(missing[:8]))

    years = pd.to_numeric(frame["연도"], errors="coerce")
    if years.notna().sum() == 0:
        raise ValueError("年度 項目에 올바른 年度가 없읍니다.")
    latest_year = int(years.max())
    frame = frame.loc[years.eq(latest_year), required].copy()
    for column in ("시도", "시군구", "동"):
        frame[column] = frame[column].fillna("").astype(str).str.strip()
    frame = frame.loc[frame["시도"].ne("") & frame["동"].ne("")]
    if frame.empty:
        raise ValueError("最近 年度의 邑·面·洞 資料가 없읍니다.")
    return frame, latest_year


try:
    with st.spinner("人口 資料를 펼쳐 보는 중입니다…"):
        population, year = load_latest_population()
except Exception as exc:
    st.error("人口 資料를 불러오지 못하였읍니다. 原本 資料의 所在와 公開 與否를 確認하여 주십시오.")
    with st.expander("資料 接續 障礙의 內譯"):
        st.code(str(exc), language="text")
        st.write(DATA_URL)
    st.stop()

st.caption(f"資料年度 {year}年 · 原本 所載 最近 年度 · 單位: 명")
# 1960년대 문체 재현: '-ㅂ니다'는 유지하고 '있-/없-/하였-' 뒤에는
# 옛 표기 '-읍니다'를 쓴다. 모든 '-습니다'를 일괄 치환하지 않는다.
# 근거: 국립국어원 『국어생활』 1988년 가을호 「물음과 대답」
# https://www.korean.go.kr/nkview/nklife/1988_3/14_19.html
st.markdown(
    "本欄에는 우리 고장의 男女 年齡別 人口를 圖表로 실었읍니다. "
    "市·道, 市·郡·區, 邑·面·洞을 차례로 고르시면 各 世代의 分布를 살펴보실 수 있읍니다."
)

col1, col2, col3 = st.columns(3)
with col1:
    province = st.selectbox("一. 市·道 選擇", sorted(population["시도"].unique()))
province_rows = population.loc[population["시도"].eq(province)]
with col2:
    district = st.selectbox(
        "二. 市·郡·區 選擇",
        sorted(province_rows["시군구"].unique()),
        format_func=lambda value: value or "市·郡·區 區分 없음",
    )
district_rows = province_rows.loc[province_rows["시군구"].eq(district)]
with col3:
    town = st.selectbox("三. 邑·面·洞 選擇", sorted(district_rows["동"].unique()))
selected = district_rows.loc[district_rows["동"].eq(town)]


def age_counts(sex):
    columns = [f"{sex}_{age}" for age in AGES]
    values = selected[columns].astype(str).apply(
        lambda series: pd.to_numeric(
            series.str.replace(",", "", regex=False).str.strip(), errors="coerce"
        )
    )
    if values.isna().any().any() or values.lt(0).any().any():
        raise ValueError("年齡別 人口에 빠진 數値 또는 올바르지 않은 數値가 있읍니다.")
    return values.sum(axis=0).to_numpy()


try:
    male, female = age_counts("남"), age_counts("여")
except ValueError as exc:
    st.error(str(exc))
    st.stop()

place = " ".join(part for part in (province, district, town) if part)
st.subheader(f"{town}의 人口 構成")
st.caption(place)
age_population = male + female
total_population = int(age_population.sum())
child_population = int(age_population[:15].sum())
elderly_population = int(age_population[65:].sum())
# 100세 이상 구간은 대표 연령을 100세로 두어 평균을 추산한다.
if total_population > 0:
    average_age = sum(
        age * count for age, count in enumerate(age_population)
    ) / total_population
    elderly_rate = elderly_population / total_population * 100
    child_rate = child_population / total_population * 100
else:
    average_age = elderly_rate = child_rate = None

# 반올림한 표시값이 아닌 실제 비율로 20% 초과 여부를 판단한다.
aging_attention = total_population > 0 and elderly_population * 5 > total_population
m1, m2, m3 = st.columns(3)
m1.metric("總人口 · 총인구", f"{total_population:,}명")
m2.metric(
    "平均年齡 · 평균연령",
    f"{average_age:.1f}세" if average_age is not None else "—",
    help="男女 合計의 年齡別 人口로 加重平均하였읍니다. 100세 이상은 100세로 보아 算出한 推算値입니다.",
)
m3.metric(
    "高齡化率 · 고령화율" + ("  ⚠︎ 注意" if aging_attention else ""),
    f"{elderly_rate:.1f}%" if elderly_rate is not None else "—",
    help="總人口 가운데 65세 이상 人口의 比率입니다. 20%를 넘으면 注意 標識을 붙입니다.",
)
st.caption("算出 基準 | 平均年齡은 100세 이상을 100세로 본 推算値이며, 高齡化率은 65세 이상 人口의 比率입니다.")

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
if total_population == 0:
    population_comment = "登錄된 人口가 없어 아이와 어르신의 分布를 견주기 어렵습니다."
else:
    if child_population > elderly_population:
        comparison = "어르신보다 아이가 많은 고장입니다."
    elif elderly_population > child_population:
        comparison = "아이보다 어르신이 많은 고장입니다."
    else:
        comparison = "아이와 어르신의 人口가 같은 고장입니다."
    population_comment = (
        f"0~14세 아이는 {child_rate:.1f}%, 65세 이상 어르신은 {elderly_rate:.1f}%로, "
        + comparison
    )
st.markdown(f"**鄕土의 世代 |** {population_comment}")
st.caption("圖表 解說 | 맨 아래에 0세, 맨 위에 100세 이상을 두었읍니다. 左側은 男子, 右側은 女子이며, 兩便 눈금은 實際 人口數입니다.")
st.divider()
st.caption(f"資料: 全國 邑·面·洞 年齡別 人口 · {year}年 | 鄕土의 오늘을 記錄하다")
