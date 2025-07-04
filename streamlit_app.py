import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_plotly_events import plotly_events
import plotly.graph_objects as go

# --- Page Setup ---
st.set_page_config(page_title="Find your dream dog to adopt", layout="wide")

# --- Load dataset once and cache in session ---
if "df" not in st.session_state:
    # Load the pre-uploaded dataset (make sure this file is in your project folder)
    df = pd.read_csv("data/allDogDescriptions_new.csv")  # update path/filename as needed
    st.session_state.df = df
else:
    df = st.session_state.df

# --- App Header ---
st.title("🐶 Find your dream dog to adopt today")
st.markdown("### 📍 Where do you live?")
st.markdown("##### Click a state bar to see its top 10 imported dog breeds")

# --- Bar Chart: Dog count by state ---
state_counts = df["contact_state"].value_counts().reset_index()
state_counts.columns = ["state", "count"]

fig_state = px.bar(
        state_counts.sort_values("count", ascending=False),
        x="state",
        y="count",
)

# 👇 Make this chart clickable
selected_state = plotly_events(fig_state, click_event=True, hover_event=False)
    
# Don't re-render the chart — already shown by plotly_events
# st.plotly_chart(fig_state, use_container_width=True)

# --- Bottom Chart: Top 10 breeds in selected state ---
if selected_state:
    clicked_state = selected_state[0]["x"]
    st.session_state.selected_state = clicked_state

    top_breeds = (
        df[df["contact_state"] == clicked_state]["breed_primary"]
        .value_counts()
        .head(10)
        .reset_index()
    )
    top_breeds.columns = ["breed", "count"]

    fig_breeds = px.bar(
        top_breeds,
        x="count",
        y="breed",
         orientation="h",
        title=f"Top 10 Dog Breeds in {clicked_state}",
    )
    st.plotly_chart(fig_breeds, use_container_width=True)
else:
        st.info("Click a state bar above to explore its top breeds.")

# --- Graph 2: Dog breeds and related characteristics ---
if "df" in st.session_state:
    df = st.session_state.df

    # Filter missing values just in case
    df = df.dropna(subset=["breed_primary", "age", "sex", "size", "contact_state"])

    # --- Section title and description ---
    st.markdown("### 🐕 What type of dog are you looking for?")
    st.markdown("##### Choose the breed you are interested in and click the cell with your ideal age, sex, and size to see how many dogs are available")

    # --- Get top 10 breeds based on selected state ---
    if "selected_state" in st.session_state:
        selected_state = st.session_state.selected_state
        state_df = df[df["contact_state"] == selected_state]

        top_breeds = (
            state_df["breed_primary"]
            .value_counts()
            .head(10)
            .index
            .tolist()
        )
        st.markdown(f"🗺️ Filtering by state: **{selected_state}**")
    else:
        # Fallback: top 10 breeds nationally
        top_breeds = df["breed_primary"].value_counts().head(10).index.tolist()

    # --- Breed dropdown (filtered) ---
    selected_breed = st.selectbox("", top_breeds)
    st.session_state.selected_breed = selected_breed  # 👈 Store for Graph 3

    # --- Filter dataset by selected breed ---
    breed_df = df[df["breed_primary"] == selected_breed]

    # --- Group and count by sex, size, age ---
    grouped = (
        breed_df
        .groupby(["sex", "size", "age"])
        .size()
        .reset_index(name="count")
    )

    # --- Set category order for consistent layout ---
    sex_order = ["Female", "Male"]
    age_order = ["Baby", "Young", "Adult", "Senior"]
    size_order = ["Small", "Medium", "Large", "Extra Large"]

    grouped["sex"] = pd.Categorical(grouped["sex"], categories=sex_order, ordered=True)
    grouped["age"] = pd.Categorical(grouped["age"], categories=age_order, ordered=True)
    grouped["size"] = pd.Categorical(grouped["size"], categories=size_order, ordered=True)
    grouped["count"] = grouped["count"].astype(int)

    # --- Plot the heatmap (clean, no inline labels) ---
    fig = px.density_heatmap(
        grouped,
        x="age",
        y="size",
        z="count",
        facet_col="sex",
        color_continuous_scale="Greens",
        category_orders={"age": age_order, "size": size_order, "sex": sex_order},
        labels={"age": "Age Group", "size": "Size"}
    )

    fig.update_coloraxes(colorbar_title="Number of available dogs")
    fig.update_traces(
        hovertemplate="Age: %{x}<br>Size: %{y}<br>Number of available dogs: %{z}<extra></extra>"
    )
    fig.update_layout(height=500, showlegend=False)

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Dataset not loaded. Please upload it in the sidebar first.")

