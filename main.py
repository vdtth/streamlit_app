import streamlit as st
import pandas as pd
import numpy as np
from vega_datasets import data
from datetime import date, datetime
import altair as alt
from altair import datum
# from utils import get_chart
def space(num_lines=1):
    """Adds empty lines to the Streamlit app."""
    for _ in range(num_lines):
        st.write("")


st.title('Statistic results')
col1, col2 = st.columns(2)




df = pd.read_csv('https://c4ac-113-23-43-136.ngrok.io/csv')
ticker_list = list(df.coin.unique())
# ticker = ticker_list[3] #"PEOPLEUSDT"
df['Date'] = pd.to_datetime(df['Date'],format='%y-%m-%d,%H:%M')


with col1:
    start_date = st.date_input(
        "Select start date",
        date(2020, 1, 1),
        min_value=datetime.strptime("2020-01-01", "%Y-%m-%d"),
        max_value=datetime.now(),
    )

with col2:
    symbols = st.multiselect("Choose stocks to visualize", ticker_list, ticker_list[0])

lines = alt.Chart(df,title='',width= 800).mark_line().encode(
    x=alt.X('Date:T'),
    y=alt.Y('Equity:Q',scale=alt.Scale(domain=[df[df.coin.isin(symbols)].Equity.min(), df[df.coin.isin(symbols)].Equity.max()])),
    color=alt.Color('timeframe:N'),
    shape='coin:N'
).transform_filter(
    (datum.G_profit != 0)
).transform_filter(
 alt.FieldOneOfPredicate(field='coin', oneOf=symbols)
)

hover = alt.selection_single(
    fields=["Date"],
    nearest=True,
    on="mouseover",
    empty="none",
)

# Draw points on the line, and highlight based on selection
points = lines.transform_filter(hover).mark_circle(size=100)

# Draw a rule at the location of the selection
tooltips = (
    alt.Chart(df)
    .mark_rule()
    .encode(
        x=alt.X("Date"),
        y=alt.Y("Equity"),
        opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
        tooltip=[
            alt.Tooltip("Date", title="Date"),
            alt.Tooltip("Equity", title="Equity"),
            alt.Tooltip("timeframe", title="TF"),
            alt.Tooltip("Profit", title="Profit"),
        ],
    )
    .add_selection(hover)
)
chart = (lines+points+tooltips ).interactive()



st.header("Results")
st.altair_chart(
    chart, use_container_width=True
)