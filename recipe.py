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

# --- 認証機能 ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("🔐 認証が必要です")
    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == "20250505": 
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("パスワードが違います")
    return False

def load_data():
    if not os.path.exists("master_recipe_data.csv"):
        st.error("master_recipe_data.csv が見つかりません。")
        return None
    return pd.read_csv("master_recipe_data.csv")

# --- 季節判定とピックアップロジック ---
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
    # --- タイトルとロゴ ---
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, use_container_width=True)
    with col_title: st.title("過去レシピ・アーカイブ検索")
    
    df = load_data()
    if df is None: return

    if "favorites" not in st.session_state:
        st.session_state.favorites = load_favorites()

    # --- ピックアップレシピ機能 ---
    season_name, keywords = get_season_keywords()
    
    if "pickup_recipe" not in st.session_state:
        pattern = "|".join(keywords)
        seasonal_df = df[
            df['title'].str.contains(pattern, na=False) | 
            df['background'].str.contains(pattern, na=False)
        ]
        
        if not seasonal_df.empty:
            st.session_state.pickup_recipe = seasonal_df.sample(1).iloc[0]
        else:
            st.session_state.pickup_recipe = df.sample(1).iloc[0]

    with st.container():
        st.success(f"✨ 今月（{datetime.now().month}月）のおすすめレシピ")
        p_col1, p_col2 = st.columns([0.4, 0.6])
        pickup = st.session_state.pickup_recipe
        
        with p_col1:
            if pd.notna(pickup['image_url']):
                first_img = str(pickup['image_url']).split('|')[0]
                st.image(first_img, use_container_width=True)
        with p_col2:
            st.subheader(f"📖 {pickup['title']}")
            st.write(f"**季節のひとこと:** {pickup['background'][:100]}...")
            if st.button("このレシピを詳しく見る"):
                st.session_state.search_query_direct = pickup['title']
            if st.button("他のレシピを提案して"):
                del st.session_state.pickup_recipe
                st.rerun()

    st.divider()

    # --- サイドバー ---
    with st.sidebar:
        st.subheader("🔗 クイックリンク")
        st.markdown("""
        - 📺 [動画レッスンを見る](https://osakafoodstyle.stores.jp/)
        - 📢 [最新ニュース・お知らせ](https://www.osakafoodstyle.com/news/)
        - 📸 [Instagram (最新投稿)](https://www.instagram.com/osakafoodstyle/)
        """)
        st.divider()
        st.header("検索フィルタ")
        show_only_favs = st.checkbox("⭐ お気に入りだけ表示")
        st.divider()
        
        default_search = st.session_state.get("search_query_direct", "")
        search_query = st.text_input("検索キーワード", value=default_search)
        
        search_target = st.radio("検索対象", ["すべて", "材料のみ"], index=0)
        st.divider()
        selected_title = st.selectbox("タイトルから直接選ぶ", ["指定なし"] + df['title'].tolist())
        
        if st.button("検索をリセット"):
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

    st.write(f"検索結果: {len(filtered_df)} 件")

    # --- レシピ表示 ---
    if len(filtered_df) == 0:
        st.info("該当するレシピがありません。")
    else:
        cols = st.columns(2)
        for idx, (i, row) in enumerate(filtered_df.iterrows()):
            with cols[idx % 2]:
                title = row['title']
                is_fav = title in st.session_state.favorites
                h_col1, h_col2 = st.columns([0.85, 0.15])
                with h_col1: expander_label = f"📖 {title}"
                with h_col2:
                    if st.button("⭐" if is_fav else "☆", key=f"fav_{i}"):
                        if is_fav: st.session_state.favorites.remove(title)
                        else: st.session_state.favorites.append(title)
                        save_favorites(st.session_state.favorites); st.rerun()

                with st.expander(expander_label, expanded=(len(filtered_df) == 1)):
                    if pd.notna(row['image_url']):
                        for url in str(row['image_url']).split('|'):
                            if url.strip(): st.image(url.strip(), use_container_width=True)
                    st.subheader("💡 背景")
                    st.write(row['background'])
                    
                    # --- 材料表示（修正箇所：・を削除） ---
                    st.subheader("🛒 材料")
                    ingredients_map = {}
                    if pd.notna(row['ingredients']):
                        # 分割後にそのまま出力
                        ing_list = re.split(r'\n|(?<!\d)/(?!\d)| / |/ ', str(row['ingredients']))
                        for item in ing_list:
                            item = item.strip()
                            if not item: continue
                            # 箇条書き記号を入れず、そのまま表示
                            st.write(item) 
                            
                            # a(...) などの解析ロジックは維持
                            match = re.match(r'^([a-z])\s*\((.+)\)', item)
                            if match: ingredients_map[match.group(1)] = match.group(2)

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
                                    if re.search(rf'(?<![a-zA-Z]){key}(?![a-zA-Z])', step):
                                        with st.expander(f"🔍 {key}の中身を確認"):
                                            st.write(ingredients_map[key])
                                step_num += 1
                    st.subheader("✨ コツ・ポイント")
                    if pd.notna(row['tips']): st.warning(row['tips'])
                    if pd.notna(row['permalink']): st.markdown(f"[🔗 元の記事を見る]({row['permalink']})")

if __name__ == "__main__":
    if check_password(): main()
