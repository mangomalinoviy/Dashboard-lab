import dash
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import plotly.express as px
import pandas as pd
import base64
import io
from datetime import datetime, timedelta

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Дашборд процесса разработки ПО"),
    
    # Компонент для загрузки файлов
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Перетащите или ', html.A('выберите CSV файл')]),
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
    
    # Компонент для хранения данных в памяти
    dcc.Store(id='storage', data=None),
    
    # Выпадающий список для выбора периода
    html.H2("Выберите период для анализа"),
    dcc.Dropdown(
        id='period-selector',
        options=[
            {'label': 'Последние 7 дней', 'value': 7},
            {'label': 'Последние 30 дней', 'value': 30},
            {'label': 'Последние 90 дней', 'value': 90},
            {'label': 'Все данные', 'value': 0}
        ],
        value=30  # значение по умолчанию - последние 30 дней
    ),
    
    # 1 
    html.H2("График временного ряда"),
    dcc.Graph(id='time-series-chart'),
    
    # 2 
    html.H2("Круговая диаграмма"),
    dcc.Graph(id='pie-chart'),
    
    # 3 
    html.H2("Гистограмма распределения усилий"),
    dcc.Graph(id='histogram-scatter'),
    
    # 4 
    html.H2("Таблица с данными"),
    html.Div(id='data-table')
])

# Callback для обработки загруженного файла
@app.callback(
    Output('storage', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_storage(contents, filename):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            # Пробуем прочитать CSV файл
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            return df.to_dict('records')
        except Exception as e:
            print(e)
            return None
    return None

# Функция для фильтрации данных по периоду
def filter_data_by_period(data, days):
    if days == 0:  # Все данные
        return data
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Вычисляем дату, от которой будем фильтровать
    cutoff_date = df['date'].max() - timedelta(days=days)
    
    # Фильтруем данные
    filtered_df = df[df['date'] >= cutoff_date]
    return filtered_df.to_dict('records')

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
        # Возвращаем пустые графики если данных нет
        empty_fig = px.line(title="Загрузите данные для отображения")
        empty_pie = px.pie(title="Загрузите данные для отображения")
        empty_hist = px.bar(title="Загрузите данные для отображения")
        return empty_fig, empty_pie, empty_hist, "Загрузите данные для отображения"
    
    # Фильтруем данные по выбранному периоду
    filtered_data = filter_data_by_period(data, period_days)
    df = pd.DataFrame(filtered_data)
    
    # Преобразование данных
    df['date'] = pd.to_datetime(df['date'])
    
    # Группировка по дням для временного ряда
    df_daily = df.groupby('date')[['new_tasks', 'completed_tasks']].sum().reset_index()
    
    # 1. График временного ряда - динамика задач
    time_series_fig = px.line(
        df_daily, 
        x='date', 
        y=['new_tasks', 'completed_tasks'],
        title=f'Динамика новых и завершенных задач (период: {period_days} дней)',
        labels={'value': 'Количество задач', 'date': 'Дата', 'variable': 'Тип задач'}
    )
    time_series_fig.update_layout(legend_title_text='Тип задач')
    
    # 2. Круговая диаграмма - распределение по статусам
    status_counts = df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']
    pie_fig = px.pie(
        status_counts, 
        values='count', 
        names='status',
        title=f'Распределение задач по статусам (период: {period_days} дней)'
    )
    
    # 3. Гистограмма - распределение усилий по разработчикам
    developer_effort = df.groupby('developer')['effort_hours'].sum().reset_index()
    histogram_fig = px.bar(
        developer_effort,
        x='developer',
        y='effort_hours',
        title=f'Распределение усилий по команде (период: {period_days} дней)',
        labels={'developer': 'Разработчик', 'effort_hours': 'Затраченные часы'}
    )
    
    # 4. Таблица с ключевыми показателями
    # Создаем сводную таблицу с ключевыми метриками
    summary_df = pd.DataFrame({
        'Метрика': [
            'Всего новых задач',
            'Всего завершенных задач',
            'Общие затраченные часы',
            'Средние часы на задачу',
            'Эффективность (завершено/новые)'
        ],
        'Значение': [
            df['new_tasks'].sum(),
            df['completed_tasks'].sum(),
            df['effort_hours'].sum(),
            round(df['effort_hours'].sum() / max(df['new_tasks'].sum(), 1), 2),
            f"{round(df['completed_tasks'].sum() / max(df['new_tasks'].sum(), 1) * 100, 1)}%"
        ]
    })
    
    table = dash_table.DataTable(
        data=summary_df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in summary_df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'minWidth': '150px', 'width': '150px', 'maxWidth': '200px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        }
    )
    
    return time_series_fig, pie_fig, histogram_fig, table

if __name__ == '__main__':
    app.run(debug=True)


