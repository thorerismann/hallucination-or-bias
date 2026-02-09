import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px


def prepare_streamlit_page():
    st.set_page_config(page_title="Political Bias models - viz", layout="wide")
    st.title("Political Bias models — variability across runs")

def make_sidebar(df):
    st.sidebar.header("Filters")
    models = st.sidebar.multiselect("Models", sorted(df["model"].unique()), default=sorted(df["model"].unique()))
    articles = st.sidebar.multiselect("Articles", df.article_id.unique(), default=df.article_id.unique())
    runs = st.sidebar.multiselect("Runs", sorted(df["run"].unique()), default=sorted(df["run"].unique()))
    show_data = st.sidebar.checkbox("Show raw data", value=False)
    return models, articles, runs, show_data

# --- Load data ---

def load_data(filename):
    df = pd.read_csv(f'app/{filename}')
    df = df.drop(columns=[c for c in ["Unnamed: 0"] if c in df.columns])
    return df

def prepare_bias_df(bdf, models, articles, runs):
# Make ids categorical strings for clean plotting
    bdf["article_str"] = bdf["article_id"].astype(str) + 'A'
    bdf["run"] = bdf["run"].astype(str)
    dff = bdf[bdf["model"].isin(models) & bdf["article_id"].isin(articles) & bdf["run"].isin([str(x) for x in runs])].copy()
    return dff

def make_bias_1(df):
    df['a_r_slug'] = df['run'].astype(str) + '_' + df['article_id'].astype(str)
    fig = px.scatter(df, y = 'overall_bias', x = 'model',color='confidence')
    st.plotly_chart(fig, use_container_width=True)

def make_bias_2(df):
    df['m_r_slug'] = df['model'] + '_' + df['run'].astype(str)
    fig = px.scatter(df, y = 'overall_bias', x = 'article_str', color = 'model')
    st.plotly_chart(fig, use_container_width=True)

def make_bias_variance_by_model(df):
    fig = px.box(
        df,
        x="model",
        y="overall_bias",
        points="all",
        color="model"
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def make_bias_heatmap(df):
    pivot = df.pivot_table(
        index="article_str",
        columns="model",
        values="overall_bias",
        aggfunc="mean"
    )

    height = max(400, 30 * len(pivot))  # ~30px per article row

    fig = px.imshow(
        pivot,
        color_continuous_scale="RdBu",
        zmin=-1,
        zmax=1,
        aspect="auto"
    )

    fig.update_layout(
        height=height,
        margin=dict(l=200, r=20, t=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)


def make_confidence_vs_bias(df):
    fig = px.scatter(
        df,
        x="confidence",
        y=df["overall_bias"].abs(),
        color="model",
    )
    fig.update_yaxes(title="|overall_bias|")
    st.plotly_chart(fig, use_container_width=True)


def main():
    prepare_streamlit_page()
    bdf = load_data('bias_data_2.csv')
    st.write(bdf)
    wdf = load_data('web_data.csv')
    models, articles, runs, show_data = make_sidebar(bdf)
    bdf_final = prepare_bias_df(bdf, models, articles, runs)
    if show_data:
        st.dataframe(bdf_final, use_container_width=True)
    make_bias_1(bdf_final)
    make_bias_2(bdf_final)
    make_bias_variance_by_model(bdf_final)
    make_bias_heatmap(bdf_final)
    make_confidence_vs_bias(bdf_final)

main()