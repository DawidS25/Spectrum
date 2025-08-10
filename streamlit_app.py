import streamlit as st
import random
import pandas as pd
import os
import io
import base64
import requests
from datetime import datetime

# ------------------------------
# Wczytywanie pytań z CSV
# ------------------------------

df = pd.read_csv('questions.csv', sep=';')

def filter_by_category(cat):
    return df[df['categories'] == cat].to_dict(orient='records')

category_names = [
    "Śmieszne", "Światopoglądowe", "Związkowe", "Pikantne",
    "Luźne", "Przeszłość", "Wolisz", "Dylematy"
]

CATEGORIES = {cat: filter_by_category(cat) for cat in category_names}

CATEGORY_EMOJIS = {
    "Śmieszne": "😂", "Światopoglądowe": "🌍", "Związkowe": "❤️", "Pikantne": "🌶️",
    "Luźne": "😎", "Przeszłość": "📜", "Wolisz": "🤔", "Dylematy": "⚖️"
}

# ------------------------------
# Inicjalizacja sesji
# ------------------------------

def init_session_state(defaults: dict):
    for key, value in defaults.items():
        if key not in st.session_state:
            if isinstance(value, set):
                st.session_state[key] = value.copy()
            elif isinstance(value, list):
                st.session_state[key] = value[:]
            elif isinstance(value, dict):
                st.session_state[key] = value.copy()
            else:
                st.session_state[key] = value

def get_default_session_state(mode):
    common_defaults = {
        "chosen_categories": [],
        "used_ids": set(),
        "current_question": None,
        "scores": {},
        "step": "setup",
        "questions_asked": 0,
        "ask_continue": False,
        "guesser_points": None,
        "results_data": []
    }

    if mode == "2-osobowy":
        return {**common_defaults, "players": ["", ""]}
    elif mode == "3-osobowy":
        return {**common_defaults, "players": ["", "", ""], "extra_point": None}
    elif mode == "Drużynowy":
        return {
            **common_defaults,
            "team_names": ["Niebiescy", "Czerwoni"],
            "players_team_0": ["", ""],  # ⬅️ Dodane tutaj
            "players_team_1": ["", ""],
            "all_players": [],
            "use_players": True,
            "extra_point": None
        }

# ------------------------------
# Losowanie pytania
# ------------------------------

def draw_question():
    if "chosen_categories" not in st.session_state:
        return None
    all_qs = []
    for cat in st.session_state.chosen_categories:
        all_qs.extend(CATEGORIES.get(cat, []))
    available = [q for q in all_qs if q["id"] not in st.session_state.used_ids]
    if not available:
        return None
    question = random.choice(available)
    st.session_state.used_ids.add(question["id"])
    return question

# ------------------------------
# Przyciski
# ------------------------------

def setup_buttons():
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔙 Powrót"):
            st.session_state.clear()
            st.session_state.step = "mode_select"
            st.session_state.mode = "None"
            st.rerun()

    with col2:
        if all(st.session_state.players):
            if st.button("✅ Dalej"):
                st.session_state.step = "categories"
                st.rerun()
def end_buttons():
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Jeszcze nie kończymy!"):
            st.session_state.ask_continue = False
            st.session_state.current_question = draw_question()
            st.session_state.step = "game"
            st.rerun()
    with col2:
        if st.button("🔚 Koniec gry"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.step = "mode_select"
            st.session_state.mode = "None"
            st.rerun()

# ------------------------------
# Branding
# ------------------------------

if "step" in st.session_state and st.session_state.step in ["mode_select", "setup", "categories", "end"]:
    st.title("🎲 Spectrum")
    st.markdown(
        "<div style='margin-top: -20px; font-size: 10px; color: gray;'>made by Szek</div>",
        unsafe_allow_html=True
    )
def branding_szek():
    st.markdown(
        """
        <div style='margin-top: -20px; font-size: 10px; color: gray;'>Spectrum - made by Szek</div>
        """,
        unsafe_allow_html=True
        )

# ------------------------------
# Upload na github
# ------------------------------

def upload_to_github(file_path, repo, path_in_repo, token, commit_message):
    with open(file_path, "rb") as f:
        content = f.read()
    b64_content = base64.b64encode(content).decode("utf-8")

    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "message": commit_message,
        "content": b64_content,
        "branch": "main"
    }

    response = requests.put(url, headers=headers, json=data)
    return response

def get_next_game_number(repo, token, folder="wyniki"):
    url = f"https://api.github.com/repos/{repo}/contents/{folder}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 1

    files = response.json()
    today_str = datetime.today().strftime("%Y-%m-%d")
    max_num = 0
    for file in files:
        name = file["name"]
        if name.startswith("gra") and name.endswith(".xlsx") and today_str in name:
            try:
                num_part = name[3:6]
                num = int(num_part)
                if num > max_num:
                    max_num = num
            except:
                pass
    return max_num + 1

def upload_results_once(data):
    # --- Upload na GitHub tylko raz ---
    if not st.session_state.results_uploaded:
        temp_filename = "wyniki_temp.xlsx"
        with open(temp_filename, "wb") as f:
            f.write(data)

        repo = "DawidS25/SpectrumBySzek"  # zmień na swoje repo
        try:
            token = st.secrets["GITHUB_TOKEN"]
        except Exception:
            token = None

        if token:
            next_num = get_next_game_number(repo, token)
            today_str = datetime.today().strftime("%Y-%m-%d")
            file_name = f"gra{next_num:03d}_{today_str}.xlsx"
            path_in_repo = f"wyniki/{file_name}"
            commit_message = f"🎉 Wyniki gry {file_name}"

            response = upload_to_github(temp_filename, repo, path_in_repo, token, commit_message)
            if response.status_code == 201:
                st.success(f"✅ Wyniki zapisane online.")
                st.session_state.results_uploaded = True
            else:
                st.error(f"❌ Błąd zapisu: {response.status_code} – {response.json()}")
        else:
            st.warning("⚠️ Nie udało się zapisać wyników online.")

