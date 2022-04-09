import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime
import altair as alt
from altair import datum
from utils import *
import subprocess

# from utils import get_chart
def space(num_lines=1):
	"""Adds empty lines to the Streamlit app."""
	for _ in range(num_lines):
		st.write("")


st.title('Statistic results')
col1, col2 = st.columns(2)


@st.experimental_memo
def get_data(download=True):
	df = pd.read_csv('log.csv')
	df['Date'] = pd.to_datetime(df['Date'],unit='ms')

	top_equity = df.drop_duplicates(subset=['coin','timeframe'],keep='last').sort_values(by=['coin','timeframe']).sort_values(by=['Equity'],ascending=False)
	top_equity = top_equity.reset_index()
	# top_equity.drop('index',axis=1,inplace=True)
	top_equity['rank'] = list(range(1,len(top_equity)+1))
	top_equity_ = top_equity[['coin','timeframe','rank']]
	df = df.merge(top_equity_, left_on=['coin', 'timeframe'], right_on = ['coin', 'timeframe'], how='left')
	df['coin_tf'] = df['coin']+ "_"+df['timeframe'].astype(str)
	# top_equity[['coin','timeframe','rank','Equity']]

	return df

@st.experimental_memo
def get_top_chart(df,top_N):
	max_rank = df['rank'].max()
	if top_N > 0:
		lines = alt.Chart(df,title=f'Top {top_N}',width= 800).mark_line().encode(
			x=alt.X('Date:T'),
			y=alt.Y('Equity:Q',scale=alt.Scale(domain=[df.Equity.min(),df.Equity.max()])),
			color=alt.Color('coin_tf:N')
		).transform_filter(
			(datum.rank <= top_N)) 
	else:
		lines = alt.Chart(df,title=f'Bottom {top_N}',width= 800).mark_line().encode(
			x=alt.X('Date:T'),
			y=alt.Y('Equity:Q',scale=alt.Scale(domain=[df.Equity.min(),df.Equity.max()])),
			color=alt.Color('coin_tf:N')
		).transform_filter(
			(datum.rank > ( max_rank+top_N)))  
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
				alt.Tooltip("coin_tf", title="TF"),
				alt.Tooltip("Profit", title="Profit"),
			],
		)
		.add_selection(hover)
	)
	return (lines+points+tooltips ).interactive()

@st.experimental_memo
def get_chart_by_symbol(df,symbols):
	lines = alt.Chart(df,title='',width= 800).mark_line().encode(
	x=alt.X('Date:T'),
	y=alt.Y('Equity:Q',scale=alt.Scale(domain=[df[df.coin.isin(symbols)].Equity.min(), df[df.coin.isin(symbols)].Equity.max()])),
	color=alt.Color('coin_tf:N'),
	shape='coin:N',
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
				alt.Tooltip("coin_tf", title="coin"),
				alt.Tooltip("Profit", title="Profit"),
			],
		)
		.add_selection(hover)
	)
	return (lines+points+tooltips ).interactive()

df = get_data()
ticker_list = list(df.coin.unique())





start_date = st.date_input(
	"Select start date",
	date(2020, 1, 1),
	min_value=datetime.strptime("2020-01-01", "%Y-%m-%d"),
	max_value=datetime.now(),
)


	

topN = st.slider('Show top N equity', -10, 10, 5)
if st.button('Rerun'):
	subprocess.getstatusoutput('rm /home/tht/Downloads/TradingView_Alerts.csv')
	subprocess.getstatusoutput('mv /home/tht/Downloads/TradingView_Alerts* /home/tht/Downloads/TradingView_Alerts.csv')
	df1 = pd.read_csv('~/Downloads/TradingView_Alerts.csv').sort_values('Thời gian')
	# df1 = pd.read_csv('http://ad6b-116-97-117-125.ngrok.io/TV').sort_values('Thời gian')
	subprocess.getstatusoutput('rm -r history log*.csv')
	for alert in df1['Mô tả']:
		wh(alert)

uploaded_file = st.file_uploader("Upload alert")
if uploaded_file is not None:
	df1 = pd.read_csv(uploaded_file)
	subprocess.getstatusoutput('rm -r history log*.csv')
	for alert in df1['Mô tả']:
		wh(alert)


chart_all = get_chart_by_symbol(df,ticker_list) 

chart_top_equity = get_top_chart(df,topN)

st.header("All Results")
st.altair_chart(
	chart_all, use_container_width=True
)
st.header("Top N")
st.altair_chart(
	chart_top_equity, use_container_width=True
)

symbols = st.multiselect("Choose stocks to visualize", ticker_list, ticker_list[0])
chart_symbols = get_chart_by_symbol(df,symbols) 
st.header("Symbols")
st.altair_chart(
	chart_symbols, use_container_width=True
)
