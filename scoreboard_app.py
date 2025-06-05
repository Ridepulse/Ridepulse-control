import sys
import json
import os
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog, QStackedLayout,
    QListWidget, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QTime
from PyQt5.QtGui import QFont, QPixmap, QFontDatabase
from PyQt5.QtTest import QTest
import vlc
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import spotipy
from spotipy.oauth2 import SpotifyOAuth

PLAYLIST_FILE = 'video_playlists.json'
GOAL_SOUND = os.path.join("Media", "goal.mp3")
PROLEAGUE_SOUND = os.path.join("Media", "proleague.mp3")
video_path_lineup = 'Line-up'

# SPOTIFY API GEGEVENS
CLIENT_ID = "608e84d64a84485988c331ecaed17027"
CLIENT_SECRET = "a6a2863b966e4997a2213d494177e8e5"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
PLAYLIST_URI = "https://open.spotify.com/playlist/07vuLI875maidRM60L6rjV?si=61f5f5015af34261" # default playlist 'Database'

# Connect with api
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-modify-playback-state user-read-playback-state"
))

devices = sp.devices()
if not devices['devices']:
    QMessageBox.warning(self, "Spotify issue", "Open Spotify on a device.")
else:
    device_id = devices['devices'][0]['id']
sp.volume(100, device_id=device_id)

# settings scorebord
score_font = "Segui UI"
score_font_size = 30  # 28 is maximum
score_font_color = "color: white;"
score_margin_top = 4
score_margin_left = 0
score_margin_bottom = 0
score_margin_right = 0

name_font = "Rubik"
name_font_size = 12
name_font_color = "color: white;"
name_margin_top = 0
name_margin_left = 0
name_margin_bottom = 0
name_margin_right = 0

timer_font = "Segui UI"
timer_font_size = 40
timer_font_color = "color: white;"
timer_margin_top = 0
timer_margin_left = 0
timer_margin_bottom = 5
timer_margin_right = 0

