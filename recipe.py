import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image
import os
import re

# =========================
# ページ設定
# =========================
st.set_page_config(
    page_title="季節の野菜のおばんざいレシピ",
    page_icon="logo.png",
    layout="wide"
)

# =========================
# CSS（チェレステ風3連ボタン対応）
# =========================
mobile_responsive_css = """
<style>

.logo-img {
    width: 58px;
}

@media (max-width: 640px) {
    .logo-img {
        width: 58px;
    }
}

.streamlit-expanderHeader {
    background-color: #D7F3F7 !important;
    border-radius: 12px !important;
    padding: 14px !important;
    font-weight: 600;
    font-size: 20px !important;
}

.recipe-card {
    background: white;
    border-radius: 18px;
    padding: 12px;
    margin-bottom: 24px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

.recipe-title {
    font-size: 26px;
    font-weight: bold;
    margin-top: 12px;
    margin-bottom: 10px;
}

/* ---------------------------------
   修正：アプリ用3連ボックスボタン
--------------------------------- */
.link-container {
    display: flex;
    gap: 10px;
    margin: 15px 0 25px 0;
}

.box-link {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 14px 8px;
    border-radius: 12px;
    text-decoration: none !important;
    color: white !important;
    font-weight: bold;
    font-size: 15px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    transition: transform 0.15s, opacity 0.15s;
    text-align: center;
    background: #63C1CA; /* 統一感のあるチェレステブルー */
}

.box-link:hover {
    transform: translateY(-2px);
    opacity: 0.9;
}

.btn-maintext {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 4px;
    font-size: 15px;
}

.btn-subtext {
    font-size: 11px;
    font-weight: normal;
    opacity: 0.85;
    line-height: 1.3;
}

/* スマホ対応：画面幅が狭くなったら縦に並べる */
@media (max-width: 640px) {
    .link-container {
        flex-direction: column;
        gap: 10px;
    }
    .box-link {
        padding: 14px;
    }
    .btn-maintext {
        font-size: 16px;
    }
    .btn-subtext {
        font-size: 12px;
    }
}

</style>
"""

st.markdown(mobile_responsive_css, unsafe_allow_html=True)

# =========================
# ロゴ＋タイトル
# =========================
col1, col2 = st.columns([1, 12])

with col1:
    st.image("logo.png", width=72)

with col2:
    st.markdown(
        "<h1 style='margin-top:8px;'>季節の野菜のおばんざいレシピ</h1>",
        unsafe_allow_html=True
    )

# =========================
# リンク（3連ボックスボタン）
# =========================
st.markdown("""
<div class="link-container">
    <a href="https://www.instagram.com/osakafoodstyle/" target="_blank" class="box-link">
        <span class="btn-maintext">📸 Instagram</span>
        <span class="btn-subtext">日々の料理風景や<br>ミニ知識</span>
    </a>
    <a href="https://osakafoodstyle.stores.jp/" target="_blank" class="box-link">
        <span class="btn-maintext">🍳 動画レッスン</span>
        <span class="btn-subtext">本格的に学びたい<br>方へ</span>
    </a>
    <a href="https://lin.ee/SJ3pEm0" target="_blank" class="box-link">
        <span class="btn-maintext">💬 LINE公式</span>
        <span class="btn-subtext">限定レシピや<br>最新情報が届く</span>
    </a>
</div>
""", unsafe_allow_html=True)

st.divider()

# =========================
# 最新ニュース取得
# =========================
st.subheader("📢 最新ニュース")

try:
    url = "https://www.osakafoodstyle.com/news/"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    news_items = []

    for a in soup.select("a"):
        title = a.get_text(" ", strip=True)
        href = a.get("href")

        if not title or not href:
            continue

        if "/news/" in href or "osakafoodstyle.com/news" in href:
            if href.startswith("/"):
                href = "https://www.osakafoodstyle.com" + href
            elif href.startswith("news/"):
                href = "https://www.osakafoodstyle.com/" + href

            if title not in [item["title"] for item in news_items]:
                news_items.append({
                    "title": title,
                    "url": href
                })

    if news_items:
        for item in news_items[:3]:
            st.markdown(f"- [{item['title']}]({item['url']})")
    else:
        st.info("現在、表示できるお知らせがありません。")

except:
    st.info("現在、お知らせを読み込めません。")

st.divider()

# =========================
# CSV読み込み
# =========================
df = pd.read_csv("master_recipe_data.csv")

# =========================
# お気に入り
# =========================
if "favorites" not in st.session_state:
    st.session_state.favorites = []

