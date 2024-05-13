import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import sklearn
import warnings
from catboost import CatBoostRegressor
from parse_by_link import get_preprocessed_df
import joblib

warnings.filterwarnings("ignore")

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/47.0.2526.106 Safari/537.36 "}

transfermarkt = "https://www.transfermarkt.com"

relevant_features = [
    'age',
    'height',
    'player_agent',
    'joined',
    'outfitter',
    'appearances',
    'goals',
    'assists',
    'substitutions_on',
    'substitutions_off',
    'yellow_cards',
    'red_cards',
    'penalty_goals',
    'minutes_played',
    'individual',
    'international',
    'national',
    'other',
    'national_status',
    'national_matches',
    'national_goals',
    'national_assists',
    'national_yellow_cards',
    'national_red_cards',
    'avg_injuries_per_season',
    'avg_injury_duration',
    'is_injured',
    'last_injury_date',
    'club_price',
    'club_statistics_matches',
    'club_statistics_goals',
    'club_statistics_pts',
    'club_league_top_rank',
    'club_league_lowest_rank',
    'club_league_mean_rank',
    'foot_left',
    'foot_right',
    'trophies_total_score',
    'trophies_average_score',
    'trophies_max_score',
    'trophies_min_score',
    'trophies_amount',
    'club_trophies_total_score',
    'club_trophies_average_score',
    'club_trophies_max_score',
    'club_trophies_min_score',
    'club_trophies_amount',
    'followers',
    'Defender_Group',
    'Midfielder_Group',
    'Striker_Group',
    'Winger_Group',
]

r_columns = ['age', 'height', 'citizenship', 'player_agent', 'current_club', 'joined', 'outfitter', 'appearances',
             'goals', 'assists', 'substitutions_on', 'substitutions_off', 'yellow_cards', 'red_cards', 'penalty_goals',
             'minutes_played', 'individual', 'international', 'national', 'other', 'national_team', 'national_status',
             'national_matches', 'national_goals', 'national_assists', 'national_yellow_cards', 'national_red_cards',
             'avg_injuries_per_season', 'avg_injury_duration', 'is_injured', 'last_injury_date', 'club_league',
             'club_price', 'club_statistics_matches', 'club_statistics_goals', 'club_statistics_pts',
             'club_league_top_rank', 'club_league_lowest_rank', 'club_league_mean_rank', 'foot_left', 'foot_right',
             'trophies_total_score', 'trophies_average_score', 'trophies_max_score', 'trophies_min_score',
             'trophies_amount', 'club_trophies_total_score', 'club_trophies_average_score', 'club_trophies_max_score',
             'club_trophies_min_score', 'club_trophies_amount', 'followers', 'position_group', 'position_role']


def find_player(name):
    fio = name.split()
    query = ''
    for q in fio:
        if query != '':
            query += '+'
        query += q
    url = 'https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query=' + query
    html_text = requests.get(url, headers=headers)
    site = BeautifulSoup(html_text.content, "lxml")
    table = site.find_all("table", class_="items")
    players = []
    if table:
        table = table[0].find_all("table", class_="inline-table")
    else:
        return players
    for row in table:
        player = [row.find("img", class_="bilderrahmen-fixed").get("src"),
                  row.find("img", class_="bilderrahmen-fixed").get("title"),
                  transfermarkt + row.find("td", class_="hauptlink").find("a").get("href")]
        try:
            new_url = player[2]
            new_html = requests.get(new_url, headers=headers)
            new_site = BeautifulSoup(new_html.content, "lxml")
            player[0] = new_site.find("img", class_="data-header__profile-image").get("src")
        except:
            players.append(player)

        players.append(player)
    return players


def tg_predict_r(link, data):
    df1 = pd.read_excel('final_dataset_r.xlsx')
    df1 = df1[df1['link'] == link]
    columns_to_add = ['position_group', 'position_role', 'followers']
    df1_selected = df1[columns_to_add]
    df = pd.merge(data.reset_index(), df1_selected.reset_index(), left_index=True, right_index=True).reset_index()
    df = df.drop(['link', 'current_price', 'index', 'index_x', 'index_y'], axis=1)
    df = df[r_columns]

    model = CatBoostRegressor()
    model.load_model("best_model.cbm")
    prediction = np.round(model.predict(df))
    return prediction


def tg_predict_m(link, data):
    df1 = pd.read_excel('final_dataset_m.xlsx')
    df1 = df1[df1['link'] == link]
    columns_to_add = ['Defender_Group', 'Midfielder_Group', 'Striker_Group', 'Winger_Group', 'followers']
    df1_selected = df1[columns_to_add]
    df = pd.merge(data.reset_index(), df1_selected.reset_index(), left_index=True, right_index=True).reset_index()

    rf_model = joblib.load("rf_model.joblib")
    prediction = rf_model.predict(df[relevant_features])
    return prediction


def request(request_type, argc, argv, lock):
    result = 0
    if request_type == 'GET':
        if argc == 1:
            lock.acquire()
            result = find_player(argv)
            lock.release()
        elif argc == 2 and argv[0] == 'predict':
            lock.acquire()
            data = get_preprocessed_df(argv[1])
            result = [tg_predict_m(argv[1], data), tg_predict_r(argv[1], data), data['current_price']]
            lock.release()
        else:
            print("No such GET request")
    elif request_type == 'PUT':
        print("No such PUT request")
    elif request_type == 'DELETE':
        print("No such DELETE request")
    else:
        print("No such request's type")
    return result


# print(get_preprocessed_df('https://www.transfermarkt.com/kylian-kaiboue/profil/spieler/612143'))