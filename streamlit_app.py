import streamlit as st

def main():
    if "step" not in st.session_state:
        st.session_state.step = "mode_select"

    if st.session_state.step == "mode_select":
        st.title("🎲 Spectrum")
        st.markdown(
            """
            <div style='margin-top: -20px; font-size: 10px; color: gray;'>made by Szek</div>
            """,
            unsafe_allow_html=True
        )

        st.header("Wybierz tryb gry:")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("2-osobowa"):
                st.session_state.game_mode = "2players"
                st.session_state.step = "setup"  # pierwszy krok gry
                st.rerun()

        with col2:
            if st.button("3-osobowa"):
                st.session_state.game_mode = "3players"
                st.session_state.step = "setup"
                st.rerun()

        with col3:
            if st.button("Drużynowa"):
                st.session_state.game_mode = "teams"
                st.session_state.step = "setup"
                st.rerun()
        
        with col4:
            if st.button("Plansza gry"):
                st.session_state.game_mode = "game"
                st.session_state.step = "tarcza"
                st.rerun()

    else:
        if st.session_state.game_mode == "2players":
            run_2players()
        elif st.session_state.game_mode == "3players":
            run_3players()
        elif st.session_state.game_mode == "teams":
            run_teams()
        elif st.session_state.game_mode == "game":
            run_game()


