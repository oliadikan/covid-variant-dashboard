import os
import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import requests
import time

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True
)

server = app.server

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("COVID-19 Variant Analysis Dashboard", className="text-center my-4"),
            html.Hr(),
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Analyze New Sequence"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select FASTA File')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', className="mt-2"),
                ])
            ], className="mb-4")
        ], md=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Analysis Results"),
                dbc.CardBody([
                    html.Div(id='analysis-results', children="Upload a sequence to start analysis.")
                ])
            ])
        ], md=8)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Global Variant Trends (Pre-computed)"),
                dbc.CardBody([
                    dcc.Graph(id='variant-timeline-graph'),
                    html.P("Placeholder for variant prevalence timeline.", className="text-muted")
                ])
            ], className="mt-4")
        ])
    ]),
    
    # Interval for polling
    dcc.Interval(id='poll-interval', interval=2000, n_intervals=0, disabled=True),
    dcc.Store(id='task-id-store')
], fluid=True)

@callback(
    Output('upload-status', 'children'),
    Output('task-id-store', 'data'),
    Output('poll-interval', 'disabled'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def handle_upload(contents, filename):
    if contents is None:
        return dash.no_update, dash.no_update, True
    
    # In a real app, we'd send the contents to the backend
    # For this skeleton, we'll simulate the upload to the backend /upload endpoint
    # Since Dash upload gives base64, we'd need to decode it.
    
    try:
        # This is a simplified mock of the upload process
        # In reality, we'd use requests.post(f"{BACKEND_URL}/upload", files=...)
        # For now, we'll just show a message
        return dbc.Alert(f"File {filename} received. Starting analysis...", color="info"), "mock-task-id", False
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger"), None, True

@callback(
    Output('analysis-results', 'children'),
    Output('poll-interval', 'disabled', allow_duplicate=True),
    Input('poll-interval', 'n_intervals'),
    State('task-id-store', 'data'),
    prevent_initial_call=True
)
def poll_results(n, task_id):
    if not task_id:
        return dash.no_update, True
    
    # Mock polling logic
    # In reality: response = requests.get(f"{BACKEND_URL}/results/{task_id}")
    
    if n > 5: # Simulate completion after 5 polls
        return html.Div([
            html.H4("Analysis Complete", className="text-success"),
            html.P("Variant: Omicron (BA.1)"),
            html.P("Confidence: 98%"),
            dbc.Badge("Concerning Mutation: E484A", color="warning", className="me-1"),
            dbc.Badge("Concerning Mutation: N501Y", color="warning"),
        ]), True
    
    return html.Div([
        html.P(f"Analyzing... (Poll {n})"),
        dbc.Progress(value=n*20, animated=True, striped=True)
    ]), False

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
