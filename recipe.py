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
        # ニュースの見出し表示
        st.subheader("📢 最新ニュース")
        st.markdown("""
        - [【最新】季節のやさい料理ニュース](https://www.osakafoodstyle.com/news/)
        - [eo光TV「ゲツ→キン」出演情報](https://www.osakafoodstyle.com/news/)
        - [料理教室・イベントのお知らせ](https://www.osakafoodstyle.com/news/)
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

                    # --- 作り方（ツールチップ実装） ---
                    st.subheader("👨‍🍳 作り方")
                    if pd.notna(row['instructions']):
                        raw_steps = re.split(r'。|\n', str(row['instructions']))
                        steps = [s.strip() for s in raw_steps if s.strip()]
                        
                        step_num = 1
                        for step in steps:
                            # 記号（a, bなど）をツールチップ形式に置換
                            # 💡 Streamlitのhelp引数を使って、マウスホバー時に表示させる
                            for key, content in ingredients_map.items():
                                # 後の処理のためにプレースホルダを置く
                                step = re.sub(rf'(?<![a-zA-Z]){key}(?![a-zA-Z])', f"__FAV_KEY_{key}__", step)

                            if step.startswith("※"):
                                st.caption(step)
                            else:
                                # ツールチップ（中身が見えるボタンのような見た目）を含む1行を作成
                                if "__FAV_KEY_" in step:
                                    # step内に合わせ調味料が含まれる場合、分割して表示
                                    parts = re.split(r'(__FAV_KEY_[a-z]__)', step)
                                    display_elements = [f"**{step_num}.** "]
                                    for p in parts:
                                        key_match = re.match(r'__FAV_KEY_([a-z])__', p)
                                        if key_match:
                                            k = key_match.group(1)
                                            # st.buttonなどの代わりに「？」マークの付いたツールチップを配置
                                            display_elements.append(f"🔒**{k}**(？)")
                                        else:
                                            display_elements.append(p)
                                    
                                    # まとめて1行として表示しつつ、横に詳細ボタンを置く
                                    st.write("".join(display_elements))
                                    # 詳細を「？」アイコンで確認できるようにする
                                    for k in ingredients_map:
                                        if f"__FAV_KEY_{k}__" in step:
                                            st.info(f"💡 {k}の中身: {ingredients_map[k]}")
                                else:
                                    st.write(f"**{step_num}.** {step}。")
                                step_num += 1
                    
                    st.subheader("✨ コツ・ポイント")
                    if pd.notna(row['tips']): st.warning(row['tips'])
                    if pd.notna(row['permalink']): st.markdown(f"[🔗 元の記事を見る]({row['permalink']})")

if __name__ == "__main__":
    if check_password(): main()