# --- Graph 3: Compatibility by filtered traits ---
if "df" in st.session_state:
    df = st.session_state.df

    # Filter essential columns
    df = df.dropna(subset=[
        "breed_primary", "age", "sex", "size",
        "env_children", "env_dogs", "env_cats", "contact_state"
    ])

    # --- Apply state filter ---
    if "selected_state" in st.session_state:
        selected_state = st.session_state.selected_state
        df = df[df["contact_state"] == selected_state]

    # --- Get top 10 breeds in state ---
    top_breeds = df["breed_primary"].value_counts().head(10).index.tolist()

    # --- Get selected breed from session (set in Graph 2) ---
    if "selected_breed" in st.session_state:
        selected_breed = st.session_state.selected_breed
    else:
        selected_breed = top_breeds[0]  # fallback

    breed_df = df[df["breed_primary"] == selected_breed].copy()

    st.markdown("### 🧩 Will this breed get along with your household?")
    st.markdown("##### Choose age, size, and sex to see how compatible these dogs are with children, cats, and other dogs.")

    # --- Trait selection controls ---
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_age = st.radio("Age", ["Baby", "Young", "Adult", "Senior"], horizontal=True)
    with col2:
        selected_sex = st.radio("Sex", ["Female", "Male"], horizontal=True)
    with col3:
        selected_size = st.radio("Size", ["Small", "Medium", "Large", "Extra Large"], horizontal=True)

    # --- Standardize categorical values to title case ---
    breed_df["age"] = breed_df["age"].str.title()
    breed_df["sex"] = breed_df["sex"].str.title()
    breed_df["size"] = breed_df["size"].str.title()

    # --- Filter based on selected traits ---
    filtered = breed_df[
        (breed_df["age"] == selected_age) &
        (breed_df["sex"] == selected_sex) &
        (breed_df["size"] == selected_size)
    ]

    if filtered.empty:
        st.info("No dogs found for the selected combination. Try adjusting age, size, or sex.")
    else:
        def count_responses(column, label):
            mapped = filtered[column].map({
                True: "Yes",
                False: "No"
            }).fillna("Unknown")

            vc = (
                mapped
                .value_counts()
                .reindex(["Yes", "No", "Unknown"], fill_value=0)
                .reset_index()
            )
            vc.columns = ["Response", "Count"]
            vc["Trait"] = label
            return vc

        df_children = count_responses("env_children", "Children")
        df_dogs = count_responses("env_dogs", "Dogs")
        df_cats = count_responses("env_cats", "Cats")

        df_compat = pd.concat([df_children, df_dogs, df_cats], ignore_index=True)

        fig = px.bar(
            df_compat,
            x="Trait",
            y="Count",
            color="Response",
            barmode="group",
            category_orders={"Response": ["Yes", "No", "Unknown"]},
            title=f"Compatibility for {selected_breed} in {selected_state} ({selected_age}, {selected_sex}, {selected_size})"
        )

        fig.update_layout(yaxis=dict(range=[0, df_compat["Count"].max() + 1]))

        st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Please upload the dataset in the sidebar first.")

