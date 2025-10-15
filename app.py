import dash
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

app = dash.Dash(__name__)

#df = pd.read_csv('data.csv')

app.layout = html.Div([
    html.H1("Дашборд процесса разработки ПО"),
    
    # 1 
    html.H2("График временного ряда"),
    dcc.Graph(id='time-series-chart'),
    
    # 2 
    html.H2("Круговая диаграмма"),
    dcc.Graph(id='pie-chart'),
    
    # 3 
    html.H2("Гистограмма или график рассеяния"),
    dcc.Graph(id='histogram-scatter'),
    
    # 4 
    html.H2("Таблица с данными"),
    html.Div(id='data-table'),
    
    # 5 
    html.H2("Выпадающий список для выбора периода"),
    dcc.Dropdown(
        id='period-selector',
        options=[{'label': 'Месяц', 'value': 'M'}, 
                {'label': 'Квартал', 'value': 'Q'}, 
                {'label': 'Год', 'value': 'Y'}],
        value='M' # значение по умолчанию
    )])


#python app.py
if __name__ == '__main__':
    app.run(debug=True)



