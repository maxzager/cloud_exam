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
    if item:
        return pd.DataFrame(item["Options"])
    return pd.DataFrame()

unique_dates = get_unique_dates(table)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1('Volatility Smile Dashboard', style={'font-family': 'Verdana', 'color': '#2A3F5F', 'margin-top': '30px', 'textAlign': 'center'}),
        html.Div([
            dcc.Graph(id='volatility-smile-graph', style={'width': '80%', 'height': '80%', 'display': 'inline-block'}),
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
                ),
                html.Label('Comparison Mode', style={'font-family': 'Verdana', 'color': '#2A3F5F'}),
                dcc.RadioItems(
                    id='comparison-mode',
                    options=[{'label': 'None', 'value': 'none'},
                            {'label': 'Compare Data Collection Dates', 'value': 'collection'},
                            {'label': 'Compare Expiration Dates', 'value': 'expiration'}],
                    value='none',
                    style={'font-family': 'Verdana'}
                ),
                html.Label('Select Comparison Date', style={'font-family': 'Verdana', 'color': '#2A3F5F'}),
                
                dcc.Dropdown(
                    id='comparison-date-dropdown',
                    options=[{'label': date, 'value': date} for date in unique_dates],
                    value=None,
                    style={'font-family': 'Verdana'},
                    #disabled=True
                ),


            ], style={'width': '18%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding-left': '20px'})
        ], style={'padding': '20px'})
    ], style={'background-color': '#F3F6FA', 'border-radius': '5px', 'padding': '20px', 'margin': '20px'})
])


@app.callback(
    Output('volatility-smile-graph', 'figure'),
    [Input('exp-date-dropdown', 'value'),
     Input('data-collection-date-dropdown', 'value'),
     Input('comparison-mode', 'value'),
     Input('comparison-date-dropdown', 'value')])
def update_graph(selected_exp_date, selected_date, comparison_mode, comparison_date):

    # Función para obtener traces a partir de una fecha y fecha de vencimiento seleccionadas
    def get_traces(selected_date, selected_exp_date, trace_color, comparison_label):
        options_new = get_item(table, selected_date)
        filtered_options = options_new[options_new['EXP_DATE'] == selected_exp_date]

        call_options = filtered_options[filtered_options['CALL_PUT'] == 'CALL']
        put_options = filtered_options[filtered_options['CALL_PUT'] == 'PUT']

        call_trace = go.Scatter(
            x=call_options['STRIKE'],
            y=call_options['IV'],
            mode='markers+lines',
            name=f'Call Options (Collection: {comparison_label}, Expiration: {selected_exp_date})',
            marker=dict(color=trace_color[0], size=10, line=dict(width=2, color='black'))
        )

        put_trace = go.Scatter(
            x=put_options['STRIKE'],
            y=put_options['IV'],
            mode='markers+lines',
            name=f'Put Options (Collection: {comparison_label}, Expiration: {selected_exp_date})',
            marker=dict(color=trace_color[1], size=10, line=dict(width=2, color='black'))
        )

        return [call_trace, put_trace]


    traces = []
    traces += get_traces(selected_date, selected_exp_date, ('rgba(0, 180, 0, .8)', 'rgba(180, 0, 180, .8)'), selected_date)

    if comparison_mode != 'none' and comparison_date is not None:
        if comparison_mode == 'collection':
            # Si se compara la fecha de recopilación, use la misma fecha de vencimiento
            traces += get_traces(comparison_date, selected_exp_date, ('rgba(0, 80, 0, .8)', 'rgba(80, 0, 80, .8)'), comparison_date)
        elif comparison_mode == 'expiration':
            # Si se compara la fecha de vencimiento, use la fecha de vencimiento de comparación
            traces += get_traces(selected_date, comparison_date, ('rgba(0, 80, 0, .8)', 'rgba(80, 0, 80, .8)'), comparison_date)
    
    layout = go.Layout(
        title='Volatility Smile',
        xaxis=dict(title='Strike', titlefont=dict(family='Verdana', color='#2A3F5F'), tickfont=dict(family='Verdana', color='#2A3F5F')),
        yaxis=dict(title='Implied Volatility', titlefont=dict(family='Verdana', color='#2A3F5F'), tickfont=dict(family='Verdana', color='#2A3F5F')),
        hovermode='closest',
        legend=dict(font=dict(family='Verdana', color='#2A3F5F'), x=0.5, y=-0.4, xanchor='center', yanchor='top', orientation='v'),
        plot_bgcolor='#F3F6FA',
        titlefont=dict(size=18),
        margin=dict(t=60, b=120, l=50, r=50)  
    )


    return {'data': traces, 'layout': layout}
@app.callback(
    [Output('exp-date-dropdown', 'options'),
     Output('exp-date-dropdown', 'value')],
    [Input('data-collection-date-dropdown', 'value')])
def update_exp_date_dropdown(selected_date):
    options_df = get_item(table, selected_date)
    unique_exp_dates = options_df['EXP_DATE'].unique()
    options = [{'label': exp_date, 'value': exp_date} for exp_date in unique_exp_dates]
    default_value = unique_exp_dates[0] if len(unique_exp_dates) > 0 else None
    return options, default_value

@app.callback(
    [Output('comparison-date-dropdown', 'options'),
     Output('comparison-date-dropdown', 'value')],
    [Input('comparison-mode', 'value'),
     Input('data-collection-date-dropdown', 'value'),
     Input('exp-date-dropdown', 'value')])
def update_comparison_date_dropdown(comparison_mode, selected_date, selected_exp_date):
    if comparison_mode == 'collection':
        options = [{'label': date, 'value': date} for date in unique_dates if date != selected_date]
        default_value = options[0]['value'] if len(options) > 0 else None
    elif comparison_mode == 'expiration':
        options_df = get_item(table, selected_date)
        unique_exp_dates = options_df['EXP_DATE'].unique()
        options = [{'label': exp_date, 'value': exp_date} for exp_date in unique_exp_dates if exp_date != selected_exp_date]
        default_value = options[0]['value'] if len(options) > 0 else None
    else:
        options = []
        default_value = None

    return options, default_value
if __name__ == '__main__':
    app.run_server(os.getenv("HOST", "0.0.0.0"), port=os.getenv("PORT", 8080))