# ------------------------------
# Ekran kategorii
# ------------------------------

def category_selection_screen(CATEGORIES, CATEGORY_EMOJIS):
    st.header("📚 Wybierz kategorie pytań")

    if "category_selection" not in st.session_state:
        st.session_state.category_selection = set()

    cols = st.columns(4)
    for i, cat in enumerate(CATEGORIES.keys()):
        col = cols[i % 4]
        display_name = f"{CATEGORY_EMOJIS.get(cat, '')} {cat}"
        if cat in st.session_state.category_selection:
            if col.button(f"✅ {display_name}", key=f"cat_{cat}"):
                st.session_state.category_selection.remove(cat)
                st.rerun()
        else:
            if col.button(display_name, key=f"cat_{cat}"):
                st.session_state.category_selection.add(cat)
                st.rerun()

    selected_display = [f"{CATEGORY_EMOJIS.get(cat, '')} {cat}" for cat in st.session_state.category_selection]
    st.markdown(f"**Wybrane kategorie:** {', '.join(selected_display) or 'Brak'}")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔙 Powrót"):
            if "category_selection" in st.session_state:
                del st.session_state["category_selection"]
            st.session_state.step = "setup"
            st.rerun()

    with col2:
        if st.session_state.category_selection:
            if st.button("🎯 Rozpocznij grę"):
                st.session_state.chosen_categories = list(st.session_state.category_selection)
                st.session_state.step = "game"
                st.rerun()

# ------------------------------
# Kontynuacja gry
# ------------------------------

def handle_continue_decision(questions_per_round):
    st.header("❓ Czy chcesz kontynuować grę?")
    rounds_played = st.session_state.questions_asked // questions_per_round
    total_questions = st.session_state.questions_asked
    st.write(f"🥊 Rozegrane rundy: {rounds_played} → {total_questions} pytań 🧠")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Tak, kontynuuj"):
            st.session_state.ask_continue = False
            st.session_state.current_question = draw_question()
            st.rerun()
    with col2:
        if st.button("❌ Zakończ i pokaż wyniki"):
            st.session_state.step = "end"
            st.rerun()

def prepare_next_question():
    if not st.session_state.current_question:
        st.session_state.current_question = draw_question()
        if not st.session_state.current_question:
            st.success("🎉 Pytania się skończyły! Gratulacje.")
            st.session_state.step = "end"
            st.rerun()

# ------------------------------
# branding i interfejs
# ------------------------------

def round_info(q, current_round, current_question_number):
    st.markdown(f"##### 🥊 Runda {current_round}")
    branding_szek()
    st.markdown(f"#### 🧠 Pytanie {current_question_number} – kategoria: *{q['categories']}*")
    st.write(q["text"])
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"<small>id: {q['id']}</small>", unsafe_allow_html=True)
    with col2:
        if "virtual_board_step" not in st.session_state or st.session_state.virtual_board_step not in ["guess", "score"]:
            if st.button("🔄 Zmień pytanie"):
                new_q = draw_question()
                if new_q:
                    st.session_state.current_question = new_q
                st.rerun()








# ------------------------------
# Wirtualna plansza
# ------------------------------

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Ustawienie stanu strony
if "answer_slider_val" not in st.session_state:
    st.session_state.answer_slider_val = 0
if "guess_slider_val" not in st.session_state:
    st.session_state.guess_slider_val = 0

total_width = 26
half_width = total_width / 2
center_base = 90

colors = {
    "2": "#FFDAB5",
    "3": "#ADD8E6",
    "4": "#3399FF",
    "tlo": "#F5F5DC",
    "promien": "red"
}

segment_sequence = [
    ("2", colors["2"], 5),
    ("3", colors["3"], 5),
    ("4", colors["4"], 6),
    ("3", colors["3"], 5),
    ("2", colors["2"], 5)
]

def draw_answer(ax, center_angle, width, color):
    theta1 = center_angle - width / 2
    theta2 = center_angle + width / 2
    theta1_clip = max(theta1, 0)
    theta2_clip = min(theta2, 180)
    if theta1_clip >= theta2_clip:
        return
    theta = np.linspace(theta1_clip, theta2_clip, 100)
    x = np.cos(np.deg2rad(theta))
    y = np.sin(np.deg2rad(theta))
    x = np.append(x, 0)
    y = np.append(y, 0)
    ax.fill(x, y, color=color, alpha=1)
def draw_guess(guess_angle_deg):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_aspect('equal')
    ax.axis('off')
    # Tło półkola
    theta_bg = np.linspace(0, 180, 300)
    x_bg = np.cos(np.deg2rad(theta_bg))
    y_bg = np.sin(np.deg2rad(theta_bg))
    ax.fill(np.append(x_bg, 0), np.append(y_bg, 0), color=colors["tlo"])
    # Czerwony promień
    rad = np.deg2rad(guess_angle_deg)
    x_end = np.cos(rad)
    y_end = np.sin(rad)
    ax.plot([0, x_end], [0, y_end], color=colors["promien"], linewidth=3)
    return fig
