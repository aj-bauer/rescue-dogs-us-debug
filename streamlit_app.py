import streamlit as st
import pandas as pd
import altair as alt

# --- Page Setup ---
st.set_page_config(page_title="Find your dream dog to adopt", layout="wide")

# --- Load dataset---
if "df" not in st.session_state:
    df = pd.read_csv("data/allDogDescriptions_new.csv")
    df["contact_state"] = df["contact_state"].str.strip()
    st.session_state.df = df
else:
    df = st.session_state.df

# ------ Graph 1: State map for dog availability ------ 
## Add titles
st.title("🐶 Find your dream dog to adopt today")
st.markdown("## 📍 Where do you live?")
st.markdown("### Click your state to see its top 10 dog breeds in the chart below the map")

## Aggregate the number of imported dogs per state
dog_state_metric = df.groupby("contact_state")["dog_id"].count().reset_index(name="dog_count")

## Add FIPS codes for merging with topojson 
state_fips = {
    'AL': 1, 'AK': 2, 'AZ': 4, 'AR': 5, 'CA': 6, 'CO': 8, 'CT': 9, 'DE': 10,
    'FL': 12, 'GA': 13, 'HI': 15, 'ID': 16, 'IL': 17, 'IN': 18, 'IA': 19,
    'KS': 20, 'KY': 21, 'LA': 22, 'ME': 23, 'MD': 24, 'MA': 25, 'MI': 26,
    'MN': 27, 'MS': 28, 'MO': 29, 'MT': 30, 'NE': 31, 'NV': 32, 'NH': 33,
    'NJ': 34, 'NM': 35, 'NY': 36, 'NC': 37, 'ND': 38, 'OH': 39, 'OK': 40,
    'OR': 41, 'PA': 42, 'RI': 44, 'SC': 45, 'SD': 46, 'TN': 47, 'TX': 48,
    'UT': 49, 'VT': 50, 'VA': 51, 'WA': 53, 'WV': 54, 'WI': 55, 'WY': 56
}
dog_state_metric["id"] = dog_state_metric["contact_state"].map(state_fips)

## Load US map
states = alt.topo_feature(
    'https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/us-10m.json',
    'states'
)

## Selection and map interactivity
click_state = alt.selection_point(name="Select", fields=["id"])
opacity = alt.condition(click_state, alt.value(1), alt.value(0.2))

## Draw the map
chloropleth = alt.Chart(states).mark_geoshape().transform_lookup(
    lookup='id',
    from_=alt.LookupData(dog_state_metric, 'id', ['dog_count', 'contact_state'])
).encode(
    opacity=opacity,
    tooltip=[
        alt.Tooltip('contact_state:N', title='State'),
        alt.Tooltip('dog_count:Q', title='Num. of Imported Dogs')
    ]
).project(
    type='albersUsa'
).properties(
    width=600,
    height=400
).add_params(
    click_state
)

## Display map
state_map = st.altair_chart(chloropleth, use_container_width=True, on_select="rerun")

# --- Graph 2: Bar Chart - Top 10 breeds in selected state ---
## Extract selected FIPS from query params
selected_fips = st.query_params.get('_Select_id', None)

## Convert FIPS to state abbreviation
fips_state = {v: k for k, v in state_fips.items()}
selected_state = fips_state.get(int(selected_fips)) if selected_fips else None
st.session_state.selected_state = selected_state

## Filter dataset
dog_state_filtered = df[df["contact_state"] == selected_state] if selected_state else df

## Plot top 10 breeds
if selected_state:
    top_breeds = (
        dog_state_filtered["breed_primary"]
        .value_counts()
        .head(10)
        .reset_index()
    )
    top_breeds.columns = ["breed", "count"]

    bar_chart = alt.Chart(top_breeds).mark_bar().encode(
        x=alt.X("count:Q", title="Number of Dogs"),
        y=alt.Y("breed:N", sort='-x', title="Breed"),
        tooltip=[alt.Tooltip("breed:N"), alt.Tooltip("count:Q")]
    ).properties(
        title=f"Top 10 Dog Breeds in {selected_state}",
        width=400,
        height=150
    )

    st.altair_chart(bar_chart, use_container_width=True)
else:
    st.info("Click a state on the map to explore its top dog breeds.")
    