# =========================
# 検索UI
# =========================
with st.expander("🔍 レシピを検索する", expanded=True):

    search_query = st.text_input("キーワード入力（材料や料理名）")

    search_target = st.radio(
        "検索対象",
        ["すべて", "材料のみ"],
        horizontal=True
    )

    selected_title = st.selectbox(
        "タイトルから選ぶ",
        ["指定なし"] + sorted(df["title"].dropna().unique().tolist())
    )

    favorite_only = st.checkbox("⭐ お気に入りだけ表示")

# =========================
# 検索処理
# =========================
filtered_df = df.copy()

if search_query:
    if search_target == "材料のみ":
        mask = filtered_df["ingredients"].astype(str).str.contains(
            search_query,
            case=False,
            na=False
        )
    else:
        mask = filtered_df.apply(
            lambda r: r.astype(str).str.contains(
                search_query,
                case=False,
                na=False
            ).any(),
            axis=1
        )

    filtered_df = filtered_df[mask]

if selected_title != "指定なし":
    filtered_df = filtered_df[filtered_df["title"] == selected_title]

if favorite_only:
    filtered_df = filtered_df[
        filtered_df["title"].isin(st.session_state.favorites)
    ]

# =========================
# 件数表示
# =========================
st.write(f"検索結果: {len(filtered_df)} 件")

# =========================
# レシピ表示
# =========================
if len(filtered_df) == 0:

    st.info("該当するレシピがありません。")

else:

    cols = st.columns(2)

    for idx, (_, row) in enumerate(filtered_df.iterrows()):

        with cols[idx % 2]:

            st.markdown('<div class="recipe-card">', unsafe_allow_html=True)

            is_favorite = row["title"] in st.session_state.favorites

            if st.button("⭐" if is_favorite else "☆", key=f"fav_{idx}"):

                if is_favorite:
                    st.session_state.favorites.remove(row["title"])
                else:
                    st.session_state.favorites.append(row["title"])

                st.rerun()

            # 画像
            if pd.notna(row["image_url"]):

                first_image = str(row["image_url"]).split("|")[0]

                st.markdown(
                    f"""
                    <div style="
                        width:100%;
                        height:260px;
                        overflow:hidden;
                        border-radius:14px;
                    ">
                        <img src="{first_image}"
                        style="
                            width:100%;
                            height:100%;
                            object-fit:cover;
                        ">
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # タイトル
            st.markdown(
                f'<div class="recipe-title">🍽️ {row["title"]}</div>',
                unsafe_allow_html=True
            )

            # 詳細
            with st.expander("レシピを見る"):

                ingredients_map = {}

                if pd.notna(row["ingredients"]):

                    st.markdown("### 材料")

                    ing_list = re.split(
                        r'\n|(?<!\d)/(?!\d)| / |/ ',
                        str(row["ingredients"])
                    )

                    for item in ing_list:

                        item = item.strip()

                        if not item:
                            continue

                        st.write(item)

                        match = re.match(
                            r'^([a-zA-Zａ-ｚＡ-Ｚ])\s*[:：]\s*(.+)',
                            item
                        )

                        if not match:
                            match = re.match(
                                r'^([a-zA-Zａ-ｚＡ-Ｚ])\s*[(（](.+)[）)]',
                                item
                            )

                        if match:
                            key = match.group(1).upper()
                            content = match.group(2)

                            if key in ingredients_map:
                                ingredients_map[key] += f"、{content}"
                            else:
                                ingredients_map[key] = content

                if pd.notna(row["instructions"]):

                    st.markdown("### 作り方")

                    raw_steps = re.split(
                        r'。|\n',
                        str(row["instructions"])
                    )

                    steps = [
                        s.strip()
                        for s in raw_steps
                        if s.strip()
                    ]

                    step_num = 1

                    for step in steps:

                        if step.startswith("※"):
                            st.caption(step)

                        else:
                            st.write(f"**{step_num}.** {step}。")

                            for key in ingredients_map:

                                if re.search(
                                    rf'(?<![a-zA-Zａ-ｚＡ-Ｚ]){key}(?![a-zA-Zａ-ｚＡ-Ｚ])',
                                    step,
                                    re.IGNORECASE
                                ):

                                    with st.expander(f"🔍 {key}の中身を確認"):
                                        st.write(ingredients_map[key])

                            step_num += 1

            st.markdown("</div>", unsafe_allow_html=True)
                            f"[🔗 元の記事を見る]({row['permalink']})"
                        )

if __name__ == "__main__":
    main()
