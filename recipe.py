# --- 材料のリスト化部分を以下に差し替え ---
st.subheader("🛒 材料")
if pd.notna(row['ingredients']):
    # 1. まず「 / 」や「 /」などのスラッシュ区切りで分割を試みる
    # 2. 同時に、セル内での「改行」でも分割するようにする
    # re.split([改行 または 前後にスペースがあるスラッシュ])
    raw_ingredients = row['ingredients']
    
    # 改行コードとスラッシュの両方に対応
    ing_list = re.split(r'\n| \/ |\/ ', raw_ingredients)
    
    for item in ing_list:
        clean_item = item.strip()
        if clean_item:
            # 「1」と「2」に分かれてしまった後のデータを無理やり繋ぐのではなく、
            # 最初から分数を壊さないように「改行」を優先して処理します
            st.markdown(f"- {clean_item}")