def run_2players():
    import streamlit as st
    import random
    import pandas as pd
    import os
    import io
    import base64
    import requests
    from datetime import datetime

    # ------------------------------
    # PYTANIA
    # ------------------------------
    df = pd.read_csv('questions.csv', sep=';')

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

    CATEGORY_EMOJIS = {
        "Śmieszne": "😂",
        "Światopoglądowe": "🌍",
        "Związkowe": "❤️",
        "Pikantne": "🌶️",
        "Luźne": "😎",
        "Przeszłość": "📜",
        "Wolisz": "🤔",
        "Dylematy": "⚖️"
    }

    # ------------------------------
    # SESJA
    # ------------------------------
    defaults = {
        "players": ["", ""],
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

    for key, value in defaults.items():
        if key not in st.session_state:
            if isinstance(value, set):
                st.session_state[key] = value.copy()
            elif isinstance(value, list):
                st.session_state[key] = value[:]
            else:
                st.session_state[key] = value

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
    # UPLOAD DO GITHUB 
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

    # ------------------------------
    # INTERFEJS
    # ------------------------------
    if st.session_state.step in ["setup", "categories", "end"]:
        st.title("🎲 Spectrum")
        st.markdown(
            """
            <div style='margin-top: -20px; font-size: 10px; color: gray;'>made by Szek</div>
            """,
            unsafe_allow_html=True
        )

    if st.session_state.step == "setup":
        st.header("🎭 Wprowadź imiona graczy")

        player_names = []
        for i in range(2):
            name = st.text_input(f"🙋‍♂️ Gracz {i + 1}", value=st.session_state.players[i])
            player_names.append(name.strip())

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔙 Powrót"):
                # czyść wpisane imiona i inne dane powiązane z grą 3-osobową
                if "players" in st.session_state:
                    del st.session_state["players"]
                if "all_players" in st.session_state:
                    del st.session_state["all_players"]
                if "category_selection" in st.session_state:
                    del st.session_state["category_selection"]
                st.session_state.step = "mode_select"
                st.rerun()

        with col2:
            if all(player_names):
                if st.button("✅ Dalej"):
                    st.session_state.players = player_names
                    st.session_state.all_players = player_names.copy()
                    st.session_state.scores = {name: 0 for name in player_names}
                    st.session_state.results_data = []
                    st.session_state.step = "categories"
                    st.rerun()

    elif st.session_state.step == "categories":
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
                # czyść wpisane imiona i inne dane powiązane z grą 3-osobową
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

    elif st.session_state.step == "game":
        # Zapewnij domyślne wartości
        if "scores" not in st.session_state:
            st.session_state.scores = {}
        if "all_players" not in st.session_state:
            st.session_state.all_players = st.session_state.players.copy()
        for player in st.session_state.all_players:
            if player not in st.session_state.scores:
                st.session_state.scores[player] = 0

        # Na zmianę responder i guesser: tura 0 => p1 odpowiada, p2 zgaduje; tura 1 => p2 odpowiada, p1 zgaduje itd.
        turn = st.session_state.questions_asked % 2
        if turn == 0:
            responder = st.session_state.all_players[0]
            guesser = st.session_state.all_players[1]
        else:
            responder = st.session_state.all_players[1]
            guesser = st.session_state.all_players[0]

        if st.session_state.ask_continue:
            st.header("❓ Czy chcesz kontynuować grę?")
            rounds_played = st.session_state.questions_asked // 2
            total_questions = st.session_state.questions_asked
            st.write(f"🥊 Rozegrane rundy: {rounds_played} -> {total_questions} pytań 🧠")
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
        else:
            if not st.session_state.current_question:
                st.session_state.current_question = draw_question()
                if not st.session_state.current_question:
                    st.success("🎉 Pytania się skończyły! Gratulacje.")
                    st.session_state.step = "end"
                    st.rerun()

            q = st.session_state.current_question
            current_round = (st.session_state.questions_asked // 2) + 1
            current_question_number = st.session_state.questions_asked + 1

            st.markdown(f"### 🥊 Runda {current_round}")
            st.markdown(
                """
                <div style='margin-top: -20px; font-size: 10px; color: gray;'>Spectrum - made by Szek</div>
                """,
                unsafe_allow_html=True
            )
            st.subheader(f"🧠 Pytanie {current_question_number} – kategoria: *{q['categories']}*")
            st.write(q["text"])
            st.markdown(f"<small>id: {q['id']}</small>", unsafe_allow_html=True)

            if st.button("🔄 Zmień pytanie"):
                new_q = draw_question()
                if new_q:
                    st.session_state.current_question = new_q
                st.rerun()

            st.markdown(f"Odpowiada: **{responder}** &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Zgaduje: **{guesser}**", unsafe_allow_html=True)

            st.markdown(f"**Ile punktów zdobywa {guesser}?**")
            if "guesser_points" not in st.session_state:
                st.session_state.guesser_points = None

            cols = st.columns(4)
            for i, val in enumerate([0, 2, 3, 4]):
                label = f"✅ {val}" if st.session_state.guesser_points == val else f"{val}"
                if cols[i].button(label, key=f"gp_{val}_{st.session_state.questions_asked}"):
                    st.session_state.guesser_points = val
                    st.rerun()

            # Usunięte dodatkowe punkty i osoba trzecia - już nie ma extra_point ani direction_guesser

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
                        "r_pytania": current_question_number,
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
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔁 Jeszcze nie kończymy!"):
                st.session_state.ask_continue = False
                st.session_state.current_question = draw_question()
                st.session_state.step = "game"
                st.rerun()

        with col2:
            if st.button("🎮 Zagraj ponownie"):
                # Resetowanie stanu do domyślnych wartości
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
                if "results_uploaded" in st.session_state:
                    del st.session_state["results_uploaded"]
                st.rerun()

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

def run_3players():
    import streamlit as st
    import random
    import pandas as pd
    import os
    import io
    import base64
    import requests
    from datetime import datetime

    # ------------------------------
    # PYTANIA
    # ------------------------------
    df = pd.read_csv('questions.csv', sep=';')

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

    CATEGORY_EMOJIS = {
        "Śmieszne": "😂",
        "Światopoglądowe": "🌍",
        "Związkowe": "❤️",
        "Pikantne": "🌶️",
        "Luźne": "😎",
        "Przeszłość": "📜",
        "Wolisz": "🤔",
        "Dylematy": "⚖️"
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
        "results_data": []
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            if isinstance(value, set):
                st.session_state[key] = value.copy()
            elif isinstance(value, list):
                st.session_state[key] = value[:]
            else:
                st.session_state[key] = value

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
    # UPLOAD DO GITHUB 
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

    # ------------------------------
    # INTERFEJS
    # ------------------------------
    if st.session_state.step in ["setup", "categories", "end"]:
        st.title("🎲 Spectrum")
        st.markdown(
            """
            <div style='margin-top: -20px; font-size: 10px; color: gray;'>made by Szek</div>
            """,
            unsafe_allow_html=True
        )

    if st.session_state.step == "setup":
        st.header("🎭 Wprowadź imiona graczy")

        player_names = []
        for i in range(3):
            name = st.text_input(f"🙋‍♂️ Gracz {i + 1}", value=st.session_state.players[i])
            player_names.append(name.strip())

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔙 Powrót"):
                # czyść wpisane imiona i inne dane powiązane z grą 3-osobową
                if "players" in st.session_state:
                    del st.session_state["players"]
                if "all_players" in st.session_state:
                    del st.session_state["all_players"]
                if "category_selection" in st.session_state:
                    del st.session_state["category_selection"]
                st.session_state.step = "mode_select"
                st.rerun()

        with col2:
            if all(player_names):
                if st.button("✅ Dalej"):
                    st.session_state.players = player_names
                    st.session_state.all_players = player_names.copy()
                    st.session_state.scores = {name: 0 for name in player_names}
                    st.session_state.results_data = []
                    st.session_state.step = "categories"
                    st.rerun()

    elif st.session_state.step == "categories":
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
                # czyść wpisane imiona i inne dane powiązane z grą 3-osobową
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

    elif st.session_state.step == "game":
        # Zapewnij domyślne wartości
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
        direction_guesser = st.session_state.all_players[role_indices[2]]
        players = [responder, guesser, direction_guesser]

        if st.session_state.ask_continue:
            st.header("❓ Czy chcesz kontynuować grę?")
            rundy = st.session_state.questions_asked // 6
            total_questions = st.session_state.questions_asked
            st.write(f"🥊 Rozegrane rundy: {rundy} -> {total_questions} pytań 🧠")
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

            st.markdown(f"### 🥊 Runda {current_round}")
            st.markdown(
                """
                <div style='margin-top: -20px; font-size: 10px; color: gray;'>Spectrum - made by Szek</div>
                """,
                unsafe_allow_html=True
            )
            st.subheader(f"🧠 Pytanie {current_question_number} – kategoria: *{q['categories']}*")
            st.write(q["text"])
            st.markdown(f"<small>id: {q['id']}</small>", unsafe_allow_html=True)

            if st.button("🔄 Zmień pytanie"):
                new_q = draw_question()
                if new_q:
                    st.session_state.current_question = new_q
                st.rerun()

            st.markdown(f"Odpowiada: **{responder}** &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Zgaduje: **{guesser}**", unsafe_allow_html=True)

            st.markdown(f"**Ile punktów zdobywa {guesser}?**")
            if "guesser_points" not in st.session_state:
                st.session_state.guesser_points = None

            cols = st.columns(4)
            for i, val in enumerate([0, 2, 3, 4]):
                label = f"✅ {val}" if st.session_state.guesser_points == val else f"{val}"
                if cols[i].button(label, key=f"gp_{val}_{st.session_state.questions_asked}"):
                    st.session_state.guesser_points = val
                    st.rerun()

            st.markdown(f"**Czy {direction_guesser} zdobywa dodatkowy punkt?**")
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
                    st.session_state.scores[direction_guesser] += extra_point
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
                        direction_guesser: extra_point
                    }

                    # DOPISYWANIE WYNIKÓW DO LISTY W PAMIĘCI
                    if "results_data" not in st.session_state:
                        st.session_state.results_data = []

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
                if "results_uploaded" in st.session_state:
                    del st.session_state["results_uploaded"]
                st.rerun()

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


def run_teams():
    import streamlit as st
    import random
    import pandas as pd
    import os
    import io
    import base64
    import requests
    from datetime import datetime


    # ------------------------------
    # PYTANIA
    # ------------------------------
    df = pd.read_csv('questions.csv', sep=';')

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

    CATEGORY_EMOJIS = {
        "Śmieszne": "😂",
        "Światopoglądowe": "🌍",
        "Związkowe": "❤️",
        "Pikantne": "🌶️",
        "Luźne": "😎",
        "Przeszłość": "📜",
        "Wolisz": "🤔",
        "Dylematy": "⚖️"
    }

    # ------------------------------
    # SESJA
    # ------------------------------
    defaults = {
        "team_names": ["Niebiescy", "Czerwoni"],
        "team_players": {"Niebiescy": [], "Czerwoni": []},
        "use_players": True,  # zawsze True, bo nie ma opcji bez imion
        "chosen_categories": [],
        "used_ids": set(),
        "current_question": None,
        "scores": {},
        "step": "setup",
        "questions_asked": 0,
        "ask_continue": False,
        "guesser_points": None,
        "extra_point": None,
        "results_data": []
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            if isinstance(value, set):
                st.session_state[key] = value.copy()
            elif isinstance(value, list):
                st.session_state[key] = value[:] if not isinstance(value, dict) else value.copy()
            else:
                st.session_state[key] = value

    # ------------------------------
    # UPLOAD DO GITHUB (zmieniony fragment)
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
    # SETUP - wybór drużyn i graczy
    # ------------------------------
    if st.session_state.step in ["setup", "categories", "end"]:
        st.title("🎲 Spectrum")
        st.markdown(
            """
            <div style='margin-top: -20px; font-size: 10px; color: gray;'>made by Szek</div>
            """,
            unsafe_allow_html=True
        )

    if st.session_state.step == "setup":
        st.header("🎭 Wprowadź nazwy drużyn i imiona graczy")

        # Inicjalizacja sesji
        if "team_names" not in st.session_state:
            st.session_state.team_names = ["Niebiescy", "Czerwoni"]
        if "players_team_0" not in st.session_state:
            st.session_state.players_team_0 = ["", ""]
        if "players_team_1" not in st.session_state:
            st.session_state.players_team_1 = ["", ""]

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

        # Walidacja liczby graczy
        def valid_players_count():
            len0 = len([p for p in st.session_state.players_team_0 if p.strip()])
            len1 = len([p for p in st.session_state.players_team_1 if p.strip()])
            return 2 <= len0 <= 7 and 2 <= len1 <= 7

        if not valid_players_count():
            st.warning("⚠️ Każda drużyna musi mieć od 2 do 7 graczy (łącznie minimum 4, maksimum 14 imion).")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔙 Powrót"):
                # Usuń imiona graczy drużynowych
                if "players_team_0" in st.session_state:
                    del st.session_state["players_team_0"]
                if "players_team_1" in st.session_state:
                    del st.session_state["players_team_1"]
                if "team_names" in st.session_state:
                    del st.session_state["team_names"]
                if "category_selection" in st.session_state:
                    del st.session_state["category_selection"]
                st.session_state.step = "mode_select"
                st.rerun()

        with col2:
            if valid_players_count():
                if st.button("✅ Dalej"):
                    # Inicjalizacja punktów i danych
                    st.session_state.scores = {}
                    st.session_state.results_data = []

                    team_0_key = st.session_state.team_names[0]
                    team_1_key = st.session_state.team_names[1]
                    all_players = []

                    for p in st.session_state.players_team_0:
                        if p.strip():
                            player_key = f"{p.strip()}_{team_0_key}"
                            all_players.append(player_key)

                    for p in st.session_state.players_team_1:
                        if p.strip():
                            player_key = f"{p.strip()}_{team_1_key}"
                            all_players.append(player_key)

                    st.session_state.all_players = all_players

                    # Inicjalizacja punktacji graczy
                    for p in all_players:
                        st.session_state.scores[p] = 0

                    # Punktacja drużyn
                    st.session_state.scores[team_0_key] = 0
                    st.session_state.scores[team_1_key] = 0

                    # Przypisanie listy graczy do drużyn
                    st.session_state.team_players = {
                        team_0_key: [p for p in st.session_state.players_team_0 if p.strip()],
                        team_1_key: [p for p in st.session_state.players_team_1 if p.strip()]
                    }

                    # Przejście dalej
                    st.session_state.step = "categories"
                    st.rerun()

    # ------------------------------
    # KATEGORIE - bez zmian
    # ------------------------------
    if st.session_state.step == "categories":
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
                # czyść wpisane imiona i inne dane powiązane z grą 3-osobową
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
    # LOGIKA GRY
    # ------------------------------
    if st.session_state.step == "game":
        team1 = st.session_state.team_names[0]
        team2 = st.session_state.team_names[1]
        team1_players = st.session_state.team_players.get(team1, [])
        team2_players = st.session_state.team_players.get(team2, [])
        use_players = st.session_state.use_players  # zawsze True teraz

        # Inicjalizacja słownika scores dla drużyn
        for team in [team1, team2]:
            if team not in st.session_state.scores:
                st.session_state.scores[team] = 0
            for player in st.session_state.team_players.get(team, []):
                player_id = f"{player}_{team.lower()}"
                if player_id not in st.session_state.scores:
                    st.session_state.scores[player_id] = 0

        max_players = max(len(team1_players), len(team2_players))
        questions_per_round = max_players * 2

        current_q_num = st.session_state.questions_asked
        current_round = (current_q_num // questions_per_round) + 1
        question_in_round = (current_q_num % questions_per_round) + 1

        if st.session_state.ask_continue:
            st.header("❓ Czy chcesz kontynuować grę?")
            st.write(f"🥊 Rozegrane rundy: {current_round - 1} -> {max_players * 2} pytań 🧠")
            #st.markdown(f"### 🥊 Koniec rundy {current_round - 1}")
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
            st.stop()

        if not st.session_state.current_question:
            q = draw_question()
            if not q:
                st.success("🎉 Pytania się skończyły! Gratulacje.")
                st.session_state.step = "end"
                st.rerun()
            else:
                st.session_state.current_question = q

        q = st.session_state.current_question

        st.markdown(f"### 🥊 Runda {current_round}")
        st.markdown(
            """
            <div style='margin-top: -20px; font-size: 10px; color: gray;'>Spectrum - made by Szek</div>
            """,
                unsafe_allow_html=True
        )
        st.subheader(f"🧠 Pytanie {current_q_num + 1} – kategoria: *{q['categories']}*")
        st.write(q["text"])
        st.markdown(f"<small>id: {q['id']}</small>", unsafe_allow_html=True)

        if st.button("🔄 Zmień pytanie"):
            new_q = draw_question()
            if new_q:
                st.session_state.current_question = new_q
            st.rerun()

        if current_q_num % 2 == 0:
            responding_team = team1
            guessing_team = team1
            other_team = team2
            responder_idx = (current_q_num // 2) % len(team1_players)
            responder = team1_players[responder_idx]
        else:
            responding_team = team2
            guessing_team = team2
            other_team = team1
            responder_idx = (current_q_num // 2) % len(team2_players)
            responder = team2_players[responder_idx]

        #st.markdown(f"Odpowiada: **{responder}** ({responding_team})")
        #st.markdown(f"Zgadują: **{guessing_team}**")
        st.markdown(f"Odpowiada: **{responder}** &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Zgadują: **{guessing_team}**", unsafe_allow_html=True)

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

                responder_points = guesser_points

                def player_key(player_name, team_name):
                    return f"{player_name}_{team_name.lower()}"

                player_id = player_key(responder, responding_team)
                if player_id not in st.session_state.scores:
                    st.session_state.scores[player_id] = 0
                st.session_state.scores[player_id] += responder_points

                data_to_save = {
                    "runda": current_round,
                    "pytanie_nr": current_q_num + 1,
                    "kategoria": q['categories'],
                    "pytanie": q['text'],
                    "odpowiada_drużyna": responding_team,
                    "zgaduje_drużyna": guessing_team,
                    "punkty_zgaduje": guesser_points,
                    "punkty_odpowiada": extra_point,
                    "odpowiada_gracz": responder,
                    "punkty_odpowiada_gracz": responder_points
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


    # ------------------------------
    # EKRAN KOŃCOWY
    # ------------------------------
    if st.session_state.step == "end":
        total_questions = st.session_state.questions_asked
        max_players = max(len(st.session_state.team_players[st.session_state.team_names[0]]),
                        len(st.session_state.team_players[st.session_state.team_names[1]]))
        total_rounds = total_questions // (max_players * 2) if max_players > 0 else 0

        st.success(f"🎉 Gra zakończona! Oto wyniki końcowe:\n\n🥊 Liczba rund: **{total_rounds}** → **{total_questions}** pytań 🧠")

        # --- WYNIKI DRUŻYN ---
        teams_scores = [(team, st.session_state.scores.get(team, 0)) for team in st.session_state.team_names]
        teams_scores.sort(key=lambda x: x[1], reverse=True)

        points_by_team = {team: {"odpowiadanie": 0, "zgadywanie": 0} for team in st.session_state.team_names}
        for row in st.session_state.results_data:
            points_by_team[row["odpowiada_drużyna"]]["odpowiadanie"] += row.get("punkty_odpowiada", 0)
            points_by_team[row["zgaduje_drużyna"]]["zgadywanie"] += row.get("punkty_zgaduje", 0)

        trophies = ["🏆", "🥈"]

        for i, (team, score) in enumerate(teams_scores):
            trophy = trophies[i] if i < len(trophies) else ""
            odp = points_by_team[team]["odpowiadanie"]
            zgad = points_by_team[team]["zgadywanie"]
            st.write(f"{trophy} {team}: {score} punktów ({zgad} za zgadywanie + {odp} dodatkowo)")

        # --- RANKING GRACZY ---
        st.markdown("---")
        st.header("🏅 Ranking graczy")

        # Mapa gracz -> drużyna
        player_to_team = {}
        for team, players in st.session_state.team_players.items():
            for p in players:
                player_to_team[p] = team

        # Sumujemy punkty dla każdego gracza
        player_points = {}
        for row in st.session_state.results_data:
            player = row.get("odpowiada_gracz")
            points = row.get("punkty_odpowiada_gracz", 0)
            if player:
                player_points[player] = player_points.get(player, 0) + points

        if player_points:
            sorted_players = sorted(player_points.items(), key=lambda x: x[1], reverse=True)

            for idx, (player, score) in enumerate(sorted_players, start=1):
                team = player_to_team.get(player)
                # Puchar wg drużyny: pierwsza drużyna 🏆, druga 🥈
                if team == st.session_state.team_names[0]:
                    player_trophy = "🏆"
                elif team == st.session_state.team_names[1]:
                    player_trophy = "🥈"
                else:
                    player_trophy = ""

                st.write(f"{idx}. {player_trophy} **{player}** - {score} punktów")

        else:
            st.write("Brak danych o graczach odpowiadających na pytania.")

        # --- PRZYCISKI KOŃCOWE ---
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
                        st.session_state[key] = value[:] if not isinstance(value, dict) else value.copy()
                    else:
                        st.session_state[key] = value
                if "all_players" in st.session_state:
                    del st.session_state["all_players"]
                st.rerun()

        # --- Generowanie pliku Excel z wynikami w pamięci ---
        if "results_data" in st.session_state and st.session_state.results_data:

            if "results_uploaded" not in st.session_state:
                st.session_state.results_uploaded = False

            # Przygotuj dane do pliku xlsx wg Twojej struktury
            data_for_xlsx = []
            for row in st.session_state.results_data:
                data_for_xlsx.append({
                    "Nr pytania": row.get("pytanie_nr", ""),
                    "Treść pytania": row.get("pytanie", ""),
                    "Drużyna odpowiadająca": row.get("odpowiada_drużyna", ""),
                    "Gracz odpowiadający": row.get("odpowiada_gracz", ""),
                    "Punkty drużyny odpowiadającej": row.get("punkty_zgaduje", 0),
                    "Dodatkowe punkty dla drugiej drużyny": row.get("punkty_odpowiada", 0),
                })

            import io
            import pandas as pd
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pd.DataFrame(data_for_xlsx).to_excel(writer, index=False, sheet_name='Wyniki')
            data = output.getvalue()

            # Przycisk do pobrania pliku XLSX
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
                    from datetime import datetime
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
def run_game():
    import streamlit as st
    import matplotlib.pyplot as plt
    import numpy as np

    st.set_page_config(layout="centered")
    st.title("Plansza Spectrum")

    # Ustawienie stanu strony
    if "screen" not in st.session_state:
        st.session_state.screen = "tarcza"
    if "slider_val" not in st.session_state:
        st.session_state.slider_val = 0
    if "promien_val" not in st.session_state:
        st.session_state.promien_val = 0
    if "punktacja" not in st.session_state:
        st.session_state.punktacja = None
    

    # Stałe
    total_width = 25
    half_width = total_width / 2
    center_base = 90

    colors = {
        "2": "#FFDAB5",
        "3": "#ADD8E6",
        "4": "#3399FF",
        "tlo": "#F5F5DC",
        "promien": "red"
    }

    def draw_sector(ax, center_angle, width, color):
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

    def draw_circle_with_promien(promien_angle_deg):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_aspect('equal')
        ax.axis('off')
        # Tło półkola
        theta_bg = np.linspace(0, 180, 300)
        x_bg = np.cos(np.deg2rad(theta_bg))
        y_bg = np.sin(np.deg2rad(theta_bg))
        ax.fill(np.append(x_bg, 0), np.append(y_bg, 0), color=colors["tlo"])
        # Czerwony promień
        rad = np.deg2rad(promien_angle_deg)
        x_end = np.cos(rad)
        y_end = np.sin(rad)
        ax.plot([0, x_end], [0, y_end], color=colors["promien"], linewidth=3)
        return fig

    def draw_circle_with_punktacja_and_promien(punktacja_slider_val, promien_slider_val):
        shift = 90 + (punktacja_slider_val + 100) * (-175) / 200
        promien_angle = 177.5 - (st.session_state.promien_val + 100) / 200 * (177.5 - 2.5)

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_aspect('equal')
        ax.axis('off')

        # Tło półkola
        theta_bg = np.linspace(0, 180, 300)
        x_bg = np.cos(np.deg2rad(theta_bg))
        y_bg = np.sin(np.deg2rad(theta_bg))
        ax.fill(np.append(x_bg, 0), np.append(y_bg, 0), color=colors["tlo"])

        # Punktacja
        segment_sequence = [("2", colors["2"]), ("3", colors["3"]), ("4", colors["4"]), ("3", colors["3"]), ("2", colors["2"])]
        start_angle = center_base - half_width + shift
        for i, (label, color) in enumerate(segment_sequence):
            angle = start_angle + i * 5
            draw_sector(ax, angle, 5, color)

        # Promień
        rad = np.deg2rad(promien_angle)
        x_end = np.cos(rad)
        y_end = np.sin(rad)
        ax.plot([0, x_end], [0, y_end], color=colors["promien"], linewidth=1)

        return fig

    if st.session_state.screen == "tarcza":
        st.markdown("### Ustaw punktację")
        st.session_state.slider_val = st.slider("Przesuń tarczę", -100, 100, st.session_state.slider_val, label_visibility="collapsed")
        shift = 90 + (st.session_state.slider_val + 100) * (-175) / 200 

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_aspect('equal')
        ax.axis('off')
        theta_bg = np.linspace(0, 180, 300)
        x_bg = np.cos(np.deg2rad(theta_bg))
        y_bg = np.sin(np.deg2rad(theta_bg))
        ax.fill(np.append(x_bg, 0), np.append(y_bg, 0), color=colors["tlo"])

        segment_sequence = [("2", colors["2"]), ("3", colors["3"]), ("4", colors["4"]), ("3", colors["3"]), ("2", colors["2"])]
        start_angle = center_base - half_width + shift
        for i, (label, color) in enumerate(segment_sequence):
            angle = start_angle + i * 5
            draw_sector(ax, angle, 5, color)

        st.pyplot(fig)

        
        def przejdz_do_promienia():
            st.session_state.screen = "promien"
            st.session_state.promien_val = 0
            st.session_state.punktacja = st.session_state.slider_val

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔙 Powrót"):
                st.session_state.step = "mode_select"
                st.rerun()

        with col2:
            st.button("Zatwierdź", on_click=przejdz_do_promienia)


    elif st.session_state.screen == "promien":
        st.markdown("### Wskaż odpowiedź")
        st.session_state.promien_val = st.slider("Ustaw promień", -100, 100, st.session_state.promien_val, label_visibility="collapsed")
        #shift_promien = 90 - st.session_state.promien_val / 100 * 90
        shift_promien = 177.5 - (st.session_state.promien_val + 100) / 200 * (177.5 - 2.5)
        st.pyplot(draw_circle_with_promien(shift_promien))

        col1, col2 = st.columns(2)

        def przejdz_do_wyniku():
            st.session_state.screen = "wynik"
        
        def powrot_do_tarczy():
            st.session_state.screen = "tarcza"

        with col1:
            st.button("Powrót", on_click=powrot_do_tarczy)
        with col2:
            st.button("Zatwierdź", on_click=przejdz_do_wyniku)

    elif st.session_state.screen == "wynik":
        st.markdown("### Wynik rundy")
        st.pyplot(draw_circle_with_punktacja_and_promien(st.session_state.punktacja, st.session_state.promien_val))

        # Oblicz różnicę i punkty
        roznica = abs(st.session_state.punktacja - st.session_state.promien_val)
        if roznica <= 3:
            zdobyte_punkty = "4 punkty!"
        elif roznica <= 9:
            zdobyte_punkty = "3 punkty!"
        elif roznica <= 15:
            zdobyte_punkty = "2 punkty!"
        else:
            zdobyte_punkty = "0 punktów!"

        st.markdown(f"**Zdobyto {zdobyte_punkty}**")


        def nowa_runda():
            st.session_state.screen = "tarcza"
            st.session_state.slider_val = 0
            st.session_state.promien_val = 0
            st.session_state.punktacja = None
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Koniec gry"):
                st.session_state.step = "mode_select"
                st.rerun()
        with col2:
            st.button("Kolejna runda", on_click=nowa_runda)



    # git pull origin main --rebase
    # git add .
    # git commit -m ""
    # git push



if __name__ == "__main__":
    main()

# git pull origin main --rebase
# git add .
# git commit -m ""
# git push