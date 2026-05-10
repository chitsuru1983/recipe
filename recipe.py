selected_title = st.selectbox("タイトルから選ぶ", ["指定なし"] + df['title'].tolist())
        if st.button("検索をリセット"):
            st.session_state.search_query_direct = ""
            st.rerun()

    # --- 絞り込み ---
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

if __name__ == "__main__":
    main()
