import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="Recipe Library", layout="wide")

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
        
        # タイトル一覧から選ぶことも可能に
        selected_title = st.selectbox("タイトルから直接選ぶ", ["指定なし"] + df['title'].tolist())

    # データの絞り込み
    filtered_df = df.copy()
    
    if selected_title != "指定なし":
        filtered_df = filtered_df[filtered_df['title'] == selected_title]
    elif search_query:
        # タイトル、材料、背景から検索
        filtered_df = filtered_df[
            filtered_df['title'].str.contains(search_query, na=False) |
            filtered_df['ingredients'].str.contains(search_query, na=False) |
            filtered_df['background'].str.contains(search_query, na=False)
        ]

    # --- 表示エリア ---
    st.write(f"該当件数: {len(filtered_df)} 件")

    if len(filtered_df) == 0:
        st.info("該当するレシピがありません。キーワードを変えてみてください。")
    else:
        # グリッド表示（2カラム）
        cols = st.columns(2)
        for idx, row in filtered_df.iterrows():
            with cols[idx % 2]:
                with st.expander(f"📖 {row['title']}", expanded=(len(filtered_df) == 1)):
                    # 画像があれば表示（Geminiが抽出したURLを使用）
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
                    
                    st.divider()

if __name__ == "__main__":
    main()