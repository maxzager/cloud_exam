import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from scrap import MeffScraper
import plotly.graph_objs as go
import os

url = 'https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35'
scraper = MeffScraper(url)
scraper.run()
options_new = scraper.options_new

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1('Volatility Smile', style={'font-family': 'Verdana', 'color': '#2A3F5F', 'margin-top': '30px', 'textAlign': 'center'}),
        html.Div([
            dcc.Graph(id='volatility-smile-graph', style={'width': '80%', 'display': 'inline-block'}),
            html.Div([
                html.Label('Select Expiration Date', style={'font-family': 'Verdana', 'color': '#2A3F5F'}),
                dcc.Dropdown(
                    id='exp-date-dropdown',
                    options=[{'label': date, 'value': date} for date in options_new['EXP_DATE'].unique()],
                    value=options_new['EXP_DATE'].unique()[0],
                    style={'font-family': 'Verdana'}
                )
            ], style={'width': '18%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding-left': '20px'})
        ], style={'padding': '20px'})
    ], style={'background-color': '#F3F6FA', 'border-radius': '5px', 'padding': '20px', 'margin': '20px'})
])

@app.callback(
    Output('volatility-smile-graph', 'figure'),
    [Input('exp-date-dropdown', 'value')])
def update_graph(selected_date):
    filtered_options = options_new[options_new['EXP_DATE'] == selected_date]

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
        title='Volatility Smile',
        xaxis=dict(title='Strike', titlefont=dict(family='Verdana', color='#2A3F5F'), tickfont=dict(family='Verdana', color='#2A3F5F')),
        yaxis=dict(title='Implied Volatility', titlefont=dict(family='Verdana', color='#2A3F5F'), tickfont=dict(family='Verdana', color='#2A3F5F')),
        hovermode='closest',
        legend=dict(font=dict(family='Verdana', color='#2A3F5F')),
        plot_bgcolor='#F3F6FA'
    )

    return {'data': [call_trace, put_trace], 'layout': layout}

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", port=os.getenv("PORT", 8080))
