import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="Recipe Library", layout="wide")

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
    df = pd.read_csv("master_recipe_data.csv")
    return df

def main():
    st.title("📚 過去レシピ・アーカイブ検索")
    
    df = load_data()
    if df is None:
        return

    # --- 検索・フィルタエリア ---
    with st.sidebar:
        st.header("検索フィルタ")
        search_query = st.text_input("キーワード入力", "")
        selected_title = st.selectbox("タイトルから直接選ぶ", ["指定なし"] + df['title'].tolist())

    # データの絞り込み
    filtered_df = df.copy()
    if selected_title != "指定なし":
        filtered_df = filtered_df[filtered_df['title'] == selected_title]
    elif search_query:
        filtered_df = filtered_df[
            filtered_df['title'].str.contains(search_query, na=False) |
            filtered_df['ingredients'].str.contains(search_query, na=False) |
            filtered_df['background'].str.contains(search_query, na=False)
        ]

    st.write(f"該当件数: {len(filtered_df)} 件")

    if len(filtered_df) == 0:
        st.info("該当するレシピがありません。")
    else:
        cols = st.columns(2)
        for idx, (i, row) in enumerate(filtered_df.iterrows()):
            with cols[idx % 2]:
                with st.expander(f"📖 {row['title']}", expanded=(len(filtered_df) == 1)):
                    if pd.notna(row['image_url']):
                        st.image(row['image_url'], use_container_width=True)
                    
                    st.subheader("💡 背景")
                    st.write(row['background'])
                    
# --- 材料のリスト化部分を以下に差し替え ---
                    st.subheader("🛒 材料")
                    if pd.notna(row['ingredients']):
    # 「 / 」（前後にスペースがあるスラッシュ）で分割するように変更
    # これにより 1/2 などの分数が分割されるのを防ぎます
                    import re
                    ing_list = re.split(r' / | /|/ ', row['ingredients'])
    
                    for item in ing_list:
                    if item.strip():
                    st.markdown(f"- {item.strip()}")
                    
                    # --- 作り方のリスト化 ---
                    st.subheader("👨‍🍳 作り方")
                    if pd.notna(row['instructions']):
                        # 「。」で分割してステップ番号をつける
                        steps = [s.strip() for s in row['instructions'].split('。') if s.strip()]
                        for j, step in enumerate(steps, 1):
                            st.write(f"**{j}.** {step}。")
                    
                    st.subheader("✨ コツ・ポイント")
                    st.warning(row['tips'])
                    
                    if pd.notna(row['permalink']):
                        st.markdown(f"[🔗 元の記事を見る]({row['permalink']})")

if __name__ == "__main__":
    if check_password():
        main()
