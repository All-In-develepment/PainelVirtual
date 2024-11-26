from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required
import requests
from collections import defaultdict
from datetime import datetime
import re

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
 
    #response = requests.get(f'https://bet365botwebapi20231115194435.azurewebsites.net/api/PlayPixFutebolVirtual?Liga={liga}&Horas=Horas{periodo}&filtros=', headers=header)
    response = requests.get(f'https://bet365botwebapi20231115194435.azurewebsites.net/api/futebolvirtual?liga={liga}&futuro=true&Horas=Horas{periodo}&tipoOdd=&dadosAlteracao=&filtros=&confrontos=false&hrsConfrontos=240', headers=header)
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
            status = jogo.get('Resultado')

            if isinstance(status, str) and '+' in status:
                status = status.replace('+', '')
                
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

            # Padronizar o formato do Horário para garantir consistência
            formatted_horario = f"{int(hora_str):02}:{int(minuto_str):02}"

            # Armazenar as informações do jogo
            game_info = {
                'Horario': formatted_horario,  # Usar o formato padronizado
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

            teams = f'{time_a}x{time_b}'

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
                games_by_team_future[teams].append(game_info)  # Adiciona como mandante

    # Ordenar os jogos futuros por horário
    for team, games in games_by_team_future.items():
        games_by_team_future[team] = sorted(games, key=lambda game: datetime.strptime(game['Horario'], '%H:%M'))

    return games_by_team, games_by_team_future, all_games_by_team

def organize_games_details_by_teams(games_data, teamA, teamB):
    """
    Organiza os jogos entre teamA e teamB, separando entre jogos onde teamA é mandante 
    e todos os jogos entre os dois times, independentemente do mandante.
    """

    # Dicionários para armazenar os jogos
    games_teamA_home = defaultdict(list)  # Jogos com teamA como mandante contra teamB
    all_head_to_head_games = defaultdict(list)  # Todos os jogos entre teamA e teamB

    # Percorre todos os jogos fornecidos
    for game in games_data:
        # Extrai informações relevantes do jogo
        time_a = game.get('TimeA')
        time_b = game.get('TimeB')
        hora_str = game.get('Hora')
        minuto_str = game.get('Minuto')
        placar_str = game.get('Resultado')
        
        # Verifica se o placar está presente e no formato esperado
        if placar_str and '-' in placar_str:
            try:
                placar_home, placar_visitor = map(int, placar_str.split('-'))
            except ValueError:
                # Se o placar for inválido, ignore o jogo
                continue
        else:
            # Se o placar não estiver presente ou for inválido, ignore o jogo
            continue

        # Determina o status para ambos os times
        status_home = determine_status(placar_home, placar_visitor, time_a, time_b, time_a)
        status_visitor = determine_status(placar_home, placar_visitor, time_a, time_b, time_b)

        # Padronizar o formato do Horário para garantir consistência
        formatted_horario = f"{int(hora_str):02}:{int(minuto_str):02}"

        # Cria um dicionário com as informações do jogo
        game_info = {
            'Horario': formatted_horario,
            'TeamA': time_a,
            'TeamB': time_b,
            'Placar': placar_str,
            'status': status_home,  # Status do mandante
            'Hora': hora_str,
            'Minuto': minuto_str
        }

        # Cria uma cópia para o time visitante com seu status
        game_info_visitor = game_info.copy()
        game_info_visitor['status'] = status_visitor  # Status do visitante

        # Adiciona o jogo ao dicionário correto
        if time_a == teamA and time_b == teamB:
            games_teamA_home[teamA].append(game_info)  # Jogos onde teamA é mandante
        if (time_a == teamA and time_b == teamB) or (time_a == teamB and time_b == teamA):
            all_head_to_head_games[teamA].append(game_info)  # Todos os confrontos entre os dois times

    return games_teamA_home, all_head_to_head_games

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
        print(json_result)
        for linha in json_result['Linhas']:
            for coluna in linha['Colunas']:
                if 'Resultado' in coluna:
                    resultado = coluna['Resultado']
                    try:
                        # Obter gols de acordo com o formato do resultado
                        gols_time1, gols_time2 = map(lambda x: int(x.replace('+', '').strip()), resultado.split('-'))
                        soma_gols = gols_time1 + gols_time2

                        coluna['SomaGols'] = soma_gols
                        coluna['AmbasMarcam'] = (gols_time1 > 0 and gols_time2 > 0)
                        coluna['AmbasMarcamNao'] = (gols_time1 == 0 or gols_time2 == 0)
                        coluna['ParOuImpar'] = 'Par' if soma_gols % 2 == 0 else 'Ímpar'

                        # Adicionar lógicas para diferentes mercados
                        coluna['SomaGolsUnder0_5'] = soma_gols
                        coluna['SomaGolsUnder1_5'] = soma_gols
                        coluna['SomaGolsUnder2_5'] = soma_gols
                        coluna['SomaGolsUnder3_5'] = soma_gols
                        coluna['SomaGols1_5'] = soma_gols
                        coluna['SomaGols0_5'] = soma_gols

                    except ValueError as e:
                        print(f"Erro ao processar o resultado: {resultado} - Erro: {e}")

        else:
            json_result = []
            print(resposta.status_code)

    return render_template('index.html', games=json_result, enumerate=enumerate, mercado=mercado)

@kirongames.route('/next-games')
def next_games():
    periodo = request.args.get('periodo', 72)
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
    periodo = request.args.get('periodo', 72)
    liga = request.args.get('campeonato', '1')
    
    try:
        response = get_api_data(liga, periodo)
        response_details = requests.get(f'http://62.171.162.25:5000/api/jogos365/{team_a}/{team_b}/500')        
        # response_details = get_api_data(liga, 240)        

        if response.status_code == 200:
            games_data = response.json()
            details_data = response_details.json()
            
            games_teamA_home, all_head_to_head_games = organize_games_details_by_teams(details_data, team_a, team_b)
            
            # Organize games into the respective dictionaries
            games_by_team, _, all_games_by_team = organize_games_by_team(games_data)
            
            limit_last_games(games_by_team)
            limit_last_games(all_games_by_team)

            # Retrieve the specific team data
            team_a_data = games_by_team.get(team_a, [])
            team_b_data = games_by_team.get(team_b, [])
            
            # Retrieve the specific team data
            teams_details_data = games_teamA_home.get(team_a, [])
            head_to_head_data = all_head_to_head_games.get(team_a, [])
            
            # Retrieve the general data for both teams
            team_a_all_data = all_games_by_team.get(team_a, [])
            team_b_all_data = all_games_by_team.get(team_b, [])

            return jsonify({
                'teamA': team_a_data,
                'teamB': team_b_data,
                'teamA_all': team_a_all_data,
                'teamB_all': team_b_all_data,
                'teams_details_data': teams_details_data,
                'head_to_head_data': head_to_head_data,
            })
    except requests.exceptions.RequestException as e:
        flash(f'Ocorreu um erro ao se conectar à API: {str(e)}', 'danger')
        return render_template('next_games.html', games_by_team={})
    
    
@kirongames.route('/get-games', methods=['GET'])
def get_games():
    periodo = request.args.get('periodo', 72)
    liga = request.args.get('campeonato', '1')
    
    try:
        response = get_api_data(liga, periodo)

        if response.status_code == 200:
            games_data = response.json()

            if not games_data.get('Linhas'):
                return jsonify({'message': 'Nenhum jogo encontrado.'}), 200

            _, games_by_team_future, _ = organize_games_by_team(games_data)
            return jsonify(games_by_team_future), 200

        else:
            return jsonify({'message': f'Erro ao buscar os dados: {response.status_code}'}), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'Ocorreu um erro ao se conectar à API: {str(e)}'}), 500