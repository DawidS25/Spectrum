import streamlit as st
import random
import pandas as pd
import os
import io
#
# ------------------------------
# PYTANIA
# ------------------------------
import pandas as pd

# Uwaga: uwzględnij separator ';'
df = pd.read_csv('questions.csv', sep=';')

# Kategoria to pojedyncza wartość, więc nie trzeba splitować po przecinku
def filter_by_category(cat):
    return df[df['categories'] == cat].to_dict(orient='records')

funny_questions = filter_by_category('Śmieszne')
worldview_questions = filter_by_category('Światopoglądowe')
relationship_questions = filter_by_category('Związkowe')
spicy_questions = filter_by_category('Pikantne')
casual_questions = filter_by_category('Luźne')
past_questions = filter_by_category('Przeszłość')
would_you_rather_questions = filter_by_category('Wolisz')
dylema_questions = filter_by_category('Dylematy')

CATEGORIES = {
    "Śmieszne": funny_questions,
    "Światopoglądowe": worldview_questions,
    "Związkowe": relationship_questions,
    "Pikantne": spicy_questions,
    "Luźne": casual_questions,
    "Przeszłość": past_questions,
    "Wolisz": would_you_rather_questions,
    "Dylematy": dylema_questions
}


# ------------------------------
# SESJA
# ------------------------------
defaults = {
    "players": ["", "", ""],
    "chosen_categories": [],
    "used_ids": set(),
    "current_question": None,
    "scores": {},
    "step": "setup",
    "questions_asked": 0,
    "ask_continue": False,
    "guesser_points": None,
    "extra_point": None,
    "results_filename": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ------------------------------
# FUNKCJE DO PLIKU Z WYNIKAMI
# ------------------------------
def find_new_results_filename():
    base_name = "gra"
    ext = ".csv"
    num = 1
    while True:
        filename = f"{base_name}{num:04d}{ext}"
        if not os.path.exists(filename):
            return filename
        num += 1

def create_results_file(filename, players):
    header = [
        "r_pytania",
        "kategoria",
        "pytanie",
        "odpowiada",
        "zgaduje",
        "dodatkowo",
        players[0],
        players[1],
        players[2]
    ]
    with open(filename, "w", encoding="utf-8") as f:
        f.write(",".join(header) + "\n")

def append_result_to_file(filename, data_dict):
    def escape_csv(val):
        val = str(val)
        if ',' in val or '"' in val:
            val = val.replace('"', '""')
            return f'"{val}"'
        else:
            return val
    # Zachowujemy kolejność wg nagłówka
    columns = [
        "r_pytania",
        "kategoria",
        "pytanie",
        "odpowiada",
        "zgaduje",
        "dodatkowo",
    ] + st.session_state.players
    line = ",".join(escape_csv(data_dict.get(col, "")) for col in columns)
    with open(filename, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ------------------------------
# FUNKCJA LOSUJĄCA PYTANIA
# ------------------------------
def draw_question():
    all_qs = []
    for cat in st.session_state.chosen_categories:
        all_qs.extend(CATEGORIES[cat])
    available = [q for q in all_qs if q["id"] not in st.session_state.used_ids]
    if not available:
        return None
    question = random.choice(available)
    st.session_state.used_ids.add(question["id"])
    return question

# ------------------------------
# INTERFEJS
# ------------------------------
if st.session_state.step in ["setup", "categories", "end"]:
    st.title("🎲 Spectrum")


if st.session_state.step == "setup":
    st.header("🎭 Wprowadź imiona graczy")

    player_names = []
    for i in range(3):
        name = st.text_input(f"Gracz {i + 1}", value=st.session_state.players[i])
        player_names.append(name.strip())

    if all(player_names):
        if st.button("Dalej"):
            # Zapisz graczy do sesji
            st.session_state.players = player_names
            st.session_state.all_players = player_names.copy()
            st.session_state.scores = {name: 0 for name in player_names}

            # Utwórz plik wyników
            filename = find_new_results_filename()
            create_results_file(filename, player_names)
            st.session_state.results_filename = filename

            # Przejdź dalej
            st.session_state.step = "categories"
            st.rerun()


elif st.session_state.step == "categories":
    st.header("📚 Wybierz kategorie pytań")

    if "category_selection" not in st.session_state:
        st.session_state.category_selection = set()

    cols = st.columns(4)
    for i, cat in enumerate(CATEGORIES.keys()):
        col = cols[i % 4]
        if cat in st.session_state.category_selection:
            if col.button(f"✅ {cat}", key=f"cat_{cat}"):
                st.session_state.category_selection.remove(cat)
                st.rerun()  # <--- tutaj odświeżenie po kliknięciu odznaczenia
        else:
            if col.button(cat, key=f"cat_{cat}"):
                st.session_state.category_selection.add(cat)
                st.rerun()  # <--- tutaj odświeżenie po kliknięciu zaznaczenia

    st.markdown(f"**Wybrane kategorie:** {', '.join(st.session_state.category_selection) or 'Brak'}")

    if st.session_state.category_selection:
        if st.button("Rozpocznij grę"):
            st.session_state.chosen_categories = list(st.session_state.category_selection)
            st.session_state.step = "game"
            st.rerun()


elif st.session_state.step == "game":

    # Upewnij się, że wszyscy gracze mają wpisy w scores
    if "scores" not in st.session_state:
        st.session_state.scores = {}

    if "all_players" not in st.session_state:
        st.session_state.all_players = st.session_state.players.copy()

    for player in st.session_state.all_players:
        if player not in st.session_state.scores:
            st.session_state.scores[player] = 0

    # Sekwencja ról na kolejne rundy
    round_sequence = [
        (0, 2, 1),
        (1, 2, 0),
        (2, 1, 0),
        (0, 1, 2),
        (1, 0, 2),
        (2, 0, 1),
    ]

    # Zapisz pierwotną listę graczy tylko raz
    if "all_players" not in st.session_state:
        st.session_state.all_players = st.session_state.players.copy()

    # Wyznacz rolę w aktualnej rundzie
    round_index = st.session_state.questions_asked % len(round_sequence)
    role_indices = round_sequence[round_index]
    responder = st.session_state.all_players[role_indices[0]]
    guesser = st.session_state.all_players[role_indices[1]]
    direction_guesser = st.session_state.all_players[role_indices[2]]
    players = [responder, guesser, direction_guesser]

    if st.session_state.ask_continue:
        st.header("🔄 Czy chcesz kontynuować grę?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Tak, kontynuuj"):
                st.session_state.ask_continue = False
                st.session_state.current_question = draw_question()
                st.rerun()
        with col2:
            if st.button("⏹️ Zakończ i pokaż wyniki"):
                st.session_state.step = "end"
                st.rerun()

    else:
        if not st.session_state.current_question:
            st.session_state.current_question = draw_question()
            if not st.session_state.current_question:
                st.success("🎉 Pytania się skończyły! Gratulacje.")
                st.session_state.step = "end"
                st.rerun()

        q = st.session_state.current_question
        current_round = (st.session_state.questions_asked // 6) + 1
        current_question_number = st.session_state.questions_asked + 1

        st.markdown(f"### 🌀 Runda {current_round}")
        st.subheader(f"🧠 Pytanie {current_question_number} – kategoria: *{q['categories']}*")
        st.write(q["text"])
        st.markdown(f"<small>ID pytania: {q['id']}</small>", unsafe_allow_html=True)

        # 🔁 PRZYCISK ZMIANY PYTANIA
        if st.button("🔄 Zmień pytanie"):
            new_q = draw_question()
            if new_q:
                st.session_state.current_question = new_q
            st.rerun()

        st.markdown(f"Odpowiada: **{responder}** &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Zgaduje: **{guesser}**", unsafe_allow_html=True)

        # --- GUESSER POINTS BUTTONS ---
        st.markdown(f"**Ile punktów zdobywa {guesser}?**")
        if "guesser_points" not in st.session_state:
            st.session_state.guesser_points = None

        cols = st.columns(4)
        for i, val in enumerate([0, 2, 3, 4]):
            label = f"✅ {val}" if st.session_state.guesser_points == val else f"{val}"
            if cols[i].button(label, key=f"gp_{val}_{st.session_state.questions_asked}"):
                st.session_state.guesser_points = val
                st.rerun()

        # --- EXTRA POINT BUTTONS ---
        st.markdown(f"**Czy {direction_guesser} zdobywa dodatkowy punkt?**")
        if "extra_point" not in st.session_state:
            st.session_state.extra_point = None

        cols2 = st.columns(2)
        for i, val in enumerate([0, 1]):
            label = f"✅ {val}" if st.session_state.extra_point == val else f"{val}"
            if cols2[i].button(label, key=f"ep_{val}_{st.session_state.questions_asked}"):
                st.session_state.extra_point = val
                st.rerun()

        # --- ZAPISZ I DALEJ ---
        if st.session_state.guesser_points is not None and st.session_state.extra_point is not None:
            if st.button("💾 Zapisz i dalej"):
                guesser_points = st.session_state.guesser_points
                extra_point = st.session_state.extra_point

                # Reset wyborów
                st.session_state.guesser_points = None
                st.session_state.extra_point = None

                # Liczenie punktów globalnych (sumy)
                st.session_state.scores[guesser] += guesser_points
                st.session_state.scores[direction_guesser] += extra_point
                bonus = 0
                if guesser_points in [2, 3]:
                    bonus += 1
                elif guesser_points == 4:
                    bonus += 2
                if extra_point == 1:
                    bonus += 1
                st.session_state.scores[responder] += bonus

                # Punkty zdobyte TYLKO W TEJ TURZE (do zapisu)
                points_this_round = {
                    responder: bonus,
                    guesser: guesser_points,
                    direction_guesser: extra_point
                }

                # Zapis do pliku CSV
                if st.session_state.results_filename:
                    data_to_save = {
                        "r_pytania": current_question_number,
                        "kategoria": q['categories'],
                        "pytanie": q['text'],
                        "odpowiada": responder,
                        "zgaduje": guesser,
                        "dodatkowo": direction_guesser,
                        responder: points_this_round[responder],
                        guesser: points_this_round[guesser],
                        direction_guesser: points_this_round[direction_guesser],
                    }
                    append_result_to_file(st.session_state.results_filename, data_to_save)

                # Zwiększ licznik pytań
                st.session_state.questions_asked += 1

                # Co 6 pytań – pytaj o kontynuację
                if st.session_state.questions_asked % 6 == 0:
                    st.session_state.ask_continue = True
                    st.session_state.current_question = None
                else:
                    st.session_state.current_question = draw_question()

                st.rerun()


elif st.session_state.step == "end":
    total_questions = st.session_state.questions_asked
    total_rounds = total_questions // 6
    st.success(f"🎉 Gra zakończona! Oto wyniki końcowe:\n\nLiczba rund: **{total_rounds}** → **{total_questions}** pytań")

    sorted_scores = sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True)
    for name, score in sorted_scores:
        st.write(f"**{name}:** {score} punktów")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔁 Jeszcze nie kończymy!"):
            st.session_state.ask_continue = False
            st.session_state.current_question = draw_question()
            st.session_state.step = "game"
            st.rerun()

    with col2:
        if st.button("🎮 Zagraj ponownie"):
            for key, value in defaults.items():
                if isinstance(value, set):
                    st.session_state[key] = value.copy()
                elif isinstance(value, list):
                    st.session_state[key] = value[:]
                else:
                    st.session_state[key] = value
            if "all_players" in st.session_state:
                del st.session_state["all_players"]
            if "category_selection" in st.session_state:
                del st.session_state["category_selection"]
            st.rerun()

    # --- Generowanie pliku Excel do pobrania ---
    if st.session_state.results_filename:
        df_results = pd.read_csv(st.session_state.results_filename, encoding='utf-8')
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_results.to_excel(writer, index=False, sheet_name='Wyniki')
        data = output.getvalue()

        st.download_button(
            label="⬇️ Pobierz wyniki gry (XLSX)",
            data=data,
            file_name=st.session_state.results_filename.replace('.csv', '.xlsx'),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
#git add .
#git commit -m "test"
#git push
