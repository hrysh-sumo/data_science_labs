import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request
import re
from datetime import datetime
from io import StringIO
import os

# --- Функція завантаження даних ---
@st.cache_data
def load_data():
    region_names = {
        1: "Вінницька", 2: "Волинська", 3: "Дніпропетровська", 4: "Донецька",
        5: "Житомирська", 6: "Закарпатська", 7: "Запорізька", 8: "Івано-Франківська",
        9: "Київська", 10: "Кіровоградська", 11: "Луганська", 12: "Львівська",
        13: "Миколаївська", 14: "Одеська", 15: "Полтавська", 16: "Рівненська",
        17: "Сумська", 18: "Тернопільська", 19: "Харківська", 20: "Херсонська",
        21: "Хмельницька", 22: "Черкаська", 23: "Чернівецька", 24: "Чернігівська",
        25: "м.Київ"
    }

    df_list = []

    for i in range(1, 26):
        url = (
            f'https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/' 
            f'get_TS_admin.php?country=UKR&provinceID={i}&year1=1981&year2=2024&type=Mean'
        )
        try:
            resp = urllib.request.urlopen(url)
            raw = resp.read()
            now = datetime.now().strftime("%d%m%Y%H%M%S")
            fname = f'NOAA_ID{i}_{now}.csv'
            with open(fname, 'wb') as f:
                f.write(raw)

            df = clean_noaa_file(fname)
            if not df.empty:
                df['region'] = region_names[i]
                df_list.append(df)
            os.remove(fname)
        except Exception as e:
            st.warning(f"Помилка завантаження для області {i}: {e}")

    df_all = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
    return df_all


# --- Функція очищення файлу ---
def clean_noaa_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'<tt><pre>(.*?)</pre>', content, re.DOTALL)
    if not match:
        return pd.DataFrame()

    table_text = match.group(1).strip()
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
st.title("Аналіз вегетаційного індексу (VHI) для областей України")

with st.spinner("Завантаження даних..."):
    df_all = load_data()

if df_all.empty:
    st.error("Немає доступних даних.")
else:
    col1, col2 = st.columns([1, 2])

    with col1:
        selected_region = st.selectbox("Оберіть область", options=sorted(df_all['region'].unique()))
        selected_year = st.slider("Оберіть рік", min_value=1981, max_value=2024, value=2020)
        selected_start_year = st.slider("Початковий рік", min_value=1981, max_value=2024, value=2018)
        selected_end_year = st.slider("Кінцевий рік", min_value=1981, max_value=2024, value=2020)
        pct = st.slider("Відсоток регіонів для посухи (%)", min_value=0, max_value=100, value=20)

        if st.button("Аналізувати"):
            with col2:
                # Фільтрація даних
                sub = df_all[(df_all['region'] == selected_region) & (df_all['year'] == selected_year)]

                if not sub.empty:
                    st.subheader(f"VHI для {selected_region}, {selected_year}")
                    st.dataframe(sub[['week', 'VHI']])
                    fig, ax = plt.subplots()
                    ax.plot(sub['week'], sub['VHI'], marker='o')
                    ax.set_title(f"{selected_region}, {selected_year}")
                    ax.set_xlabel("Тиждень")
                    ax.set_ylabel("VHI")
                    ax.grid(True)
                    st.pyplot(fig)
                else:
                    st.warning("Дані не знайдено.")

    with col2:
        st.info("Оберіть параметри та натисніть кнопку 'Аналізувати'")
