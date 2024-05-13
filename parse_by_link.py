# Необходимые библиотеки для запуска.
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
import ast
import re
import warnings

warnings.filterwarnings("ignore")
# Настройка для парсинга страниц www.transfermarkt.com, а также
# объявление далее используемых переменных, такие как позиции
# футбольных игроков.
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36"
}
html_text = requests.get(
    "https://www.transfermarkt.com/spieler-statistik/marktwertAenderungen/marktwertetop/?plus=1",
    headers=headers,
)
site = BeautifulSoup(html_text.content, "lxml")
select_classes = site.find_all("div", class_="inline-select")
tournaments_dict = {}
for select_class in select_classes:
    find_tournaments = select_class.find("select", attrs={"name": "wettbewerb_id"})
    if find_tournaments is not None:
        countries = find_tournaments.find_all("optgroup")
        for country in countries:
            if country.text == "\nAll Competitions\n":
                tournaments_dict["All"] = {"All": 0}
            else:
                country_name = country["label"]
                tournaments_dict[country_name] = {}
                tournaments = country.find_all("option")
                for tournament in tournaments:
                    tournaments_dict[country_name][tournament.text] = tournament[
                        "value"
                    ]
html_text = requests.get(
    "https://www.transfermarkt.com/spieler-statistik/marktwertAenderungen/marktwertetop/?plus=1",
    headers=headers,
)
site = BeautifulSoup(html_text.content, "lxml")
select_classes = site.find_all("div", class_="inline-select")
countries_dict = {}
for select_class in select_classes:
    find_countries = select_class.find("select", attrs={"name": "spieler_land_id"})
    if find_countries is not None:
        countries = find_countries.find_all("option")
        for country in countries:
            countries_dict[country.text] = int(country["value"])

# Перевод позиций с немецкого.
player_position = {
    "Goalkeeper": "Torwart",
    "Defender": "Abwehr",
    "Midfielder": "Mittelfeld",
    "Forward": "Sturm",
    "All": 0,
}
player_amplua = {
    "All": 0,
    "Goalkeeper": 1,
    "Sweeper": 2,
    "Centre-Back": 3,
    "Left-Back": 4,
    "Right-Back": 5,
    "Defensive Midfield": 6,
    "Central Midfield": 7,
    "Right Midfield": 8,
    "Left Midfield": 9,
    "Attacking Midfield": 10,
    "Left Winger": 11,
    "Right Winger": 12,
    "Second Striker": 13,
    "Centre-Forward": 14,
}
# Разбиение кубков и наград по категориям: личные, международные
# национальные, иное.

# Все существующие категории.
allTypes = ["individual", "international", "national", "other"]

# Основные учитываемые личные награды.
individual = [
    "UEFA BEST PLAYER IN EUROPE",
    "FOOTBALLER OF THE YEAR",
    "FIFA BEST PLAYER",
    "TOP GOAL SCORER",
    "PLAYER OF THE YEAR",
    "TM-PLAYER OF THE SEASON",
]

# Основные учитываемые международные награды.
international = [
    "WORLD CUP WINNER",
    "CHAMPIONS LEAGUE WINNER",
    "UEFA SUPERCUP WINNER",
    "EUROPEAN CHAMPION CLUBS' CUP",
    "FIFA CLUB WORLD CUP WINNER",
    "UEFA CUP WINNER",
    "INTERCONTINENTAL CUP WINNER",
    "CUP WINNERS CUP WINNER",
]

# Основные учитываемые национальные награды.
national = [
    "ENGLISH CHAMPION",
    "ENGLISH FA CUP WINNER",
    "SPANISH CHAMPION",
    "SPANISH SUPER CUP WINNER",
    "SPANISH CUP WINNER",
    "GERMAN CUP WINNER",
    "GERMAN CHAMPION",
    "GERMAN SUPER CUP WINNER",
    "FRENCH SUPERCUP WINNER",
    "FRENCH CUP WINNER",
    "FRENCH CHAMPION",
    "FRENCH LEAGUE CUP WINNER",
    "ITALIAN CHAMPION",
    "ITALIAN CUP WINNER",
    "ITALIAN SUPER CUP WINNER",
]
# Premier League (England)
# LaLiga (Spain)
# Bundesliga (Germany)
# Ligue 1 (France)
# Serie A (Italy)
years = [
    "23/24",
    "22/23",
    "21/22",
    "20/21",
    "19/20",
    "18/19",
    "17/18",
    "16/17",
    "15/16",
    "14/15",
    "13/14",
]
# Веса основных трофеев клуба (главных футбольных трофеев в мире).
club_competition_weights = {
    'FIFA Club World Cup winner': 10,
    'UEFA Champions League Winner': 10,
    'UEFA Europa League Winner': 9,
    'UEFA Supercup Winner': 8,
    'Intercontinental Cup Winner': 8,
    'UEFA Cup Winner': 9,
    'Cup Winners Cup Winner': 8,
    'Inter-Cities Fairs Cup winner': 7,
    'European Champion Clubs’ Cup winner': 10,
    'Intertoto-Cup Winner': 6,
    'Conference League winner': 7,
    'English Champion': 9,
    'German Champion': 9,
    'Spanish Champion': 9,
    'Italian Champion': 9,
    'French Champion': 9,
    'FA Cup Winner': 8,
    'German Cup winner': 8,
    'Spanish Cup winner': 8,
    'Italian Cup winner': 8,
    'French Cup winner': 8,
    'English League Cup winner': 7,
    'French league cup winner': 7,
    'League Cup Winner': 7,
    'English Supercup Winner': 7,
    'German Super Cup Winner': 7,
    'Spanish Super Cup winner': 7,
    'Italian Super Cup winner': 7,
    'French Supercup Winner': 7,
    'English 2nd tier champion': 6,
    'German 2. Bundesliga Champion': 6,
    'Spanish 2nd tier champion': 6,
    'Italian Serie B champion': 6,
    'French 2nd tier champion': 6,
    'English 3rd tier champion': 5,
    'German 3. Liga Champion': 5,
    'English 4th tier champion': 4,
    'Football League Trophy Winner': 3,
    'German U19 Champion': 4,
    'French Youth Cup winner': 4,
    'U21 Premier League Sieger': 4,
    'Landespokal Winners (for all)': 3,
    'Italian Lega Pro Champion (A/B/C)': 3,
    'Italian Lega Pro 2 Champion (B/C/D)': 3,
    'Scudetto Serie D': 3,
    'Mitropacup': 3,
    'Winner Copa RFEF': 2,
    'Winner Coupe Charles Drago': 2,
    'Winner of the German Amateur championship': 2,
    'Copa Catalunya Winner': 2,
    'Copa Eva Duarte Winner': 2,
    'Western German Cup Winner': 2,
}


