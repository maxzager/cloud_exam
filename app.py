import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import os
import boto3
from aws_handler import get_unique_dates, get_item
import numpy as np
from scipy.interpolate import griddata

aws_access_key_id = os.environ.get("aws_access_key_id")
aws_secret_access_key = os.environ.get("aws_secret_access_key")

dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name="eu-central-1"
)
table = dynamodb.Table('MeffScrapping')
unique_dates = get_unique_dates(table)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1('Implied Volatility Dashboard', style={'font-family': 'Verdana', 'color': '#2A3F5F', 'margin-top': '30px', 'textAlign': 'center'}),
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
                ),
            ], style={'width': '18%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding-left': '20px'})
        ], style={'padding': '20px'}),
        html.Div([
            dcc.Graph(id='call-volatility-surface-graph', style={'width': '80%', 'height': '80%', 'display': 'inline-block'})
        ], style={'padding': '20px'}),
        html.Div([
            dcc.Graph(id='put-volatility-surface-graph', style={'width': '80%', 'height': '80%', 'display': 'inline-block'})
        ], style={'padding': '20px'})
    ], style={'background-color': '#F3F6FA', 'border-radius': '5px', 'padding': '20px', 'margin': '20px'})
])

def interpolate_iv(options_new, moneyness, ttm):
    """
    Performs interpolation of implied volatility (IV) to create the volatility surface.

    Args:
        options_new (DataFrame): DataFrame with options pricing and volatility.
        moneyness (np.array): Array of moneyness values for the options.
        ttm (np.array): Array of time-to-maturity values for the options.

    Returns:
        xi, yi, zi (np.arrays): Meshgrid arrays for moneyness, time-to-maturity, and interpolated IV.
    """
    x = options_new['MONEYNES']
    y = options_new['TTM']
    z = options_new['IV']
    xi, yi = np.meshgrid(moneyness, ttm)
    zi = griddata((x, y), z, (xi, yi), method='linear')
    return xi, yi, zi


@app.callback(
    Output('volatility-smile-graph', 'figure'),
    [Input('exp-date-dropdown', 'value'),
     Input('data-collection-date-dropdown', 'value'),
     Input('comparison-mode', 'value'),
     Input('comparison-date-dropdown', 'value')])
def update_graph(selected_exp_date, selected_date, comparison_mode, comparison_date):
    """
    Callback for updating the volatility smile graph.

    Args:
        selected_exp_date (str): The selected expiration date.
        selected_date (str): The selected data collection date.
        comparison_mode (str): The selected comparison mode.
        comparison_date (str): The selected comparison date.

    Returns:
        dict: A dictionary containing the updated data and layout for the graph.
    """

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
            traces += get_traces(comparison_date, selected_exp_date, ('rgba(0, 80, 0, .8)', 'rgba(80, 0, 80, .8)'), comparison_date)
        elif comparison_mode == 'expiration':
            traces += get_traces(selected_date, comparison_date, ('rgba(0, 80, 0, .8)', 'rgba(80, 0, 80, .8)'), comparison_date)

    layout = go.Layout(
        title='Volatility Skew calculated for Meff Options',
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
    Output('volatility-surface-graph', 'figure'),
    [Input('data-collection-date-dropdown', 'value')])
@app.callback(
    Output('call-volatility-surface-graph', 'figure'),
    [Input('data-collection-date-dropdown', 'value')])
def update_call_vol_surface(selected_date):
    """
    Callback for updating the call volatility surface graph.

    Args:
        selected_date (str): The selected data collection date.

    Returns:
        dict: A dictionary containing the updated data and layout for the graph.
    """
    options_new = get_item(table, selected_date)
    filtered_options = options_new[options_new['CALL_PUT'] == 'CALL']

    moneyness = filtered_options['MONEYNES'].unique()
    ttm = filtered_options['TTM'].unique()
    moneyness.sort()
    ttm.sort()

    strikes, ttm, iv_matrix = interpolate_iv(filtered_options, moneyness, ttm)

    surface_trace = go.Surface(x=moneyness, y=ttm, z=iv_matrix, colorscale='Viridis')

    layout = go.Layout(
        title='Call Volatility Surface calculated for Meff Options',
        scene=dict(
            xaxis_title='Moneyness',
            yaxis_title='Time to Maturity (TTM)',
            zaxis_title='Implied Volatility',
            aspectmode='cube'
        ),
        plot_bgcolor='#F3F6FA',
        titlefont=dict(size=18),
        margin=dict(t=60, b=120, l=50, r=50)
    )

    return {'data': [surface_trace], 'layout': layout}

@app.callback(
    Output('put-volatility-surface-graph', 'figure'),
    [Input('data-collection-date-dropdown', 'value')])
def update_put_vol_surface(selected_date):
    """
    Callback for updating the put volatility surface graph.

    Args:
        selected_date (str): The selected data collection date.

    Returns:
        dict: A dictionary containing the updated data and layout for the graph.
    """
    options_new = get_item(table, selected_date)
    filtered_options = options_new[options_new['CALL_PUT'] == 'PUT']

    moneyness = filtered_options['MONEYNES'].unique()
    ttm = filtered_options['TTM'].unique()
    moneyness.sort()
    ttm.sort()

    strikes, ttm, iv_matrix = interpolate_iv(filtered_options, moneyness, ttm)

    surface_trace = go.Surface(x=moneyness, y=ttm, z=iv_matrix, colorscale='Viridis')

    layout = go.Layout(
        title='Put Volatility Surface calculated for Meff Options',
        scene=dict(
            xaxis_title='Moneyness',
            yaxis_title='Time to Maturity (TTM)',
            zaxis_title='Implied Volatility',
            aspectmode='cube'
        ),
        plot_bgcolor='#F3F6FA',
        titlefont=dict(size=18),
        margin=dict(t=60, b=120, l=50, r=50)
    )

    return {'data': [surface_trace], 'layout': layout}


@app.callback(
    [Output('exp-date-dropdown', 'options'),
     Output('exp-date-dropdown', 'value')],
    [Input('data-collection-date-dropdown', 'value')])
def update_exp_date_dropdown(selected_date):
    """
    Callback for updating the expiration date dropdown options.

    Args:
        selected_date (str): The selected data collection date.

    Returns:
        tuple: A tuple containing the options and value for the expiration date dropdown.
    """
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
    """
    Callback for updating the comparison date dropdown options.

    Args:
        comparison_mode (str): The selected comparison mode.
        selected_date (str): The selected data collection date.
        selected_exp_date (str): The selected expiration date.

    Returns:
        tuple: A tuple containing the options and value for the comparison date dropdown.
    """
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