class DraggableListWidget(QListWidget):
    def __init__(self, playlist, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.playlist = playlist
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def dropEvent(self, event):
        super().dropEvent(event)
        self.playlist.clear()
        for index in range(self.count()):
            self.playlist.append(self.item(index).text())

class ScoreboardDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.is_fullscreen = False

        regular_path = os.path.join("Fonts", "Rubik-Regular.ttf")
        bold_path = os.path.join("Fonts", "Rubik-Bold.ttf")

        font_id_reg = QFontDatabase.addApplicationFont(regular_path)
        font_id_bold = QFontDatabase.addApplicationFont(bold_path)

        if font_id_reg == -1 or font_id_bold == -1:
            print("Kon Rubik fonts niet laden.")
        else:
            rubik_family = QFontDatabase.applicationFontFamilies(font_id_reg)[0]
            print(f"Rubik geladen als: {rubik_family}")

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Scoreboard Display")
        self.setGeometry(0, 0, 480, 300)
        self.setContentsMargins(0,0,0,0)
        self.setStyleSheet("background-color: transparant;")
        self.setWindowFlag(Qt.FramelessWindowHint)

        screen_count = QApplication.desktop().screenCount()
        if screen_count > 1:
            screen_rect = QApplication.desktop().screenGeometry(1)
            self.move(screen_rect.left(), screen_rect.top())

        self.stack = QStackedLayout()
        self.setLayout(self.stack)
        self.main_container = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_container.setLayout(self.main_layout)

        # Shared Labels
        self.sporting_score = QLabel("0")
        self.sporting_score.setFont(QFont(score_font, score_font_size, QFont.Bold))
        self.sporting_score.setStyleSheet(score_font_color)
        self.sporting_score.setAlignment(Qt.AlignCenter)
        self.sporting_score.setContentsMargins(score_margin_left, score_margin_top, score_margin_right, score_margin_bottom)
        self.top_sporting_score = QLabel("0")
        self.top_sporting_score.setFont(QFont(score_font, score_font_size, QFont.Bold))
        self.top_sporting_score.setStyleSheet(score_font_color)
        self.top_sporting_score.setAlignment(Qt.AlignCenter)
        self.top_sporting_score.setContentsMargins(score_margin_left, score_margin_top, score_margin_right, score_margin_bottom)
        self.top2_sporting_score = QLabel("0")
        self.top2_sporting_score.setFont(QFont(score_font, score_font_size, QFont.Bold))
        self.top2_sporting_score.setStyleSheet(score_font_color)
        self.top2_sporting_score.setAlignment(Qt.AlignCenter)
        self.top2_sporting_score.setContentsMargins(score_margin_left, score_margin_top, score_margin_right, score_margin_bottom)

        self.sporting_name = QLabel("SPORTING")
        self.sporting_name.setFont(QFont(name_font, name_font_size, QFont.Black))
        self.sporting_name.setStyleSheet(name_font_color)
        self.sporting_name.setAlignment(Qt.AlignCenter)
        self.sporting_name.setContentsMargins(name_margin_left, name_margin_top, name_margin_right, name_margin_bottom)
        self.top_sporting_name = QLabel("SPORTING")
        self.top_sporting_name.setFont(QFont(name_font, name_font_size, QFont.ExtraBold))
        self.top_sporting_name.setStyleSheet(name_font_color)
        self.top_sporting_name.setAlignment(Qt.AlignCenter)
        self.top_sporting_name.setContentsMargins(name_margin_left, name_margin_top, name_margin_right, name_margin_bottom)
        self.top2_sporting_name = QLabel("SPORTING")
        self.top2_sporting_name.setFont(QFont(name_font, name_font_size, QFont.ExtraBold))
        self.top2_sporting_name.setStyleSheet(name_font_color)
        self.top2_sporting_name.setAlignment(Qt.AlignCenter)
        self.top2_sporting_name.setContentsMargins(name_margin_left, name_margin_top, name_margin_right, name_margin_bottom)

        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont(timer_font, timer_font_size, QFont.Bold))
        self.timer_label.setStyleSheet(timer_font_color)
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setContentsMargins(timer_margin_left, timer_margin_top, timer_margin_right, timer_margin_bottom)
        self.top_timer_label = QLabel("00:00")
        self.top_timer_label.setFont(QFont(timer_font, timer_font_size, QFont.Bold))
        self.top_timer_label.setStyleSheet(timer_font_color)
        self.top_timer_label.setAlignment(Qt.AlignCenter)
        self.top_timer_label.setContentsMargins(timer_margin_left, timer_margin_top, timer_margin_right, timer_margin_bottom)
        self.top2_timer_label = QLabel("00:00")
        self.top2_timer_label.setFont(QFont(timer_font, timer_font_size, QFont.Bold))
        self.top2_timer_label.setStyleSheet(timer_font_color)
        self.top2_timer_label.setAlignment(Qt.AlignCenter)
        self.top2_timer_label.setContentsMargins(timer_margin_left, timer_margin_top, timer_margin_right, timer_margin_bottom)

        self.visitor_score = QLabel("0")
        self.visitor_score.setFont(QFont(score_font, score_font_size, QFont.Bold))
        self.visitor_score.setStyleSheet(score_font_color)
        self.visitor_score.setAlignment(Qt.AlignCenter)
        self.visitor_score.setContentsMargins(score_margin_left, score_margin_top, score_margin_right, score_margin_bottom)
        self.top_visitor_score = QLabel("0")
        self.top_visitor_score.setFont(QFont(score_font, score_font_size, QFont.Bold))
        self.top_visitor_score.setStyleSheet(score_font_color)
        self.top_visitor_score.setAlignment(Qt.AlignCenter)
        self.top_visitor_score.setContentsMargins(score_margin_left, score_margin_top, score_margin_right, score_margin_bottom)
        self.top2_visitor_score = QLabel("0")
        self.top2_visitor_score.setFont(QFont(score_font, score_font_size, QFont.Bold))
        self.top2_visitor_score.setStyleSheet(score_font_color)
        self.top2_visitor_score.setAlignment(Qt.AlignCenter)
        self.top2_visitor_score.setContentsMargins(score_margin_left, score_margin_top, score_margin_right, score_margin_bottom)

        self.visitor_name = QLabel("VISITORS")
        self.visitor_name.setFont(QFont(name_font, name_font_size, QFont.Bold))
        self.visitor_name.setStyleSheet(name_font_color)
        self.visitor_name.setAlignment(Qt.AlignCenter)
        self.visitor_name.setContentsMargins(name_margin_left, name_margin_top, name_margin_right, name_margin_bottom)
        self.top_visitor_name = QLabel("VISITORS")
        self.top_visitor_name.setFont(QFont(name_font, name_font_size, QFont.Bold))
        self.top_visitor_name.setStyleSheet(name_font_color)
        self.top_visitor_name.setAlignment(Qt.AlignCenter)
        self.top_visitor_name.setContentsMargins(name_margin_left, name_margin_top, name_margin_right, name_margin_bottom)
        self.top2_visitor_name = QLabel("VISITORS")
        self.top2_visitor_name.setFont(QFont(name_font, name_font_size, QFont.Bold))
        self.top2_visitor_name.setStyleSheet(name_font_color)
        self.top2_visitor_name.setAlignment(Qt.AlignCenter)
        self.top2_visitor_name.setContentsMargins(name_margin_left, name_margin_top, name_margin_right, name_margin_bottom)

        # --- TOP Scoreboard (480 width) ---
        top_widget = QWidget()
        top_widget.setFixedSize(480, 60)
        top_widget.setStyleSheet("background-color: black;")
        top_widget.setContentsMargins(0, 0, 0, 0)
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        top_left_layout = QVBoxLayout()
        top_left_layout.setContentsMargins(0,0,0,0)
        top_left_layout.setSpacing(0)
        top_left_layout.addWidget(self.top_sporting_score)
        top_left_layout.addWidget(self.top_sporting_name)

        top_right_layout = QVBoxLayout()
        top_right_layout.setContentsMargins(0,0,0,0)
        top_right_layout.setSpacing(0)
        top_right_layout.addWidget(self.top_visitor_score)
        top_right_layout.addWidget(self.top_visitor_name)

        top_layout.addLayout(top_left_layout)
        top_layout.addWidget(self.top_timer_label)
        top_layout.addLayout(top_right_layout)
        top_widget.setLayout(top_layout)

        # Sponsor display area
        sponsor_container = QWidget()
        sponsor_layout = QVBoxLayout()
        sponsor_layout.setContentsMargins(0, 0, 0, 0)
        sponsor_layout.setSpacing(0)
        sponsor_container.setContentsMargins(0, 0, 0, 0)

        self.sponsor_label = QLabel()
        self.sponsor_label.setFixedSize(360, 180)
        self.sponsor_label.setContentsMargins(0,0,0,0)
        self.sponsor_label.setStyleSheet("background-color: black;")
        self.sponsor_label.setAlignment(Qt.AlignCenter)

        sponsor_layout.addWidget(self.sponsor_label)
        sponsor_container.setLayout(sponsor_layout)

        # --- BOTTOM Scoreboard (360 width) ---
        self.bottom_widget = QWidget()
        self.bottom_widget.setFixedSize(360, 60)
        self.bottom_widget.setStyleSheet("background-color: black;")
        self.bottom_widget.setContentsMargins (0,0,0,0)
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)

        bottom_left_layout = QVBoxLayout()
        bottom_left_layout.addWidget(self.sporting_score)
        bottom_left_layout.addWidget(self.sporting_name)
        bottom_left_layout.setContentsMargins(0, 0, 0, 0)
        bottom_left_layout.setSpacing(0)

        bottom_right_layout = QVBoxLayout()
        bottom_right_layout.addWidget(self.visitor_score)
        bottom_right_layout.addWidget(self.visitor_name)
        bottom_right_layout.setContentsMargins(0, 0, 0, 0)
        bottom_right_layout.setSpacing(0)

        bottom_layout.addLayout(bottom_left_layout)
        bottom_layout.addWidget(self.timer_label)
        bottom_layout.addLayout(bottom_right_layout)
        self.bottom_widget.setLayout(bottom_layout)

        self.main_layout.addWidget(top_widget)
        self.main_layout.addWidget(sponsor_container)
        self.main_layout.addWidget(self.bottom_widget)

        self.lineup_label = QLabel()
        self.lineup_label.setFixedSize(360, 240)
        self.lineup_label.setStyleSheet("background-color: black;")
        self.lineup_label.setAlignment(Qt.AlignLeft)

        #visible when content player is active
        lineup_scoreboard = QWidget()
        lineup_scoreboard.setFixedSize(480, 60)
        lineup_scoreboard.setStyleSheet("background-color: black;")  # match your main layout
        lineup_scoreboard.setContentsMargins(0,0,0,0)
        score_layout = QHBoxLayout()
        score_layout.setContentsMargins(0, 0, 0, 0)
        score_layout.setSpacing(0)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.top2_sporting_score)
        left_layout.addWidget(self.top2_sporting_name)
        left_layout.setSpacing(0)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.top2_visitor_score)
        right_layout.addWidget(self.top2_visitor_name)
        right_layout.setSpacing(0)

        score_layout.addLayout(left_layout)
        score_layout.addWidget(self.top2_timer_label)
        score_layout.addLayout(right_layout)

        lineup_scoreboard.setLayout(score_layout)

        self.lineup_container = QWidget()
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(0)
        video_layout.addWidget(self.lineup_label)
        self.lineup_container.setLayout(video_layout)
        self.lineup_container.setFixedSize(480, 240)

        self.lineup_page = QWidget()
        full_layout = QVBoxLayout()
        full_layout.setContentsMargins(0, 0, 0, 0)
        full_layout.setSpacing(0)
        full_layout.addWidget(lineup_scoreboard)
        full_layout.addWidget(self.lineup_container, alignment=Qt.AlignLeft)
        self.lineup_page.setLayout(full_layout)

        self.setLayout(self.main_layout)
        self.stack.addWidget(self.main_container)  # index 0
        self.stack.addWidget(self.lineup_page)  # index 1

