import base64
import io
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash import dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("YNAB Register Analysis", style={'textAlign': 'center', 'marginBottom': 50, 'marginTop': 50}),
        ]),
        dbc.Col([
            dcc.Upload(
                id='upload-data',
                children=dbc.Button('Upload YNAB Register', id='upload-button'),
                style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'},
            ),
            ])
        ], align='center', justify='center'),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='graph1'),
                ]),
                dbc.Col([
                    dcc.Graph(id='graph2'),
                ]),
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='graph3'),
                ]),
                dbc.Col([
                    dcc.Graph(id='graph4'),
                    ]),
            ]),
        ], width=12, align='center'),
        dbc.Col([
            dash_table.DataTable(
                id='table',
                virtualization=True, 
            )
        ])
    ])
], fluid=True)

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    return df

@app.callback(
    [Output('graph1', 'figure'), Output('graph2', 'figure'), Output('graph3', 'figure'), Output('graph4', 'figure'), Output('table', 'data'), Output('table', 'columns')],
    [Input('upload-data', 'contents')]
)
def update_graphs(contents):
    if contents is None:
        return {}, {}, {}, {}, [], []

    df = parse_contents(contents)

    # Data cleaning and processing
    df['Date'] = pd.to_datetime(df['Date'])
    df['Outflow'] = df['Outflow'].replace({'\$': '', ',': ''}, regex=True).astype(float)
    df['Inflow'] = df['Inflow'].replace({'\$': '', ',': ''}, regex=True).astype(float)
    df['Memo'] = df['Memo'].fillna('No Memo')
    df['Flag'] = df['Flag'].fillna('No Flag')
    df['Category Group'] = df['Category Group'].fillna('No Category')
    df['Category'] = df['Category'].fillna('No Category')
    df['Month-Year'] = df['Date'].dt.to_period('M').astype(str)  # Convert Period to string
    df['Month'] = df['Date'].dt.month
    df['Net Worth'] = df['Inflow'] - df['Outflow']

    # Create the figures for your graphs
    fig1 = px.line(df.groupby('Month-Year')[['Outflow', 'Inflow']].sum().reset_index(), x='Month-Year', y=['Outflow', 'Inflow'], title='Monthly Inflow vs Outflow')
    fig2 = px.area(df.pivot_table(values='Outflow', index='Month-Year', columns='Category', aggfunc='sum', fill_value=0).reset_index().melt(id_vars='Month-Year'), x='Month-Year', y='value', color='Category', title='Category Spending Over Time')
    fig3 = px.imshow(df.pivot_table(values='Outflow', index='Month', columns='Category', aggfunc='sum', fill_value=0), title='Seasonal Analysis of Expenses')
    df['Net Worth'] = df['Inflow'] - df['Outflow']
    net_worth_over_time = df.groupby('Month-Year')['Net Worth'].sum().cumsum()
    fig4 = px.line(net_worth_over_time.reset_index(), x='Month-Year', y='Net Worth', title='Net Worth Over Time')

    # Prepare data and columns for the DataTable
    data = df.to_dict('records')
    columns = [{"name": i, "id": i} for i in df.columns if i not in ['Flag', 'Category Group/Category', 'Cleared', 'Month-Year', 'Month']]

    return fig1, fig2, fig3, fig4, data, columns

if __name__ == '__main__':
    app.run_server(debug=True)
