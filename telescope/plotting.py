from typing import List

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.figure_factory as ff
import streamlit as st

from telescope.metrics.result import PairwiseResult, BootstrapResult

DARKGREEN = "#2E8B57"
LIGHTGREEN = '#9ACD32'
ORANGE = '#F6C575'
RED = '#DB6646'

T1_COLOR = DARKGREEN
T2_COLOR = LIGHTGREEN
T3_COLOR = ORANGE
T4_COLOR = RED

def update_cua(x_scores, y_scores, crit_err_thr=.0, major_err_thr=0.3, minor_err_thr=0.6):
    total = len(x_scores)

    no_err_old = 0
    minor_err_old = 0
    major_err_old = 0
    crit_err_old = 0

    no_err_new = 0
    minor_err_new = 0
    major_err_new = 0
    crit_err_new = 0

    for index, (old, new) in enumerate(zip(x_scores, y_scores)):
        if old >= minor_err_thr:
            no_err_old+=1
        elif old >= major_err_thr:
            minor_err_old+=1
        elif old >= crit_err_thr:
            major_err_old+=1
        else:
            crit_err_old += 1
        if new >= minor_err_thr:
            no_err_new+=1
        elif new >= major_err_thr:
            minor_err_new+=1
        elif new >= crit_err_thr:
            major_err_new+=1
        else:
            crit_err_new+=1

    assert total == (no_err_old+minor_err_old+major_err_old+crit_err_old) == (no_err_new+minor_err_new+major_err_new+crit_err_new)

    no_err_old = (no_err_old/total)*100
    minor_err_old = (minor_err_old/total)*100
    major_err_old = (major_err_old/total)*100
    crit_err_old = (crit_err_old/total)*100
        
    no_err_new = (no_err_new/total)*100
    minor_err_new = (minor_err_new/total)*100
    major_err_new = (major_err_new/total)*100
    crit_err_new = (crit_err_new/total)*100

    r = [0,1]
    raw_data = {'T4Bars': [crit_err_old, crit_err_new], 'T3Bars': [major_err_old, major_err_new],'T2Bars': [minor_err_old, minor_err_new],'T1Bars': [no_err_old, no_err_new]}
    df = pd.DataFrame(raw_data)

    T4Bars = raw_data['T4Bars']
    T3Bars = raw_data['T3Bars']
    T2Bars = raw_data['T2Bars']
    T1Bars = raw_data['T1Bars']
        
    # plot
    barWidth = 0.85
    names = ('System X','System Y')
        
    ax1 = plt.bar(r, T4Bars, color=T4_COLOR, edgecolor='white', width=barWidth)
    ax2 = plt.bar(r, T3Bars, bottom=T4Bars, color=T3_COLOR, edgecolor='white', width=barWidth)
    ax3 = plt.bar(r, T2Bars, bottom=[i+j for i,j in zip(T4Bars, T3Bars)], color=T2_COLOR, edgecolor='white', width=barWidth)
    ax4 = plt.bar(r, T1Bars, bottom=[i+j+k for i,j,k in zip(T4Bars, T3Bars, T2Bars)], color=T1_COLOR, edgecolor='white', width=barWidth)
        
    for r1, r2, r3, r4 in zip(ax1, ax2, ax3, ax4):
        h1 = r1.get_height()
        h2 = r2.get_height()
        h3 = r3.get_height()
        h4 = r4.get_height()
        plt.text(r1.get_x() + r1.get_width() / 2., h1 / 2., "{:.2f}".format(h1), ha="center", va="center", color="white", fontsize=12, fontweight="bold")
        plt.text(r2.get_x() + r2.get_width() / 2., h1 + h2 / 2., "{:.2f}".format(h2), ha="center", va="center", color="white", fontsize=12, fontweight="bold")
        plt.text(r3.get_x() + r3.get_width() / 2., h1 + h2 + h3 / 2., "{:.2f}".format(h3), ha="center", va="center", color="white", fontsize=12, fontweight="bold")
        plt.text(r4.get_x() + r4.get_width() / 2., h1 + h2 + h3 + h4 / 2., "{:.2f}".format(h4), ha="center", va="center", color="white", fontsize=12, fontweight="bold")
        
    # Custom x axis
    plt.xticks(r, names)
    plt.xlabel("Model")
    return plt

