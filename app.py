"""
US Programs Heat Map with Device Type Filters — Render Deployment Version
========================================================================
"""

import os
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go

# ---------------------------------------------------
# 1.  Set up Supabase connection
# ---------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not (SUPABASE_URL and SUPABASE_KEY):
    raise ValueError("Supabase credentials not found in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------
# 2.  Data loading with error handling
# ---------------------------------------------------
def load_data():
    """Load data from Supabase with error handling"""
    try:
        # Get device categories
        device_response = supabase.table("device_categories").select("*").execute()
        device_categories = pd.DataFrame(device_response.data)
        device_dict = dict(zip(device_categories['id'], device_categories['name']))

        # Get programs data
        programs_response = supabase.table("programs").select("*").execute()
        programs_data = programs_response.data

        if not programs_data:
            raise ValueError("No rows returned from Supabase programs table.")

        df_programs = pd.DataFrame(programs_data)
        return df_programs, device_dict
    except Exception as e:
        print(f"Error loading data: {e}")
        # Return empty data for graceful degradation
        return pd.DataFrame(), {}

df_programs, device_dict = load_data()

# ---------------------------------------------------
# 3.  Process and prepare data
# ---------------------------------------------------
# Define US regions
state_to_region = {
    # Southwest
    'AZ': 'Southwest', 'NM': 'Southwest', 'TX': 'Southwest', 'OK': 'Southwest',
    # West
    'CA': 'West', 'OR': 'West', 'WA': 'West', 'NV': 'West', 'ID': 'West',
    'MT': 'West', 'WY': 'West', 'CO': 'West', 'UT': 'West',
    # Southeast
    'FL': 'Southeast', 'GA': 'Southeast', 'SC': 'Southeast', 'NC': 'Southeast',
    'VA': 'Southeast', 'AL': 'Southeast', 'MS': 'Southeast', 'TN': 'Southeast',
    'KY': 'Southeast', 'AR': 'Southeast', 'LA': 'Southeast',
    # Midwest
    'IL': 'Midwest', 'IN': 'Midwest', 'MI': 'Midwest', 'OH': 'Midwest',
    'WI': 'Midwest', 'MN': 'Midwest', 'IA': 'Midwest', 'MO': 'Midwest',
    'ND': 'Midwest', 'SD': 'Midwest', 'NE': 'Midwest', 'KS': 'Midwest',
    # Mid-Atlantic
    'NY': 'Mid-Atlantic', 'NJ': 'Mid-Atlantic', 'PA': 'Mid-Atlantic',
    'DE': 'Mid-Atlantic', 'MD': 'Mid-Atlantic', 'WV': 'Mid-Atlantic',
    # Northeast
    'ME': 'Northeast', 'NH': 'Northeast', 'VT': 'Northeast', 'MA': 'Northeast',
    'RI': 'Northeast', 'CT': 'Northeast'
}

# Region center coordinates for labels
region_centers = {
    'Southwest': {'lat': 34, 'lon': -106},
    'West': {'lat': 42, 'lon': -117},
    'Southeast': {'lat': 32, 'lon': -83},
    'Midwest': {'lat': 42, 'lon': -92},
    'Mid-Atlantic': {'lat': 40, 'lon': -76},
    'Northeast': {'lat': 43, 'lon': -71}
}

# Process data if available
device_options = []
df_us_programs = pd.DataFrame()

if not df_programs.empty and device_dict:
    # Filter for US states only and add device names and regions
    df_us_programs = df_programs[df_programs['state_province'].str.len() == 2].copy()
    df_us_programs['device_name'] = df_us_programs['device_category_id'].map(device_dict)
    df_us_programs['region'] = df_us_programs['state_province'].map(state_to_region)
    
    # Get unique device types for filter options
    device_options = [{'label': device_name, 'value': device_name} 
                     for device_name in sorted(df_us_programs['device_name'].dropna().unique())]

# ---------------------------------------------------
# 4.  Create Dash App
# ---------------------------------------------------
# Initialize the Dash app
app = dash.Dash(__name__)

# This is important for Render deployment
server = app.server

app.layout = html.Div([
    html.H1("US Energy Incentive Programs Heat Map", 
            style={'textAlign': 'center', 'marginBottom': 30}),
    
    # Show error message if no data
    html.Div(id='error-message', style={'textAlign': 'center', 'color': 'red', 'marginBottom': 20}),
    
    html.Div([
        html.Div([
            html.Label("Filter by Device Type:", style={'fontWeight': 'bold', 'marginBottom': 10}),
            dcc.Dropdown(
                id='device-filter',
                options=device_options,
                value=[option['value'] for option in device_options],
                multi=True,
                placeholder="Select device types...",
                style={'marginBottom': 20}
            ),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        
        html.Div([
            html.Label("Filter by Region:", style={'fontWeight': 'bold', 'marginBottom': 10}),
            dcc.Dropdown(
                id='region-filter',
                options=[{'label': region, 'value': region} 
                        for region in sorted(set(state_to_region.values())) if region],
                value=list(set(state_to_region.values())),
                multi=True,
                placeholder="Select regions...",
                style={'marginBottom': 20}
            ),
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'}),
    ]) if device_options else html.Div(),
    
    html.Div([
        html.Button("Select All Devices", id="select-all-devices", n_clicks=0, 
                   style={'marginRight': 10, 'marginBottom': 10}),
        html.Button("Clear All Devices", id="clear-all-devices", n_clicks=0,
                   style={'marginRight': 10, 'marginBottom': 10}),
        html.Button("Select All Regions", id="select-all-regions", n_clicks=0,
                   style={'marginRight': 10, 'marginBottom': 10}),
        html.Button("Clear All Regions", id="clear-all-regions", n_clicks=0,
                   style={'marginBottom': 10}),
    ], style={'textAlign': 'center'}) if device_options else html.Div(),
    
    dcc.Graph(id='programs-map', style={'height': '700px'}),
    
    html.Div(id='summary-stats', style={'marginTop': 20, 'padding': 20, 'backgroundColor': '#f9f9f9'})
])

# ---------------------------------------------------
# 5.  Callback functions with error handling
# ---------------------------------------------------
@callback(
    Output('error-message', 'children'),
    Input('programs-map', 'id')  # Dummy input to trigger on load
)
def show_error_message(_):
    if df_programs.empty or not device_dict:
        return html.Div([
            html.H3("⚠️ Unable to load data"),
            html.P("Please check your Supabase connection and try again later."),
            html.P("Make sure SUPABASE_URL and SUPABASE_KEY environment variables are set correctly.")
        ])
    return ""

@callback(
    Output('device-filter', 'value'),
    [Input('select-all-devices', 'n_clicks'),
     Input('clear-all-devices', 'n_clicks')],
    prevent_initial_call=True
)
def update_device_selection(select_all, clear_all):
    if not device_options:
        return []
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'select-all-devices':
        return [option['value'] for option in device_options]
    elif button_id == 'clear-all-devices':
        return []
    
    return dash.no_update

@callback(
    Output('region-filter', 'value'),
    [Input('select-all-regions', 'n_clicks'),
     Input('clear-all-regions', 'n_clicks')],
    prevent_initial_call=True
)
def update_region_selection(select_all, clear_all):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'select-all-regions':
        return list(set(state_to_region.values()))
    elif button_id == 'clear-all-regions':
        return []
    
    return dash.no_update

@callback(
    [Output('programs-map', 'figure'),
     Output('summary-stats', 'children')],
    [Input('device-filter', 'value'),
     Input('region-filter', 'value')]
)
def update_map(selected_devices, selected_regions):
    # Handle case where no data is available
    if df_us_programs.empty:
        fig = go.Figure()
        fig.add_trace(go.Choropleth(
            locations=[],
            z=[],
            locationmode="USA-states",
            colorscale="Greens"
        ))
        fig.update_geos(scope="usa")
        fig.update_layout(title="No data available")
        return fig, [html.P("No data available")]
    
    # Filter data based on selections
    filtered_df = df_us_programs.copy()
    
    if selected_devices:
        filtered_df = filtered_df[filtered_df['device_name'].isin(selected_devices)]
    else:
        filtered_df = filtered_df.iloc[0:0]
    
    if selected_regions:
        filtered_df = filtered_df[filtered_df['region'].isin(selected_regions)]
    else:
        filtered_df = filtered_df.iloc[0:0]
    
    # Calculate statistics for filtered data
    if len(filtered_df) > 0:
        state_totals = filtered_df.groupby('state_province').size().reset_index(name='programs')
        state_totals.columns = ['state', 'programs']
        state_totals['region'] = state_totals['state'].map(state_to_region)
        
        region_totals = filtered_df.groupby('region').size().reset_index(name='total_programs')
        region_device_counts = filtered_df.groupby(['region', 'device_name']).size().reset_index(name='count')
        
        hover_texts = []
        for _, state_row in state_totals.iterrows():
            state = state_row['state']
            region = state_row['region']
            
            if region and region in selected_regions:
                region_total = region_totals[region_totals['region'] == region]['total_programs'].values
                region_total = region_total[0] if len(region_total) > 0 else 0
                
                region_devices = region_device_counts[region_device_counts['region'] == region]
                
                hover_text = f"<b>{region} Region</b><br>"
                hover_text += f"Total Programs: {region_total}<br><br>"
                hover_text += "<b>By Device Type:</b><br>"
                
                for _, device_row in region_devices.iterrows():
                    hover_text += f"{device_row['device_name']}: {device_row['count']}<br>"
                
                hover_texts.append(hover_text)
            else:
                hover_texts.append(f"<b>{state}</b><br>No data for selected filters")
        
        state_totals['hover_text'] = hover_texts
        
        fig = px.choropleth(
            state_totals,
            locations="state",
            locationmode="USA-states",
            color="programs",
            color_continuous_scale="Greens",
            scope="usa",
            labels={"programs": "Number of Programs"},
            title=f"Programs for Selected Device Types ({len(filtered_df)} total programs)",
            hover_data={'hover_text': True, 'programs': False, 'state': False}
        )
        
        fig.update_traces(hovertemplate='%{customdata[0]}<extra></extra>')
        
        for region, coords in region_centers.items():
            if region in selected_regions:
                fig.add_scattergeo(
                    lon=[coords['lon']],
                    lat=[coords['lat']],
                    text=region,
                    mode='text',
                    textfont=dict(size=14, color='black', family='Arial Black'),
                    showlegend=False,
                    hoverinfo='skip'
                )
        
        total_programs = len(filtered_df)
        total_states = len(state_totals)
        total_regions = len(region_totals)
        
        device_breakdown = filtered_df.groupby('device_name').size().sort_values(ascending=False)
        
        summary_children = [
            html.H3("Summary Statistics"),
            html.P(f"Total Programs: {total_programs}"),
            html.P(f"States with Programs: {total_states}"),
            html.P(f"Regions with Programs: {total_regions}"),
            html.H4("Programs by Device Type:"),
            html.Ul([html.Li(f"{device}: {count}") for device, count in device_breakdown.items()])
        ]
        
    else:
        fig = go.Figure()
        fig.add_trace(go.Choropleth(
            locations=[],
            z=[],
            locationmode="USA-states",
            colorscale="Greens"
        ))
        fig.update_geos(scope="usa")
        fig.update_layout(title="No data available for selected filters")
        
        summary_children = [
            html.H3("Summary Statistics"),
            html.P("No programs match the selected filters.")
        ]
    
    fig.update_geos(
        lakecolor="white",
        landcolor="#E5E5E5",
        showcountries=False,
        showlakes=True,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=60, b=0))
    
    return fig, summary_children

# ---------------------------------------------------
# 6.  Run the app
# ---------------------------------------------------
if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Use debug=False for production
    app.run_server(host='0.0.0.0', port=port, debug=False)