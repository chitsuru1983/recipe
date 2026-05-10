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
        try:
            return pd.read_csv(FAV_FILE)['title'].tolist()
        except:
            return []
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
    if df is None: return

    if "favorites" not in st.session_state:
        st.session_state.favorites = load_favorites()

    # --- サイドバー ---
    with st.sidebar:
        st.subheader("🔗 クイックリンク")
        st.markdown("""
        - 📺 [動画レッスンを見る](https://osakafoodstyle.stores.jp/)
        - 📢 [最新ニュース・お知らせ](https://www.osakafoodstyle.com/news/)
        """)
        st.divider()
        
        st.header("検索フィルタ")
        show_only_favs = st.checkbox("⭐ お気に入りだけ表示")
        st.divider()
        search_query = st.text_input("検索キーワード", "")
        search_target = st.radio("検索対象", ["材料のみ", "すべて"], index=1)
        st.divider()
        selected_title = st.selectbox("タイトルから直接選ぶ", ["指定なし"] + df['title'].tolist())

    # --- 絞り込み ---
    filtered_df = df.copy()
    if show_only_favs:
        filtered_df = filtered_df[filtered_df['title'].isin(st.session_state.favorites)]
    if search_query:
        if search_target == "材料のみ":
            mask = filtered_df['ingredients'].str.contains(search_query, na=False, case=False)
        else:
            mask = filtered_df.apply(lambda r: r.astype(str).str.contains(search_query, case=False).any(), axis=1)
        filtered_df = filtered_df[mask]
    if selected_title != "指定なし":
        filtered_df = filtered_df[filtered_df['title'] == selected_title]

    st.write(f"該当件数: {len(filtered_df)} 件")

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
                    # 画像表示
                    if pd.notna(row['image_url']):
                        for url in str(row['image_url']).split('|'):
                            if url.strip(): st.image(url.strip(), use_container_width=True)
                    
                    st.subheader("💡 背景")
                    st.write(row['background'])
                    
                    # --- 材料解析 ---
                    st.subheader("🛒 材料")
                    ingredients_map = {}
                    if pd.notna(row['ingredients']):
                        ing_list = re.split(r'\n|(?<!\d)/(?!\d)| / |/ ', str(row['ingredients']))
                        for item in ing_list:
                            item = item.strip()
                            if not item: continue
                            st.markdown(f"- {item}")
                            match = re.match(r'^([a-z])\s*\((.+)\)', item)
                            if match:
                                ingredients_map[match.group(1)] = match.group(2)

                    # --- 作り方（スッキリ版） ---
                    st.subheader("👨‍🍳 作り方")
                    if pd.notna(row['instructions']):
                        raw_steps = re.split(r'。|\n', str(row['instructions']))
                        steps = [s.strip() for s in raw_steps if s.strip()]
                        
                        step_num = 1
                        for step in steps:
                            # 文字置換ではなく、そのまま表示
                            if step.startswith("※"):
                                st.caption(step)
                            else:
                                st.write(f"**{step_num}.** {step}。")
                                # そのステップに a や b が含まれていれば、折りたたみで中身を表示
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