class ControlPanel(QWidget):
    def __init__(self, display_window):
        super().__init__()
        self.display = display_window
        self.is_fullscreen = False
        self.top_video_playlist = []
        self.vlc_instance = vlc.Instance()
        self.top_video_index = 0
        self.top_video_player = self.vlc_instance.media_player_new()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer_running = False
        self.elapsed_seconds = 0

        self.lineup_inputs = []
        self.lineup_index = 0
        self.lineup_files = []

        self.goal_input = QLineEdit()
        self.wissel_input = QLineEdit()

        self.image_timer = QTimer()
        self.image_timer.setSingleShot(True)
        self.image_timer.timeout.connect(self.show_next_sponsor)

        self.video_timer = QTimer()
        self.video_timer.setSingleShot(True)
        self.video_timer.timeout.connect(self.show_next_sponsor)

        self.mute_button = QPushButton("Muted")
        self.mute_button.setCheckable(True)
        self.mute_button.setChecked(True)  # Default is muted
        self.mute_button.clicked.connect(self.toggle_mute)

        self.remaining_time = QTime(0, 0, 0)
        self.goal_sound = QMediaPlayer()
        self.goal_sound.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(GOAL_SOUND))))
        self.proleague_sound = QMediaPlayer()
        self.proleague_sound.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(PROLEAGUE_SOUND))))
        self.initUI()
        self.load_playlists()
        self.load_sponsor_folder()
        self.vlc_instance = vlc.Instance()
        self.load_playlists()
        self.top_video_playlist = []
        self.current_playlist_index = 0
        self.playlist_loop_active = True

        self.media_player = self.vlc_instance.media_player_new()
        self.start_sponsors_loop()

        self.loop_instance = vlc.Instance()
        self.loop_player = self.loop_instance.media_player_new()
        self.loop_video_path = 'default.jpg' # Standaard layout foto
        self.start_loop_video()

    def create_button(self, text, callback):
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        return btn

    def start_loop_video(self):
        if not os.path.exists(self.loop_video_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {video_path} ")
            return

        screens = QApplication.screens()
        if len(screens) < 3:
            QMessageBox.warning(self, "Screen issue", f"Only {len(screens)} screens connected.")

            return

        screen = screens[2]
        geo = screen.geometry()
        if hasattr(self, "loop_window") and self.loop_window:
            self.loop_window.close()

        self.loop_window = QWidget()
        self.loop_window.setGeometry(geo)
        self.loop_window.move(geo.topLeft())
        self.loop_window.setWindowFlags(Qt.FramelessWindowHint)
        self.loop_window.showFullScreen()
        self.loop_window.raise_()
        self.loop_window.activateWindow()
        QApplication.processEvents()  # Cruciaal: winId wordt pas dan geldig
        media = self.loop_instance.media_new(self.loop_video_path)
        self.loop_player.set_media(media)
        win_id = int(self.loop_window.winId())
        if sys.platform.startswith("linux"):
            self.loop_player.set_xwindow(win_id)
        else:
            self.loop_player.set_hwnd(win_id)

        self.loop_player.play()
        def check_loop():
            state = self.loop_player.get_state()
            if state == vlc.State.Ended or state == vlc.State.Stopped:
                #self.loop_player.stop()   (not needed, unless software crashes)
                self.loop_player.play()
            QTimer.singleShot(1000, check_loop)

        QTimer.singleShot(1000, check_loop)

    def set_loop_video(self, video_path):
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {video_path} ")
            return

        self.loop_video_path = video_path
        media = self.loop_instance.media_new(video_path)
        self.loop_player.set_media(media)
        self.loop_player.play()

    def reset_loop_video(self, video_path):
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {video_path} ")
            return

        self.loop_video_path = video_path
        self.loop_player.stop()
        if hasattr(self, "loop_window") and self.loop_window:
            self.loop_window.close()
            self.loop_window = None

        self.start_loop_video() #herstart nieuw venster met start layout.

    def initUI(self):
        self.setWindowTitle("Ridepulse System")
        self.showMaximized()

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #dcdcdc;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QLineEdit, QListWidget {
                background-color: #2d2d30;
                border: 1px solid #444;
                padding: 4px;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QLabel {
                font-weight: bold;
                margin-top: 6px;
            }
        """)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- Scoreboard Section ---
        scoreboard_layout = QVBoxLayout()
        scoreboard_layout.setSpacing(10)

        def labeled_input(label_text, default_text=""):
            layout = QVBoxLayout()
            label = QLabel(label_text)
            input_field = QLineEdit(default_text)
            layout.addWidget(label)
            layout.addWidget(input_field)
            return layout, input_field

        name1_layout, self.team1_name = labeled_input("Team 1", "SPORTING")
        scoreboard_layout.addLayout(name1_layout)

        scoreboard_layout.addWidget(
            self.create_button("Goal Home", lambda: self.add_sporting_goal(self.display.sporting_score)))
        scoreboard_layout.addWidget(
            self.create_button("-1 score", lambda: self.lower_goal(self.display.sporting_score)))

        name2_layout, self.team2_name = labeled_input("Team 2", "")
        scoreboard_layout.addLayout(name2_layout)

        scoreboard_layout.addWidget(
            self.create_button("Goal Visitors", lambda: self.add_visitor_goal(self.display.visitor_score)))
        scoreboard_layout.addWidget(
            self.create_button("-1 score", lambda: self.lower_goal(self.display.visitor_score)))
        scoreboard_layout.addWidget(self.create_button("Update Scoreboard", self.update_scoreboard))

        timer_layout, self.timer_input = labeled_input("Timer (MM:SS)", "00:00")
        scoreboard_layout.addLayout(timer_layout)

        self.toggle_timer_btn = QPushButton("Start Timer")
        self.toggle_timer_btn.clicked.connect(self.toggle_timer)
        scoreboard_layout.addWidget(self.toggle_timer_btn)
        scoreboard_layout.addWidget(self.create_button("Update Timer", self.update_timer_value))
        scoreboard_layout.addWidget(self.create_button("Reset (1e helft)", self.reset_timer_eerstehelft))
        scoreboard_layout.addWidget(self.create_button("Reset (2e helft)", self.reset_timer_tweedehelft))
        scoreboard_layout.addWidget(QLabel(""))
        scoreboard_layout.addWidget(self.create_button("Start Sponsors", self.start_sponsors_loop))
        scoreboard_layout.addWidget(self.create_button("Toggle Fullscreen", self.toggle_fullscreen))
        scoreboard_layout.addWidget(self.create_button("Exit", self.exit_application))

        # --- Video Section ---
        video_layout = QVBoxLayout()
        video_layout.setSpacing(10)

        video_layout.addWidget(QLabel("Top Video Playlist (not working)"))

        self.top_list = DraggableListWidget(self.top_video_playlist)
        self.top_list.setMinimumHeight(100)
        video_layout.addWidget(self.top_list)

        video_layout.addWidget(self.create_button("Add Video", self.add_video))
        video_layout.addWidget(self.create_button("Remove Video", self.remove_video))
        video_layout.addWidget(QLabel(""))
        video_layout.addWidget(self.create_button("Play Playlist", self.play_top_playlist))
        video_layout.addWidget(self.create_button("Stop Playlist", self.stop_top_playlist))
        video_layout.addWidget(self.create_button("Save Playlist", self.save_playlists))
        video_layout.addWidget(self.mute_button)

        lineup_layout = QVBoxLayout()
        lineup_layout.setSpacing(10)
        lineup_layout.addWidget(QLabel("Line-up Players"))
        for i in range(12):
            line_input = QLineEdit()
            self.lineup_inputs.append(line_input)
            lineup_layout.addWidget(line_input)

        lineup_layout.addWidget(self.create_button("Start Line-up Sequence", self.start_lineup))
        lineup_layout.addWidget(self.create_button("Play Pro League Sound", self.play_proleague_sound))
        lineup_layout.addWidget(QLabel("Goal Visual"))
        lineup_layout.addWidget(self.goal_input)
        lineup_layout.addWidget(self.create_button("Play Goal Visual", self.play_goal_video))

        # --- Wissel Input ---
        lineup_layout.addWidget(QLabel("OUT and IN"))
        lineup_layout.addWidget(self.wissel_input)
        lineup_layout.addWidget(self.create_button("Play Wisselspeler Visual", self.play_wissel_video))

        spotify_layout = QVBoxLayout()
        spotify_layout.setSpacing(10)
        spotify_layout.addWidget(QLabel("Spotify"))
        spotify_layout.addWidget(self.create_button("Start Database playlist", self.start_playlist_database))
        spotify_layout.addWidget(self.create_button("Start Pre-game playlist", self.start_playlist_pregame))
        spotify_layout.addWidget(self.create_button("Start House of House (Pre-game playlist)", self.start_house_of_house))
        spotify_layout.addWidget(self.create_button("Start Half-Time playlist", self.start_playlist_halftime))
        spotify_layout.addWidget(self.create_button("Start Playlist Winst/Gelijkspel", self.start_playlist_winst))
        spotify_layout.addWidget(self.create_button("Start Playlist Verlies", self.start_playlist_verlies))
        spotify_layout.addWidget(QLabel(""))
        spotify_layout.addWidget(self.create_button("Pauzeer muziek", self.pause_spotify))
        spotify_layout.addWidget(self.create_button("Hervat muziek", self.play_spotify))
        spotify_layout.addWidget(self.create_button("Next Song", self.spotify_next))
        spotify_layout.addWidget(self.create_button("Previous Song", self.spotify_previous))

        loop_video_layout = QVBoxLayout()
        loop_video_layout.addWidget(QLabel("Loop Video (3e scherm)"))
        loop_video_layout.addWidget(self.create_button("Toon Main", lambda: self.set_loop_video("Main.mp4")))
        loop_video_layout.addWidget(self.create_button("Toon Gameday", lambda: self.set_loop_video("Gameday.mp4")))
        loop_video_layout.addWidget(self.create_button("Reset boarding", lambda: self.reset_loop_video("default.jpg")))

        main_layout.addLayout(scoreboard_layout, 1)
        main_layout.addLayout(video_layout, 1)
        main_layout.addLayout(lineup_layout, 1)
        main_layout.addLayout(spotify_layout, 1)
        main_layout.addLayout(loop_video_layout, 1)

        self.setLayout(main_layout)

    def spotify_next(self):
        sp.next_track(device_id=device_id)

    def spotify_previous(self):
        sp.previous_track(device_id=device_id)

    def pause_spotify(self):
        playback = sp.current_playback()
        if playback and playback["is_playing"]:
            sp.pause_playback(device_id=device_id)
        else:
            QMessageBox.warning(self, "Spotify", "Spotify is already paused.")

    def play_spotify(self):
        playback = sp.current_playback()
        if playback and playback["is_playing"]:
            QMessageBox.warning(self, "Spotify", "Spotify is already playing.")
        else:
            sp.start_playback(device_id=device_id)

    def start_playlist_database(self, name):
        PLAYLIST_URI = "https://open.spotify.com/playlist/07vuLI875maidRM60L6rjV?si=61f5f5015af34261"
        sp.shuffle(state=True, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)

    def start_playlist_halftime(self, name):
        PLAYLIST_URI = "https://open.spotify.com/playlist/5mCSX2xOfz36RGraeFSGRo?si=cf9237d90e93408e"
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)

    def start_playlist_pregame(self, name):
        PLAYLIST_URI = "https://open.spotify.com/playlist/6OhoNbXkzzltrDNj12UFzT?si=69930d487cf148b3"
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)

    def start_house_of_house(self, name):
        PLAYLIST_URI = "https://open.spotify.com/playlist/6OhoNbXkzzltrDNj12UFzT?si=69930d487cf148b3"
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI, offset={"position": 4})

    def start_playlist_winst(self, name):
        PLAYLIST_URI = "https://open.spotify.com/playlist/0McXB0TUQ4wv7rGdQuDJhZ?si=34a0b8b962704a53"
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)

    def start_playlist_verlies(self, name):
        PLAYLIST_URI = "https://open.spotify.com/playlist/0NLX1L4Zo2SPx5lNHF6Ywy?si=82993e6aa8f04b10"
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)

    def pause_playlist(self):
        sp.pause_playback(device_id=device_id)

    def exit_application(self):
        screens = QApplication.screens()
        if len(screens) >= 3:
            self.loop_window.close()
        self.display.close()
        self.close()
        QApplication.quit()

    def toggle_mute(self):
        is_muted = self.mute_button.isChecked()
        self.media_player.audio_set_mute(is_muted)
        self.mute_button.setText(f" {'Muted' if is_muted else 'Unmuted'}")

    def update_scoreboard(self):
        self.display.sporting_name.setText(self.team1_name.text())
        self.display.visitor_name.setText(self.team2_name.text())
        self.display.top_sporting_name.setText(self.team1_name.text())
        self.display.top_visitor_name.setText(self.team2_name.text())

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.showNormal()
        else:
            self.showFullScreen()
        self.is_fullscreen = not self.is_fullscreen

    def add_sporting_goal(self, label):
        score = int(label.text()) + 1
        label.setText(str(score))
        self.display.top_sporting_score.setText(str(score))
        self.display.top2_sporting_score.setText(str(score))
        self.goal_sound.stop()  # Ensures it replays properly
        self.goal_sound.play()

    def add_visitor_goal(self, label):
        score = int(label.text()) + 1
        label.setText(str(score))
        self.display.top_visitor_score.setText(str(score))
        self.display.top2_visitor_score.setText(str(score))

    def lower_goal(self, label):
        score = max(0, int(label.text()) - 1)
        label.setText(str(score))

        if label == self.display.sporting_score:
            self.display.top_sporting_score.setText(str(score))
            self.display.top2_sporting_score.setText(str(score))
        elif label == self.display.visitor_score:
            self.display.top_visitor_score.setText(str(score))
            self.display.top2_visitor_score.setText(str(score))

    def toggle_timer(self):
        if self.timer_running:
            self.timer.stop()
            self.toggle_timer_btn.setText("Start Timer")
        else:
            self.timer.start(1000)
            self.toggle_timer_btn.setText("Stop Timer")
        self.timer_running = not self.timer_running

    def reset_timer_eerstehelft(self):
        self.timer.stop()
        self.toggle_timer_btn.setText("Start Timer")
        self.timer_running = not self.timer_running
        self.elapsed_seconds = 0
        self.display.timer_label.setText("00:00")
        self.display.top_timer_label.setText("00:00")
        self.display.top2_timer_label.setText("00:00")

    def reset_timer_tweedehelft(self):
        self.timer.stop()
        self.toggle_timer_btn.setText("Start Timer")
        self.timer_running = not self.timer_running
        self.elapsed_seconds = 45 * 60
        self.display.timer_label.setText("45:00")
        self.display.top_timer_label.setText("45:00")
        self.display.top2_timer_label.setText("45:00")

    def update_timer(self):
        self.elapsed_seconds += 1
        minutes, seconds = divmod(self.elapsed_seconds, 60)
        if self.elapsed_seconds == 240:
            self.show_greg_visual()

        self.display.timer_label.setText(f"{minutes:02}:{seconds:02}")
        self.display.top_timer_label.setText(f"{minutes:02}:{seconds:02}")
        self.display.top2_timer_label.setText(f"{minutes:02}:{seconds:02}")

    def show_greg_visual(self):
        image_path = os.path.join("Media", "greg.png")
        if not os.path.exists(image_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {image_path}")
            return

        self.display.stack.setCurrentIndex(1)
        self.display.lineup_label.setPixmap(QPixmap(image_path).scaled(
            self.display.lineup_label.size(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        ))
        self.display.lineup_label.show()

        # Sluit na 60 seconden
        QTimer.singleShot(60000, self.hide_lineup_visual)

    def hide_lineup_visual(self):
        self.display.lineup_label.clear()
        self.display.lineup_label.hide()
        self.display.stack.setCurrentIndex(0)

    def update_timer_value(self):
        self.timer.stop()
        self.toggle_timer_btn.setText("Start Timer")
        self.timer_running = not self.timer_running
        text = self.timer_input.text().strip()
        try:
            minutes, seconds = map(int, text.split(":"))
            self.elapsed_seconds = minutes * 60 + seconds
            self.display.timer_label.setText(f"{minutes:02}:{seconds:02}")
            self.display.top_timer_label.setText(f"{minutes:02}:{seconds:02}")
            self.display.top2_timer_label.setText(f"{minutes:02}:{seconds:02}")
        except Exception:
            QMessageBox.critical(self, "Invalid Format", "Please enter MM:SS")

    def add_video(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Add Video")
        if filename:
            self.top_video_playlist.append(filename)
            self.top_list.addItem(filename)

    def remove_video(self):
        current = self.top_list.currentRow()
        if current >= 0:
            self.top_video_playlist.pop(current)
            self.top_list.takeItem(current)

    def play_top_playlist(self):
        self.top_video_player.stop()

        if not self.top_video_playlist:
            print("No videos in playlist.")
            return

        self.current_playlist_index = 0
        self.playlist_loop_active = True
        self.play_next_video()

    def play_next_video(self):
        try:
           if not self.playlist_loop_active:
                return
                self.current_playlist_index = (self.current_playlist_index + 1) % len(self.top_video_playlist)
                video_path = self.top_video_playlist[self.current_playlist_index]
                media = self.top_video_player.media_new(video_path)
                self.top_video_vlc.set_media(media)
                self.top_video_vlc.play()
                self.top_video_vlc.audio_set_mute(self.mute_button.isChecked())

        except Exception as e:
            print(f"Error in play_next_video: {e}")

        if not self.top_video_player or not self.display.top_video_label:
            print("Video player or display label not initialized.")
            return

        if self.current_playlist_index >= len(self.top_video_playlist):
            self.current_playlist_index = 0  # Loop back to start

        video_path = self.top_video_playlist[self.current_playlist_index]

        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            self.current_playlist_index += 1
            QTimer.singleShot(500, self.play_next_video)
            return

        media = self.vlc_instance.media_new(video_path)
        self.top_video_player.set_media(media)
        self.display.top_video_label.show()
        QTest.qWait(50)
        try:
            if sys.platform.startswith('linux'):
                self.top_video_player.set_xwindow(int(self.display.top_video_label.winId()))
            else:
                self.top_video_player.set_hwnd(int(self.display.top_video_label.winId()))
        except Exception as e:
            print(f"Failed to set video output window: {e}")
            self.current_playlist_index += 1
            QTimer.singleShot(1000, self.play_next_video)
            return
        self.top_video_player.audio_set_mute(self.mute_button.isChecked())
        self.top_video_player.play()

        def check_duration():
            duration = self.top_video_player.get_length()
            if duration > 0:
                print(f"Duration: {duration}ms")
                QTimer.singleShot(duration, self.play_next_video)
                self.current_playlist_index += 1
            else:
                # Try again after a short wait
                QTimer.singleShot(200, check_duration)

        QTimer.singleShot(200, check_duration)

    def play_video(self):
        if self.top_video_index >= len(self.top_video_playlist):
            self.top_video_index = 0  # Loop
        media = self.vlc_instance.media_new(self.top_video_playlist[self.top_video_index])
        self.top_video_player.set_media(media)
        if sys.platform.startswith('linux'):
            self.top_video_player.set_xwindow(int(self.display.sponsor_label.winId()))
        else:
            self.top_video_player.set_hwnd(int(self.display.sponsor_label.winId()))

        # Use VLC event instead of polling
        events = self.top_video_player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self.on_video_end)

        self.top_video_player.play()

    def on_video_end(self, event):
        self.top_video_index += 1
        self.play_video()

    def stop_top_playlist(self):
        self.top_video_player.stop()

    def load_playlists(self):
        if os.path.exists(PLAYLIST_FILE):
            with open(PLAYLIST_FILE, 'r') as f:
                data = json.load(f)
                self.top_video_playlist = data.get("top", [])

        if hasattr(self, 'top_list'):
            self.top_list.clear()
            self.top_list.addItems(self.top_video_playlist)

    def save_playlists(self):
        data = {"top": self.top_video_playlist}
        with open(PLAYLIST_FILE, 'w') as f:
            json.dump(data, f)

    def start_sponsors_loop(self):
        self.top_video_player.stop()
        folder_path = "Sponsors"
        if not os.path.isdir(folder_path):
            return
        self.sponsor_files = [os.path.join(folder_path, f) for f in sorted(os.listdir(folder_path)) if f.lower().endswith((".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mov"))]
        if not self.sponsor_files:
            return
        self.sponsor_index = 0
        self.show_next_sponsor()

    def show_next_sponsor(self):
        if not self.sponsor_files:
            return

        file_path = self.sponsor_files[self.sponsor_index]
        self.sponsor_index = (self.sponsor_index + 1) % len(self.sponsor_files)

        ext = os.path.splitext(file_path)[1].lower()

        if ext in [".png", ".jpg", ".jpeg"]:
            self.display.sponsor_label.clear()
            pixmap = QPixmap(file_path).scaled(
                self.display.sponsor_label.width(), self.display.sponsor_label.height(),
                Qt.IgnoreAspectRatio, Qt.SmoothTransformation
            )
            self.display.sponsor_label.setPixmap(pixmap)

            self.video_timer.stop()
            self.image_timer.start(5000)  # Show image for 5 seconds
        elif ext in [".mp4", ".avi", ".mov"]:
            self.image_timer.stop()
            self.display.sponsor_label.clear()

            if self.media_player.is_playing():
                self.media_player.stop()

            media = self.vlc_instance.media_new(file_path)
            self.media_player.set_media(media)
            self.media_player.audio_set_mute(self.mute_button.isChecked())

            if sys.platform.startswith("linux"):
                self.media_player.set_xwindow(int(self.display.sponsor_label.winId()))
            else:
                self.media_player.set_hwnd(int(self.display.sponsor_label.winId()))

            self.media_player.play()

            def poll_video_finished():
                if not self.media_player.is_playing():
                    QTimer.singleShot(100, self.show_next_sponsor)
                else:
                    QTimer.singleShot(200, poll_video_finished)

            QTimer.singleShot(100, poll_video_finished)

    def start_video_timer(self):
        duration = self.media_player.get_length()
        if duration <= 0:
            duration = 1000  # Default fallback
        self.video_timer.start(duration)

    def load_sponsor_folder(self):
        folder = os.path.join(os.getcwd(), "Sponsors")
        if os.path.isdir(folder):
            for file in os.listdir(folder):
                if file.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
                    full_path = os.path.join(folder, file)
                    if full_path not in self.top_video_playlist:
                        self.top_video_playlist.append(full_path)
            if hasattr(self, 'top_list'):
                self.top_list.clear()
                self.top_list.addItems(self.top_video_playlist)

    def start_lineup(self):
        self.lineup_files = [inp.text().strip() + ".mp4" for inp in self.lineup_inputs if inp.text().strip()]
        if not self.lineup_files:
            QMessageBox.warning(self, "No Input", "Please enter at least one player number.")
            return

        self.lineup_index = 0
        self.display.stack.setCurrentIndex(1)  # show lineup
        self.display.lineup_label.show()
        self.lineup_event_attached = False  # <- initialize flag
        self.lineup_vlc_instance = vlc.Instance()
        self.lineup_video_player = self.lineup_vlc_instance.media_player_new()
        self.play_next_lineup_video()

    def play_next_lineup_video(self):
        if self.lineup_index >= len(self.lineup_files):
            self.hide_lineup_visual()
           # self.lineup_video_player.stop()
          #  self.display.lineup_label.hide()
          #  self.display.stack.setCurrentIndex(0)  # show main layout
            return

        file_name = self.lineup_files[self.lineup_index]
        video_path = os.path.join(os.getcwd(), video_path_lineup, file_name)

        if not os.path.exists(video_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {video_path} ")
            self.lineup_index += 1
            QTimer.singleShot(10, self.play_next_lineup_video)
            return

        media = self.lineup_vlc_instance.media_new(video_path)
        self.lineup_video_player.set_media(media)
        self.lineup_video_player.audio_set_mute(self.mute_button.isChecked())

        if sys.platform.startswith("linux"):
            self.lineup_video_player.set_xwindow(int(self.display.lineup_label.winId()))
        else:
            self.lineup_video_player.set_hwnd(int(self.display.lineup_label.winId()))

        self.lineup_video_player.play()
        def check_duration_and_queue_next():
            duration = self.lineup_video_player.get_length()
            if duration > 0:
                QTimer.singleShot(duration, self.play_next_lineup_video)
                self.lineup_index += 1
            else:
                QTimer.singleShot(10, check_duration_and_queue_next)

        QTimer.singleShot(10, check_duration_and_queue_next)

    def play_proleague_sound(self):
        self.proleague_sound.stop() #start vanaf het begin
        self.proleague_sound.play()

    def play_goal_video(self):
        filename = self.goal_input.text().strip()
        if not filename:
            QMessageBox.warning(self, "No Input", "Please add a player number in the input field.")
            return

        video_path = os.path.join(os.getcwd(), video_path_lineup, filename + ".mp4")
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {video_path}")
            return

        self.play_single_video(video_path)

    def play_wissel_video(self):
        filename = self.wissel_input.text().strip()
        if not filename:
            QMessageBox.warning(self, "No Input", "Please add a player number in the input field.")
            return

        video_path = os.path.join(os.getcwd(), video_path_lineup, filename + ".mp4")
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {video_path}")
            return

        self.play_single_video(video_path)

    def play_single_video(self, video_path):
        self.display.stack.setCurrentIndex(1)
        self.display.lineup_label.show()

        # Zet een tijdelijke VLC speler op
        player = vlc.Instance().media_player_new()
        media = vlc.Instance().media_new(video_path)
        player.set_media(media)
        player.audio_set_mute(self.mute_button.isChecked())

        if sys.platform.startswith("linux"):
            player.set_xwindow(int(self.display.lineup_label.winId()))
        else:
            player.set_hwnd(int(self.display.lineup_label.winId()))

        player.play()

        def check_end():
            if not player.is_playing():
                player.stop()
                self.display.lineup_label.hide()
                self.display.stack.setCurrentIndex(0)
            else:
                QTimer.singleShot(300, check_end)

        QTimer.singleShot(1000, check_end)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    display = ScoreboardDisplay()
    panel = ControlPanel(display)
    display.show()
    panel.show()
    sys.exit(app.exec_())
