from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required
import requests
from collections import defaultdict
from datetime import datetime

kirongames = Blueprint('kirongames', __name__, template_folder='templates', url_prefix='/kirongames')

@kirongames.before_request
@login_required
def before_request():
    """ Protect all of the kirongames routes. """
    pass

def get_api_data(liga, periodo):
    """Fetch data from the external API."""
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6IlJvbmFsZG8gRXN0cmVsYSIsIklkIjoiMTYxNDMwIiwiQXRpdm8iOiJTIiwiRW1haWwiOiJyb25hbGRvZXN0cmVsYUB5YWhvby5jb20uYnIiLCJOb21lIjoiUm9uYWxkbyBFc3RyZWxhIiwiRGF0YUV4cGlyYWNhbyI6IjIwMjUtMTEtMTkgMTA6NDE6MjQiLCJEYXRhRXhwaXJhY2FvVG9rZW4iOiIyMDI0LTEyLTE5IDEzOjQxOjI2IiwiSVAiOiIxODkuNTkuMTc1LjEyNSIsIkd1aWQiOiI5OTIxMGE0MC0zMGFlLTQ2MjItOTM5MS1mOTNjOTgyZWNhZDIiLCJEYXRhRXhwaXJhY2FvQm90IjoiIiwibmJmIjoxNzMyMDIzNjg2LCJleHAiOjE3MzQ2MTU2ODYsImlhdCI6MTczMjAyMzY4NiwiaXNzIjoic2VsZiIsImF1ZCI6Imh0dHA6Ly9sb2NhbGhvc3Q6NTc3MzEvIn0.NTG7nBniKFYvBo1vJ4OqnpTcp80jZoMrrJeweBv38Ok'
    }
    response = requests.get(f'https://bet365botwebapi20231115194435.azurewebsites.net/api/PlayPixFutebolVirtual?Liga={liga}&Horas=Horas{periodo}&filtros=', headers=header)
    return response

def process_games_data(games_data):
    """Process the games data to calculate scores."""
    for linha in games_data['Linhas']:
        for coluna in linha['Colunas']:
            if 'Resultado' in coluna:
                soma_gols = sum(map(int, coluna['Resultado'].split('-')))
                coluna['SomaGols'] = soma_gols
                
def determine_status(placar_a, placar_b, time_a, time_b, time_verificado):
    """Process status the game based in placar."""
    if time_verificado == time_a:  # Se estamos verificando o status do time mandante
        if placar_a > placar_b:
            return "V"  # Vitória
        elif placar_a < placar_b:
            return "D"  # Derrota
        else:
            return "E"  # Empate
    elif time_verificado == time_b:  # Se estamos verificando o status do time visitante
        if placar_a < placar_b:
            return "V"  # Vitória
        elif placar_a > placar_b:
            return "D"  # Derrota
        else:
            return "E"  # Empate
    return "N/A"  # Caso o time não seja encontrado

def organize_games_by_team(games_data):
    """Organize games by team and split into past and future games."""
    games_by_team = defaultdict(list)  # Jogos passados
    games_by_team_future = defaultdict(list)  # Jogos futuros
    all_games_by_team = defaultdict(list)  # Todos os jogos por time

    # Converte a hora de atualização para um objeto datetime
    update_time = datetime.strptime(games_data['DataAtualizacao'], "%Y-%m-%dT%H:%M:%S.%f")

    for linha in games_data['Linhas']:
        for jogo in linha['Colunas']:
            time_a = jogo.get('TimeA')
            time_b = jogo.get('TimeB')
            hora_str = jogo.get('Hora')
            minuto_str = jogo.get('Minuto')

            # Verificar se os times e o horário estão presentes e válidos
            if time_a and time_b and hora_str and minuto_str:
                try:
                    # Converter a hora e minuto para um objeto datetime
                    game_time = update_time.replace(hour=int(hora_str), minute=int(minuto_str))
                except ValueError:
                    # Caso o horário seja inválido, ignorar o jogo
                    continue
            else:
                # Se não houver hora ou times, ignorar o jogo
                continue

            status = jogo.get('Resultado')

            # Determinar o resultado do jogo (se for válido e já ocorreu)
            if isinstance(status, str) and '-' in status:
                try:
                    placar_a, placar_b = map(int, status.split('-'))

                    # Determinar o status do time baseado em suas posições
                    team_status_a = determine_status(placar_a, placar_b, time_a, time_b, time_a)  # Para o time mandante
                    team_status_b = determine_status(placar_a, placar_b, time_a, time_b, time_b)  # Para o time visitante

                except ValueError:
                    team_status_a = "Erro: Placar inválido"
                    team_status_b = "Erro: Placar inválido"
            else:
                team_status_a = "N/A"  # Jogos sem resultado ainda
                team_status_b = "N/A"

            # Armazenar as informações do jogo
            game_info = {
                'Horario': jogo.get('Horario', '00:00'),
                'Hora': hora_str,
                'Minuto': minuto_str,
                'TeamA': time_a,
                'TeamB': time_b,
                'PrimeiroMarcar': jogo.get('PrimeiroMarcar', ''),
                'UltimoMarcar': jogo.get('UltimoMarcar', ''),
                'Resultado': status if status else 'N/A',
                'Resultado_FT': jogo.get('Resultado_FT', 'N/A'),
                'Resultado_HT': jogo.get('Resultado_HT', 'N/A'),
                'status': team_status_a  # Armazena status para o time mandante
            }

            # Armazenar status do time visitante também
            game_info_visitante = game_info.copy()
            game_info_visitante['status'] = team_status_b  # Armazena status para o time visitante

            if status:
                # Adicionar o jogo ao dicionário de todos os jogos do time
                all_games_by_team[time_a].append(game_info)  # Adiciona como mandante
                all_games_by_team[time_b].append(game_info_visitante)  # Adiciona como visitante

            # Verificar se o jogo já aconteceu
            if status and game_time < update_time:
                # Adicionar o jogo apenas ao time mandante
                games_by_team[time_a].append(game_info)  # Adiciona como mandante
            elif not status and game_time > update_time:
                # Adicionar o jogo futuro apenas ao time mandante
                games_by_team_future[time_a].append(game_info)  # Adiciona como mandante

    return games_by_team, games_by_team_future, all_games_by_team


