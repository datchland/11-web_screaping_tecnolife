import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

conn = sqlite3.connect("products.db")
df = pd.read_sql("select * from products", conn)

st.title("گوشی‌های موبایل")
st.caption(f"{len(df)} محصول")

cols = st.columns(4)
for i, row in df.iterrows():
    with cols[i % 4]:
        with st.container(border=True):
            if row["image"]:
                st.image(row["image"])

            st.write(f"**{row['name']}**")
            st.write(row["price"])

            if row.get("brand"):
                st.write(f"برند: {row['brand']}")
            if row.get("storage"):
                st.write(f"حافظه داخلی: {row['storage']}")
            if row.get("ram"):
                st.write(f"رم: {row['ram']}")
            if row.get("colors"):
                st.write(f"رنگ‌ها: {row['colors']}")
            if row.get("rating"):
                st.write(f"⭐ {row['rating']}")

            if row.get("intro"):
                with st.expander("توضیحات"):
                    st.write(row["intro"])

            st.link_button("مشاهده", row["link"])