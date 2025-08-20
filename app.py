import streamlit as st
import requests
from main import generate_card
import os

directories = ["art_crops", "cards", "pixel"]
for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)

sets = requests.get("https://api.scryfall.com/sets").json()["data"]
set_options = {s["name"]: s["code"] for s in sets}

st.set_page_config(page_title="MTG CLI Proxy")
st.title("MTG CLI Proxy")

chosen_set = st.selectbox("Choose a set", list(set_options.keys()))
set_code = set_options[chosen_set]

cards = requests.get(f"https://api.scryfall.com/cards/search?q=set:{set_code}").json()["data"]
max_number = max(int(c["collector_number"]) for c in cards if c["collector_number"].isdigit())

card_num = st.slider("Select card number", 1, max_number, 1)

if st.button("Generate"):
    path = generate_card(set_code, card_num)
    st.image(path)
