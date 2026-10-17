"""واجهة Streamlit للوحة تحليل المنافسين — تصميم داكن/فاتح مع دعم كامل للعربية والإنجليزية."""
from __future__ import annotations

import html
import math
import os

import pandas as pd
import plotly.express as px
import streamlit as st

import market_ai as ai
import market_engine as eng
import ui_theme
from review_cards import render_review_cards

MIN_SELECTION = 2
MAX_SELECTION = 4
CARDS_PER_ROW = 4

MARK_SVG = (
    "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
    "stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
    "<path d='M4 20V4'/><path d='M4 20h16'/><path d='M9 16V9'/>"
    "<path d='M14 16v-4'/><path d='M19 16V6'/></svg>"
)

st.set_page_config(
    page_title="Mobile App Market Analysis",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# STATE — theme + language + selection
# ============================================================================
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
st.session_state.setdefault("theme_light", st.session_state["theme"] == "light")
st.session_state.setdefault("lang", "ar")
st.session_state.setdefault("selected_apps", [])
st.session_state.setdefault("search_query", "fitness tracker")

THEME = "light" if st.session_state["theme_light"] else "dark"
LANG = st.session_state["lang"]
RTL = LANG == "ar"
LANG_LABELS = {"ar": "العربية", "en": "English"}

STRINGS = {
    # Chrome
    "app_kicker": {"ar": "منصة ذكاء المنافسين", "en": "Competitor intelligence"},
    "main_title": {"ar": "تحليل سوق تطبيقات الجوال", "en": "Mobile App Market Analysis"},
    "main_subtitle": {
        "ar": "منصة متكاملة لتحليل المنافسين واستخراج الرؤى من تعليقات المستخدمين",
        "en": "A complete workspace for competitor research and insight extraction from user reviews",
    },
    "sidebar_brand_tag": {"ar": "تحليل المنافسين", "en": "Competitor analysis"},
    "language_label": {"ar": "تغيير اللغة", "en": "Change language"},
    # Sidebar groups
    "group_analysis": {"ar": "إعدادات التحليل", "en": "Analysis"},
    "api_key_label": {"ar": "مفتاح Gemini API", "en": "Gemini API key"},
    "store_region": {"ar": "منطقة ومتجر التطبيقات", "en": "App store region"},
    "n_reviews_label": {"ar": "عدد المراجعات لكل تطبيق", "en": "Reviews per app"},
    "stars_label": {"ar": "نطاق التقييم", "en": "Rating range"},
    "stars_from": {"ar": "من", "en": "From"},
    "stars_to": {"ar": "إلى", "en": "To"},
    "theme_toggle_label": {"ar": "الوضع الفاتح", "en": "Light mode"},
    # Steps
    "step1_short": {"ar": "البحث", "en": "Search"},
    "step2_short": {"ar": "الاختيار", "en": "Select"},
    "step3_short": {"ar": "التحليل", "en": "Analyze"},
    "step1_title": {"ar": "البحث عن التطبيقات", "en": "Search apps"},
    "step1_hint": {
        "ar": "ابحث عن التطبيقات بالاسم أو الكلمة المفتاحية.",
        "en": "Search for apps by name or keyword.",
    },
    "search_label": {"ar": "البحث عن تطبيق", "en": "Search apps"},
    "search_ph": {"ar": "مثال: fitness, health, meditation", "en": "e.g. fitness, health, meditation"},
    "search_btn": {"ar": "بحث", "en": "Search"},
    "spinner_search": {"ar": "جارٍ البحث...", "en": "Searching..."},
    "empty_results": {
        "ar": "لا توجد نتائج مطابقة. جرّب كلمة مفتاحية أخرى.",
        "en": "No matching apps. Try a different keyword.",
    },
    "step2_title": {"ar": "اختيار التطبيقات", "en": "Select apps"},
    "step2_hint": {
        "ar": "اختر من ٢ إلى ٤ تطبيقات لمقارنتها.",
        "en": "Pick between 2 and 4 apps to compare.",
    },
    "select_btn": {"ar": "اختر للمقارنة", "en": "Select"},
    "deselect_btn": {"ar": "إلغاء الاختيار", "en": "Remove"},
    "chip_select": {"ar": "غير مُختار", "en": "Not selected"},
    "chip_selected": {"ar": "مُختار", "en": "Selected"},
    "selection_count": {"ar": "{n} من {max} مُختارة", "en": "{n} of {max} selected"},
    "selection_need": {
        "ar": "اختر تطبيقين على الأقل لبدء التحليل.",
        "en": "Select at least two apps to run the analysis.",
    },
    "step3_title": {"ar": "بدء التحليل", "en": "Run the analysis"},
    "step3_hint": {
        "ar": "يتم سحب المراجعات وتصنيف المشاعر وحفظ النتائج محليًا.",
        "en": "Reviews are fetched, classified and stored locally.",
    },
    "run_btn": {"ar": "سحب وتحليل البيانات", "en": "Fetch & analyze"},
    "run_done": {"ar": "تم سحب البيانات وتحليلها.", "en": "Data fetched and analyzed."},
    "flag_active": {"ar": "قيد التنفيذ", "en": "In progress"},
    "flag_done": {"ar": "مكتمل", "en": "Done"},
    # Tabs
    "tab_compare": {"ar": "لوحة المقارنة", "en": "Comparison"},
    "tab_ai": {"ar": "تحليل الذكاء الاصطناعي", "en": "AI analysis"},
    # Dashboard
    "dashboard_title": {"ar": "لوحة تحليل المنافسين", "en": "Competitor dashboard"},
    "kpi_reviews": {"ar": "إجمالي المراجعات", "en": "Total reviews"},
    "kpi_avg": {"ar": "متوسط التقييم", "en": "Avg rating"},
    "kpi_pos": {"ar": "نسبة الإيجابي", "en": "Positive %"},
    "kpi_neg": {"ar": "نسبة السلبي", "en": "Negative %"},
    "section_timeline": {"ar": "اتجاهات التقييم عبر الزمن", "en": "Rating trends over time"},
    "section_stars": {"ar": "توزيع النجوم", "en": "Star distribution"},
    "section_log": {"ar": "سجل المراجعات ({n})", "en": "Review log ({n})"},
    "download_btn": {"ar": "تحميل تقرير CSV", "en": "Download CSV report"},
    "no_data": {"ar": "لا توجد بيانات في النطاق المحدد.", "en": "No data in the selected range."},
    # Review cards
    "box_section": {"ar": "بطاقات المراجعات", "en": "Review cards"},
    "box_filter_sent": {"ar": "فلتر المشاعر", "en": "Sentiment filter"},
    "box_filter_stars": {"ar": "نطاق التقييم", "en": "Rating range"},
    "box_all": {"ar": "الكل", "en": "All"},
    "box_showing": {
        "ar": "{n} مراجعة · اسحب داخل الصندوق لعرض الباقي",
        "en": "{n} reviews · scroll for more",
    },
    "box_empty": {"ar": "لا توجد مراجعات مطابقة للفلتر.", "en": "No reviews match the filter."},
    "box_likes": {"ar": "إعجاب", "en": "likes"},
    # AI
    "ai_desc": {
        "ar": "يحلل Gemini المراجعات السلبية لاستخراج الفجوات والفرص التنافسية",
        "en": "Gemini analyzes negative reviews to extract competitive gaps and opportunities",
    },
    "gen_btn": {"ar": "تشغيل التحليل بالذكاء الاصطناعي", "en": "Run AI analysis"},
    "spinner_ai": {"ar": "جارٍ التحليل...", "en": "Analyzing..."},
}


def t(key: str) -> str:
    return STRINGS.get(key, {}).get(LANG, STRINGS.get(key, {}).get("ar", key))


# ============================================================================
# COLORS + CONSTANTS
# ============================================================================
SENT_COLOR = ui_theme.SENTIMENT_COLORS[THEME]
APP_COLORS = ui_theme.APP_COLORS[THEME]
STORE_REGIONS = {
    "العربية": ("ar", "sa"),
    "English": ("en", "us"),
}
REVIEW_OPTIONS = [200, 500, 800, 1000, 2000]


# ============================================================================
# CALLBACKS (state updates run before the script reruns)
# ============================================================================
def _sync_theme_toggle() -> None:
    st.session_state["theme"] = "light" if st.session_state["theme_light"] else "dark"


def _switch_lang() -> None:
    st.session_state["lang"] = "en" if st.session_state["lang"] == "ar" else "ar"


def _toggle_app(app_id: str) -> None:
    chosen = list(st.session_state.get("selected_apps", []))
    if app_id in chosen:
        chosen.remove(app_id)
    elif len(chosen) < MAX_SELECTION:
        chosen.append(app_id)
    st.session_state["selected_apps"] = chosen


def _run_search() -> None:
    st.session_state.pop("search_error", None)
    st.session_state["searched"] = True
    try:
        found = cached_search_apps(
            st.session_state.get("search_query", ""),
            st.session_state["store_lang"],
            st.session_state["store_country"],
        )
    except RuntimeError as exc:
        st.session_state["search_error"] = str(exc)
        return
    st.session_state["results"] = found
    st.session_state["selected_apps"] = []
    st.session_state.pop("analyzed", None)
    st.session_state.pop("ai_report", None)
    st.session_state.pop("csv_report", None)


# ============================================================================
# STYLESHEET (single call, applied before any widget renders)
# ============================================================================
_RESULTS = st.session_state.get("results", [])
_CHOSEN = [
    app_id for app_id in st.session_state.get("selected_apps", [])
    if app_id in {app["appId"] for app in _RESULTS}
]
ui_theme.apply_theme(THEME, rtl=RTL, selected_app_ids=_CHOSEN)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_search_apps(query, lang, country):
    return eng.search_apps(query, lang, country)


@st.cache_data(ttl=300, max_entries=4, show_spinner=False)
def cached_csv_report(reviews: pd.DataFrame) -> bytes:
    return eng.build_csv_report(reviews)


# ============================================================================
# SIDEBAR — settings rail
# ============================================================================
with st.sidebar:
    st.markdown(
        "<div class='sidebar-brand'>"
        f"<span class='mark'>{MARK_SVG}</span>"
        f"<span class='tag'>{html.escape(t('sidebar_brand_tag'))}</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='sidebar-group'>{html.escape(t('group_analysis'))}</div>",
        unsafe_allow_html=True,
    )

    default_key = os.getenv("GEMINI_API_KEY", "")
    if not default_key:
        try:
            default_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            default_key = ""
    api_key = st.text_input(t("api_key_label"), value=default_key, type="password")

    market = st.selectbox(t("store_region"), list(STORE_REGIONS))
    st.session_state["store_lang"], st.session_state["store_country"] = STORE_REGIONS[market]

    n_reviews = st.selectbox(
        t("n_reviews_label"), REVIEW_OPTIONS, index=0, key="n_reviews"
    )

    st.markdown(f"**{t('stars_label')}**")
    c_from, c_to = st.columns(2)
    star_from = c_from.selectbox(t("stars_from"), [1, 2, 3, 4, 5], index=0)
    star_to = c_to.selectbox(t("stars_to"), [1, 2, 3, 4, 5], index=4)
    selected_stars = (star_from, star_to) if star_from <= star_to else (star_to, star_from)

# ============================================================================
# LAYOUT PRIMITIVES
# ============================================================================
def render_stepper(active_step: int) -> None:
    items = []
    for number, label in ((1, t("step1_short")), (2, t("step2_short")), (3, t("step3_short"))):
        if number < active_step:
            state, dot = "done", "✓"
        elif number == active_step:
            state, dot = "active", str(number)
        else:
            state, dot = "todo", str(number)
        items.append(
            f"<li data-state='{state}'><span class='dot' aria-hidden='true'>{dot}</span>"
            f"{html.escape(label)}</li>"
        )
    st.markdown("<ol class='stepper'>" + "".join(items) + "</ol>", unsafe_allow_html=True)


def step_head(number: int, title: str, hint: str, state: str = "active") -> None:
    flag = ""
    if state == "done":
        flag = f"<span class='flag' data-tone='done'>{html.escape(t('flag_done'))}</span>"
    elif state == "active":
        flag = f"<span class='flag' data-tone='active'>{html.escape(t('flag_active'))}</span>"
    st.markdown(
        "<div class='step-head'>"
        f"<span class='badge' aria-hidden='true'>{number}</span>"
        f"<span class='copy'><span class='title'>{html.escape(title)}</span>"
        f"<span class='hint'>{html.escape(hint)}</span></span>"
        f"{flag}</div>",
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown(f"<div class='panel-title'>{html.escape(text)}</div>", unsafe_allow_html=True)


def render_app_card(app: dict, selected: bool, disabled: bool) -> None:
    token = ui_theme.card_token(app["appId"])
    icon = html.escape(app["icon"], quote=True)
    title = html.escape(app["title"])
    developer = html.escape(app["developer"])
    chip = t("chip_selected") if selected else t("chip_select")
    with st.container(key=f"appcard_{token}"):
        st.markdown(
            "<div class='app-card-body'>"
            "<div class='app-card-top'>"
            f"<img class='app-card-icon' src='{icon}' alt='' loading='lazy'>"
            f"<span class='app-card-titles'><span class='app-card-title' title='{title}'>{title}</span>"
            f"<span class='app-card-dev'>{developer}</span></span>"
            f"<span class='app-card-score'>★ {float(app['score'] or 0):.1f}</span>"
            "</div>"
            f"<span class='app-card-id'>{html.escape(app['appId'])}</span>"
            f"<span class='app-card-chip' data-selected='{str(selected).lower()}'>{html.escape(chip)}</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.button(
            t("deselect_btn") if selected else t("select_btn"),
            key=f"sel_{token}",
            type="primary" if selected else "secondary",
            icon=":material/check_circle:" if selected else None,
            on_click=_toggle_app,
            args=(app["appId"],),
            disabled=disabled,
            width="stretch",
        )


# ============================================================================
# CHARTS
# ============================================================================
DONUT_CIRC = 2 * math.pi * 46


def donut_svg(segments, size=168, stroke=16):
    total = sum(value for _, value in segments) or 1
    offset = 0.0
    parts = []
    for color, value in segments:
        length = DONUT_CIRC * (value / total)
        parts.append(
            f"<circle class='ring-seg' cx='60' cy='60' r='46' stroke-width='{stroke}' "
            f"style='stroke:{color};stroke-dasharray:{length:.2f} {DONUT_CIRC:.2f};"
            f"stroke-dashoffset:{-offset:.2f}'></circle>"
        )
        offset += length
    return (
        f"<svg class='donut' viewBox='0 0 120 120' width='{size}' height='{size}'>"
        "<g transform='rotate(-90 60 60)'>"
        f"<circle class='ring-track' cx='60' cy='60' r='46' stroke-width='{stroke}'></circle>"
        + "".join(parts) + "</g></svg>"
    )


def gradient_bars(items):
    columns = []
    for label, value, maximum, color in items:
        height = 0.0 if maximum <= 0 else max(3.0, min(100.0, value / maximum * 100))
        columns.append(
            "<div class='barcol'>"
            "<div class='plot'>"
            f"<span class='barval' style='color:{html.escape(color, quote=True)}'>{value:.2f}</span>"
            f"<div class='bar' style='--h:{height:.1f}%;--c:{color}'></div>"
            "</div>"
            f"<em style='color:{html.escape(color, quote=True)}'>{html.escape(str(label))}</em>"
            "</div>"
        )
    return "<div class='bars'>" + "".join(columns) + "</div>"


def count_value(label, color, target, suffix=""):
    return f"""<div class='kpi'>
        <div class='kpi-label'>{html.escape(label)}</div>
        <div class='kpi-value num' style='color: {color}'><span>{int(target)}{html.escape(suffix)}</span></div>
    </div>"""


def style_fig(fig, legend=True):
    palette = ui_theme.PALETTES[THEME]
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=palette["text"], family='Segoe UI, Tahoma, Arial, sans-serif'),
        margin=dict(l=0, r=0, t=10, b=0),
        hovermode='x unified',
        legend=dict(orientation='h', y=1.12, x=0, title=None, font=dict(color=palette["text"]))
        if legend else dict(visible=False),
        xaxis=dict(showgrid=False, linecolor=palette["border"], title=None,
                   tickfont=dict(color=palette["muted"])),
        yaxis=dict(showgrid=True, gridcolor=palette["plot_grid"], zeroline=False,
                   tickfont=dict(color=palette["muted"])),
    )
    return fig


