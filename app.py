import dash
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import plotly.express as px
import pandas as pd
import base64
import io

app = dash.Dash(__name__)

# Инициализируем пустой DataFrame
df = pd.read_csv("data.csv")

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
    html.Div(id='data-table'),
    
    # 5 
    html.H2("Выпадающий список для выбора периода"),
    dcc.Dropdown(
        id='period-selector',
        options=[
            {'label': 'День', 'value': 'D'},
            {'label': 'Неделя', 'value': 'W'}, 
            {'label': 'Месяц', 'value': 'M'}, 
            {'label': 'Квартал', 'value': 'Q'}, 
            {'label': 'Год', 'value': 'YE'}
        ],
        value='D' # значение по умолчанию
    )
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

# Основной callback для обновления графиков
@app.callback(
    [Output('time-series-chart', 'figure'),
    Output('pie-chart', 'figure'),
    Output('histogram-scatter', 'figure'),
    Output('data-table', 'children')],
    [Input('storage', 'data'),
    Input('period-selector', 'value')]
)
def update_graphs(data, period):
    if not data:
        # Возвращаем пустые графики если данных нет
        empty_fig = px.line(title="Загрузите данные для отображения")
        empty_pie = px.pie(title="Загрузите данные для отображения")
        empty_hist = px.bar(title="Загрузите данные для отображения")
        return empty_fig, empty_pie, empty_hist, "Загрузите данные для отображения"
    
    df = pd.DataFrame(data)
    
    # Преобразование данных
    df['date'] = pd.to_datetime(df['date'])
    
    # Группировка по периоду для временного ряда
    df_period = df.groupby(pd.Grouper(key='date', freq=period)).sum().reset_index()
    
    # 1. График временного ряда - динамика задач
    time_series_fig = px.line(
        df_period, 
        x='date', 
        y=['new_tasks', 'completed_tasks'],
        title='Динамика новых и завершенных задач',
        labels={'value': 'Количество задач', 'date': 'Дата', 'variable': 'Тип задач'}
    )
    
    # 2. Круговая диаграмма - распределение по статусам
    status_counts = df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']
    pie_fig = px.pie(
        status_counts, 
        values='count', 
        names='status',
        title='Распределение задач по статусам'
    )
    
    # 3. Гистограмма - распределение усилий по разработчикам
    developer_effort = df.groupby('developer')['effort_hours'].sum().reset_index()
    histogram_fig = px.bar(
        developer_effort,
        x='developer',
        y='effort_hours',
        title='Распределение усилий по команде (часы)',
        labels={'developer': 'Разработчик', 'effort_hours': 'Затраченные часы'}
    )
    
    # 4. Таблица с ключевыми показателями
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
        }
    )
    
    return time_series_fig, pie_fig, histogram_fig, table

if __name__ == '__main__':
    app.run(debug=True)