# Функция получения сведений о национальной сборной по ссылке на игрока.
def NationalTeamCareer(url: str):
    """
    :param url: ссылка на профиль игрока на transfermarkt.com
    :return: кортеж из двух элементов, где первый - словарь с основной
    информацией о национальной сборной игрока, такие как:
    статус, уровень команды, дебюь, количество матчей и голов;
    а второй элемент кортежа - ссылка на информацию о сборной на сайте transfermarkt.com
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")

    national_team_career_section = soup.find(
        "div", class_="box", attrs={"data-viewport": "Laenderspielkarriere"}
    )
    national_team_data = []
    if national_team_career_section:
        for row in national_team_career_section.find_all(
                "div", class_="national-career__row"
        ):
            cells = row.find_all("div", class_="grid__cell")
            if cells:
                status_class = cells[0].get("class", [])
                status = (
                    "Playing"
                    if "national-career__cell--green" in status_class
                    else "Not Playing"
                    if "national-career__cell--red" in status_class
                    else "Unknown"
                )

                team_level = cells[1].get_text(strip=True)
                debut = cells[2].get_text(strip=True)
                matches = cells[3].get_text(strip=True)
                goals = cells[4].get_text(strip=True)

                national_team_data.append(
                    {
                        "Status": status,
                        "Team Level": team_level,
                        "Debut": debut,
                        "Matches": matches,
                        "Goals": goals,
                    }
                )

    latest_national_team_data = national_team_data[0] if national_team_data else {}
    national_player_profile_link = soup.find("a", text="Go to national player profile")
    national_player_profile_url = (
        f"https://www.transfermarkt.com{national_player_profile_link['href']}"
        if national_player_profile_link
        else "Not available"
    )

    return latest_national_team_data, national_player_profile_url


# Функция получения ссылки на игроков на сайте по параметрам (возраст, ценовой диапазон и т.п.).
def cook_link(
        min_age: int,
        max_age: int,
        min_cost: str,
        max_cost: str,
        pos: str,
        amp: str,
        trnmt_country: str,
        trnmt: str,
        nation: str,
        club_country: str,
):
    """
    :param min_age: минимальный возраст для искомых игроков.
    :param max_age: максимальный возраст для искомых игроков.
    :param min_cost: минимальная стоимость для искомых игроков.
    :param max_cost: максимальная стоимость для искомых игроков.
    :param pos: позиции искомых игроков.
    :param amp: амплуа искомых игроков.
    :param trnmt_country: страна турнира, на котором должны были играть искомые игроки.
    :param trnmt: название турнира, на котором должны были играть искомые игроки.
    :param nation: национальность искомых игроков.
    :param club_country: страна клуба искомых игроков.
    :return: ссылка на сайт tranfermakt.com с искомыми игроками на странице поиска.
    """
    link_on_list = "https://www.transfermarkt.com/spieler-statistik/marktwertAenderungen/marktwertetop/?plus=1"
    position = player_position[pos]
    amplua = player_amplua[amp]
    participates_in_tournament = tournaments_dict[trnmt_country][trnmt]
    nationality = countries_dict[nation]
    clubs_country = countries_dict[club_country]
    link_on_list += f"&galerie=0"
    link_on_list += f"&position={str(position)}"
    link_on_list += f"&spielerposition_id={str(amplua)}"
    link_on_list += f"&spieler_land_id={str(nationality)}"
    link_on_list += f"&verein_land_id={str(clubs_country)}"
    link_on_list += f"&wettbewerb_id={str(participates_in_tournament)}"
    link_on_list += f"&alter={str(min_age)}+-+{str(max_age)}"
    link_on_list += f"&filtern_nach_alter={str(min_age)}%3B{str(max_age)}"
    link_on_list += f"&minAlter={str(min_age)}"
    link_on_list += f"&maxAlter={str(max_age)}"
    link_on_list += f"&minMarktwert={str(min_cost)}"
    link_on_list += f"&maxMarktwert={str(max_cost)}"
    link_on_list += "&yt0=%D0%9F%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D1%8C"
    return link_on_list


# Пример получения ссылки запроса по параметрам игрока.
link_on_list = cook_link(
    16,
    20,
    "100.000",
    "50.000.000",
    "Forward",
    "All",
    "Germany",
    "Bundesliga",
    "Germany",
    "Germany",
)


# Функция получения ссылки на игроков на сайте по параметрам (возраст, ценовой диапазон и т.п.).
def cook_link(
        min_age: int,
        max_age: int,
        min_cost: str,
        max_cost: str,
        pos: str,
        amp: str,
        trnmt_country: str,
        trnmt: str,
        nation: str,
        club_country: str,
):
    """
    :param min_age: минимальный возраст для искомых игроков.
    :param max_age: максимальный возраст для искомых игроков.
    :param min_cost: минимальная стоимость для искомых игроков.
    :param max_cost: максимальная стоимость для искомых игроков.
    :param pos: позиции искомых игроков.
    :param amp: амплуа искомых игроков.
    :param trnmt_country: страна турнира, на котором должны были играть искомые игроки.
    :param trnmt: название турнира, на котором должны были играть искомые игроки.
    :param nation: национальность искомых игроков.
    :param club_country: страна клуба искомых игроков.
    :return: ссылка на сайт tranfermakt.com с искомыми игроками на странице поиска.
    """
    link_on_list = "https://www.transfermarkt.com/spieler-statistik/marktwertAenderungen/marktwertetop/?plus=1"
    position = player_position[pos]
    amplua = player_amplua[amp]
    participates_in_tournament = tournaments_dict[trnmt_country][trnmt]
    nationality = countries_dict[nation]
    clubs_country = countries_dict[club_country]
    link_on_list += f"&galerie=0"
    link_on_list += f"&position={str(position)}"
    link_on_list += f"&spielerposition_id={str(amplua)}"
    link_on_list += f"&spieler_land_id={str(nationality)}"
    link_on_list += f"&verein_land_id={str(clubs_country)}"
    link_on_list += f"&wettbewerb_id={str(participates_in_tournament)}"
    link_on_list += f"&alter={str(min_age)}+-+{str(max_age)}"
    link_on_list += f"&filtern_nach_alter={str(min_age)}%3B{str(max_age)}"
    link_on_list += f"&minAlter={str(min_age)}"
    link_on_list += f"&maxAlter={str(max_age)}"
    link_on_list += f"&minMarktwert={str(min_cost)}"
    link_on_list += f"&maxMarktwert={str(max_cost)}"
    link_on_list += "&yt0=%D0%9F%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D1%8C"
    return link_on_list


# Пример получения ссылки запроса по параметрам игрока.
link_on_list = cook_link(
    16,
    20,
    "100.000",
    "50.000.000",
    "Forward",
    "All",
    "Germany",
    "Bundesliga",
    "Germany",
    "Germany",
)


# Подсчёт весов трофеев клуба.
def calculate_club_score(trophies_string, competition_weights):
    """
    :param trophies_string: список трофеев клуба в виде строки (т.к. в исходном
    датафрейме список трофеев хранится строкой).
    :param competition_weights:  веса соревнований, объявлены выше.
    :return: кортеж из 4 элементов: сумма весов, средний вес, максимальный и минимальный.
    """
    try:
        trophies_list = ast.literal_eval(trophies_string)
    except (ValueError, SyntaxError):
        trophies_list = []

    scores = []
    for trophy in trophies_list:
        match = re.match(r'(\d+)x\s(.+)', trophy)
        if match:
            count = int(match.group(1))
            trophy_name = match.group(2)
            if trophy_name in competition_weights:
                # Умножаем балл трофея на количество и добавляем результат один раз
                score = competition_weights[trophy_name] * count
                scores.append(score)  # Добавляем результат умножения один раз
        else:
            if trophy in competition_weights:
                scores.append(competition_weights[trophy])

    if not scores:  # Если список пустой
        min_score_from_weights = min(competition_weights.values()) if competition_weights else 0
        # Возвращаем минимальное значение из весов соревнований, если список пуст
        return [0, 0, 0, min_score_from_weights]

    total_score = sum(scores)
    average_score = total_score / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    # Используем минимальное значение из весов, если есть баллы, иначе берем минимальное из весов соревнований
    min_score = min(scores) if scores else min(competition_weights.values())

    return total_score, average_score, max_score, min_score


# Функция получения основных данных об игроке по ссылке.
def ParseLink(url: str):
    """
    :param url: ссылка на профиль игрока на transfermarkt.com
    :return: словарь основных данных об игроке, находящихся на главной
    странице этого игрока, такие как текущая цена, ссылки на соц. сети, имя,
    возраст, рост.
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    info = soup.find("div", class_="box viewport-tracking")
    s = str(BeautifulSoup(response.content, 'html.parser'))
    index = s.find('Market value')
    text = s[index:index + 100]
    pattern = re.compile(r"€\d*\.?\d*[mk]")
    price = re.search(pattern, text).group()
    info_fields = info.findAll(
        "span",
        class_=[
            "info-table__content info-table__content--regular info-table__content--flex",
            "info-table__content info-table__content--regular",
        ],
    )
    fields = [field.text.replace(":", "").strip() for field in info_fields]
    club_link = np.nan
    answers = []
    info_answers = info.findAll(
        "span",
        class_=[
            "info-table__content info-table__content--bold info-table__content--flex",
            "info-table__content info-table__content--bold",
        ],
    )
    answers = [" ".join(answer.text.split()) for answer in info_answers]
    club_link = info_answers[fields.index("Current club")].find('a')
    if club_link != None:
        club_link = "https://www.transfermarkt.com" + club_link['href']
    else:
        club_link = np.nan

    data = dict(zip(fields, answers))

    if info.find("div", class_="socialmedia-icons") != None:
        socials = [
            (social.get("title"), social.get("href"))
            for social in info.find("div", class_="socialmedia-icons").findAll("a")
        ]
        data["Social-Media"] = socials
    else:
        data["Social-Media"] = [np.nan]
    data['link'] = url
    data['current_value'] = price
    data['club_link'] = club_link
    return data