def get_sentiment_label(sent: str) -> str:
    if LANG == "ar":
        return {"Positive": "إيجابي", "Neutral": "محايد", "Negative": "سلبي"}.get(sent, sent)
    return sent


def kpi_row(df):
    total = len(df)
    avg = float(df['score'].mean())
    pos_pct = (df['sentiment'] == 'Positive').mean() * 100
    neg_pct = (df['sentiment'] == 'Negative').mean() * 100
    avg_frac = f"{avg - int(avg):.2f}"[1:]
    st.markdown(
        "<div class='kpi-grid'>" +
        count_value(t("kpi_reviews"), "var(--text)", total) +
        count_value(t("kpi_avg"), ui_theme.STAR_COLORS[THEME][1], int(avg), avg_frac) +
        count_value(t("kpi_pos"), SENT_COLOR["Positive"], round(pos_pct), "%") +
        count_value(t("kpi_neg"), SENT_COLOR["Negative"], round(neg_pct), "%") +
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================================
# DASHBOARD RENDERERS
# ============================================================================
def render_app_dashboard(df, info, key):
    st.markdown(f"""
        <div class='app-head'>
            <img src='{html.escape(info['icon'])}' alt=''>
            <div>
                <div class='app-name'>{html.escape(info['title'])}</div>
                <div class='app-dev'>{html.escape(info['developer'])} · ★ {info['score']:.1f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    df = df.copy()
    df["type"] = df["sentiment"].map(get_sentiment_label)
    kpi_row(df)

    span = (df["review_at"].max() - df["review_at"].min()).days
    freq = "W" if span > 90 else "D"
    df["period"] = df["review_at"].dt.to_period(freq).dt.start_time

    section_title(t("section_timeline"))
    type_colors = {get_sentiment_label(name): color for name, color in SENT_COLOR.items()}
    chart = df.groupby(["period", "type"]).size().reset_index(name="count")
    fig = px.area(chart, x="period", y="count", color="type", color_discrete_map=type_colors,
                  line_shape="spline", labels={"period": "Date", "count": "Count"})
    fig.update_traces(line=dict(width=2.5))
    st.plotly_chart(style_fig(fig), width='stretch', key=f"area_{key}")

    section_title(t("section_stars"))
    stars = df["score"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0).reset_index()
    stars.columns = ["stars", "count"]
    stars["star_label"] = stars["stars"].astype(str)
    fig = px.bar(stars, x="stars", y="count", color="star_label",
                 color_discrete_map={str(star): ui_theme.STAR_COLORS[THEME][(star - 1) % 3]
                                     for star in range(1, 6)})
    fig.update_xaxes(type="category")
    st.plotly_chart(style_fig(fig, legend=False), width='stretch', key=f"stars_{key}")

    section_title(t("box_section"))
    render_review_cards(
        df,
        key=key,
        language=LANG,
        translate=t,
        sentiment_label=get_sentiment_label,
        app_title=info["title"],
    )

    section_title(t("section_log").format(n=len(df)))
    col_map = {
        "user_name": "User" if LANG == "en" else "المستخدم",
        "score": "Rating" if LANG == "en" else "التقييم",
        "content": "Comment" if LANG == "en" else "التعليق",
        "thumbs_up": "Likes" if LANG == "en" else "إعجابات",
        "app_version": "Version" if LANG == "en" else "الإصدار",
    }
    table = df.rename(columns=col_map)
    date_col = "Date" if LANG == "en" else "التاريخ"
    table[date_col] = df["review_at"].dt.date
    type_col = "Type" if LANG == "en" else "النوع"
    table[type_col] = df["sentiment"].map(get_sentiment_label)

    if LANG == "ar":
        cols = ["المستخدم", "التقييم", "النوع", "التاريخ", "إعجابات", "الإصدار", "التعليق"]
    else:
        cols = ["User", "Rating", "Type", "Date", "Likes", "Version", "Comment"]

    st.dataframe(
        table[cols].sort_values(date_col, ascending=False),
        width='stretch', height=400, hide_index=True,
        column_config={
            "Rating" if LANG == "en" else "التقييم": st.column_config.NumberColumn(format="%d ★"),
            "Date" if LANG == "en" else "التاريخ": st.column_config.DateColumn(),
            "Comment" if LANG == "en" else "التعليق": st.column_config.TextColumn(width="large"),
        }
    )


def render_comparison(df, full):
    order = list(df["app_title"].unique())
    cmap = {title: ui_theme.STAR_COLORS[THEME][index % 3] for index, title in enumerate(order)}

    section_title(t("dashboard_title"))

    c1, c2 = st.columns(2)
    with c1:
        section_title(t("kpi_avg"))
        avg = df.groupby("app_title")["score"].mean().reset_index()
        st.markdown(
            gradient_bars([
                (row["app_title"], float(row["score"]), 5.0, cmap[row["app_title"]])
                for _, row in avg.iterrows()
            ]),
            unsafe_allow_html=True,
        )

    with c2:
        section_title(t("kpi_pos"))
        sent = df.groupby(["app_title", "sentiment"]).size().reset_index(name="n")
        apps = list(sent["app_title"].unique())
        donut_cols = st.columns(len(apps))
        for col, app in zip(donut_cols, apps):
            sub = sent[sent["app_title"] == app]
            counts = {row["sentiment"]: int(row["n"]) for _, row in sub.iterrows()}
            total = sum(counts.values()) or 1
            pos_pct = counts.get("Positive", 0) / total * 100
            segments = [
                (SENT_COLOR["Positive"], counts.get("Positive", 0)),
                (SENT_COLOR["Neutral"], counts.get("Neutral", 0)),
                (SENT_COLOR["Negative"], counts.get("Negative", 0)),
            ]
            with col:
                st.markdown(
                    "<div class='donut-wrap'>"
                    + donut_svg(segments, size=150)
                    + f"<div class='donut-center'><b style='color:{SENT_COLOR['Positive']}'>{pos_pct:.0f}%</b>"
                      f"<span>{get_sentiment_label('Positive')}</span></div>"
                    "</div>"
                    f"<div class='donut-app'>{html.escape(str(app))}</div>",
                    unsafe_allow_html=True,
                )
        legend = "<div class='donut-legend'>" + "".join(
            f"<span><i style='background:{SENT_COLOR[name]}'></i>{get_sentiment_label(name)}</span>"
            for name in ("Positive", "Neutral", "Negative")
        ) + "</div>"
        st.markdown(legend, unsafe_allow_html=True)

    section_title(t("section_stars"))
    stars = df.groupby(["app_title", "score"]).size().reset_index(name="count")
    star_colors = {title: ui_theme.STAR_COLORS[THEME][index % 3]
                   for index, title in enumerate(order)}
    fig = px.bar(stars, x="score", y="count", color="app_title", barmode="group",
                 color_discrete_map=star_colors, labels={"score": "Stars"})
    fig.update_xaxes(type="category")
    st.plotly_chart(style_fig(fig), width='stretch')

    section_title(t("box_section"))
    render_review_cards(
        df,
        key="all",
        language=LANG,
        translate=t,
        sentiment_label=get_sentiment_label,
    )

    if st.button("إعداد تقرير CSV" if RTL else "Prepare CSV report", key="prepare_report"):
        with st.spinner("جارٍ إعداد التقرير..." if RTL else "Preparing report..."):
            st.session_state["csv_report"] = cached_csv_report(full)
    if st.session_state.get("csv_report"):
        st.download_button(
            t("download_btn"), data=st.session_state["csv_report"],
            file_name="competitor_report.csv", mime="text/csv; charset=utf-8",
            type="primary", icon=":material/download:",
        )


# ============================================================================
# TOP BAR
# ============================================================================
ANALYZED = st.session_state.get("analyzed")
ENOUGH = MIN_SELECTION <= len(_CHOSEN) <= MAX_SELECTION
if ANALYZED:
    ACTIVE_STEP = 4
elif ENOUGH:
    ACTIVE_STEP = 3
elif _RESULTS:
    ACTIVE_STEP = 2
else:
    ACTIVE_STEP = 1

with st.container(key="topbar"):
    brand_col, action_col, theme_col = st.columns([5, 1, 1.3], vertical_alignment="center")
    with brand_col:
        st.markdown(
            f"<span class='topbar-eyebrow'>{html.escape(t('app_kicker'))}</span>",
            unsafe_allow_html=True,
        )
        st.title(t("main_title"))
    with action_col:
        st.button(
            LANG_LABELS["en" if LANG == "ar" else "ar"],
            key="lang_switch",
            icon=":material/translate:",
            on_click=_switch_lang,
            help=t("language_label"),
        )
    with theme_col:
        st.toggle(t("theme_toggle_label"), key="theme_light", on_change=_sync_theme_toggle)

st.markdown(
    "<div class='workspace-intro'><span class='workspace-kicker'>"
    + ("من البحث إلى الرؤية" if RTL else "FROM DISCOVERY TO DECISION")
    + "</span><h2>"
    + ("افهم السوق. اكتشف فرصتك." if RTL else "Understand the market. Find your edge.")
    + "</h2><p>" + html.escape(t("main_subtitle")) + "</p></div>",
    unsafe_allow_html=True,
)
render_stepper(ACTIVE_STEP)

# ============================================================================
# STEP 1 — SEARCH
# ============================================================================
step_head(1, t("step1_title"), t("step1_hint"), "done" if _RESULTS else "active")

query_col, search_col = st.columns([5, 1], vertical_alignment="bottom")
with query_col:
    st.text_input(
        t("search_label"), key="search_query", placeholder=t("search_ph"),
        label_visibility="collapsed",
    )
search_col.button(
    t("search_btn"), type="primary", icon=":material/search:",
    on_click=_run_search, width="stretch",
)

if st.session_state.get("search_error"):
    st.error(st.session_state["search_error"])
elif st.session_state.get("searched") and not _RESULTS:
    st.info(t("empty_results"))

if not _RESULTS:
    st.markdown(
        "<div class='discovery-empty'><span class='discovery-symbol'>⌕</span><h3>"
        + ("ابدأ باكتشاف منافسيك" if RTL else "Your next insight starts with a search")
        + "</h3><p>"
        + ("ابحث عن اسم تطبيق أو فئة، ثم اختر التطبيقات التي تريد مقارنتها."
           if RTL else "Search an app name or category, then choose the apps you want to compare.")
        + "</p><div class='discovery-next'><span>02 · " + html.escape(t("step2_title"))
        + "</span><span>03 · " + html.escape(t("step3_title"))
        + "</span></div></div>", unsafe_allow_html=True,
    )

# ============================================================================
# STEP 2 — SELECT
# ============================================================================
if _RESULTS:
    step_head(2, t("step2_title"), t("step2_hint"), "done" if ENOUGH else "active")

    for start in range(0, len(_RESULTS), CARDS_PER_ROW):
        columns = st.columns(CARDS_PER_ROW, gap="small")
        for column, app in zip(columns, _RESULTS[start:start + CARDS_PER_ROW]):
            with column:
                is_selected = app["appId"] in _CHOSEN
                render_app_card(
                    app,
                    selected=is_selected,
                    disabled=not is_selected and len(_CHOSEN) >= MAX_SELECTION,
                )

    st.caption(t("selection_count").format(n=len(_CHOSEN), max=MAX_SELECTION))

# ============================================================================
# STEP 3 — RUN
# ============================================================================
if _RESULTS:
    step_head(3, t("step3_title"), t("step3_hint"), "done" if ANALYZED else "active")
    if not ENOUGH:
        st.info(t("selection_need"))
    run_clicked = st.button(
        t("run_btn"), type="primary", icon=":material/cloud_download:", disabled=not ENOUGH,
        key="run_analysis",
    )

    if run_clicked:
        selected_apps = [app for app in _RESULTS if app["appId"] in _CHOSEN]
        bar = st.progress(0.0)
        status = st.empty()
        succeeded, failed = [], []
        for index, info in enumerate(selected_apps):
            status.markdown(f"**{html.escape(info['title'])}**")
            try:
                eng.save_app(info)
                saved = 0
                for raw in eng.iter_review_batches(
                    info["appId"], n_reviews,
                    st.session_state["store_lang"], st.session_state["store_country"],
                    progress_cb=lambda value, index=index: bar.progress(
                        min((index + value) / len(selected_apps), 1.0)
                    ),
                ):
                    frame = eng.reviews_to_frame(raw, info["appId"])
                    saved += eng.save_reviews(frame)
                if not saved:
                    raise RuntimeError("لا توجد مراجعات متاحة." if RTL else "No reviews available.")
                succeeded.append(info)
            except Exception as exc:
                failed.append(f"{info['title']}: {exc}")
        bar.empty()
        for message in failed:
            st.error(message)
        if succeeded:
            st.session_state["analyzed"] = succeeded
            st.session_state.pop("ai_report", None)
            st.session_state.pop("csv_report", None)
            st.session_state["run_done_flash"] = True
            st.rerun()
        else:
            status.empty()

# ============================================================================
# RESULTS — comparison, per-app dashboards, AI analysis
# ============================================================================
if ANALYZED:
    if st.session_state.pop("run_done_flash", False):
        st.success(t("run_done"))
    full = eng.load_reviews([app["appId"] for app in ANALYZED])
    combined = full[(full["score"] >= selected_stars[0]) & (full["score"] <= selected_stars[1])]
    combined = combined.dropna(subset=["review_at"])
    if combined.empty:
        st.warning(t("no_data"))
        st.stop()

    tab_names = [t("tab_compare")] + [app["title"] for app in ANALYZED] + [t("tab_ai")]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        render_comparison(combined, full)

    for tab, info in zip(tabs[1:-1], ANALYZED):
        with tab:
            single = combined[combined["app_id"] == info["appId"]]
            if single.empty:
                st.warning(t("no_data"))
            else:
                render_app_dashboard(single, info, key=info["appId"])

    with tabs[-1]:
        st.markdown(t("ai_desc"))
        if st.button(t("gen_btn"), type="primary", icon=":material/auto_awesome:"):
            with st.spinner(t("spinner_ai")):
                try:
                    st.session_state["ai_report"] = ai.generate_gap_analysis(api_key, full, language=LANG)
                except ai.AIAnalysisError as exc:
                    st.error(str(exc))
        if st.session_state.get("ai_report"):
            st.markdown(st.session_state["ai_report"])
