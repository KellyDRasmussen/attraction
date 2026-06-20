import streamlit as st

st.set_page_config(
    page_title="Data in Denmark",
    page_icon="🇩🇰",
    layout="wide",
)

pg = st.navigation([
    st.Page("pages/0_Migration_Explorer.py", title="Migration Explorer",  icon="✈️"),
    st.Page("pages/1_Demographic_Change.py", title="Demographic Change",  icon="📊"),
    st.Page("pages/2_Population_Explorer.py", title="Population Explorer", icon="🔍"),
])
pg.run()