def plot_bucket_comparison(pairwise_result) -> None:
    min_score = min([min(pairwise_result.x_result.seg_scores), min(pairwise_result.y_result.seg_scores)])
    max_score = max([max(pairwise_result.x_result.seg_scores), max(pairwise_result.y_result.seg_scores)])

    col1, col2, col3 = st.beta_columns(3)
    with col1:
        red_bucket = st.slider('Red bucket max treshold', min_score, .3, value=.1, step=0.1)
            
    with col2:
        yellow_bucket = st.slider('Yellow bucket max treshold', red_bucket, 0.5, value=0.3, step=0.1)
        
    with col3:
        blue_bucket = st.slider('Blue bucket max treshold', yellow_bucket, 0.8, value=0.7, step=0.1)
        
    right, left  = st.beta_columns(2)
    left.pyplot(update_cua(pairwise_result.x_result.seg_scores, pairwise_result.y_result.seg_scores, red_bucket, yellow_bucket, blue_bucket))
    plt.clf()
    right.markdown("""
    The bucket analysis separates translations according to 4 different categories:
        
    - **Green bucket:** Translations without errors.
    - **Blue bucket:** Translations with minor errors.
    - **Yellow bucket:** Translations with major errors.
    - **Red bucket:** Translations with critical errors.
    """
    )


def plot_system_results(pairwise_results: List[PairwiseResult]) -> None:
    summary = {
        "x": [p_res.x_result.sys_score for p_res in pairwise_results],
        "y": [p_res.y_result.sys_score for p_res in pairwise_results],
    }

    st.dataframe(
        pd.DataFrame.from_dict(
            summary,
            orient="index",
            columns=[r.metric for r in pairwise_results],
        )
    )

def plot_pairwise_distributions(pairwise_result: PairwiseResult) -> None:
    scores = np.array([pairwise_result.x_result.seg_scores, pairwise_result.y_result.seg_scores]).T
    hist_data = [scores[:, i] for i in range(scores.shape[1])]
    fig = ff.create_distplot(
        hist_data,
        ["System X", "System Y"],
        bin_size=[0.1 for _ in range(scores.shape[1])],
    )
    st.plotly_chart(fig)


def plot_segment_comparison(pairwise_result: PairwiseResult) -> None:
    scores = np.array([pairwise_result.x_result.seg_scores, pairwise_result.y_result.seg_scores]).T
    chart_data = pd.DataFrame(scores, columns=["x_score", "y_score"])

    chart_data["difference"] = np.absolute(scores[:, 0] - scores[:, 1])
    chart_data["source"] = pairwise_result.src
    chart_data["reference"] = pairwise_result.ref
    chart_data["x"] = pairwise_result.system_x
    chart_data["y"] = pairwise_result.system_y

    c = (
        alt.Chart(chart_data)
        .mark_circle()
        .encode(
            x="x_score",
            y="y_score",
            size="difference",
            color=alt.Color("difference"),
            tooltip=[
                "x",
                "y",
                "reference",
                "difference",
                "source",
                "x_score",
                "y_score",
            ],
        )
    )
    st.altair_chart(c, use_container_width=True)

def plot_bootstraping_result(bootstrap_result: BootstrapResult):
    data = []
    metric_x_wins = bootstrap_result.win_count[0] / sum(bootstrap_result.win_count)
    metric_y_wins = bootstrap_result.win_count[1] / sum(bootstrap_result.win_count)
    metric_ties = bootstrap_result.win_count[2] / sum(bootstrap_result.win_count)
    data.append(
        {
            "metric": bootstrap_result.metric,
            "x win (%)": metric_x_wins,
            "y win (%)": metric_y_wins,
            "ties (%)": metric_ties,
        }
    )
    df = pd.DataFrame(data)
    st.dataframe(df)