def limit_last_games(games_by_team):
    """Limit the results to the last 20 games per team."""
    for team, games in games_by_team.items():
        games_by_team[team] = sorted(games, key=lambda x: (x['Hora'], x['Minuto']), reverse=True)[:20]

@kirongames.route('/')
def index():
    mercado = request.args.get('mercado', 'over2_5')  # valor padrão se o parâmetro não for passado
    periodo = ( request.args.get('periodo', 24))  # valor padrão de 12
    liga = request.args.get('campeonato', '1')
    
    resposta =  get_api_data(liga, periodo)
    if resposta.status_code == 200:
        json_result = resposta.json()
        for linha in json_result['Linhas']:
            for coluna in linha['Colunas']:
                if 'Resultado' in coluna:
                    soma_gols = int(coluna['Resultado'].split('-')[0]) + int(coluna['Resultado'].split('-')[1])
                    coluna['SomaGols'] = soma_gols
                    # Calcule a soma dos gols para os outros mercados
                    coluna['SomaGols1_5'] = soma_gols
                    coluna['SomaGols0_5'] = soma_gols


                    coluna['SomaGolsUnder0_5'] = soma_gols
                    coluna['SomaGolsUnder1_5'] = soma_gols
                    coluna['SomaGolsUnder2_5'] = soma_gols
                    coluna['SomaGolsUnder3_5'] = soma_gols

                    # Calculos para Ambas Marcam
                    gols_time1 = int(coluna['Resultado'].split('-')[0])
                    gols_time2 = int(coluna['Resultado'].split('-')[1])
                    
                    coluna['AmbasMarcam'] = (gols_time1 > 0 and gols_time2 > 0)
                    coluna['AmbasMarcamNao'] = (gols_time1 == 0 or gols_time2 == 0)
                    coluna['SomaGols'] = gols_time1 + gols_time2

                    # Adicionando a lógica para Par ou Ímpar
                    if soma_gols % 2 == 0:
                        coluna['ParOuImpar'] = 'Par'
                    else:
                        coluna['ParOuImpar'] = 'Ímpar'
    else:
        json_result = []
        print(resposta.status_code)

    return render_template('index.html', games=json_result, enumerate=enumerate, mercado=mercado)

@kirongames.route('/next-games')
def next_games():
    periodo = request.args.get('periodo', 48)
    liga = request.args.get('campeonato', '1')

    try:
        response = get_api_data(liga, periodo)

        if response.status_code == 200:
            games_data = response.json()

            if not games_data.get('Linhas'):
                flash('Nenhum jogo encontrado.', 'info')
                return render_template('next_games.html', games_by_team={})

            _, games_by_team_future, _ = organize_games_by_team(games_data)

            return render_template('next_games.html', games_by_team_future=games_by_team_future)

        else:
            flash(f'Erro ao buscar os dados: {response.status_code}', 'danger')
            return render_template('next_games.html', games_by_team={})

    except requests.exceptions.RequestException as e:
        flash(f'Ocorreu um erro ao se conectar à API: {str(e)}', 'danger')
        return render_template('next_games.html', games_by_team={})

@kirongames.route('/get_game_details/<team_a>/<team_b>')
def get_game_details(team_a, team_b):
    periodo = request.args.get('periodo', 48)
    liga = request.args.get('campeonato', '1')
    
    try:
        response = get_api_data(liga, periodo)
        print("response\n", response)

        if response.status_code == 200:
            games_data = response.json()

            # Organize games into the respective dictionaries
            games_by_team, _, all_games_by_team = organize_games_by_team(games_data)
            
            limit_last_games(games_by_team)
            limit_last_games(all_games_by_team)
            # Retrieve the specific team data
            team_a_data = games_by_team.get(team_a, [])
            team_b_data = games_by_team.get(team_b, [])
            
            # Retrieve the general data for both teams
            team_a_all_data = all_games_by_team.get(team_a, [])
            team_b_all_data = all_games_by_team.get(team_b, [])

            return jsonify({
                'teamA': team_a_data,
                'teamB': team_b_data,
                'teamA_all': team_a_all_data,
                'teamB_all': team_b_all_data,
            })
    except requests.exceptions.RequestException as e:
        flash(f'Ocorreu um erro ao se conectar à API: {str(e)}', 'danger')
        return render_template('next_games.html', games_by_team={})