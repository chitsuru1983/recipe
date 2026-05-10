import streamlit as st
import pandas as pd
import re
import os

# --- ページ設定 ---
st.set_page_config(
    page_title="やさいレシピ図鑑", 
    page_icon="https://www.osakafoodstyle.com/wp/wp-content/uploads/2019/02/d247b1549c9d065bc7e2e04638f35fa8.jpg", 
    layout="wide"
)

# --- お気に入りデータの管理 ---
FAV_FILE = "favorites.csv"

def load_favorites():
    if os.path.exists(FAV_FILE):
        try:
            # タイトル列のみをリストで返す
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

    # セッション状態にお気に入りを保持
    if "favorites" not in st.session_state:
        st.session_state.favorites = load_favorites()

    # --- サイドバー ---
    with st.sidebar:
        st.subheader("🔗 クイックリンク")
        st.markdown("""
        - 📺 [動画レッスンを見る](https://osakafoodstyle.stores.jp/)
        - 📢 [最新ニュース・お知らせ](https://www.osakafoodstyle.com/news/)
        - 📸 [Instagram (最新の投稿)](https://www.instagram.com/osakafoodstyle/)
        """)
        st.divider()
        
        st.header("検索フィルタ")
        show_only_favs = st.checkbox("⭐ お気に入りだけ表示")
        st.divider()
        
        search_query = st.text_input("検索キーワード", "")
        search_target = st.radio("検索対象", ["すべて", "材料のみ"], index=0)
        st.divider()
        
        selected_title = st.selectbox("タイトルから直接選ぶ", ["指定なし"] + df['title'].tolist())

    # --- 絞り込みロジック ---
    filtered_df = df.copy()
    
    # お気に入り絞り込み
    if show_only_favs:
        filtered_df = filtered_df[filtered_df['title'].isin(st.session_state.favorites)]
    
    # キーワード検索
    if search_query:
        if search_target == "材料のみ":
            mask = filtered_df['ingredients'].str.contains(search_query, na=False, case=False)
        else:
            # 全文検索
            mask = filtered_df.apply(lambda r: r.astype(str).str.contains(search_query, case=False).any(), axis=1)
        filtered_df = filtered_df[mask]
    
    # タイトル直接選択
    if selected_title != "指定なし":
        filtered_df = filtered_df[filtered_df['title'] == selected_title]

    st.write(f"該当件数: {len(filtered_df)} 件")

    # --- レシピ表示エリア ---
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
                    # 画像（複数対応）
                    if pd.notna(row['image_url']):
                        for url in str(row['image_url']).split('|'):
                            if url.strip():
                                st.image(url.strip(), use_container_width=True)
                    
                    st.subheader("💡 背景")
                    st.write(row['background'])
                    
                    # --- 材料解析（a, bの中身を抽出） ---
                    st.subheader("🛒 材料")
                    ingredients_map = {}
                    if pd.notna(row['ingredients']):
                        ing_raw = str(row['ingredients'])
                        ing_list = re.split(r'\n|(?<!\d)/(?!\d)| / |/ ', ing_raw)
                        for item in ing_list:
                            item = item.strip()
                            if not item: continue
                            st.markdown(f"- {item}")
                            
                            # a(...) や b(...) の形式から中身を抽出
                            match = re.match(r'^([a-z])\s*\((.+)\)', item)
                            if match:
                                ingredients_map[match.group(1)] = match.group(2)

                    # --- 作り方（※除外・a/b詳細折りたたみ） ---
                    st.subheader("👨‍🍳 作り方")
                    if pd.notna(row['instructions']):
                        raw_steps = re.split(r'。|\n', str(row['instructions']))
                        steps = [s.strip() for s in raw_steps if s.strip()]
                        
                        step_num = 1
                        for step in steps:
                            if step.startswith("※"):
                                # 注釈は番号なしで表示
                                st.caption(step)
                            else:
                                # 通常のステップ
                                st.write(f"**{step_num}.** {step}。")
                                
                                # 手順の中に a や b があれば、折りたたみで詳細を表示
                                for key in ingredients_map:
                                    # 単独の英字として含まれているか判定
                                    if re.search(rf'(?<![a-zA-Z]){key}(?![a-zA-Z])', step):
                                        with st.expander(f"🔍 {key}の中身を確認"):
                                            st.write(ingredients_map[key])
                                step_num += 1
                    
                    # --- コツ・ポイント ---
                    st.subheader("✨ コツ・ポイント")
                    if pd.notna(row['tips']):
                        st.warning(row['tips'])
                    
                    # 元記事リンク
                    if pd.notna(row['permalink']):
                        st.markdown(f"[🔗 元の記事を見る]({row['permalink']})")

if __name__ == "__main__":
    if check_password():
        main()