def draw_score(answer_slider, guess_slider):
    answer_deg = 90 + (answer_slider + 100) * (-175) / 200
    guess_deg = 177.5 - (guess_slider + 100) / 200 * (177.5 - 2.5)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_aspect('equal')
    ax.axis('off')

    # Tło półkola
    theta_bg = np.linspace(0, 180, 300)
    x_bg = np.cos(np.deg2rad(theta_bg))
    y_bg = np.sin(np.deg2rad(theta_bg))
    ax.fill(np.append(x_bg, 0), np.append(y_bg, 0), color=colors["tlo"])

    start_angle = center_base - half_width + answer_deg
    current_angle = start_angle
    for label, color, width in segment_sequence:
        center_angle = current_angle + width / 2
        draw_answer(ax, center_angle, width, color)
        current_angle += width

    # Promień
    rad = np.deg2rad(guess_deg)
    x_end = np.cos(rad)
    y_end = np.sin(rad)
    ax.plot([0, x_end], [0, y_end], color=colors["promien"], linewidth=1)

    return fig

def answer_board():
    answer_slider = st.slider("Przesuń tarczę", -100, 100, st.session_state.answer_slider_val, label_visibility="collapsed")
    answer_deg = 90 + (answer_slider + 100) * (-175) / 200 

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_aspect('equal')
    ax.axis('off')
    theta_bg = np.linspace(0, 180, 300)
    x_bg = np.cos(np.deg2rad(theta_bg))
    y_bg = np.sin(np.deg2rad(theta_bg))
    ax.fill(np.append(x_bg, 0), np.append(y_bg, 0), color=colors["tlo"])

    start_angle = center_base - half_width + answer_deg
    current_angle = start_angle
    for label, color, width in segment_sequence:
        center_angle = current_angle + width / 2
        draw_answer(ax, center_angle, width, color)
        current_angle += width

    st.pyplot(fig)
    return answer_slider

def guess_board():
    guess_slider = st.slider("Ustaw promień", -100, 100, st.session_state.guess_slider_val, label_visibility="collapsed")
    guess_deg = 177.5 - (guess_slider + 100) / 200 * (177.5 - 2.5)
    st.pyplot(draw_guess(guess_deg))
    return guess_slider

def direction_board():
    guess_deg = 177.5 - (st.session_state.guess_slider_val + 100) / 200 * (177.5 - 2.5)
    st.pyplot(draw_guess(guess_deg))
    
    if "director_choice" not in st.session_state:
        st.session_state.director_choice = None

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(("✅ " if st.session_state.director_choice == "left" else "") + "⬅ Lewo"):
            st.session_state.director_choice = "left"
            st.rerun()

    with col2:
        if st.button(("✅ " if st.session_state.director_choice == "perfect" else "") + "⏺ Idealnie"):
            st.session_state.director_choice = "perfect"
            st.rerun()

    with col3:
        if st.button(("✅ " if st.session_state.director_choice == "right" else "") + "➡ Prawo"):
            st.session_state.director_choice = "right"
            st.rerun()
    

def score_board(responder, guesser, director = None):
    st.pyplot(draw_score(st.session_state.answer_slider_val, st.session_state.guess_slider_val))
    diff = st.session_state.answer_slider_val - st.session_state.guess_slider_val
    if abs(diff) <= 3:
        guesser_points = 4
    elif abs(diff) <= 9:
        guesser_points = 3
    elif abs(diff) <= 15:
        guesser_points = 2
    else:
        guesser_points = 0
    
    if guesser_points == 0:
        responder_points = 0
    elif guesser_points in [2, 3]:
        responder_points = 1
    elif guesser_points == 4:
        responder_points = 2
    else:
        responder_points = 0
    extra_points = 0
    if st.session_state.mode != "2-osobowy":
        if diff <= -4 and st.session_state.director_choice == "left":
            extra_points = 1
        elif diff >= 4 and st.session_state.director_choice == "right":
            extra_points = 1
        elif abs(diff) <= 3 and st.session_state.director_choice == "perfect":
            extra_points = 1
        if extra_points == 1:
            responder_points += extra_points
        responder_name = responder.split("_")[0]
        st.markdown(f"Punktacja: {guesser}: {guesser_points}; {director}: {extra_points}; {responder_name}: {responder_points}")
    else:
        st.markdown(f"Punktacja: {guesser}: {guesser_points}; {responder}: {responder_points}")
    return guesser_points, responder_points, extra_points