# --- Graph 3: Dog breeds and related characteristics ---
if "df" in st.session_state:
    df = st.session_state.df

    # Filter missing values
    df = df.dropna(subset=["breed_primary", "age", "sex", "size", "contact_state"])

    # Get selected state or fallback to national
    selected_state = st.session_state.get("selected_state", None)
    state_df = df[df["contact_state"] == selected_state] if selected_state else df

    # Get top breeds
    top_breeds = (
        state_df["breed_primary"]
        .value_counts()
        .head(10)
        .index
        .tolist()
    )

    st.markdown("## 🐕 What type of dog are you looking for?")
    st.markdown("### Choose the breed you are interested in")

    state_label = selected_state if selected_state else "None (National)"
    st.markdown(f"🗺️ Filtering by state: **{state_label}**")

    if not top_breeds:
        st.warning("No breed data found for the selected state. Please choose a different state.")
        st.stop()

    selected_breed = st.selectbox("", top_breeds)
    st.session_state.selected_breed = selected_breed

    # Filter dataset by breed
    breed_df = state_df[state_df["breed_primary"] == selected_breed]

    # Group and count
    grouped = (
        breed_df.groupby(["sex", "size", "age"])
        .size()
        .reset_index(name="count")
    )

    # Set category orders
    sex_order = ["Female", "Male"]
    age_order = ["Baby", "Young", "Adult", "Senior"]
    size_order = ["Small", "Medium", "Large", "Extra Large"]

    grouped["sex"] = pd.Categorical(grouped["sex"], categories=sex_order, ordered=True)
    grouped["age"] = pd.Categorical(grouped["age"], categories=age_order, ordered=True)
    grouped["size"] = pd.Categorical(grouped["size"], categories=size_order, ordered=True)

    # Heatmap chart
    heatmap = alt.Chart(grouped).mark_rect().encode(
        x=alt.X("age:N", title="Age", sort=age_order),
        y=alt.Y("size:N", title="Size", sort=size_order),
        color=alt.Color("count:Q", scale=alt.Scale(scheme='greens'), title="Count"),
        tooltip=["age:N", "size:N", "count:Q"]
    ).properties(
        width=800,
        height=400
    )

    final_chart = heatmap.facet(
        column=alt.Column("sex:N", title=None, sort=sex_order)
    ).resolve_scale(color="independent")

    st.altair_chart(final_chart, use_container_width=True)

else:
    st.warning("Dataset not loaded. Please upload it in the sidebar first.")

# --- Graph 4: Compatibility by filtered traits ---
if "df" in st.session_state:
    df = st.session_state.df

    df = df.dropna(subset=[
        "breed_primary", "age", "sex", "size",
        "env_children", "env_dogs", "env_cats", "contact_state"
    ])

    # Get selected state or national fallback
    selected_state = st.session_state.get("selected_state", None)
    df = df[df["contact_state"] == selected_state] if selected_state else df

    # Top breeds
    top_breeds = df["breed_primary"].value_counts().head(10).index.tolist()

    # Select breed from session or fallback
    if "selected_breed" in st.session_state:
        selected_breed = st.session_state.selected_breed
    elif top_breeds:
        selected_breed = top_breeds[0]
    else:
        selected_breed = None

    # Handle empty fallback
    if not selected_breed:
        st.warning("No breed data found for the selected state. Please choose a different state.")
        st.stop()

    breed_df = df[df["breed_primary"] == selected_breed].copy()

    st.markdown("## 🧩 Will this breed get along with your household?")
    st.markdown("### Choose age, size, and sex to see how compatible these dogs are with children, cats, and dogs.")

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_age = st.radio("Age", ["Baby", "Young", "Adult", "Senior"], horizontal=True)
    with col2:
        selected_sex = st.radio("Sex", ["Female", "Male"], horizontal=True)
    with col3:
        selected_size = st.radio("Size", ["Small", "Medium", "Large", "Extra Large"], horizontal=True)

    # Standardize
    breed_df["age"] = breed_df["age"].str.title()
    breed_df["sex"] = breed_df["sex"].str.title()
    breed_df["size"] = breed_df["size"].str.title()

    filtered = breed_df[
        (breed_df["age"] == selected_age) &
        (breed_df["sex"] == selected_sex) &
        (breed_df["size"] == selected_size)
    ]

    if filtered.empty:
        st.info("No dogs found for the selected combination. Try adjusting age, size, or sex.")
    else:
        def count_responses(column, label):
            mapped = filtered[column].map({True: "Yes", False: "No"})
            vc = (
                mapped.value_counts()
                .reindex(["Yes", "No"], fill_value=0)
                .reset_index()
            )
            vc.columns = ["Response", "Count"]
            vc["Trait"] = label
            return vc

        df_children = count_responses("env_children", "Children")
        df_dogs = count_responses("env_dogs", "Dogs")
        df_cats = count_responses("env_cats", "Cats")

        df_compat = pd.concat([df_children, df_dogs, df_cats], ignore_index=True)

        state_label = selected_state if selected_state else "the US"

        bar_chart = alt.Chart(df_compat).mark_bar().encode(
            x=alt.X("Trait:N", title=None),
            y=alt.Y("Count:Q", title="Number of Dogs"),
            color=alt.Color("Response:N", title="Compatible", scale=alt.Scale(domain=["Yes", "No"])),
            tooltip=["Trait", "Response", "Count"]
        ).properties(
            width=400,
            height=400,
            title=f"Compatibility for {selected_breed} in {state_label} ({selected_age}, {selected_sex}, {selected_size})"
        )

        st.altair_chart(bar_chart, use_container_width=True)

        st.markdown(
            "*Note: Each compatibility trait is recorded separately.*"
        )

else:
    st.warning("Please upload the dataset in the sidebar first.")