# Получает на вход url и name игрока
# Возвращает датафрейм из одной строки с информацией об игроке
def get_player_info(url: str, name: str):
    """
    :param url: ссылка на профиль игрока на transfermarkt.com
    :param name: имя, которое нужно присвоить игроку в датафрейме для индексации.
    :return: pandas датафрейм, состоящий из строки с основной информацией об игроке.
    """
    data = ParseLink(url)
    if len(data["Social-Media"]) > 1:
        for media in data["Social-Media"]:
            if media[0] == "Instagram":
                data["Social-Media"] = [media[1]]
                break
        else:
            data["Social-Media"] = [media[1]]
    df = pd.DataFrame(data, index=[0])
    df["player"] = name
    return df


def calculate_player_score(trophies_string: str, competition_weights: dict):
    """
    :param trophies_string: список трофеев игрока в виде строки (т.к. в исходном
    датафрейме список трофеев хранится строкой).
    :param competition_weights:  веса соревнований, объявлены выше.
    :return: кортеж из 4 элементов: сумма весов, средний вес, максимальный и минимальный.
    """
    try:
        trophies_list = ast.literal_eval(trophies_string)
    except (ValueError, SyntaxError):
        trophies_list = []

    scores = []  # Список для хранения баллов каждого трофея
    for trophy in trophies_list:
        match = re.match(r'(\d+)x\s(.+)', trophy)
        if match:
            count = int(match.group(1))
            trophy_name = match.group(2)
            score = competition_weights.get(trophy_name, 0) * count
        else:
            score = competition_weights.get(trophy, 0)

        scores.append(score)  # Добавляем балл трофея в список

    total_score = sum(scores)
    average_score = total_score / len(scores) if scores else 0  # Среднее значение
    max_score = max(scores) if scores else 0  # Наивысшее значение
    min_score = min(scores) if scores else 0  # Наименьшее значение

    return total_score, average_score, max_score, min_score


