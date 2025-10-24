import dash
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import base64
import io
from datetime import datetime, timedelta

# Настройка темы
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Цветовая схема
colors = {
    'background': '#f8f9fa',
    'text': '#2c3e50',
    'primary': '#3498db',
    'secondary': '#2ecc71',
    'accent': '#e74c3c',
    'card_bg': '#ffffff'
}

app.layout = html.Div(style={'backgroundColor': colors['background'], 'padding': '20px'}, children=[
    # Заголовок
    html.Div([
        html.H1("📊 Дашборд процесса разработки ПО", 
                style={'textAlign': 'center', 'color': colors['text'], 'marginBottom': '30px'}),
        html.P("Интерактивная аналитика разработки программного обеспечения", 
               style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '18px'})
    ]),
    
    # Карточка загрузки файлов
    html.Div([
        html.Div([
            html.H3("📁 Загрузка данных", style={'color': colors['text'], 'marginBottom': '15px'}),
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    html.I(className="fas fa-cloud-upload-alt", style={'fontSize': '24px', 'marginBottom': '10px'}),
                    html.Div(['Перетащите или ', html.A('выберите CSV файл')])
                ]),
                style={
                    'width': '100%',
                    'height': '120px',
                    'lineHeight': '120px',
                    'borderWidth': '2px',
                    'borderStyle': 'dashed',
                    'borderRadius': '10px',
                    'textAlign': 'center',
                    'backgroundColor': '#ecf0f1',
                    'borderColor': colors['primary'],
                    'cursor': 'pointer'
                },
                multiple=False
            ),
        ], className="six columns", style={'backgroundColor': colors['card_bg'], 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
        
        # Карточка выбора периода
        html.Div([
            html.H3("📅 Период анализа", style={'color': colors['text'], 'marginBottom': '15px'}),
            dcc.Dropdown(
                id='period-selector',
                options=[
                    {'label': '🕐 Последние 7 дней', 'value': 7},
                    {'label': '📊 Последние 30 дней', 'value': 30},
                    {'label': '📈 Последние 90 дней', 'value': 90},
                    {'label': '📋 Все данные', 'value': 0}
                ],
                value=30,
                style={'borderRadius': '5px'}
            ),
            html.Div(id='period-info', style={'marginTop': '15px', 'color': colors['text']})
        ], className="six columns", style={'backgroundColor': colors['card_bg'], 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
    ], className="row", style={'marginBottom': '30px'}),
    
    # Компонент для хранения данных
    dcc.Store(id='storage', data=None),
    
    # KPI метрики
    html.Div(id='kpi-cards', className="row", style={'marginBottom': '30px'}),
    
    # Первый ряд графиков
    html.Div([
        # График временного ряда
        html.Div([
            html.H3("📈 Динамика задач", style={'color': colors['text'], 'marginBottom': '15px'}),
            dcc.Graph(id='time-series-chart')
        ], className="six columns", style={'backgroundColor': colors['card_bg'], 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
        
        # Круговая диаграмма
        html.Div([
            html.H3("🔄 Распределение по статусам", style={'color': colors['text'], 'marginBottom': '15px'}),
            dcc.Graph(id='pie-chart')
        ], className="six columns", style={'backgroundColor': colors['card_bg'], 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
    ], className="row", style={'marginBottom': '30px'}),
    
    # Второй ряд графиков
    html.Div([
        # Гистограмма распределения усилий
        html.Div([
            html.H3("👥 Распределение усилий по команде", style={'color': colors['text'], 'marginBottom': '15px'}),
            dcc.Graph(id='histogram-scatter')
        ], className="six columns", style={'backgroundColor': colors['card_bg'], 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
    ], className="row", style={'marginBottom': '30px'}),

    # Таблица с данными
    html.Div([
        html.H3("📋 Детальные данные", style={'color': colors['text'], 'marginBottom': '15px'}),
        html.Div(id='data-table')
    ], style={'backgroundColor': colors['card_bg'], 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
])

# Callback для обработки загруженного файла
@app.callback(
    [Output('storage', 'data'),
     Output('period-info', 'children')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_storage(contents, filename):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            date_range = f"Данные загружены: {df['date'].min()} - {df['date'].max()}"
            return df.to_dict('records'), date_range
        except Exception as e:
            print(e)
            return None, "Ошибка при загрузке файла"
    return None, "Загрузите CSV файл для начала работы"

# Функция для фильтрации данных по периоду
def filter_data_by_period(data, days):
    if days == 0:
        return data
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    cutoff_date = df['date'].max() - timedelta(days=days)
    filtered_df = df[df['date'] >= cutoff_date]
    return filtered_df.to_dict('records')

# Callback для KPI карточек
@app.callback(
    Output('kpi-cards', 'children'),
    [Input('storage', 'data'),
     Input('period-selector', 'value')]
)
def update_kpi_cards(data, period_days):
    if not data:
        return html.Div("Загрузите данные для отображения метрик", style={'textAlign': 'center', 'color': colors['text']})
    
    filtered_data = filter_data_by_period(data, period_days)
    df = pd.DataFrame(filtered_data)
    
    total_new_tasks = df['new_tasks'].sum()
    total_completed = df['completed_tasks'].sum()
    total_hours = df['effort_hours'].sum()
    efficiency = (total_completed / total_new_tasks * 100) if total_new_tasks > 0 else 0
    
    kpi_cards = [
        html.Div([
            html.Div([
                html.H3(f"{total_new_tasks}", style={'color': colors['primary'], 'margin': '0'}),
                html.P("Новых задач", style={'color': colors['text'], 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px'})
        ], className="three columns", style={'backgroundColor': colors['card_bg'], 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'margin': '5px'}),
        
        html.Div([
            html.Div([
                html.H3(f"{total_completed}", style={'color': colors['secondary'], 'margin': '0'}),
                html.P("Завершено задач", style={'color': colors['text'], 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px'})
        ], className="three columns", style={'backgroundColor': colors['card_bg'], 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'margin': '5px'}),
        
        html.Div([
            html.Div([
                html.H3(f"{total_hours}", style={'color': colors['accent'], 'margin': '0'}),
                html.P("Затрачено часов", style={'color': colors['text'], 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px'})
        ], className="three columns", style={'backgroundColor': colors['card_bg'], 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'margin': '5px'}),
        
        html.Div([
            html.Div([
                html.H3(f"{efficiency:.1f}%", style={'color': '#f39c12', 'margin': '0'}),
                html.P("Эффективность", style={'color': colors['text'], 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px'})
        ], className="three columns", style={'backgroundColor': colors['card_bg'], 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'margin': '5px'})
    ]
    
    return kpi_cards

# Основной callback для обновления графиков
@app.callback(
    [Output('time-series-chart', 'figure'),
     Output('pie-chart', 'figure'),
     Output('histogram-scatter', 'figure'),
     Output('data-table', 'children')],
    [Input('storage', 'data'),
     Input('period-selector', 'value')]
)
def update_graphs(data, period_days):
    if not data:
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Загрузите данные для отображения", 
                               paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return empty_fig, empty_fig, empty_fig, empty_fig, "Загрузите данные для отображения"
    
    filtered_data = filter_data_by_period(data, period_days)
    df = pd.DataFrame(filtered_data)
    df['date'] = pd.to_datetime(df['date'])
    
    # 1. График временного ряда
    df_daily = df.groupby('date')[['new_tasks', 'completed_tasks']].sum().reset_index()
    time_series_fig = px.line(
        df_daily, 
        x='date', 
        y=['new_tasks', 'completed_tasks'],
        title='',
        labels={'value': 'Количество задач', 'date': 'Дата', 'variable': 'Тип задач'},
        color_discrete_map={'new_tasks': colors['primary'], 'completed_tasks': colors['secondary']}
    )
    time_series_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    
    # 2. Круговая диаграмма статусов
    status_counts = df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']
    pie_fig = px.pie(
        status_counts, 
        values='count', 
        names='status',
        title='',
        color_discrete_sequence=[colors['primary'], colors['secondary'], colors['accent']]
    )
    pie_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
    
    # 3. Гистограмма распределения усилий
    developer_effort = df.groupby('developer').agg({
        'effort_hours': 'sum',
        'completed_tasks': 'sum'
    }).reset_index()
    
    histogram_fig = px.bar(
        developer_effort,
        x='developer',
        y='effort_hours',
        title='',
        labels={'developer': 'Разработчик', 'effort_hours': 'Затраченные часы'},
        color='completed_tasks',
        color_continuous_scale='Viridis'
    )
    histogram_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # 5. Таблица с данными
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'minWidth': '100px', 'width': '100px', 'maxWidth': '180px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'backgroundColor': colors['card_bg'],
            'color': colors['text']
        },
        style_header={
            'backgroundColor': colors['primary'],
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            }
        ]
    )
    
    return time_series_fig, pie_fig, histogram_fig, table

if __name__ == '__main__':
    app.run(debug=True)