def virtual_scoreboard_2(q_per_r, responder, guesser, director = None):
    if "virtual_board_step" not in st.session_state:
        st.session_state.virtual_board_step = "answer"

    if st.session_state.virtual_board_step == "answer":
        answer_slider = answer_board()
        if st.button("Zatwierdź odpowiedź"):
            st.session_state.answer_slider_val = answer_slider
            st.session_state.virtual_board_step = "guess"
            st.rerun()

    elif st.session_state.virtual_board_step == "guess":
        guess_slider = guess_board()
        if director is None:
            if st.button("Zatwierdź punktację"):
                st.session_state.guess_slider_val = guess_slider
                st.session_state.virtual_board_step = "score"
                st.rerun()
        else:
            if st.button("Zatwierdź punktację"):
                st.session_state.guess_slider_val = guess_slider
                st.session_state.virtual_board_step = "direction"
                st.rerun()
    
    elif st.session_state.virtual_board_step == "direction":
        direction = direction_board()
        if st.session_state.director_choice is not None:
            if st.button("Zatwierdź kierunek"):
                st.session_state.direction = direction
                st.session_state.virtual_board_step = "score"
                st.rerun()
    
    elif st.session_state.virtual_board_step == "score":

        points = score_board(responder, guesser, director)
        if st.button("✅ Następne pytanie!"):
            # Reset planszy
            del st.session_state.virtual_board_step
            if "director_choice" in st.session_state:
                del st.session_state.director_choice
            st.session_state.answer_slider_val = 0
            st.session_state.guess_slider_val = 0

            if st.session_state.mode == "2-osobowy":
                st.session_state.scores[guesser] += points[0]
                st.session_state.scores[responder] += points[1]
            else: 
                st.session_state.scores[guesser] += points[0]
                st.session_state.scores[responder] += points[1] + points[2]
                st.session_state.scores[director] += points[2]

            # Zapis do results_data
            q = st.session_state.current_question
            current_question_number = st.session_state.questions_asked + 1
            current_round = current_question_number // q_per_r

            if st.session_state.mode == "Drużynowy":
                points_this_round = {
                    responder: points[1] + points[2],
                    guesser: points[0],
                    director: points[2],
                }
            elif st.session_state.mode == "3-osobowy":
                points_this_round = {
                    responder: points[1] + points[2],
                    guesser: points[0],
                    director: points[2],
                }
            elif st.session_state.mode == "2-osobowy":
                points_this_round = {
                    responder: points[1],
                    guesser: points[0],
                }

            # Dopisywanie wyników do pamięci
            if "results_data" not in st.session_state:
                st.session_state.results_data = []

            if st.session_state.mode == "Drużynowy":
                data_to_save = {
                "runda": current_round,
                "pytanie_nr": current_question_number,
                "kategoria": q['categories'],
                "pytanie": q['text'],
                "odpowiada": responder,
                "zgaduje_drużyna": guesser,
                "kierunek_drużyna": director,
                "punkty_za_odpowiedź": points_this_round[responder],
                guesser: points_this_round[guesser],
                director: points_this_round[director],
                }
            elif st.session_state.mode == "3-osobowy":
                data_to_save = {
                    "runda": current_round,
                    "nr_pytania": current_question_number,
                    "kategoria": q['categories'],
                    "pytanie": q['text'],
                    "odpowiada": responder,
                    "zgaduje": guesser,
                    "dodatkowo": director,
                    responder: points_this_round[responder],
                    guesser: points_this_round[guesser],
                    director: points_this_round[director],
                }
            elif st.session_state.mode == "2-osobowy":
                data_to_save = {
                    "nr_pytania": current_question_number,
                    "kategoria": q['categories'],
                    "pytanie": q['text'],
                    "odpowiada": responder,
                    "zgaduje": guesser,
                    responder: points_this_round[responder],
                    guesser: points_this_round[guesser],
                }

            st.session_state.results_data.append(data_to_save)

            # Obsługa postępu gry
            st.session_state.questions_asked += 1

            if st.session_state.questions_asked % q_per_r == 0:
                st.session_state.ask_continue = True
                st.session_state.current_question = None
            else:
                st.session_state.current_question = draw_question()

            st.rerun()








# ------------------------------
# Tryby gry
# ------------------------------

# ------------------------------
# Tryb drużynowy
# ------------------------------

