import streamlit as st
from streamlit_option_menu import option_menu
import scorecard, attendance, home

st.set_page_config(
    page_title="GCU Apps",
)


class MultiApp:

    def __init__(self):
        self.apps = []

    def add_app(self, title, func):

        self.apps.append({
            "title": title,
            "function": func
        })

    def run():
        # app = st.sidebar(
        with st.sidebar:
            app = option_menu(
                menu_title='GCU Applications ',
                options=['Home', 'Score Card', 'Attendance','Results'],
                icons=['house-fill', 'trophy-fill', 'person-circle'],
                menu_icon='chat-text-fill',
                default_index=1,
                styles={
                    "container": {"padding": "5!important", "background-color": 'black'},
                    "icon": {"color": "white", "font-size": "15px"},
                    "nav-link": {"color": "white", "font-size": "15px", "text-align": "left", "margin": "0px",
                                 "--hover-color": "blue"},
                    "nav-link-selected": {"background-color": "#02ab21"}, }

            )

        if app == "Home":
            home.app()
        if app == "Score Card":
            scorecard.app()
        if app == "Attendance":
            attendance.app()
        if app == "Results":
            gcu_program_result.app()


    run()
