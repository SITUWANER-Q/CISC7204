print('Testing layout construction...')
try:
    import pandas as pd
    import dash
    from dash import html, dcc

    # Load data
    simulated_df = pd.read_excel('simulated_samples.xlsx')
    print(f'Data loaded: {simulated_df.shape}')

    # Mock colors
    academic_colors = {
        'primary': '#08519c',
        'secondary': '#74c476',
        'accent': '#ff6600',
        'text_primary': '#2C3E50',
        'text_secondary': '#7F8C8D',
        'background': '#f8f9fa',
        'section_bg': '#ffffff'
    }

    # Create a simple layout with just the problematic component
    test_layout = html.Div([
        html.H1('Test App'),
        # Add chapter 6
        html.Div([
            html.H2('Chapter 6: Simulated Data Interactive Analysis',
                   style={'fontFamily': 'Times New Roman', 'fontWeight': '600',
                          'color': academic_colors['primary'], 'fontSize': '1.8em', 'marginBottom': '15px',
                          'borderBottom': f"3px solid {academic_colors['primary']}40", 'paddingBottom': '10px'}),
            dcc.Dropdown(
                id='simulated-boxplot-variable',
                options=[{'label': 'Test', 'value': 'test'}],
                value='test'
            )
        ])
    ])

    test_app = dash.Dash(__name__, suppress_callback_exceptions=True)
    test_app.layout = test_layout

    print('Test app created')

    # Check layout
    layout_str = str(test_app.layout)
    if 'simulated-boxplot-variable' in layout_str:
        print('SUCCESS: Component found in test layout')
    else:
        print('Component NOT found in test layout')

    print('Layout length:', len(layout_str))

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