# Функция для получения основных статистик по сезонам у игрока.
def PlayerBasicStatsSeasons(player_profile_base: str, seasons: list):
    """
    :param player_profile_base: ссылка на профиль игрока на transfermarkt.com
    :param seasons: список годов, для которых нужно собрать статистики.
    :return: кортеж из двух элементов, где первый - словарь статистик по всем сезонам,
    второй - словарь, который по ключу (сезон) даёт словарь с собранной информацией по
    сезону, такой как:
    количество сыграных игр, голов, помощей, замен, жёлтых и
    красных карточек, голов с пенальти и сыгранных минут.
    """
    global headers
    indexes = [1, 2, 4, 5, 6, 8, 9]
    keys = [
        "goals",
        "assists",
        "substitutions on",
        "substitutions off",
        "yellow cards",
        "red cards",
        "penalty goals",
        "minutes played",
        "appearances",
    ]

    stats_dict = {}
    stats_dict_each_tournament = {}
    for season in seasons:
        stats_dict[season] = {}
        stats_dict_each_tournament[season] = {}

        for key in keys:
            stats_dict[season][key] = 0

        html_text = requests.get(
            player_profile_base + str(season) + "/plus/1#gesamt", headers=headers
        )
        player_site = BeautifulSoup(html_text.content, "lxml")
        tournaments = player_site.find_all("tr", class_="odd") + player_site.find_all(
            "tr", class_="even"
        )

        for i, tournament in enumerate(tournaments):

            tournament_title = tournament.find(
                "td", class_="hauptlink no-border-links"
            ).text
            tournament_info = tournament.find_all("td", class_="zentriert")
            tournament_timings = tournament.find_all("td", class_="rechts")

            stats_dict_each_tournament[season][tournament_title] = {}

            for j, i in enumerate(indexes):
                char = tournament_info[i].text.replace(".", "")
                if char == "-":
                    stats_dict_each_tournament[season][tournament_title][keys[j]] = 0
                else:
                    stats_dict_each_tournament[season][tournament_title][keys[j]] = int(
                        char
                    )
                    stats_dict[season][keys[j]] += int(char)

            appearances = tournament.find(
                "td", class_="zentriert player-profile-performance-data"
            ).text.replace(".", "")
            if appearances and appearances != "-":
                stats_dict[season]["appearances"] += int(appearances)
                stats_dict_each_tournament[season][tournament_title][
                    "appearances"
                ] = int(appearances)
            minutes_played = tournament_timings[-1].text[:-1].replace(".", "")
            if minutes_played and minutes_played != "-":
                stats_dict[season]["minutes played"] += int(minutes_played)
                stats_dict_each_tournament[season][tournament_title][
                    "minutes played"
                ] = int(minutes_played)

    return (stats_dict, stats_dict_each_tournament)


# Функция для обработки статистик в датафрейм (таблицу).
def PlayerStatsSeasonsDF(link: str, seasons: list):
    """
    :param link: ссылка на сезонные статистики игрока на transfermarkt.com
    :param seasons: список годов, для которых нужно собрать статистики.
    :return: pandas датафрейм с собранными данными, такими как:
    количество сыграных игр, голов, помощей, замен, жёлтых и
    красных карточек, голов с пенальти и сыгранных минут.
    """
    dictionaries = PlayerBasicStatsSeasons(link, seasons)
    for_each_season = dictionaries[0]
    stats = {
        "appearances": [0],
        "goals": [0],
        "assists": [0],
        "substitutions on": [0],
        "substitutions off": [0],
        "yellow cards": [0],
        "red cards": [0],
        "penalty goals": [0],
        "minutes played": [0],
    }

    for key in for_each_season.keys():
        for statistic in for_each_season[key]:
            stats[statistic][0] += for_each_season[key][statistic]

    df = pd.DataFrame(data=stats)
    return df


# Функция изменяющая ссылку нужным образом для поиска статистики по сезонам игрока.
def transform_link(link: str):
    """
    :param link: ссылка на профиль игрока на transfermarkt.com
    :return: ссылка, имеющий нужный вид для для поиска статистики по сезонам игрока.
    """
    return link.replace("profil", "leistungsdaten") + "/saison/"


# Функция, возвращающая список всех трофеев игрока по ссылке на его профиль.
def Trophies(url: str):
    """
    :param url: ссылка на профиль игрока на transfermarkt.com
    :return: список названий трофеев и наград игрока.
    """
    # Получение содержимого страницы.
    url = url.replace("profil", "erfolge")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    info = soup.findAll("h2", class_="content-box-headline")

    # Обработка названий трофеев.
    trophies = [trophie.text.strip() for trophie in info][:-1]
    return trophies


# Функция, возвращающая тип для конкретного трофея по его названию.
def TrophyType(trophie: str):
    """
    :param url: название типа трофея (личный, международный, национальный,
    иное) по его названию.
    :return: название типа трофея.
    """
    trophie = trophie.upper()
    if trophie in individual:
        return "individual"
    elif trophie in international:
        return "international"
    elif trophie in national:
        return "national"
    else:
        return "other"


# Функция возвращающая количество кубков по каждому типу для конкретного игрока по ссылке на его профиль.
def TrophyCount(url: str):
    """
    :param url: ссылка на профиль игрока на transfermarkt.com
    :return: словарь с данными о национальной сборной игрока, такие как:
    название, статус.
    """
    # Список трофеев игрока.
    trophies = Trophies(url)

    # Массив значений того, сколько раз был выигран трофей.
    count = list(map(int, [trophie.split()[0][:-1] for trophie in trophies]))

    # Массив с типом каждого трофея: индивидуальный, международный, национальный, иное.
    types = [TrophyType(" ".join(trophie.split()[1::]).upper()) for trophie in trophies]

    # Массив пар (количество, тип).
    typeCount = list(zip(types, count))

    # Возвращаем словарь {тип: количество}, суммируя по каждой паре.
    df = {
        trophyType: sum(pair[1] for pair in typeCount if pair[0] == trophyType)
        for trophyType in allTypes
    }
    return pd.DataFrame(data=df, index=[0])