def run_druzynowy():
    init_session_state(get_default_session_state("Drużynowy"))
    if st.session_state.step == "setup":
        st.header("🎭 Wprowadź nazwy drużyn i imiona graczy")

        # Nazwy drużyn
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.team_names[0] = st.text_input("👫 Nazwa drużyny 1", value=st.session_state.team_names[0])
        with col2:
            st.session_state.team_names[1] = st.text_input("👫 Nazwa drużyny 2", value=st.session_state.team_names[1])

        # Funkcja renderująca pola imion graczy
        def render_players_inputs(team_index):
            st.write(f"**Imiona graczy drużyny {st.session_state.team_names[team_index]}:**")
            players_key = f"players_team_{team_index}"
            players_list = st.session_state[players_key]

            for i, player_name in enumerate(players_list):
                new_name = st.text_input(
                    f"🙋‍♂️ Imię {i + 1}. osoby z drużyny {st.session_state.team_names[team_index]}",
                    value=player_name,
                    key=f"player_{team_index}_{i}"
                )
                st.session_state[players_key][i] = new_name.strip()

            if len(players_list) < 7:
                if st.button(f"➕ Dodaj kolejnego gracza do drużyny {st.session_state.team_names[team_index]}", key=f"add_player_{team_index}"):
                    st.session_state[players_key].append("")
                    st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            render_players_inputs(0)
        with col2:
            render_players_inputs(1)

        def valid_players_count():
            len0 = len([p for p in st.session_state.players_team_0 if p.strip()])
            len1 = len([p for p in st.session_state.players_team_1 if p.strip()])
            return 2 <= len0 <= 7 and 2 <= len1 <= 7
        def valid_balance():
            len0 = len([p for p in st.session_state.players_team_0 if p.strip()])
            len1 = len([p for p in st.session_state.players_team_1 if p.strip()])
            return -1 <= len0 - len1 <= 1

        if not valid_players_count():
            st.warning("⚠️ Każda drużyna musi mieć od 2 do 7 graczy.")
        if not valid_balance():
            st.warning("⚠️ Drużyny nie są zbalansowane. Maksymalna róznica to 1 gracz.")
        len0 = len([p for p in st.session_state.players_team_0 if p.strip()])
        len1 = len([p for p in st.session_state.players_team_1 if p.strip()])
        if len0 - len1 == 1 or len0 - len1 == -1:
            st.warning("⚠️ Drużyny nie są równe. Na pewno chcesz kontynuować?")


        all_players = []
        for team_index in [0, 1]:
            team_key = st.session_state.team_names[team_index]
            players_list = st.session_state[f"players_team_{team_index}"]
            for p in players_list:
                if p.strip():
                    player = f"{p.strip()}_{team_key}"
                    all_players.append(player)
        st.session_state.all_players = all_players

        for p in all_players:
            st.session_state.scores[p] = 0
        
        for t in st.session_state.team_names:
            st.session_state.scores[t] = 0
        
        st.session_state.team_players = {
            st.session_state.team_names[0]: [p for p in st.session_state.players_team_0 if p.strip()],
            st.session_state.team_names[1]: [p for p in st.session_state.players_team_1 if p.strip()]
            }
        

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔙 Powrót"):
                st.session_state.clear()
                st.session_state.step = "mode_select"
                st.session_state.mode = "None"
                st.rerun()
        with col2:
            if valid_players_count() and valid_balance():
                if st.button("✅ Dalej"):
                    st.session_state.step = "categories"
                    st.rerun()

    elif st.session_state.step == "categories":
        category_selection_screen(CATEGORIES, CATEGORY_EMOJIS)

    elif st.session_state.step == "game":
        team1 = st.session_state.team_names[0]
        team2 = st.session_state.team_names[1]
        team1_players = st.session_state.team_players.get(team1, [])
        team2_players = st.session_state.team_players.get(team2, [])

        max_players = max(len(team1_players), len(team2_players))
        questions_per_round = max_players * 2

        #current_question_number = st.session_state.questions_asked
        #current_round = (current_question_number // questions_per_round) + 1

        if st.session_state.ask_continue:
            handle_continue_decision(questions_per_round)
        else:
            prepare_next_question()
            q = st.session_state.current_question
            current_round = (st.session_state.questions_asked // questions_per_round) + 1
            current_question_number = st.session_state.questions_asked + 1
            round_info(q, current_round, current_question_number)

            if current_question_number % 2 == 0:
                guessing_team = team1
                other_team = team2
                responder_idx = (current_question_number // 2) % len(team1_players)
                responder_temp = team1_players[responder_idx]
                responder = f"{responder_temp}_{guessing_team}"
            else:
                guessing_team = team2
                other_team = team1
                responder_idx = (current_question_number // 2) % len(team2_players)
                responder_temp = team2_players[responder_idx]
                responder = f"{responder_temp}_{guessing_team}"

            responder_name = responder.split("_")[0]
            
            st.markdown(f"Odpowiada: **{responder_name}** &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Zgadują: **{guessing_team}** &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Kierunek: **{other_team}**", unsafe_allow_html=True)

            if st.session_state.virtual_board:
                virtual_scoreboard_2(questions_per_round, responder, guessing_team, other_team)
            else:
                st.markdown(f"**Ile punktów zdobywają {guessing_team}?**")
                if "guesser_points" not in st.session_state:
                    st.session_state.guesser_points = None

                cols = st.columns(4)
                for i, val in enumerate([0, 2, 3, 4]):
                    label = f"✅ {val}" if st.session_state.guesser_points == val else f"{val}"
                    if cols[i].button(label, key=f"gp_{val}_{st.session_state.questions_asked}"):
                        st.session_state.guesser_points = val
                        st.rerun()

                st.markdown(f"**Dodatkowe punkty dla drużyny {other_team}?**")
                extra_points_options = [0, 1]

                if "extra_point" not in st.session_state:
                    st.session_state.extra_point = None

                cols2 = st.columns(len(extra_points_options))
                for i, val in enumerate(extra_points_options):
                    label = f"✅ {val}" if st.session_state.extra_point == val else f"{val}"
                    if cols2[i].button(label, key=f"ep_{val}_{st.session_state.questions_asked}"):
                        st.session_state.extra_point = val
                        st.rerun()

                if st.session_state.guesser_points is not None and st.session_state.extra_point is not None:
                    if st.button("💾 Zapisz i dalej"):
                        guesser_points = st.session_state.guesser_points
                        extra_point = st.session_state.extra_point

                        st.session_state.guesser_points = None
                        st.session_state.extra_point = None

                        st.session_state.scores[guessing_team] += guesser_points
                        st.session_state.scores[other_team] += extra_point

                        responder_points = 0
                        if guesser_points == 0:
                            responder_points = 0
                        elif guesser_points in [2, 3]:
                            responder_points = 1
                        elif guesser_points == 4:
                            responder_points = 2
                        else:
                            responder_points = 0
                        
                        player_id = f"{responder_name}_{guessing_team}"
                        st.session_state.scores[player_id] += responder_points + extra_point

                        data_to_save = {
                            "runda": current_round,
                            "pytanie_nr": current_question_number,
                            "kategoria": q['categories'],
                            "pytanie": q['text'],
                            "odpowiada": responder,
                            "zgaduje_drużyna": guessing_team,
                            "kierunek_drużyna": other_team,
                            "punkty_za_odpowiedź": responder_points + extra_point,
                            guessing_team: guesser_points,
                            other_team: extra_point,
                            }
                        if "results_data" not in st.session_state:
                            st.session_state.results_data = []
                        st.session_state.results_data.append(data_to_save)

                        st.session_state.questions_asked += 1

                        if st.session_state.questions_asked % questions_per_round == 0:
                            st.session_state.ask_continue = True
                            st.session_state.current_question = None
                        else:
                            st.session_state.current_question = draw_question()

                        st.rerun()


    if st.session_state.step == "end":
        total_questions = st.session_state.questions_asked
        max_players = max(len(st.session_state.team_players[st.session_state.team_names[0]]),
                        len(st.session_state.team_players[st.session_state.team_names[1]]))
        total_rounds = total_questions // (max_players * 2) if max_players > 0 else 0

        st.success(f"🎉 Gra zakończona! Oto wyniki końcowe:\n\n🥊 Liczba rund: **{total_rounds}** → **{total_questions}** pytań 🧠")

        # --- WYNIKI DRUŻYN ---
        teams_scores = [(team, st.session_state.scores.get(team, 0)) for team in st.session_state.team_names]
        teams_scores.sort(key=lambda x: x[1], reverse=True)

        trophies = ["🏆", "🥈"]

        for i, (team, score) in enumerate(teams_scores):
            trophy = trophies[i] if i < len(trophies) else ""
            st.write(f"{trophy} {team}: {score} punktów")

        # --- RANKING GRACZY ---
        st.markdown("---")
        st.header("🏅 Ranking graczy")

        players_scores = [(player, st.session_state.scores.get(player, 0)) for player in st.session_state.all_players]
        players_scores.sort(key=lambda x: x[1], reverse=True)


        team1 = st.session_state.team_names[0]
        team2 = st.session_state.team_names[1]
        if st.session_state.scores.get(team1, 0) > st.session_state.scores.get(team2, 0):
            winning_team = team1
        elif st.session_state.scores.get(team1, 0) < st.session_state.scores.get(team2, 0):
            winning_team = team2
        else:
            winning_team = [team1, team2]

        for idx, (player, score) in enumerate(players_scores, start=1):
            player_name, player_team = player.split("_", 1)
            if player_team in winning_team:
                player_trophy = "🏆"
            else:
                player_trophy = "🥈"
            st.write(f"{idx}. {player_trophy} **{player_name}** - {score} punktów")

        st.markdown("---")
        end_buttons()

        # --- Generowanie pliku Excel z wyników w pamięci ---
        if "results_data" in st.session_state and st.session_state.results_data:

            if "results_uploaded" not in st.session_state:
                st.session_state.results_uploaded = False

            df_results = pd.DataFrame(st.session_state.results_data)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_results.to_excel(writer, index=False, sheet_name='Wyniki')
            data = output.getvalue()

            st.download_button(
                label="💾 Pobierz wyniki gry (XLSX)",
                data=data,
                file_name="wyniki_gry.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # --- Upload na GitHub tylko raz ---
            if not st.session_state.results_uploaded:
                temp_filename = "wyniki_temp.xlsx"
                with open(temp_filename, "wb") as f:
                    f.write(data)

                repo = "DawidS25/SpectrumBySzek"
                try:
                    token = st.secrets["GITHUB_TOKEN"]
                except Exception:
                    token = None

                if token:
                    next_num = get_next_game_number(repo, token)
                    today_str = datetime.today().strftime("%Y-%m-%d")
                    file_name = f"gra{next_num:03d}_{today_str}.xlsx"
                    path_in_repo = f"wyniki/{file_name}"
                    commit_message = f"🎉 Wyniki gry {file_name}"

                    response = upload_to_github(temp_filename, repo, path_in_repo, token, commit_message)
                    if response.status_code == 201:
                        st.success(f"✅ Wyniki zapisane online.")
                        st.session_state.results_uploaded = True
                    else:
                        st.error(f"❌ Błąd zapisu: {response.status_code} – {response.json()}")
                else:
                    st.warning("⚠️ Nie udało się zapisać wyników online.")


















# ------------------------------
# Tryb 2-osobowy
# ------------------------------

def run_2osobowy():
    init_session_state(get_default_session_state("2-osobowy"))
    virtual_board_val = st.session_state.virtual_board
    if st.session_state.step == "setup":
        st.header("🎭 Wprowadź imiona graczy")
        for i in range(2):
            st.session_state.players[i] = st.text_input(
                f"🙋‍♂️ Gracz {i + 1}", value=st.session_state.players[i]
            ).strip()

        setup_buttons()
    
    elif st.session_state.step == "categories":
        category_selection_screen(CATEGORIES, CATEGORY_EMOJIS)

    
    elif st.session_state.step == "game":
        if "scores" not in st.session_state:
            st.session_state.scores = {}
        if "all_players" not in st.session_state:
            st.session_state.all_players = st.session_state.players.copy()
        for player in st.session_state.all_players:
            if player not in st.session_state.scores:
                st.session_state.scores[player] = 0

        turn = st.session_state.questions_asked % 2
        if turn == 0:
            responder = st.session_state.all_players[0]
            guesser = st.session_state.all_players[1]
        else:
            responder = st.session_state.all_players[1]
            guesser = st.session_state.all_players[0]

        if st.session_state.ask_continue:
            handle_continue_decision(2)
        else:
            prepare_next_question()
            q = st.session_state.current_question
            current_round = (st.session_state.questions_asked // 2) + 1
            current_question_number = st.session_state.questions_asked + 1
            round_info(q, current_round, current_question_number)


            st.markdown(f"Odpowiada: **{responder}** &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Zgaduje: **{guesser}**", unsafe_allow_html=True)

            if st.session_state.virtual_board:
                virtual_scoreboard_2(2, responder, guesser)
            else:
                st.markdown(f"**Ile punktów zdobywa {guesser}?**")
                if "guesser_points" not in st.session_state:
                    st.session_state.guesser_points = None

                cols = st.columns(4)
                for i, val in enumerate([0, 2, 3, 4]):
                    label = f"✅ {val}" if st.session_state.guesser_points == val else f"{val}"
                    if cols[i].button(label, key=f"gp_{val}_{st.session_state.questions_asked}"):
                        st.session_state.guesser_points = val
                        st.rerun()

                if st.session_state.guesser_points is not None:
                    if st.button("💾 Zapisz i dalej"):
                        guesser_points = st.session_state.guesser_points

                        # Reset wyborów
                        st.session_state.guesser_points = None

                        # Liczenie punktów dla respondera według zasad:
                        if guesser_points == 0:
                            responder_points = 0
                        elif guesser_points in [2, 3]:
                            responder_points = 1
                        elif guesser_points == 4:
                            responder_points = 2
                        else:
                            responder_points = 0  # Bezpieczna wartość na wypadek błędu

                        # Aktualizacja wyników
                        st.session_state.scores[guesser] += guesser_points
                        st.session_state.scores[responder] += responder_points

                        points_this_round = {
                            responder: responder_points,
                            guesser: guesser_points,
                        }

                        # Dopisywanie wyników do pamięci
                        if "results_data" not in st.session_state:
                            st.session_state.results_data = []

                        data_to_save = {
                            "nr_pytania": current_question_number,
                            "kategoria": q['categories'],
                            "pytanie": q['text'],
                            "odpowiada": responder,
                            "zgaduje": guesser,
                            responder: points_this_round[responder],
                            guesser: points_this_round[guesser],
                        }

                        st.session_state.results_data.append(data_to_save)

                        st.session_state.questions_asked += 1

                        # Po 2 pytaniach pokazujemy pytanie czy kontynuować
                        if st.session_state.questions_asked % 2 == 0:
                            st.session_state.ask_continue = True
                            st.session_state.current_question = None
                        else:
                            st.session_state.current_question = draw_question()

                        st.rerun()

    elif st.session_state.step == "end":
        total_questions = st.session_state.questions_asked
        total_rounds = total_questions // 2  # 2 pytania na rundę w trybie 2 graczy
        st.success(f"🎉 Gra zakończona! Oto wyniki końcowe:\n\n🥊 Liczba rund: **{total_rounds}** → **{total_questions}** pytań 🧠")

        sorted_scores = sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True)
        medale = ["🏆", "🥈", "🥉"]
        for i, (name, score) in enumerate(sorted_scores):
            medal = medale[i] if i < 3 else ""
            st.write(f"{medal} **{name}:** {score} punktów")

        st.markdown("---")
        end_buttons()
        
        if "results_data" in st.session_state and st.session_state.results_data:

            if "results_uploaded" not in st.session_state:
                st.session_state.results_uploaded = False

            df_results = pd.DataFrame(st.session_state.results_data)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_results.to_excel(writer, index=False, sheet_name='Wyniki')
            data = output.getvalue()

            st.download_button(
                label="💾 Pobierz wyniki gry (XLSX)",
                data=data,
                file_name="wyniki_gry.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            upload_results_once(data)

# ------------------------------
# Tryb 3-osobowy
# ------------------------------
def run_3osobowy():
    init_session_state(get_default_session_state("3-osobowy"))
    if st.session_state.step == "setup":
        st.header("🎭 Wprowadź imiona graczy")

        for i in range(3):
            st.session_state.players[i] = st.text_input(
                f"🙋‍♂️ Gracz {i + 1}", value=st.session_state.players[i]
            ).strip()

        setup_buttons()
    

    elif st.session_state.step == "categories":
        category_selection_screen(CATEGORIES, CATEGORY_EMOJIS)

    elif st.session_state.step == "game":
        if "scores" not in st.session_state:
            st.session_state.scores = {}
        if "all_players" not in st.session_state:
            st.session_state.all_players = st.session_state.players.copy()
        for player in st.session_state.all_players:
            if player not in st.session_state.scores:
                st.session_state.scores[player] = 0

        round_sequence = [
            (0, 2, 1),
            (1, 2, 0),
            (2, 1, 0),
            (0, 1, 2),
            (1, 0, 2),
            (2, 0, 1),
        ]

        round_index = st.session_state.questions_asked % len(round_sequence)
        role_indices = round_sequence[round_index]
        responder = st.session_state.all_players[role_indices[0]]
        guesser = st.session_state.all_players[role_indices[1]]
        director = st.session_state.all_players[role_indices[2]]


        if st.session_state.ask_continue:
            handle_continue_decision(6)
        else:
            prepare_next_question()
            q = st.session_state.current_question
            current_round = (st.session_state.questions_asked // 6) + 1
            current_question_number = st.session_state.questions_asked + 1
            round_info(q, current_round, current_question_number)

            st.markdown(f"Odpowiada: **{responder}** &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Zgaduje: **{guesser}** &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Kierunek: **{director}**", unsafe_allow_html=True)

            if st.session_state.virtual_board:
                virtual_scoreboard_2(6, responder, guesser, director)
            else:
                st.markdown(f"**Ile punktów zdobywa {guesser}?**")
                if "guesser_points" not in st.session_state:
                    st.session_state.guesser_points = None

                cols = st.columns(4)
                for i, val in enumerate([0, 2, 3, 4]):
                    label = f"✅ {val}" if st.session_state.guesser_points == val else f"{val}"
                    if cols[i].button(label, key=f"gp_{val}_{st.session_state.questions_asked}"):
                        st.session_state.guesser_points = val
                        st.rerun()

                st.markdown(f"**Czy {director} zdobywa dodatkowy punkt?**")
                if "extra_point" not in st.session_state:
                    st.session_state.extra_point = None

                cols2 = st.columns(2)
                for i, val in enumerate([0, 1]):
                    label = f"✅ {val}" if st.session_state.extra_point == val else f"{val}"
                    if cols2[i].button(label, key=f"ep_{val}_{st.session_state.questions_asked}"):
                        st.session_state.extra_point = val
                        st.rerun()

                if st.session_state.guesser_points is not None and st.session_state.extra_point is not None:
                    if st.button("💾 Zapisz i dalej"):
                        guesser_points = st.session_state.guesser_points
                        extra_point = st.session_state.extra_point

                        # Reset wyborów
                        st.session_state.guesser_points = None
                        st.session_state.extra_point = None

                        # Liczenie punktów globalnych
                        st.session_state.scores[guesser] += guesser_points
                        st.session_state.scores[director] += extra_point
                        bonus = 0
                        if guesser_points in [2, 3]:
                            bonus += 1
                        elif guesser_points == 4:
                            bonus += 2
                        if extra_point == 1:
                            bonus += 1
                        st.session_state.scores[responder] += bonus

                        points_this_round = {
                            responder: bonus,
                            guesser: guesser_points,
                            director: extra_point
                        }

                        # DOPISYWANIE WYNIKÓW DO LISTY W PAMIĘCI
                        if "results_data" not in st.session_state:
                            st.session_state.results_data = []

                        data_to_save = {
                            "nr_pytania": current_question_number,
                            "kategoria": q['categories'],
                            "pytanie": q['text'],
                            "odpowiada": responder,
                            "zgaduje": guesser,
                            "dodatkowo": director,
                            responder: points_this_round[responder],
                            guesser: points_this_round[guesser],
                            director: points_this_round[director],
                        }

                        st.session_state.results_data.append(data_to_save)

                        st.session_state.questions_asked += 1

                        if st.session_state.questions_asked % 6 == 0:
                            st.session_state.ask_continue = True
                            st.session_state.current_question = None
                        else:
                            st.session_state.current_question = draw_question()

                        st.rerun()

    elif st.session_state.step == "end":
        total_questions = st.session_state.questions_asked
        total_rounds = total_questions // 6
        st.success(f"🎉 Gra zakończona! Oto wyniki końcowe:\n\n🥊 Liczba rund: **{total_rounds}** → **{total_questions}** pytań 🧠")

        sorted_scores = sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True)
        medale = ["🏆", "🥈", "🥉"]
        for i, (name, score) in enumerate(sorted_scores):
            medal = medale[i] if i < 3 else ""
            st.write(f"{medal} **{name}:** {score} punktów")

        st.markdown("---")
        end_buttons()

        # --- Generowanie pliku Excel z wyników w pamięci ---
        if "results_data" in st.session_state and st.session_state.results_data:

            if "results_uploaded" not in st.session_state:
                st.session_state.results_uploaded = False

            df_results = pd.DataFrame(st.session_state.results_data)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_results.to_excel(writer, index=False, sheet_name='Wyniki')
            data = output.getvalue()

            st.download_button(
                label="💾 Pobierz wyniki gry (XLSX)",
                data=data,
                file_name="wyniki_gry.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # --- Upload na GitHub tylko raz ---
            if not st.session_state.results_uploaded:
                temp_filename = "wyniki_temp.xlsx"
                with open(temp_filename, "wb") as f:
                    f.write(data)

                repo = "DawidS25/SpectrumBySzek"
                try:
                    token = st.secrets["GITHUB_TOKEN"]
                except Exception:
                    token = None

                if token:
                    next_num = get_next_game_number(repo, token)
                    today_str = datetime.today().strftime("%Y-%m-%d")
                    file_name = f"gra{next_num:03d}_{today_str}.xlsx"
                    path_in_repo = f"wyniki/{file_name}"
                    commit_message = f"🎉 Wyniki gry {file_name}"

                    response = upload_to_github(temp_filename, repo, path_in_repo, token, commit_message)
                    if response.status_code == 201:
                        st.success(f"✅ Wyniki zapisane online.")
                        st.session_state.results_uploaded = True
                    else:
                        st.error(f"❌ Błąd zapisu: {response.status_code} – {response.json()}")
                else:
                    st.warning("⚠️ Nie udało się zapisać wyników online.")


# ------------------------------
# Ekran głowny - wybór trybu
# ------------------------------

if "step" not in st.session_state:
    st.session_state.step = "mode_select"
if "mode" not in st.session_state:
    st.session_state.mode = "None"
if "virtual_board" not in st.session_state:
    st.session_state.virtual_board = False

if "pending_mode" not in st.session_state:
    st.session_state.pending_mode = None  # <-- użyj do przechowania klikniętego przycisku

def select_mode_and_step_later(mode, step):
    st.session_state.pending_mode = mode
    st.session_state.pending_step = step

def select_mode_and_step(mode, step):
    st.session_state.mode = mode
    st.session_state.step = step
    st.rerun()


if st.session_state.step == "mode_select":
    st.title("🎮 Wybierz tryb gry")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("2-osobowy"):
            select_mode_and_step_later("2-osobowy", "setup")
    with col2:
        if st.button("3-osobowy"):
            select_mode_and_step_later("3-osobowy", "setup")
    with col3:
        if st.button("Drużynowy"):
            select_mode_and_step_later("Drużynowy", "setup")
    virtual_board_val = st.checkbox("🖥️ Użyj wirtualnej planszy")
    st.session_state.virtual_board = virtual_board_val

    if st.session_state.pending_mode is not None:
        st.session_state.mode = st.session_state.pending_mode
        st.session_state.step = st.session_state.pending_step
        st.session_state.pending_mode = None
        st.rerun()

#virtual_board_val = st.session_state.get("virtual_board", False)
if st.session_state.mode == "2-osobowy":
    run_2osobowy()
elif st.session_state.mode == "3-osobowy":
    run_3osobowy()
elif st.session_state.mode == "Drużynowy":
    run_druzynowy()


# git pull origin main --rebase
# git add .
# git commit -m ""
# git push