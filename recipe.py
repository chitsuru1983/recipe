import streamlit as st
import pandas as pd

# ページ設定は一番上に配置
st.set_page_config(page_title="Recipe Library", layout="wide")

# --- 2. 認証機能 ---
def check_password():
    """パスワードが正しいか確認し、成否を返す"""
    if st.session_state.get("password_correct", False):
        return True

    # 認証用UI
    st.title("🔐 認証が必要です")
    password = st.text_input("パスワードを入力してください", type="password")
    
    if st.button("ログイン"):
        if password == "20250505": 
            st.session_state["password_correct"] = True
            st.rerun()  # 状態を保存して再起動
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
        search_query = st.text_input("キーワード入力 (タイトル・材料など)", "")
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

    # --- 表示エリア ---
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
                    st.subheader("🛒 材料")
                    st.info(row['ingredients'])
                    st.subheader("👨‍🍳 作り方")
                    st.write(row['instructions'])
                    st.subheader("✨ コツ・ポイント")
                    st.warning(row['tips'])
                    
                    if pd.notna(row['permalink']):
                        st.markdown(f"[🔗 元の記事を見る]({row['permalink']})")

if __name__ == "__main__":
    # 認証に成功した場合のみ main() を実行
    if check_password():
        main()
