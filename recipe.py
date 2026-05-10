import streamlit as st
import pandas as pd
import re
import os

# ページ設定
st.set_page_config(page_title="Recipe Library", layout="wide")

# --- お気に入りデータの管理 ---
FAV_FILE = "favorites.csv"

def load_favorites():
    if os.path.exists(FAV_FILE):
        return pd.read_csv(FAV_FILE)['title'].tolist()
    return []

def save_favorites(fav_list):
    pd.DataFrame(fav_list, columns=['title']).to_csv(FAV_FILE, index=False)

# --- 認証機能 ---
def check_password():
    if st.session_state.get("password_correct", False):
        return True

    st.title("🔐 認証が必要です")
    password = st.text_input("パスワードを入力してください", type="password")
    
    if st.button("ログイン"):
        if password == "20250505": 
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    return False

def load_data():
    if not pd.io.common.file_exists("master_recipe_data.csv"):
        st.error("master_recipe_data.csv が見つかりません。")
        return None
    return pd.read_csv("master_recipe_data.csv")

def main():
    st.title("📚 過去レシピ・アーカイブ検索")
    
    df = load_data()
    if df is None:
        return

    # お気に入りリストの読み込み
    if "favorites" not in st.session_state:
        st.session_state.favorites = load_favorites()

    # --- 検索・フィルタエリア ---
    with st.sidebar:
        st.header("検索フィルタ")
        
        # お気に入り絞り込みスイッチ
        show_only_favs = st.checkbox("⭐ お気に入りだけ表示")
        
        st.divider()
        
        # 検索キーワード
        search_query = st.text_input("検索キーワード", "")
        
        # 検索対象の選択
        search_target = st.radio(
            "検索対象を選んでください",
            ["材料のみ", "すべて (タイトル・材料・本文)"],
            index=1
        )
        
        st.divider()
        
        # 直接選択
        selected_title = st.selectbox("タイトルから直接選ぶ", ["指定なし"] + df['title'].tolist())

    # --- データの絞り込みロジック ---
    filtered_df = df.copy()
    
    # 1. お気に入り絞り込み
    if show_only_favs:
        filtered_df = filtered_df[filtered_df['title'].isin(st.session_state.favorites)]

    # 2. キーワード検索
    if search_query:
        if search_target == "材料のみ":
            # 材料欄のみから検索
            filtered_df = filtered_df[
                filtered_df['ingredients'].str.contains(search_query, na=False, case=False)
            ]
        else:
            # タイトル、材料、背景、作り方、コツすべてから検索
            filtered_df = filtered_df[
                filtered_df['title'].str.contains(search_query, na=False, case=False) |
                filtered_df['ingredients'].str.contains(search_query, na=False, case=False) |
                filtered_df['background'].str.contains(search_query, na=False, case=False) |
                filtered_df['instructions'].str.contains(search_query, na=False, case=False) |
                filtered_df['tips'].str.contains(search_query, na=False, case=False)
            ]

    # 3. タイトル直接選択
    if selected_title != "指定なし":
        filtered_df = filtered_df[filtered_df['title'] == selected_title]

    # --- 表示エリア ---
    st.write(f"該当件数: {len(filtered_df)} 件")

    if len(filtered_df) == 0:
        st.info("該当するレシピがありません。条件を変えてみてください。")
    else:
        cols = st.columns(2)
        for idx, (i, row) in enumerate(filtered_df.iterrows()):
            with cols[idx % 2]:
                title = row['title']
                is_fav = title in st.session_state.favorites
                
                # ヘッダー部分（タイトルとお気に入りボタン）
                h_col1, h_col2 = st.columns([0.85, 0.15])
                with h_col1:
                    expander_label = f"📖 {title}"
                with h_col2:
                    if st.button("⭐" if is_fav else "☆", key=f"fav_{i}"):
                        if is_fav:
                            st.session_state.favorites.remove(title)
                        else:
                            st.session_state.favorites.append(title)
                        save_favorites(st.session_state.favorites)
                        st.rerun()

                with st.expander(expander_label, expanded=(len(filtered_df) == 1)):
                    # 画像（全表示）
                    if pd.notna(row['image_url']):
                        all_images = str(row['image_url']).split('|')
                        for img_url in all_images:
                            url = img_url.strip()
                            if url:
                                st.image(url, use_container_width=True)
                    
                    st.subheader("💡 背景")
                    st.write(row['background'])
                    
                    # 材料
                    st.subheader("🛒 材料")
                    if pd.notna(row['ingredients']):
                        ing_list = re.split(r'\n|(?<!\d)/(?!\d)| / |/ ', str(row['ingredients']))
                        for item in ing_list:
                            if item.strip():
                                st.markdown(f"- {item.strip()}")
                    
                    # 作り方
                    st.subheader("👨‍🍳 作り方")
                    if pd.notna(row['instructions']):
                        steps = [s.strip() for s in str(row['instructions']).split('。') if s.strip()]
                        for j, step in enumerate(steps, 1):
                            st.write(f"**{j}.** {step}。")
                    
                    # コツ
                    st.subheader("✨ コツ・ポイント")
                    if pd.notna(row['tips']):
                        st.warning(row['tips'])
                    
                    if pd.notna(row['permalink']):
                        st.markdown(f"[🔗 元の記事を見る]({row['permalink']})")

if __name__ == "__main__":
    if check_password():
        main()
