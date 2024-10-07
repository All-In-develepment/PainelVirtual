from flask import Blueprint, json, render_template, request
from flask_login import login_required
import requests
import pandas as pd

kirongames = Blueprint('kirongames', __name__, template_folder='templates', 
                        url_prefix='/kirongames')

@kirongames.before_request
@login_required
def before_request():
    """ Protect all of the kirongames routes. """
    pass

# Rota para a página inicial do blueprint kirongames
@kirongames.route('/')
def index():
    mercado = request.args.get('mercado', 'over2_5')  # valor padrão se o parâmetro não for passado
    periodo = request.args.get('periodo', 24)  # valor padrão de 12
    liga = request.args.get('campeonato', '1')
    
    header = {'Content-Type': 'application/json', 'Accept': 'application/json', 'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6IlJvbmFsZG8gRXN0cmVsYSIsIklkIjoiMTYxNDMwIiwiQXRpdm8iOiJTIiwiRW1haWwiOiJyb25hbGRvZXN0cmVsYUB5YWhvby5jb20uYnIiLCJOb21lIjoiUm9uYWxkbyBFc3RyZWxhIiwiRGF0YUV4cGlyYWNhbyI6IjIwMjQtMTEtMDEgMTU6MjM6NTkiLCJEYXRhRXhwaXJhY2FvVG9rZW4iOiIyMDI0LTEwLTMxIDE4OjI0OjAwIiwiSVAiOiIxODkuNTkuMTk1LjMiLCJHdWlkIjoiMzMxZTVkMzUtODcxOC00YTRiLTk0NDgtZGJmMDMwZmUwMzhiIiwiRGF0YUV4cGlyYWNhb0JvdCI6IiIsIm5iZiI6MTcyNzgwNzA0MCwiZXhwIjoxNzMwMzk5MDQwLCJpYXQiOjE3Mjc4MDcwNDAsImlzcyI6InNlbGYiLCJhdWQiOiJodHRwOi8vbG9jYWxob3N0OjU3NzMxLyJ9.2nn0i8OaZO0AEZWJu5kHhnqEZ2fgJ-26T2DT5U17dxE'}
    resposta =  requests.get(f'https://bet365botwebapi20231115194435.azurewebsites.net/api/PlayPixFutebolVirtual?Liga={liga}&Horas=Horas{periodo}&filtros=', headers=header)
    
    if resposta.status_code == 200:
        json_result = resposta.json()
        for linha in json_result['Linhas']:
            for coluna in linha['Colunas']:
                if 'Resultado' in coluna:
                    soma_gols = int(coluna['Resultado'].split('-')[0]) + int(coluna['Resultado'].split('-')[1])
                    coluna['SomaGols'] = soma_gols
    else:
        json_result = 0
        print(resposta.status_code)
    
    return render_template('index.html', games=json_result, enumerate=enumerate, mercado=mercado)