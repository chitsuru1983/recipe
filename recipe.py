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
    page_title="季節の野菜のおばんざいレシピ", 
    page_icon=icon_image,
    layout="wide"
)

# --- データ読み込み関数の定義 ---
@st.cache_data
def load_data():
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
        return "夏", ["夏", "ナス", "トマト", "キュウリ", "ピーマン", "ズッキリ"]
    elif 9 <= month <= 11:
        return "秋", ["秋", "きのこ", "サツマイモ", "カボチャ", "レンコン", "里芋"]
    else:
        return "冬", ["冬", "白菜", "大根", "ブロッコリー", "ほうれん草", "カブ"]

def main():
    # ヘッダーエリア
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, use_container_width=True)
    with col_title: 
        st.title("過去レシピ・アーカイブ検索")
    
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
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button("このレシピを詳しく見る", use_container_width=True):
                    st.session_state.search_query_direct = pickup['title']
                    st.rerun()
            with b_col2:
                if st.button("他のレシピを提案して", use_container_width=True):
                    del st.session_state.pickup_recipe
                    st.rerun()

    st.divider()

    # --- 検索セクション（サイドバーから移動） ---
    with st.expander("🔍 レシピを検索する", expanded=False):
        search_query = st.text_input("キーワード入力 (材料や料理名)", value=st.session_state.get("search_query_direct", ""))
        
        # 細かいオプションはさらに分けてスッキリ
        opt_col1, opt_col2 = st.columns(2)
        with opt_col1:
            search_target = st.radio("検索対象", ["すべて", "材料のみ"], horizontal=True)
            show_only_favs = st.checkbox("⭐ お気に入りだけ表示")
        with opt_col2:
            selected_title = st.selectbox("タイトルから選ぶ", ["指定なし"] + df['title'].tolist())
        
        if st.button("検索条件をリセット", use_container_width=True):
            st.session_state.search_query_direct = ""
            st.rerun()

    # --- 絞り込みロジック ---
    filtered_df = df.copy()
    if show_only_favs:
        filtered_df = filtered_df[filtered_df['title'].isin(st.session_state.favorites)]
    if search_query:
        if search_target == "材料のみ":
            mask = filtered_df['ingredients'].astype(str).str.contains(search_query, na=False, case=False)
        else:
            mask = filtered_df.apply(lambda r: r.astype(str).str.contains(search_query, case=False).any(), axis=1)
        filtered_df = filtered_df[mask]
    if selected_title != "指定なし":
        filtered_df = filtered_df[filtered_df['title'] == selected_title]

    st.write(f"検索結果: **{len(filtered_df)}** 件")

    # --- レシピ表示 ---
    if len(filtered_df) == 0:
        st.info("該当するレシピがありません。")
    else:
        # スマホだと2列は狭い場合があるため、画面幅に応じて自動調整されるよう配慮
        cols = st.columns(2)
        for idx, (i, row) in enumerate(filtered_df.iterrows()):
            with cols[idx % 2]:
                title = row['title']
                is_fav = title in st.session_state.favorites
                h_col1, h_col2 = st.columns([0.8, 0.2])
                with h_col1: expander_label = f"📖 {title}"
                with h_col2:
                    if st.button("⭐" if is_fav else "☆", key=f"fav_{i}"):
                        if is_fav: st.session_state.favorites.remove(title)
                        else: st.session_state.favorites.append(title)
                        save_favorites(st.session_state.favorites)
                        st.rerun()

                with st.expander(expander_label, expanded=(len(filtered_df) == 1)):
                    if pd.notna(row['image_url']):
                        for url in str(row['image_url']).split('|'):
                            if url.strip(): st.image(url.strip(), use_container_width=True)
                    st.subheader("💡 背景")
                    st.write(row['background'])
                    
                    st.subheader("🛒 材料")
                    ingredients_map = {}
                    if pd.notna(row['ingredients']):
                        ing_list = re.split(r'\n|(?<!\d)/(?!\d)| / |/ ', str(row['ingredients']))
                        for item in ing_list:
                            item = item.strip()
                            if not item: continue
                            st.write(item)
                            match = re.match(r'^([a-zA-Zａ-ｚＡ-Ｚ])\s*[:：]\s*(.+)', item)
                            if not match:
                                match = re.match(r'^([a-zA-Zａ-ｚＡ-Ｚ])\s*[(（](.+)[）)]', item)
                            if match:
                                key = match.group(1).upper()
                                content = match.group(2)
                                if key in ingredients_map:
                                    ingredients_map[key] += f"、{content}"
                                else:
                                    ingredients_map[key] = content

                    st.subheader("👨‍🍳 作り方")
                    if pd.notna(row['instructions']):
                        raw_steps = re.split(r'。|\n', str(row['instructions']))
                        steps = [s.strip() for s in raw_steps if s.strip()]
                        step_num = 1
                        for step in steps:
                            if step.startswith("※"): st.caption(step)
                            else:
                                st.write(f"**{step_num}.** {step}。")
                                for key in ingredients_map:
                                    if re.search(rf'(?<![a-zA-Zａ-ｚＡ-Ｚ]){key}(?![a-zA-Zａ-ｚＡ-Ｚ])', step, re.IGNORECASE):
                                        with st.expander(f"🔍 {key}の中身を確認"):
                                            st.write(ingredients_map[key])
                                step_num += 1
                    
                    st.subheader("✨ コツ・ポイント")
                    if pd.notna(row['tips']): st.warning(row['tips'])
                    if pd.notna(row['permalink']): st.markdown(f"[🔗 元の記事を見る]({row['permalink']})")

    # --- フッター（クイックリンク） ---
    st.divider()
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1: st.markdown("📺 [動画レッスン](https://osakafoodstyle.stores.jp/)")
    with f_col2: st.markdown("📢 [最新ニュース](https://www.osakafoodstyle.com/news/)")
    with f_col3: st.markdown("📸 [Instagram](https://www.instagram.com/osakafoodstyle/)")

if __name__ == "__main__":
    main()
