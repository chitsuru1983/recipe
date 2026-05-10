import streamlit as st
import pandas as pd
import re
import os
from PIL import Image
from datetime import datetime
import random

# --- ページ設定 ---
LOGO_PATH = "logo.png"
if os.path.exists(LOGO_PATH):
    icon_image = Image.open(LOGO_PATH)
else:
    icon_image = "🥦"

st.set_page_config(
    page_title="やさいレシピ図鑑", 
    page_icon=icon_image,
    layout="wide"
)

# --- データ読み込み関数の定義 (追加) ---
@st.cache_data
def load_data():
    # CSVファイル名は実際のファイル名に合わせて変更してください
    csv_file = "master_recipe_data.csv"
    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    else:
        st.error(f"データファイル {csv_file} が見つかりません。")
        return None

# --- お気に入りデータの管理 ---
FAV_FILE = "favorites.csv"
def load_favorites():
    if os.path.exists(FAV_FILE):
        try:
            return pd.read_csv(FAV_FILE)['title'].tolist()
        except: return []
    return []

def save_favorites(fav_list):
    pd.DataFrame(fav_list, columns=['title']).to_csv(FAV_FILE, index=False)

# --- 季節判定 ---
def get_season_keywords():
    month = datetime.now().month
    if 3 <= month <= 5:
        return "春", ["春", "たけのこ", "アスパラ", "菜の花", "キャベツ", "新玉"]
    elif 6 <= month <= 8:
        return "夏", ["夏", "ナス", "トマト", "キュウリ", "ピーマン", "ズッキーニ"]
    elif 9 <= month <= 11:
        return "秋", ["秋", "きのこ", "サツマイモ", "カボチャ", "レンコン", "里芋"]
    else:
        return "冬", ["冬", "白菜", "大根", "ブロッコリー", "ほうれん草", "カブ"]

def main():
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, use_container_width=True)
    with col_title: st.title("過去レシピ・アーカイブ検索")
    
    df = load_data()
    if df is None: return

    if "favorites" not in st.session_state:
        st.session_state.favorites = load_favorites()

    # --- ピックアップレシピ ---
    season_name, keywords = get_season_keywords()
    if "pickup_recipe" not in st.session_state:
        pattern = "|".join(keywords)
        seasonal_df = df[
            df['title'].str.contains(pattern, na=False) | 
            df['background'].str.contains(pattern, na=False)
        ]
        st.session_state.pickup_recipe = seasonal_df.sample(1).iloc[0] if not seasonal_df.empty else df.sample(1).iloc[0]

    with st.container():
        st.success(f"✨ 今月（{datetime.now().month}月）のおすすめレシピ")
        p_col1, p_col2 = st.columns([0.4, 0.6])
        pickup = st.session_state.pickup_recipe
        with p_col1:
            if pd.notna(pickup['image_url']):
                st.image(str(pickup['image_url']).split('|')[0], use_container_width=True)
        with p_col2:
            st.subheader(f"📖 {pickup['title']}")
            st.write(f"**季節のひとこと:** {pickup['background'][:100]}...")
            if st.button("このレシピを詳しく見る"):
                st.session_state.search_query_direct = pickup['title']
                st.rerun()
            if st.button("他のレシピを提案して"):
                del st.session_state.pickup_recipe
                st.rerun()

    st.divider()

    # --- サイドバー ---
    with st.sidebar:
        st.subheader("🔗 クイックリンク")
        st.markdown("- 📺 [動画レッスン](https://osakafoodstyle.stores.jp/)\n- 📢 [最新ニュース](https://www.osakafoodstyle.com/news/)\n- 📸 [Instagram](https://www.instagram.com/osakafoodstyle/)")
        st.divider()
        st.header("検索フィルタ")
        show_only_favs = st.checkbox("⭐ お気に入りだけ表示")
        search_query = st.text_input("検索キーワード", value=st.session_state.get("search_query_direct", ""))
        search_target = st.radio("検索対象", ["すべて", "材料のみ"], index=0)
        selected_title = st.selectbox("タイトルから選ぶ