# Функция для получения основной информации о национальной сборной по ссылке на профиль игрока.
def NationalTeamCareer(url: str):
    """
    :param url: ссылка на профиль игрока на transfermarkt.com
    :return: словарь с данными о национальной сборной игрока, такие как:
    название, статус.
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")

    national_team_data = []
    national_player_profile_url = "Not available"

    national_team_career_section = soup.find(
        "div", class_="box", attrs={"data-viewport": "Laenderspielkarriere"}
    )
    if national_team_career_section:
        for row in national_team_career_section.find_all(
                "div", class_="national-career__row"
        ):
            cells = row.find_all("div", class_="grid__cell")
            if cells:
                status_class = cells[0].get("class", [])
                status_code = 0 if "national-career__cell--red" in status_class else 2
                team_level = cells[1].get_text(strip=True)
                team_name = re.sub(r" U\d+$", "", team_level)
                if " U" in team_level:
                    status_code = 1

                national_team_data.append(
                    {
                        "National Team": team_name,
                        "National Status": status_code,
                    }
                )

    if national_team_data:
        latest_national_team_data = national_team_data[0]
        national_player_profile_link = soup.find(
            "a", text="Go to national player profile"
        )
        if national_player_profile_link and national_player_profile_link.get("href"):
            national_player_profile_url = (
                f"https://www.transfermarkt.com{national_player_profile_link['href']}"
            )
    else:
        latest_national_team_data = {"National Team": "Unknown", "National Status": 0}

    return latest_national_team_data, national_player_profile_url


# Функция для получения информации о национальной сборной по ссылке на игрока.
def scrape_national_team_stats(url: str):
    """
    :param url: ссылка на профиль игрока на transfermarkt.com
    :return: словарь с данными о национальной сборной игрока, такие как:
    количество матчей, голов, помощей, жёлтых и красных карточек.
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    team_name_section = soup.find("div", class_="dataName")
    team_name = (
        team_name_section.find("span", class_="hide-for-small").text.strip()
        if team_name_section
        else "Unknown"
    )

    stats_table = soup.find("table", class_="items")
    player_stats = {}
    if stats_table:
        footer = stats_table.find("tfoot")
        if footer:
            totals = footer.find("tr")
            cols = totals.find_all("td")
            if len(cols) >= 9:
                player_stats = {
                    "National Matches": cols[2].text.strip(),
                    "National Goals": cols[3].text.strip(),
                    "National Assists": cols[4].text.strip(),
                    "National Yellow Cards": cols[5].text.strip(),
                    "National Red Cards": cols[7].text.strip(),
                }

    return player_stats


# Функция для обработки информации о национальной сборной по ссылке на игрока в виде датафрейма (таблицы).
def get_national_data(url: str):
    """
    :param url: ссылка на профиль игрока на transfermarkt.com
    :return: pandas датафрейм с данными о национальной сборной игрока, такие как:
    количество матчей, голов, помощей, жёлтых и красных карточек.
    """
    national_team_career_data, profile_url = NationalTeamCareer(url)
    national_team_stats = scrape_national_team_stats(profile_url)

    combined_data = {**national_team_career_data, **national_team_stats}
    players_data = [combined_data]
    for player in players_data:
        for key, value in player.items():
            if value == "-":
                player[key] = 0
    return pd.DataFrame(players_data)


