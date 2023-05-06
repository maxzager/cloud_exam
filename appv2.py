import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import os
import boto3
import pandas as pd

dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
table = dynamodb.Table('MeffScrapping')


def get_unique_dates(table):
    unique_dates = set()
    response = table.scan()
    for item in response['Items']:
        unique_dates.add(item['Date'])
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        for item in response['Items']:
            unique_dates.add(item['Date'])
    return unique_dates

def get_item(table, date):
    response = table.get_item(
        Key={
            'Date': date
        }
    )
    item = response.get('Item')
    return item

unique_dates = get_unique_dates(table)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1('Volatility Smile Dashboard', style={'font-family': 'Verdana', 'color': '#2A3F5F', 'margin-top': '30px', 'textAlign': 'center'}),
        html.Div([
            dcc.Graph(id='volatility-smile-graph', style={'width': '80%', 'display': 'inline-block'}),
            html.Div([
                html.Label('Select Data Collection Date', style={'font-family': 'Verdana', 'color': '#2A3F5F'}),
                dcc.Dropdown(
                    id='data-collection-date-dropdown',
                    options=[{'label': date, 'value': date} for date in unique_dates],
                    value=list(unique_dates)[-1],
                    style={'font-family': 'Verdana'}
                ),
                html.Label('Select Expiration Date', style={'font-family': 'Verdana', 'color': '#2A3F5F'}),
                dcc.Dropdown(
                    id='exp-date-dropdown',
                    style={'font-family': 'Verdana'}
                )
            ], style={'width': '18%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding-left': '20px'})
        ], style={'padding': '20px'})
    ], style={'background-color': '#F3F6FA', 'border-radius': '5px', 'padding': '20px', 'margin': '20px'})
])

@app.callback(
    [Output('exp-date-dropdown', 'options'),
     Output('exp-date-dropdown', 'value')],
    [Input('data-collection-date-dropdown', 'value')])
def update_exp_date_options(selected_date):
    item = get_item(table, selected_date)
    options_new = pd.DataFrame(item["Options"])
    exp_dates = options_new['EXP_DATE'].unique()
    return [{'label': date, 'value': date} for date in exp_dates], exp_dates[0]

@app.callback(
    Output('volatility-smile-graph', 'figure'),
    [Input('exp-date-dropdown', 'value'),
     Input('data-collection-date-dropdown', 'value')])
def update_graph(selected_exp_date, selected_date):
    item = get_item(table, selected_date)
    options_new = pd.DataFrame(item["Options"])
    filtered_options = options_new[options_new['EXP_DATE'] == selected_exp_date]

    call_options = filtered_options[filtered_options['CALL_PUT'] == 'CALL']
    put_options = filtered_options[filtered_options['CALL_PUT'] == 'PUT']

    call_trace = go.Scatter(
        x=call_options['STRIKE'],
        y=call_options['IV'],
        mode='markers+lines',
        name='Call Options',
        marker=dict(color='rgba(0, 152, 0, .8)', size=10, line=dict(width=2, color='black'))
    )
    print("Selected date:", selected_date)
    print("Filtered options:", filtered_options)

    put_trace = go.Scatter(
        x=put_options['STRIKE'],
        y=put_options['IV'],
        mode='markers+lines',
        name='Put Options',
        marker=dict(color='rgba(152, 0, 152, .8)', size=10, line=dict(width=2, color='black'))
    )

    layout = go.Layout(
        title='Volatility Smile from ' + selected_date + ' for the ' + selected_exp_date + ' expiration date',
        xaxis=dict(title='Strike', titlefont=dict(family='Verdana', color='#2A3F5F'), tickfont=dict(family='Verdana', color='#2A3F5F')),
        yaxis=dict(title='Implied Volatility', titlefont=dict(family='Verdana', color='#2A3F5F'), tickfont=dict(family='Verdana', color='#2A3F5F')),
        hovermode='closest',
        legend=dict(font=dict(family='Verdana', color='#2A3F5F')),
        plot_bgcolor='#F3F6FA',
        titlefont=dict(size=18),
        annotations=[
        dict(
            text="Meff Options Data scrapped for academic purposes",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.2,
            font=dict(family='Verdana', size=12, color='#2A3F5F'),
            xanchor="center",
            yanchor="top",
            bgcolor=None,
            bordercolor=None,
            borderwidth=None,
            borderpad=None
        )
    ]
    )

    return {'data': [call_trace, put_trace], 'layout': layout}

if __name__ == '__main__':
    app.run_server(os.getenv("HOST", "0.0.0.0"), port=os.getenv("PORT", 8080))
