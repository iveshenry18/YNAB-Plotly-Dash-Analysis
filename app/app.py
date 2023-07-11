import base64
import io
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import dash_table
import flask
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

server = flask.Flask(__name__)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], server=server)  # Dark theme applied

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("YNAB Register Analysis", style={'textAlign': 'center', 'marginBottom': 50, 'marginTop': 50}),
        ]),
        dbc.Col([
            dcc.Upload(
                id='upload-data',
                children=dbc.Button('Upload YNAB Register', id='upload-button', color="primary", className="mr-1"),
                style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'},
            ),
        ]),
    ], align='center', justify='center'),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='graph1', style={'height': '400px'}),
                ], width=6),
                dbc.Col([
                    dcc.Graph(id='graph2', style={'height': '400px'}),
                ], width=6),
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='graph3', style={'height': '400px'}),
                ], width=6),
                dbc.Col([
                    dcc.Graph(id='graph4', style={'height': '400px'}),
                ], width=6),
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='pie-chart', style={'height': '400px'}),
                ], width=12),
            ]),
        ], width=9),
        dbc.Col([
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date_placeholder_text="Start Period",
                end_date_placeholder_text="End Period",
                display_format='YYYY-MM',
                style={
                    'backgroundColor': '#252525',
                    'color': 'white',
                    'padding': '10px',
                    'borderRadius': '5px',
                },
            ),
            dcc.Dropdown(
                id='category-dropdown',
                placeholder="Select Category",
                style={
                    'backgroundColor': '#252525',
                    'color': 'white',
                    'padding': '10px',
                    'borderRadius': '5px',
                },
            ),
            dash_table.DataTable(
                id='table',
                virtualization=True, 
                style_as_list_view=True,
                style_header={'backgroundColor': '#252525', 'color': 'white'},
                style_cell={'backgroundColor': '#252525', 'color': 'white'},
                style_cell_conditional=[
                    {'if': {'column_id': c},
                    'textAlign': 'left'}
                    for c in ['Date', 'Description', 'Category', 'Memo', 'Outflow', 'Inflow', 'Running Balance', 'Account', 'Account Type', 'Flag', 'Category Group/Category', 'Cleared', 'Month-Year', 'Month', 'Net Worth']
                ],
            ),
        ], width=3),
    ]),
], fluid=True, style={'backgroundColor': '#252525'})

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    return df

@app.callback(
    [Output('graph1', 'figure'), Output('graph2', 'figure'), Output('graph3', 'figure'), Output('graph4', 'figure'), Output('pie-chart', 'figure'), Output('table', 'data'), Output('table', 'columns'), Output('category-dropdown', 'options')],
    [Input('upload-data', 'contents'), Input('category-dropdown', 'value'), Input('date-picker-range', 'start_date'), Input('date-picker-range', 'end_date')]
)
def update_graphs(contents, selected_category, start_date, end_date):
    if contents is None:
        return {}, {}, {}, {}, {}, [], [], []

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

    # Filter data based on the selected category and date range
    if selected_category is not None:
        df = df[df['Category'] == selected_category]
    if start_date is not None:
        df = df[df['Date'] >= start_date]
    if end_date is not None:
        df = df[df['Date'] <= end_date]

    # Create the figures for your graphs
    fig1 = px.line(df.groupby('Month-Year')[['Outflow', 'Inflow']].sum().reset_index(), x='Month-Year', y=['Outflow', 'Inflow'], title='Monthly Inflow vs Outflow', template='plotly_dark')
    fig2 = px.area(df.pivot_table(values='Outflow', index='Month-Year', columns='Category', aggfunc='sum', fill_value=0).reset_index().melt(id_vars='Month-Year'), x='Month-Year', y='value', color='Category', title='Category Spending Over Time', template='plotly_dark')
    fig3 = px.imshow(df.pivot_table(values='Outflow', index='Category', columns='Month-Year', aggfunc='sum', fill_value=0), title='Seasonal Analysis of Expenses', template='plotly_dark')
    df['Net Worth'] = df['Inflow'] - df['Outflow']
    net_worth_over_time = df.groupby('Month-Year')['Net Worth'].sum().cumsum()
    fig4 = px.line(net_worth_over_time.reset_index(), x='Month-Year', y='Net Worth', title='Net Worth Over Time', template='plotly_dark')
    fig5 = px.pie(df, values='Outflow', names='Category', title='Expenses Breakdown by Category', template='plotly_dark')

    # Prepare data and columns for the DataTable
    data = df.to_dict('records')
    columns = [{"name": i, "id": i} for i in df.columns if i not in ['Flag', 'Category Group/Category', 'Cleared', 'Month-Year', 'Month']]

    # Prepare options for the dropdown menu
    options = [{'label': category, 'value': category} for category in df['Category'].unique()]

    return fig1, fig2, fig3, fig4, fig5, data, columns, options

if __name__ == '__main__':
    app.run_server(debug=True)