# Функция для обработки информации о клубе игрока.
def get_club_info(url: str):
    """
    :param url: ссылка на профиль игрока на transfermarkt.com
    :return: pandas датафрейм с данными о клубе игрока, такие как:
    лига, цена, статистики клуба, трофеи, занятые места в лиге.
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    league = soup.find("span", class_="data-header__club").find("a").text.strip()
    price = soup.find("a", class_="data-header__market-value-wrapper")
    if price:
        price = price.text.split()[0]
    else:
        price = "NaN"

    statistic_url = url.replace("startseite", "tabelle")
    response = requests.get(statistic_url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    statistic = soup.find("tr", class_="table-highlight").findAll(
        "td", class_="zentriert"
    )[2:6]
    statistic = {
        "Matches": statistic[0].text,
        "Goals": statistic[1].text,
        "+/-": statistic[2].text,
        "Pts": statistic[3].text,
    }

    trophies_url = url.replace("startseite", "erfolge")
    response = requests.get(trophies_url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    trophies = []
    for trophy in soup.findAll("h2", class_=""):
        trophies.append(trophy.text)
    table = soup.find("div", class_="large-4 columns").findAll(
        "td", class_="zentriert", style=""
    )
    trophies_last_ten_years = []
    for year in table:
        if year.text in years:
            trophies_last_ten_years.append(
                year.next_sibling.next_sibling.next_sibling.next_sibling.text
            )
        else:
            break

    ranking_url = url.replace("startseite", "platzierungen")
    response = requests.get(ranking_url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    league_rankings = []
    count = 0
    for rank in soup.findAll("td", class_="zentriert"):
        if count >= 11:
            break
        ranking = rank.find("b")
        if ranking:
            if count != 0:
                league_rankings.append(ranking.text)
            count += 1

    return pd.DataFrame(
        {
            "club_league: ": league,
            "club_price: ": price,
            "club_statistics: ": str(statistic),
            "club_trophies: ": str(trophies),
            "trophies_in_recent_years: ": str(trophies_last_ten_years),
            "club_league_rankings: ": str(league_rankings),
        },
        index=[0],
    )


# Основные поля, собираемые в датасет в травмах игрока.
fields = ["season", "injury", "from", "until", "days", "games_missed"]


# Функция для сбора данных о травмах игрока по ссылке на профиль игрока.
def get_injuries(url: str):
    """
    :param url: ссылка на профиль игрока на transfermarkt.com
    :return: pandas датафрейм с данными о травмах игрока, такие как:
    сезон, название травмы, сроки травмы, количество пропущенных игр.
    """
    url = url.replace("profil", "verletzungen")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    info = list(
        filter(lambda x: (x.find("td", class_=['hauptlink']) != None), soup.findAll("tr", class_=["odd", "even"])))
    current = [
        1 - (info_.find("td", class_="zentriert bg_rot_20") is None) for info_ in info
    ]
    info = list(map(lambda x: (x.findAll(string=True)[1::]), info))
    data = [{field: data_ for (field, data_) in zip(fields, info_)} for info_ in info]
    df = pd.DataFrame(data)
    df["is_current"] = current
    try:
        df["days"] = df["days"].str.extract("(\d+)", expand=False).astype(int)
    except:
        df["days"] = np.nan
    # Агрегация метрик
    final_df = pd.DataFrame()
    final_df["avg_injuries_per_season"] = [
        df.groupby("season")["days"].count().values.mean()
    ]
    final_df["avg_injury_duration"] = [df["days"].mean()]
    final_df["is_injured"] = [df["is_current"].max()]
    try:
        final_df["last_injury_date"] = [df.iloc[0]["until"]]
    except:
        final_df["last_injury_date"] = [np.nan]
    return final_df


# Фукнкция для получения истории цен на игрока.
def get_market_value_history(url: str):
    """
    :param url: ссылка на профиль игрока на transfermarkt.com
    :return: список истории цен игрока за всё время
    """

    player_id = url.split('/')[-1]

    response = requests.get(
        f'https://www.transfermarkt.us/ceapi/marketValueDevelopment/graph/{player_id}',
        headers=headers).json()

    market_value_history = []
    for cur_value in response['list']:
        market_value_history.append({'value': cur_value['mw'],
                                     'date': cur_value['datum_mw']})

    return market_value_history


# Функция для получения основных статистик игроков.
competition_weights = {
    'Champions League Winner': 10,
    'FIFA Club World Cup winner': 10,
    'Europa League Winner': 9,
    'UEFA Supercup Winner': 8,
    'Champions League runner-up': 8,
    'Europa League runner-up': 7,
    'UEFA Super Cup runner-up': 6,
    'Conference League winner': 6,
    'Conference League runner up': 5,
    'Champions League Participant': 4,
    'Europa League Participant': 3,
    'English Champion': 9,
    'German Champion': 9,
    'Spanish Champion': 9,
    'Italian Champion': 9,
    'French Champion': 9,
    'FA Cup Winner': 8,
    'German Cup winner': 8,
    'Spanish Cup winner': 8,
    'English Supercup Winner': 7,
    'French Supercup Winner': 7,
    'Italian Super Cup winner': 7,
    'English League Cup winner': 6,
    'French league cup winner': 6,
    'FA Cup Runner up': 5,
    'German Cup runner-up': 5,
    'English League Cup runner-up': 4,
    'French league cup runner-up': 4,
    'German Runner Up': 3,
    'relegated from 1st league': 3,
    'English 2nd tier champion': 7,
    'German 2. Bundesliga Champion': 7,
    'Spanish 2nd tier champion': 7,
    'Italian Serie B champion': 7,
    'French 2nd tier champion': 7,
    'Promoted to 1st league': 6,
    'English 3rd tier champion': 5,
    'Promoted to 2. Liga': 5,
    'German 3. Liga Champion': 5,
    'Promoted to third tier': 4,
    'Promotion to 4th division': 3,
    'relegated from 2nd league': 3,
    'relegated from 3rd league': 3,
    'Relegation from 4th division': 2,
    'German Regionalliga Bavaria Champion': 4,
    'German Regionalliga West Champion': 4,
    'Italians U19s Cup Winner': 4,
    'U21 Premier League Sieger': 4,
    'Landespokal Württemberg Winner': 3,
    'Italian Lega Pro Champion (A/C)': 3,
    'Scudetto Serie D': 3,
    'Italienischer Pokalsieger (Serie C)': 3,
    'Herbstmeister (Autumn Champion)': 2,
    'Copa Catalunya Winner': 1
}


def generate_details_df(links: list, names: list):
    """
    :param links: список ссылок на профили игроков на transfermarkt.com.
    :param names: список присваевамых имён (индексам) записям игроков.
    :return: pandas датафрейм с основными данными об игроках.
    """
    details_df = pd.DataFrame()
    for i in (range(len(links))):
        try:
            temp_df = get_player_info(links[i], names[i])
            temp_df['index'] = i
            details_df = pd.concat([details_df, temp_df])
        except:
            print(f"ERROR. Link: {links[i]} ; i={i}")
            continue
    details_df.index = details_df['index']
    return details_df.drop(columns=['index'])


# Функция для получения подробной личной статистики игроков.
def generate_performance_df(links):
    """
    :param links: список ссылок на профили игроков на transfermarkt.com.
    :return: pandas датафрейм с подробной личной статистики об игроке за последние годы.
    """
    performance_df = pd.DataFrame()
    for i in (range(len(links))):
        try:
            temp_df = PlayerStatsSeasonsDF(transform_link(links[i]), ["2023", "2022"])
            temp_df['index'] = i
            performance_df = pd.concat([performance_df, temp_df])
        except:
            print(f"ERROR. Link: {links[i]} ; i={i}")
            continue
    performance_df.index = performance_df['index']
    return performance_df.drop(columns=['index'])


# Функция для получения списка трофеев и наград игроков.
def generate_trophies_df(links):
    """
    :param links: список ссылок на профили игроков на transfermarkt.com.
    :return: pandas датафрейм, содержащий списки трофеев и наград игроков.
    """
    trophies_df = pd.DataFrame()
    for i in range(len(links)):
        try:
            temp_df = TrophyCount(links[i])
            temp_df['index'] = i
            trophies_df = pd.concat([trophies_df, temp_df])
        except:
            print(f"ERROR. Link: {links[i]} ; i={i}")
            continue
    trophies_df.index = trophies_df['index']
    return trophies_df.drop(columns=['index'])


# Функция для получения данных о национальных сборных игроков.
def generate_national_df(links):
    """
    :param links: список ссылок на профили игроков на transfermarkt.com.
    :return: pandas датафрейм, содержащий информацию о национальных сборных игроков.
    """
    national_df = pd.DataFrame()
    for i in range(len(links)):
        try:
            temp_df = get_national_data(links[i])
            temp_df['index'] = i
            national_df = pd.concat([national_df, temp_df])
        except:
            print(f"ERROR. Link: {links[i]} ; i={i}")
            continue
    try:
        national_df.index = national_df['index']
    except:
        national_df.index = 0

    return national_df.drop(columns=['index'])


# Функция для получения данных о травмах игроков.
def generate_injuries_df(links):
    """
    :param links: список ссылок на профили игроков на transfermarkt.com.
    :return: pandas датафрейм, содержащий информацию о травмах игроков.
    """
    injuries_df = pd.DataFrame()
    for i in range(len(links)):
        try:
            temp_df = get_injuries(links[i])
            temp_df['index'] = i
            injuries_df = pd.concat([injuries_df, temp_df])
        except:
            print(f"ERROR. Link: {links[i]} ; i={i}")
            continue
    try:
        injuries_df.index = injuries_df['index']
    except:
        injuries_df.index = 0

    return injuries_df.drop(columns=['index'])


# Функция для получения данных о клубах игроков.
def generate_clubs_df(clublinks):
    """
    :param clublinks: список ссылок на профили клубов игроков на transfermarkt.com.
    :return: pandas датафрейм, содержащий информацию о клубах игроков.
    """
    clubs_df = pd.DataFrame()
    club_dict = {}
    for i in range(len(clublinks)):
        try:
            if clublinks[i] in club_dict:
                temp_df = club_dict[clublinks[i]]
                temp_df['index'] = i
            else:
                temp_df = get_club_info(clublinks[i])
                temp_df['index'] = i
                club_dict[clublinks[i]] = temp_df

            clubs_df = pd.concat([clubs_df, temp_df])
        except:
            print(f"ERROR. Link: {clublinks[i]} ; i={i}")
            continue
    clubs_df.index = clubs_df['index']
    try:
        clubs_df.index = clubs_df['index']
    except:
        clubs_df.index = 0

    return clubs_df.drop(columns=['index'])


# Функция для получения истории цен игроков.
def generate_price_history_df(links):
    """
    :param links: список ссылок на профили игроков на transfermarkt.com.
    :return: pandas датафрейм, содержащий историю цен игроков.
    """
    price_df = pd.DataFrame()
    for i in range(len(links)):
        try:
            temp_df = pd.DataFrame([';'.join([str(x) for x in get_market_value_history(links[i])])],
                                   columns=["price_history"])
            temp_df['index'] = i
            price_df = pd.concat([price_df, temp_df])
        except:
            print(f"ERROR. Link: {links[i]} ; i={i}")
            continue
    try:
        price_df.index = price_df['index']
    except:
        price_df.index = 0

    return price_df.drop(columns=['index'])


def get_months_since_date(date):
    if type(date) == str and date != '-':
        try:
            delta = relativedelta(datetime.now(), datetime.strptime(date, '%b %d, %Y'))
        except:
            return np.nan
        return (delta.months + delta.years * 12)
    return np.nan


# Конвертирование столбцов с ценами к числовому виду.
def price_to_number(price):
    if type(price) != str:
        return np.nan
    koef = 1
    if price[-1] == 'n':
        koef = 1e9
    elif price[-1] == 'm':
        koef = 1e6
    elif price[-1] == 'k':
        koef = 1e3
    return float(re.sub('[^\d\.]', '', price)) * koef


def get_df_by_link(link: str) -> pd.DataFrame:
    try:
        details_df = generate_details_df([link], [0])
    except:
        details_df = pd.DataFrame()

    try:
        performance_df = generate_performance_df([link])
    except:
        performance_df = pd.DataFrame()

    try:
        trophies_df = generate_trophies_df([link])
    except:
        trophies_df = pd.DataFrame()

    try:
        national_df = generate_national_df([link])
    except:
        national_df = pd.DataFrame()

    try:
        injuries_df = generate_injuries_df([link])
    except:
        injuries_df = pd.DataFrame()

    try:
        clubs_df = generate_clubs_df([details_df['club_link'][0]])
    except:
        clubs_df = pd.DataFrame()

    try:
        price_history_df = generate_price_history_df([link])
    except:
        price_history_df = pd.DataFrame()

    result = details_df
    for df in [performance_df, trophies_df, national_df, injuries_df, clubs_df, price_history_df]:
        try:
            result = result.merge(df, on='index', how='left')
        except:
            continue
    try:
        result['Full name'] = result['Full name'].fillna(result['Name in home country'])
    except:
        try:
            result['Full name'] = result['Name in home country']
        except:
            ...
    try:
        result.drop(columns=['Name in home country'], inplace=True)
    except:
        ...
    try:
        result.drop(columns=['player'], inplace=True)
    except:
        ...
    return result


def get_preprocessed_df(link: str) -> pd.DataFrame:
    df = get_df_by_link(link)
    # Конвертирование возраста и высоты к числовому виду.
    df['Date of birth/Age'] = df['Date of birth/Age'].apply(
        lambda x: int(re.search(r"\(([A-Za-z0-9_]+)\)", x).group(1)) if type(x) == str else np.nan)
    df['Height'] = df['Height'].apply(
        lambda x: float(x.replace(",", ".").replace(' m', "")) if type(x) == str else np.nan)
    try:
        df['last_injury_date'] = df['last_injury_date'].apply(get_months_since_date)
    except:
        df['last_injury_date'] = 0
    try:
        df['Joined'] = df['Joined'].apply(get_months_since_date)
    except:
        df['Joined'] = 0
    try:
        df['Contract expires'] = -df['Contract expires'].apply(get_months_since_date)
    except:
        df['Contract expires'] = 0
    try:
        df['Date of last contract extension'] = df['Date of last contract extension'].apply(get_months_since_date)
    except:
        df['Date of last contract extension'] = 0
    renames = {'club_league:': 'club_league',
               'club_price:': 'club_price',
               'Date of birth/Age': 'age',
               'club_trophies:': 'club_trophies',
               'trophies_in_recent_years:':
                   'trophies_in_recent_years:',
               'Full name': 'full_name',
               'Place of birth': 'place_of_birth',
               'Height': 'height',
               'Citizenship': 'citizenship',
               'Position': 'position',
               'Foot:': 'foot',
               'Player agent': 'player_agent',
               'Current club': 'current_club',
               'Joined': 'joined',
               'Contract expires': 'contract_expires',
               'Date of last contract extension': 'date_of_last_contract_extension',
               'Outfitter': 'outfitter',
               'Foot': 'foot',
               'Social-Media': 'social_media',
               'Contract option': 'contract_option',
               'substitutions on': 'substitutions_on',
               'substitutions off': 'substitutions_off',
               'yellow cards': 'yellow_cards',
               'red cards': 'red_cards',
               'penalty goals': 'penalty_goals',
               'minutes played': 'minutes_played',
               'National Status': 'national_status',
               'National Team': 'national_team',
               'National Matches': 'national_matches',
               'National Goals': 'national_goals',
               'National Assists': 'national_assists',
               'National Yellow Cards': 'national_yellow_cards',
               'National Red Cards': 'national_red_cards',
               'club_league: ': 'club_league',
               'club_price: ': 'club_price',
               'club_statistics: ': 'club_statistics',
               'club_trophies: ': 'club_trophies',
               'trophies_in_recent_years: ': 'trophies_in_recent_years',
               'club_league_rankings: ': 'club_league_rankings',
               'current_value': 'current_price',
               'National Status': 'national_status'
               }
    for col, new_name in renames.items():
        try:
            df.rename(columns={col: new_name}, inplace=True)
        except:
            pass

    df['club_price'] = df['club_price'].apply(price_to_number)
    df['current_price'] = df['current_price'].apply(price_to_number)

    # Разбиение столбца club_statistics, содержащий в себе словарь, на несколько столбцов.
    df['club_statistics'] = df['club_statistics'].apply(lambda x:
                                                        ast.literal_eval(x)
                                                        if type(x) == str else np.nan)

    df['club_statistics_matches'] = df['club_statistics'].apply(lambda x:
                                                                float(x['Matches']
                                                                      if x['Matches'].isdigit() else np.nan)
                                                                if type(x) == dict else np.nan)

    df['club_statistics_goals'] = df['club_statistics'].apply(lambda x:
                                                              float(x['Goals'].split(':')[0]
                                                                    if x['Goals'].split(':')[
                                                                  0].isdigit() else np.nan)
                                                              if type(x) == dict else np.nan)

    df['club_statistics_own_goals'] = df['club_statistics'].apply(lambda x:
                                                                  float(x['Goals'].split(':')[1]
                                                                        if ':' in x and x['Goals'].split(':')[
                                                                      1].isdigit() else np.nan)
                                                                  if type(x) == dict else np.nan)

    df['club_statistics_pts'] = df['club_statistics'].apply(lambda x:
                                                            float(x['Pts'] if x['Pts'].isdigit() else np.nan)
                                                            if type(x) == dict else np.nan)

    # Генерация признаков из столбца club_league_rankings, содержащего массив мест команды в лиге, таких как:
    # наилучшее место в лиге, наихудшее и среднее.
    df['club_league_rankings'] = df['club_league_rankings'].apply(lambda x:
                                                                  list(map(int, ast.literal_eval(x)))
                                                                  if type(x) == str else np.nan)

    df['club_league_top_rank'] = df['club_league_rankings'].apply(lambda x:
                                                                  min(x)
                                                                  if type(x) == list and len(x) > 0 else np.nan)

    df['club_league_lowest_rank'] = df['club_league_rankings'].apply(lambda x:
                                                                     max(x)
                                                                     if type(x) == list and len(x) > 0 else np.nan)

    df['club_league_mean_rank'] = df['club_league_rankings'].apply(lambda x:
                                                                   np.array(x).mean()
                                                                   if type(x) == list and len(x) > 0 else np.nan)

    age_mean = df.age.mean()
    df['age'].fillna(value=age_mean, inplace=True)

    height_mean = df.height.mean()
    df['height'].fillna(value=height_mean, inplace=True)

    df['avg_injuries_per_season'].fillna(value=0, inplace=True)
    df['avg_injury_duration'].fillna(value=0, inplace=True)
    df['is_injured'].fillna(value=0, inplace=True)
    df['last_injury_date'].fillna(value=0, inplace=True)

    df['foot'].fillna(value='right', inplace=True)
    # Применим One Hot Encoder к foot.
    df['foot_left'] = (df['foot'] != 'right').astype(int)
    df['foot_right'] = (df['foot'] != 'left').astype(int)

    try:
        df['outfitter'] = 1 - df['outfitter'].isna()
    except:
        df['outfitter'] = 0
    try:
        df['player_agent'] = 1 - df['player_agent'].isna()
    except:
        df['player_agent'] = 0
    # Считаем значения весов для каждого игрока, применяя функцию calculate_player_score построчно к таблице.
    results = df['trophies_in_recent_years'].apply(lambda x: calculate_player_score(x, competition_weights))
    # Создание новых столбцов.
    df[['trophies_total_score', 'trophies_average_score', 'trophies_max_score', 'trophies_min_score']] = pd.DataFrame(
        results.tolist(), index=df.index)
    # Подсчёт количества трофеев.
    trophies_amount = []
    for t in df['trophies_in_recent_years']:
        try:
            trophies_amount.append(len(ast.literal_eval(t)))
        except:
            trophies_amount.append(0)
    # Создание столбца с количеством трофеев.
    df['trophies_amount'] = trophies_amount
    # Удалим более ненужный столбец со списком трофеев.
    results = df['club_trophies'].apply(lambda x: calculate_club_score(x, club_competition_weights))

    df[['club_trophies_total_score', 'club_trophies_average_score', 'club_trophies_max_score',
        'club_trophies_min_score']] = pd.DataFrame(results.tolist(), index=df.index)
    # Количество трофеев.
    trophies_amount = []
    for t in df['club_trophies']:
        try:
            trophies_amount.append(len(ast.literal_eval(t)))
        except:
            trophies_amount.append(0)
    # Создание столбца с количеством трофеев.
    df['club_trophies_amount'] = trophies_amount

    # Удалим ненужные столбцы.
    # Приведём название столбца к единому стилю нейминга столбцов.
    df.rename(columns={"National Status": "national_status"}, inplace=True)
    # В оставшихся столбцах пропуски заполним нулями.
    fill_zeros = ['club_statistics_pts', 'club_league_top_rank', 'club_league_lowest_rank',
                  'club_league_mean_rank', 'club_statistics_matches', 'club_statistics_goals',
                  'national_team', 'national_matches', 'national_goals', 'national_assists',
                  'national_yellow_cards', 'national_red_cards', 'national_status',
                  'club_price', 'joined', ]
    for col in fill_zeros:
        try:
            df[col].fillna(value=0, inplace=True)
        except:
            pass
    drop_cols = ['Unnamed: 0', 'index', '2nd club', '3nd club', '4nd club', 'club_statistics_own_goals',
                 'date_of_last_contract_extension', 'Last contract extension', 'club_statistics',
                 'сontract_option', 'On loan from', 'Contract there expires', 'contract_expires',
                 'trophies_in_recent_years', 'foot', 'club_league_rankings']
    for col in drop_cols:
        try:
            df.drop(columns=[col], inplace=True)
        except:
            pass

    df.drop(columns=['social_media', 'full_name', 'price_history',
                     'club_trophies', 'position', 'place_of_birth', 'club_link'], inplace=True)
    return df


# link = 'https://www.transfermarkt.com/jude-bellingham/profil/spieler/581678'
# jude = get_preprocessed_df(link)
# jude.to_excel("jude.xlsx")
# jude = pd.read_excel("jude.xlsx")
# print(jude.columns.size)
# print(get_preprocessed_df('https://www.transfermarkt.com/kylian-kaiboue/profil/spieler/612143'))
