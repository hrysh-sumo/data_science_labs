    lines = [line.rstrip(', ').strip() for line in table_text.splitlines() if line.strip()]
    data_str = '\n'.join(lines)

    df = pd.read_csv(
        StringIO(data_str),
        sep=r',\s*',
        engine='python',
        names=['year', 'week', 'SMN', 'SMT', 'VCI', 'TCI', 'VHI']
    )

    df = df[df['year'].astype(str).str.match(r'^\d{4}$', na=False)]
    df['year'] = df['year'].astype(int)
    df['week'] = df['week'].astype(int)
    df['VHI'] = pd.to_numeric(df['VHI'], errors='coerce')
    df = df[df['VHI'].notna() & (df['VHI'] != -1)]

    return df


# --- Головна частина додатка ---
st.title("Аналіз вегетаційного індексу (VCI, TCI, VHI)")

with st.spinner("Завантаження даних..."):
    df_all = load_data()

if df_all.empty:
    st.error("Немає доступних даних.")
else:
    col1, col2 = st.columns([1, 2])

    with col1:
        selected_region = st.selectbox("Оберіть область", options=sorted(df_all['region'].unique()))
        selected_index = st.selectbox("Оберіть індекс", options=["VCI", "TCI", "VHI"])
        year_range = st.slider("Оберіть діапазон років", 1981, 2024, (2010, 2020))
        week_range = st.slider("Оберіть діапазон тижнів", 1, 52, (1, 52))

        sort_asc = st.checkbox("Сортувати за зростанням")
        sort_desc = st.checkbox("Сортувати за спаданням")

        if st.button("Скинути фільтри"):
            # Скидання до початкових значень
            st.session_state.selected_region = sorted(df_all['region'].unique())[0]
            st.session_state.selected_index = "VHI"
            st.session_state.year_range = (2010, 2020)
            st.session_state.week_range = (1, 52)
            st.session_state.sort_asc = False
            st.session_state.sort_desc = False
            st.experimental_rerun()

    with col2:
        # Фільтрація даних
        filtered = df_all[
            (df_all['region'] == selected_region) &
            df_all['year'].between(*year_range) &
            df_all['week'].between(*week_range)
        ]

        # Сортування
        if sort_asc and sort_desc:
            st.warning("Не можна одночасно сортувати за зростанням і спаданням!")
        elif sort_asc:
            filtered = filtered.sort_values(by=selected_index)
        elif sort_desc:
            filtered = filtered.sort_values(by=selected_index, ascending=False)

        # Вкладки
        tab1, tab2, tab3 = st.tabs(["Таблиця", "Графік", "Порівняння"])

        with tab1:
            st.subheader(f"{selected_index} для {selected_region}")
            st.dataframe(filtered[['year', 'week', selected_index]])

        with tab2:
            st.subheader(f"{selected_index} по тижнях")
            fig, ax = plt.subplots()
            ax.plot(filtered['week'], filtered[selected_index], marker='o', linestyle='-')
            ax.set_title(f"{selected_region}, {year_range[0]}–{year_range[1]}")
            ax.set_xlabel("Тиждень")
            ax.set_ylabel(selected_index)
            ax.grid(True)
            st.pyplot(fig)

        with tab3:
            st.subheader(f"Порівняння по регіонах — середнє {selected_index}")
            comparison = df_all[
                df_all['region'] != selected_region
            ].groupby('region')[selected_index].mean().reset_index()

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(comparison['region'], comparison[selected_index])
            avg = filtered[selected_index].mean()
            ax.axhline(avg, color='red', linestyle='--', label=f"Середнє {selected_region}")
            ax.set_xticklabels(comparison['region'], rotation=90)
            ax.set_ylabel(selected_index)
            ax.legend()
            st.pyplot(fig)
