"""Elections cote in Paris with streamlit"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk
import datetime
import plotly.express as px

# SETTING PAGE CONFIG TO WIDE MODE AND LOAD CSS FILE
st.set_page_config(layout="wide")

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.title("Presidential election vote by district")


    
# METRICS TO DISPLAY AND COLORS SELECTION
candidates_2022 = ['le_pen_marine', 'macron_emmanuel', 'melenchon_jean_luc', 'zemmour_eric', 'pecresse_valerie',\
                    'jadot_yannick', 'roussel_fabien', 'arthaud_nathalie', 'lassalle_jean', 'dupont_aignan_nicolas', 'poutou_philippe']

candidates_2022_renamed = ['Marine Le Pen', 'Emmanuel Macron', 'Jean-Luc Mélanchon', 'Eric Zemmour', 'Valérie Pecresse',\
                    'Yannick Jadot', 'Fabien Roussel', 'Nathalie Arthaud', 'Jean Lassalle', 'Nicolas Dupont-Aignan', 'Philippe Poutou']

candidates_2017 = ['le_pen_marine', 'macron_emmanuel', 'melenchon_jean_luc', 'hamon_benoit', 'asselineau_francois',\
                    'fillon_francois', 'cheminade_jacques', 'arthaud_nathalie', 'dupont_aignan_nicolas', 'poutou_philippe']

candidates_2017_renamed = ['Marine Le Pen',  'Emmanuel Macron', 'Jean-Luc Mélanchon', 'Benoit Hamon', 'Francois Asselineau',\
                    'Francois Fillon', 'Jacques Cheminade', 'Nathalie Arthaud', 'Nicolas Dupont-Aignan', 'Philippe Poutou']

COLOR_RANGE = [
    [140, 237, 176],
    [118, 229, 170],
    [96, 221, 164],
    [73, 213, 159],
    [50, 205, 158],
    [43, 187, 153],
    [31, 162, 141],
    [22, 147, 132],
    [12, 126, 120],
    [2, 105, 105],
]

metric_selected = 'Emmanuel Macron'

# LOAD DATA 
@st.experimental_singleton
def load_data(name):
    json = pd.read_json(name)
    return json

#  CREATE DATAFRAME
@st.experimental_singleton
def dataframe_agg (data, list_metric):
    df = pd.DataFrame()
    for i in list_metric:
        df['coordinates'] = data["features"].apply(lambda row: row["geometry"]["coordinates"])
        df['arrondissements'] = data["features"].apply(lambda row: row["properties"]["arr_bv"])
        df['id_bvote'] = data["features"].apply(lambda row: row["properties"]["id_bvote"])
        df['annee'] = data["features"].apply(lambda row: row["properties"]["annee"])
        df['nb_exprime'] = data["features"].apply(lambda row: row["properties"]["nb_exprime"])
        #df['numero_tour'] = data["features"].apply(lambda row: row["properties"]["numero_tour"])
        df[i] = data["features"].apply(lambda row: row["properties"][i])
        df[i] = df[i].astype(int)
        df['arrondissements'] = df['arrondissements'].astype('str') + ' eme'

        df.rename(columns={'le_pen_marine':'Marine Le Pen', 'nb_votant':'Votants', 'nb_inscrit':'Inscrits',\
        'nb_vote_blanc':'Votes blanc', 'macron_emmanuel':'Emmanuel Macron', 'melenchon_jean_luc':'Jean-Luc Mélanchon',\
        'zemmour_eric':'Eric Zemmour', 'pecresse_valerie':'Valérie Pecresse', 'jadot_yannick':'Yannick Jadot', \
        'roussel_fabien':'Fabien Roussel', 'arthaud_nathalie':'Nathalie Arthaud', 'dupont_aignan_nicolas':'Nicolas Dupont-Aignan',\
        'poutou_philippe':'Philippe Poutou', 'lassalle_jean':'Jean Lassalle', 'fillon_francois':'Francois Fillon',\
        'hamon_benoit':'Benoit Hamon', 'asselineau_francois':'Francois Asselineau', 'cheminade_jacques' :'Jacques Cheminade'}, inplace=True)

    return df


# UPDATE DATAFRAME AND FILTER ON SELECTED METRIC
@st.experimental_singleton
def update_dataframe(data, metric_selected):
    """
    Create a dataframe with only one metric (one that has been selected below)
    """
    df = data[['coordinates', 'annee', 'arrondissements', 'nb_exprime', metric_selected]]
    df[metric_selected].fillna(0, inplace=True)
    df.rename(columns={metric_selected:'metric'}, inplace=True)
    df['mix'] = round(df.metric / df.metric.sum() * 100, 2)
    #df['part'] = round(df.metric / df.nb_exprime * 100, 2)

    return df

# GET METRICS FOR SELECTOR MENU
@st.experimental_singleton
def list_metrics(data):
    """
    To give only dimensions in the select box and not metrics
    """
    column_name = data.columns.to_list()
    dimension = ['coordinates', 'annee', 'numero_tour', 'arrondissements', 'id_bvote', 'nb_exprime']

    list_metric = np.setdiff1d(column_name, dimension).tolist()

    return list_metric


# GENERATE DATAFRAME
data_2022 = load_data("2022_1T_presidentielles.geojson")
data_2017 = load_data("2017_1T_presidentielles.geojson")

df_2022 = dataframe_agg(data_2022, candidates_2022)
df_2017 = dataframe_agg(data_2017, candidates_2017)
#st.write(df_2022)

@st.experimental_singleton
def get_podium(data, list_candidates):
    podium = data.groupby(by='annee')[list_candidates].sum()
    podium = podium.unstack(level=1).reset_index()
    podium.rename(columns={'level_0':'candidates', 0:'votes'}, inplace=True)
    podium.sort_values(by='votes', ascending=False, inplace=True)
    podium['rank'] = podium['votes'].rank(ascending=False)

    return podium

#st.write(st.session_state)
#def update_selectbox():
#    st.session.select_box = st.session

# INITIALIZE METRIC LIST AND PODIUM DATA
if 'list' not in st.session_state:
    st.session_state['list'] = list_metrics(df_2022)

if 'year' not in st.session_state:
    st.session_state['year'] = '2022'

if 'podium' not in st.session_state:
    st.session_state['podium'] = get_podium(df_2022, candidates_2022_renamed)

podium = st.session_state.podium


# STREAMLIT DISPLAY
col_num1, col_num2, col_num3, col_num4, = st.columns((1.5, 0.2, 0.2,1.5)) 


if 'df' not in st.session_state:
    st.session_state['df'] = update_dataframe(df_2022, metric_selected)

df = st.session_state.df


with col_num2:
    if st.button('2022'):
        st.session_state['list'] = list_metrics(df_2022)
        st.session_state['df'] = update_dataframe(df_2022, metric_selected)
        st.session_state['podium'] = get_podium(df_2022, candidates_2022_renamed)
        podium = st.session_state.podium
        #st.session_state['selectbox'] = st.selectbox('', st.session_state['list'])

with col_num3:
    if st.button('2017'):
        st.session_state['list'] = list_metrics(df_2017)
        st.session_state['df'] = update_dataframe(df_2017, metric_selected)
        st.session_state['podium'] = get_podium(df_2017, candidates_2017_renamed)
        podium = st.session_state.podium
        st.session_state['year'] = '2017'
        
with col_num1:
        metric_selected = st.selectbox('', options=st.session_state['list'], key='select_box')
        if st.session_state['year'] == '2017':
            st.session_state['df'] = update_dataframe(df_2017, metric_selected)
            df = st.session_state['df']
        elif st.session_state['year'] == '2022':
            st.session_state['df'] = update_dataframe(df_2022, metric_selected)
            df = st.session_state['df']


# GET DATA TO GENERATE COLORS PALETTE
metric_min = df[['metric']].min()[0]
metric_max = df[['metric']].max()[0]

BREAKS = [metric_min, (metric_max/10)*2, (metric_max/10)*3, (metric_max/10)*4, (metric_max/10)*5,\
    (metric_max/10)*6, (metric_max/10)*7, (metric_max/10)*8, (metric_max/10)*9, metric_max]

@st.experimental_singleton
def color_scale(val):
    for i, b in enumerate(BREAKS):
        if val < b:
            return COLOR_RANGE[i]
    return COLOR_RANGE[i]

df['fill_color'] = df['metric'].apply(lambda row: color_scale(row))


## DISPLAY MAP
col1, blank, col2 = st.columns((1.8,0.2,1.2))

with col1:

    st.subheader("Votes by polling station")
    # FUNCTION FOR MAPS
    def map (data): 
        #map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
                longitude=2.3323,
                latitude=48.8595,
                zoom=11,
                min_zoom=5,
                max_zoom=15,
                pitch=0,
                bearing=0
        )

        map_layer = pdk.Layer(
                "PolygonLayer",
                data,
                id="geojson",
                opacity=0.7,
                get_polygon='coordinates',
                filled=True,
                extruded=True,
                wireframe=True,
                get_elevation="elevation",
                get_fill_color="fill_color",
                get_line_color=[222, 247, 236, 0.8],
                auto_highlight=True,
                pickable=True,
        )
        # renommer en metric la colonne de donénes
        tooltip = {"html": "<b>Votes number:</b> {metric} <br /><b>% total:</b> {mix}% "}

        r = pdk.Deck(
        layers=[map_layer],
        initial_view_state=initial_view_state,
        tooltip=tooltip,
        )

        st.pydeck_chart(r) 

    map(df)



# DISPLAY HISTOGRAM
with col2:
    st.write(podium)
    my_podium = podium[podium.candidates == metric_selected]['rank'].values[0]
    st.subheader("This candidate came in :point_right: : #" + str(int(my_podium))+" place")
    #st.write(my_podium)
    st.subheader("Top 5 : districts that voted the most for this candidate")
    histo = df.groupby(['arrondissements']).agg({'metric':'sum'}).sort_values(by='metric', ascending=False).head(5) / df.metric.sum()
    histo = histo.reset_index()
    

    fig = px.bar(histo.sort_values(by='metric'), x='metric',y='arrondissements', text='metric', color_discrete_sequence=['rgb(22, 147, 132)'], hover_data={'metric':False, 'arrondissements':False})

    fig.update_layout(
        plot_bgcolor='rgb(14,17,23)',
        height=400,
        width=500,
        xaxis=dict(
                showline=False,
                showgrid=False,
                showticklabels=False,
                ticks=None,
                title='',
                tickfont=dict(
                    family='Source Sans Pro',
                    size=12,
                    color='#CCCCCC',
                ),
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showline=False,
                ticks='outside',
                title='',
                tickfont=dict(
                    family='Source Sans Pro',
                    size=15,
                    color='#CCCCCC',
                ),
                
            ))
    fig.update_traces(texttemplate='%{text:.0%}', textposition='inside')

    st.plotly_chart(fig)