import sys
import json
import os
import time
import ctypes
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog, QStackedLayout, QMessageBox, QSizePolicy, QDialog
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QTime
from PyQt5.QtGui import QFont, QPixmap, QFontDatabase
import vlc
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import subprocess


PLAYLIST_FILE = 'video_playlists.json'
GOAL_SOUND = os.path.join("Media", "goal.mp3")
PROLEAGUE_SOUND = os.path.join("Media", "proleague.wav")
PREGAME_MIXTAPE = os.path.join("Media", "pregame_mixtape.mp3")
COUNTDOWN = os.path.join("Media", "countdown.mp3")
video_path_lineup = 'Line-up-Visuals'
video_path_goal = 'Goal-Visuals'

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
    print("open spotify!")
else:
    device_id = devices['devices'][0]['id']

config_file = "config.json"

if not os.path.exists(config_file):
    app = QApplication([])
    QMessageBox.critical(None, "Configuratiefout", f"Kan het configuratiebestand '{config_file}' niet vinden.")
    sys.exit(1)

try:
    with open(config_file, "r") as f:
        config = json.load(f)
except json.JSONDecodeError:
    app = QApplication([])
    QMessageBox.critical(None, "Configuratiefout", f"'{config_file}' bevat geen geldige JSON.")
    sys.exit(1)


# settings scorebord
score_font = config["score_font"]
score_font_size = config["score_font_size"]
score_font_color = config["score_font_color"]
score_margin_top = config["score_margin_top"]
score_margin_left = config["score_margin_left"]
score_margin_bottom = config["score_margin_bottom"]
score_margin_right = config["score_margin_right"]

name_font = config["name_font"]
name_font_size = config["name_font_size"]
name_font_color = config["name_font_color"]
name_margin_top = config["name_margin_top"]
name_margin_left = config["name_margin_left"]
name_margin_bottom = config["name_margin_bottom"]
name_margin_right = config["name_margin_right"]

timer_font = config["timer_font"]
timer_font_size = config["timer_font_size"]
timer_font_color = config["timer_font_color"]
timer_margin_top = config["timer_margin_top"]
timer_margin_left = config["timer_margin_left"]
timer_margin_bottom = config["timer_margin_bottom"]
timer_margin_right = config["timer_margin_right"]

# settings displays
controlpanel_display_number = config["controlpanel_display_number"]
scoreboard_display_number = config["scoreboard_display_number"]
ledboarding_display_number = config["ledboarding_display_number"]

#settings spotify
DATABASE_URL = config["database_url"]
HALFTIME_URL = config["halftime_url"]
PREGAME_URL = config["pregame_url"]
WIN_URL = config["win_url"]
LOSE_URL = config["lose_url"]

#settings sponsors
sponsor_duration = config["sponsor_duration"]
show_greg = config["show_greg"]

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
            screen_rect = QApplication.desktop().screenGeometry(scoreboard_display_number)
            self.move(screen_rect.left(), screen_rect.top())

        self.stack = QStackedLayout()
        self.setLayout(self.stack)
        self.main_container = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_container.setLayout(self.main_layout)

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

        self.video_widget = QVideoWidget()
        self.video_widget.setFixedSize(360, 180)
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setStyleSheet("background-color: black;")
        self.video_widget.hide()

        sponsor_layout.addWidget(self.sponsor_label)
        sponsor_layout.addWidget(self.video_widget)
        sponsor_container.setLayout(sponsor_layout)

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

        lineup_scoreboard = QWidget()
        lineup_scoreboard.setFixedSize(480, 60)
        lineup_scoreboard.setStyleSheet("background-color: black;")
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

        self.greg_label = QLabel()
        self.greg_label.setFixedSize(480, 300)
        self.greg_label.setStyleSheet("background-color: black;")
        self.greg_label.setAlignment(Qt.AlignCenter)

        self.greg_page = QWidget()
        greg_layout = QVBoxLayout()
        greg_layout.setContentsMargins(0, 0, 0, 0)
        greg_layout.addWidget(self.greg_label)
        self.greg_page.setLayout(greg_layout)

        self.stack.addWidget(self.greg_page)  # index 2

class CountdownDialog(QDialog):
    def __init__(self, seconds, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 150)
        self.setWindowTitle("Halftime")
        self.setObjectName("HalftimeCountdown")
        self.setModal(False)
        layout = QVBoxLayout(self)
        title = QLabel("Remaining time:")
        title.setStyleSheet("font-size: 20px;")
        self.label = QLabel("--:--")
        self.label.setStyleSheet("font-size: 35px;")
        layout.addWidget(title)
        layout.addWidget(self.label)
        self.seconds = seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self._tick()
        self.timer.start(1000)

    def _tick(self):
        m, s = divmod(max(0, self.seconds), 60)
        self.label.setText(f"{m:02}:{s:02}")
        if self.seconds <= 0:
            self.timer.stop()
            self.accept()
        self.seconds -= 1

class ControlPanel(QWidget):
    def __init__(self, display_window):
        super().__init__()
        self.display = display_window
        self.is_fullscreen = True
        self.vlc_instance = vlc.Instance()
        self.lineup_vlc_instance = vlc.Instance()
        self.lineup_video_player = self.lineup_vlc_instance.media_player_new()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer_running = False
        self.elapsed_seconds = 0

        self.lineup_inputs = []
        self.lineup_index = 0
        self.lineup_files = []
        self.top_video_playlist = []

        self.goal_input = QLineEdit()

        self.image_timer = QTimer()
        self.image_timer.setSingleShot(True)
        self.image_timer.timeout.connect(self.show_next_sponsor)

        self.video_timer = QTimer()
        self.video_timer.setSingleShot(True)
        self.video_timer.timeout.connect(self.show_next_sponsor)

        self.playlist_fullscreen = False
        self.remaining_time = QTime(0, 0, 0)

        self.media_timer = QTimer()
        self.media_timer.timeout.connect(self.update_remaining_time)
        self.time_remaining_label = QLabel("Time remaining: --:--")
        self.time_remaining_label.setStyleSheet("color: red; font-size: 20px; padding: 4px;")

        self.goal_sound = QMediaPlayer()
        self.goal_sound.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(GOAL_SOUND))))
        self.pregame_mixtape = QMediaPlayer()
        self.pregame_mixtape.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(PREGAME_MIXTAPE))))
        self.countdown = QMediaPlayer()
        self.countdown.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(COUNTDOWN))))
        self.proleague_sound = QMediaPlayer()
        self.proleague_sound.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(PROLEAGUE_SOUND))))
        self.initUI()
        self.load_sponsor_folder()
        self.vlc_instance = vlc.Instance()
        for p in [self.goal_sound, self.pregame_mixtape, self.countdown, self.proleague_sound]:
            p.durationChanged.connect(self._update_time_remaining_signal)
            p.positionChanged.connect(self._update_time_remaining_signal)
            p.mediaStatusChanged.connect(self._clear_time_remaining_on_stop)
        self.active_player = None

        self.loop_instance = vlc.Instance()
        self.loop_player = self.loop_instance.media_player_new()
        self.loop_list_player = self.loop_instance.media_list_player_new()
        self.loop_video_path = os.path.join("Media", "default.jpg")
        self.start_loop_video()

        self.sponsor_vlc_instance = vlc.Instance()
        self.sponsor_player = self.sponsor_vlc_instance.media_player_new()

        self.sponsor_em = self.sponsor_player.event_manager()
        self.sponsor_em.event_attach(
            vlc.EventType.MediaPlayerEndReached,
            lambda e: QTimer.singleShot(0, self._on_sponsor_end)
        )
        self.sponsor_em.event_attach(
            vlc.EventType.MediaPlayerEncounteredError,
            lambda e: QTimer.singleShot(0, self._on_sponsor_end)
        )

        self.sponsor_watchdog = QTimer(self)
        self.sponsor_watchdog.setInterval(200)
        self.sponsor_watchdog.timeout.connect(self._sponsor_watchdog_tick)
        self._sp_last_ms = -1
        self._sp_frozen_for = 0

        self.spotify_timer = QTimer(self)
        self.spotify_timer.setInterval(1000)
        self.spotify_timer.timeout.connect(self.update_spotify_remaining)
        self.current_spotify_track_id = None

        self.start_sponsors_loop()

    def create_button(self, text, callback):
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        return btn

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.qmedia_player.stop()
            self.display.video_widget.hide()
            self.display.sponsor_label.show()
            self.show_next_sponsor()

    def _set_active_local_player(self, player: QMediaPlayer):
        self.active_player = player
        self.time_remaining_label.setText("Time remaining: --:--")

    def _update_time_remaining_signal(self, *args):
        player = self.sender()
        if getattr(self, "active_player", None) is not player:
            return
        dur = player.duration()   # ms
        pos = player.position()   # ms
        if dur and dur > 0 and pos >= 0:
            remaining = max(0, (dur - pos) // 1000)
            m, s = divmod(remaining, 60)
            self.time_remaining_label.setText(f"Time remaining: {m:02}:{s:02}")

    def _clear_time_remaining_on_stop(self, status):
        if getattr(self, "active_player", None) is self.sender():
            if status in (QMediaPlayer.EndOfMedia, QMediaPlayer.NoMedia, QMediaPlayer.InvalidMedia):
                self.time_remaining_label.setText("Time remaining: --:--")

    def update_spotify_remaining(self):
        try:
            playback = sp.current_playback()
            if not playback or not playback.get("is_playing") or not playback.get("item"):
                return

            track_id = playback["item"]["id"]

            dur = playback["item"]["duration_ms"] // 1000
            pos = playback["progress_ms"] // 1000
            remaining = max(0, dur - pos)
            m, s = divmod(remaining, 60)
            self.time_remaining_label.setText(f"Time remaining: {m:02}:{s:02}")

            if self.current_spotify_track_id != track_id:
                self.current_spotify_track_id = track_id
                dur = playback["item"]["duration_ms"] // 1000
                remaining = max(0, dur - pos)
                m, s = divmod(remaining, 60)
                self.time_remaining_label.setText(f"Time remaining: {m:02}:{s:02}")

        except Exception:
            pass

    def _stop_all_local_media(self):
        for p in [self.goal_sound, self.pregame_mixtape, self.countdown, self.proleague_sound]:
            try:
                p.stop()
            except Exception:
                pass

    def _play_local_media(self, player: QMediaPlayer):
        self._stop_all_local_media()
        self._set_active_local_player(player)
        player.stop()  # reset positie naar 0
        player.play()


    def start_loop_video(self):
        if not os.path.exists(self.loop_video_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {self.loop_video_path} ")
            return

        screens = QApplication.screens()
        if len(screens) < 3:
            QMessageBox.warning(self, "Screen issue", f"Only {len(screens)} screens connected.")
            return

        screen = screens[ledboarding_display_number]
        geo = screen.geometry()
        if hasattr(self, "loop_window") and self.loop_window:
            self.loop_window.close()

        # Maak venster voor de video
        self.loop_window = QWidget()
        self.loop_window.setGeometry(geo)
        self.loop_window.move(geo.topLeft())
        self.loop_window.setWindowFlags(Qt.FramelessWindowHint)
        self.loop_window.showFullScreen()
        self.loop_window.raise_()
        self.loop_window.activateWindow()
        QApplication.processEvents()

        win_id = int(self.loop_window.winId())
        if sys.platform.startswith("linux"):
            self.loop_player.set_xwindow(win_id)
        else:
            self.loop_player.set_hwnd(win_id)

        # Zet video in een MediaList en activeer loop-modus
        media = self.loop_instance.media_new(self.loop_video_path)
        try:
            media.add_option("input-repeat=-1")  # herhaal oneindig
            media.add_option("no-video-title-show")
        except Exception:
            pass

        media_list = self.loop_instance.media_list_new([self.loop_video_path])
        self.loop_list_player.set_media_list(media_list)
        self.loop_list_player.set_media_player(self.loop_player)
        try:
            self.loop_list_player.set_playback_mode(vlc.PlaybackMode.loop)
        except Exception:
            self.loop_list_player.set_playback_mode(1)  # fallback

        # Events om vastlopers te voorkomen
        em = self.loop_player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerPaused, lambda e: self.loop_player.play())
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError, lambda e: self.loop_list_player.play())

        self.loop_list_player.play()

    def set_loop_video(self, video_path):
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {video_path} ")
            return

        self.loop_video_path = video_path
        media_list = self.loop_instance.media_list_new([video_path])
        self.loop_list_player.set_media_list(media_list)
        try:
            self.loop_list_player.set_playback_mode(vlc.PlaybackMode.loop)
        except Exception:
            self.loop_list_player.set_playback_mode(1)
        self.loop_list_player.play()

    def reset_loop_video(self, video_path):
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {video_path} ")
            return

        self.loop_video_path = video_path
        try:
            self.loop_list_player.stop()
        except Exception:
            try:
                self.loop_player.stop()
            except Exception:
                pass

        if hasattr(self, "loop_window") and self.loop_window:
            self.loop_window.close()
            self.loop_window = None

        self.start_loop_video()

    def initUI(self):
        self.setWindowTitle("Ridepulse System")
        self.move(QApplication.screens()[controlpanel_display_number].geometry().topLeft())
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
                font-size: 18px;
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
        self.team1_name.returnPressed.connect(self.update_scoreboard)

        scoreboard_layout.addWidget(
            self.create_button("Goal Home", lambda: self.add_sporting_goal(self.display.sporting_score)))
        scoreboard_layout.addWidget(
            self.create_button("-1 score", lambda: self.lower_goal(self.display.sporting_score)))

        name2_layout, self.team2_name = labeled_input("Team 2", "")
        scoreboard_layout.addLayout(name2_layout)
        self.team2_name.returnPressed.connect(self.update_scoreboard)

        scoreboard_layout.addWidget(
            self.create_button("Goal Visitors", lambda: self.add_visitor_goal(self.display.visitor_score)))
        scoreboard_layout.addWidget(
            self.create_button("-1 score", lambda: self.lower_goal(self.display.visitor_score)))

        timer_layout, self.timer_input = labeled_input("Timer (MM:SS)", "00:00")
        self.timer_input.returnPressed.connect(self.update_timer_value)
        scoreboard_layout.addLayout(timer_layout)

        self.toggle_timer_btn = QPushButton("Start Match")
        self.toggle_timer_btn.clicked.connect(self.toggle_timer)
        scoreboard_layout.addWidget(self.toggle_timer_btn)
        scoreboard_layout.addWidget(self.create_button("Update Timer", self.update_timer_value))
        scoreboard_layout.addWidget(self.create_button("Reset (1e helft)", self.reset_timer_eerstehelft))
        scoreboard_layout.addWidget(self.create_button("Reset (2e helft)", self.reset_timer_tweedehelft))
        scoreboard_layout.addWidget(QLabel(""))
        scoreboard_layout.addWidget(self.create_button("Add Sponsors", self.add_sponsor_files))
        scoreboard_layout.addWidget(self.create_button("Remove Sponsors", self.remove_sponsor_files))
        scoreboard_layout.addWidget(self.create_button("Start Sponsors", self.start_sponsors_loop))
        scoreboard_layout.addWidget(QLabel(""))
        scoreboard_layout.addWidget(self.create_button("Toggle Fullscreen", self.toggle_fullscreen))
        scoreboard_layout.addWidget(self.create_button("Exit", self.exit_application))

        lineup_layout = QVBoxLayout()
        lineup_layout.setSpacing(10)

        lineup_layout.addWidget(QLabel("Line-up Players"))
        for i in range(13):
            line_input = QLineEdit()
            self.lineup_inputs.append(line_input)
            lineup_layout.addWidget(line_input)
        for i, line_input in enumerate(self.lineup_inputs):
            if i < len(self.lineup_inputs) - 1:
                line_input.returnPressed.connect(self.lineup_inputs[i + 1].setFocus)
            else:
                line_input.returnPressed.connect(self.start_lineup)  #laatste = start

        lineup_layout.addWidget(self.create_button("Start Line-up Sequence", self.start_lineup))
        lineup_layout.addWidget(QLabel("Goal Visual"))
        lineup_layout.addWidget(self.goal_input)
        self.goal_input.returnPressed.connect(self.play_goal_video)

        spotify_layout = QVBoxLayout()
        spotify_layout.setSpacing(10)
        timeupdate_layout = QVBoxLayout()
        timeupdate_layout.setSpacing(10)
        timeupdate_layout.addWidget(QLabel("Starting Time Match"))
        self.match_time_input = QLineEdit("20:00")
        self.match_time_input.returnPressed.connect(self.update_match_time)
        timeupdate_layout.addWidget(self.match_time_input)
        spotify_layout.addLayout(timeupdate_layout)
        spotify_layout.addWidget(QLabel("Audio"))
        btn = self.create_button("T-60' - Start Database Playlist", self.start_playlist_database)
        btn._offset = 60
        btn._desc = "Start Database Playlist"
        spotify_layout.addWidget(btn)

        btn = self.create_button("T-30' - Start Pre-game Playlist (tot I Gotta Feeling)", self.start_playlist_pregame)
        btn._offset = 30
        btn._desc = "Start Pre-game Playlist (tot I Gotta Feeling)"
        spotify_layout.addWidget(btn)

        btn = self.create_button("T-20' - OMROEP: Opstelling tegenstander", self.dummy_button)
        btn._offset = 20
        btn._desc = "OMROEP: Opstelling tegenstander"
        spotify_layout.addWidget(btn)

        btn = self.create_button("T-18' - Start Baila de Gasolina (ATCS)", self.start_baila)
        btn._offset = 18
        btn._desc = "Start Baila de Gasolina (ATCS)"
        spotify_layout.addWidget(btn)

        btn = self.create_button("T-15' - Start 10' Mixtape", self.start_pregame_mixtape)
        btn._offset = 15
        btn._desc = "Start 10' Mixtape"
        spotify_layout.addWidget(btn)

        btn = self.create_button("T-07' - OMROEP: Opstelling Sporting", self.dummy_button)
        btn._offset = 7
        btn._desc = "OMROEP: Opstelling Sporting"
        spotify_layout.addWidget(btn)

        spotify_layout.addWidget(self.create_button("Indien Nodig - Start Synrise (07:35)", self.start_synrise))
        spotify_layout.addWidget(QLabel(""))
        btn = self.create_button("T-5' - Start Countdown (na signaal steward)", self.start_countdown)
        btn._offset = 5
        btn._desc = "Start Countdown (na signaal steward)"
        spotify_layout.addWidget(btn)

        btn = self.create_button("T-2' - Play Pro League Hymne", self.play_proleague_hymne)
        btn._offset = 2
        btn._desc = "Play Pro League Hymne"
        spotify_layout.addWidget(btn)
        spotify_layout.addWidget(QLabel(""))
        spotify_layout.addWidget(self.create_button("Start Half-Time playlist", self.start_playlist_halftime))
        spotify_layout.addWidget(self.create_button("Start Playlist Winst", self.start_playlist_winst))
        spotify_layout.addWidget(self.create_button("Start Playlist Gelijkspel (Database)", self.start_playlist_database))
        spotify_layout.addWidget(self.create_button("Start Playlist Verlies", self.start_playlist_verlies))
        spotify_layout.addWidget(self.create_button("MUZIEK UIT BIJ SPIONKOP", self.dummy_button))
        spotify_layout.addWidget(self.create_button("Start EUROMIR", self.start_euromir))

        loop_video_layout = QVBoxLayout()
        loop_video_layout.setSpacing(10)
        loop_video_layout.addWidget(self.time_remaining_label)
        loop_video_layout.addWidget(QLabel("Local Audio Controls"))
        loop_video_layout.addWidget(self.create_button("Stop All Local Media", self.stop_all_local_media))
        loop_video_layout.addWidget(QLabel("Spotify Controls"))
        loop_video_layout.addWidget(self.create_button("Pause Spotify", self.pause_spotify))
        loop_video_layout.addWidget(self.create_button("Resume Spotify", self.play_spotify))
        loop_video_layout.addWidget(self.create_button("Next Spotify Song", self.spotify_next))
        loop_video_layout.addWidget(self.create_button("Previous Spotify Song", self.spotify_previous))
        loop_video_layout.addWidget(QLabel("Other Software"))
        loop_video_layout.addWidget(self.create_button("Open Spotify", self.open_spotify_app))
        loop_video_layout.addWidget(self.create_button("Open LedSet", self.open_ledset_app))
        loop_video_layout.addWidget(self.create_button("Render New Loop", self.run_rendering))
        loop_video_layout.addWidget(QLabel("Loop Video (3e scherm)"))
        loop_video_layout.addWidget(self.create_button("Toon Main", lambda: self.set_loop_video("Main.mp4")))
        loop_video_layout.addWidget(self.create_button("Toon Gameday", lambda: self.set_loop_video("Gameday.mp4")))
        loop_video_layout.addWidget(self.create_button("Reset boarding", lambda: self.reset_loop_video(os.path.join("Media", "default.jpg"))))

        main_layout.addLayout(scoreboard_layout, 1)
        main_layout.addLayout(lineup_layout, 1)
        main_layout.addLayout(spotify_layout, 1)
        main_layout.addLayout(loop_video_layout, 1)

        self.setLayout(main_layout)

    def run_rendering(self):
        try:
            script_path = os.path.join(os.path.dirname(__file__), "Rendering Boarding", "rendering.py")

            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Kon rendering.py niet starten:\n{e}")

    def open_match_time_dialog(self):
        dlg = MatchTimeDialog(self.match_time_input.text(), self)
        if dlg.exec_() == QDialog.Accepted:
            self.match_time_input.setText(dlg.get_time())
            self.update_match_time()

    def update_match_time(self):
        text = self.match_time_input.text().strip()
        try:
            start_time = QTime.fromString(text, "HH:mm")
            if not start_time.isValid():
                raise ValueError

            for btn in self.findChildren(QPushButton):
                if hasattr(btn, "_offset") and hasattr(btn, "_desc"):
                    offset = btn._offset
                    new_time = start_time.addSecs(-offset * 60)
                    btn.setText(new_time.toString("HH:mm") + " - " + btn._desc)

        except Exception:
            QMessageBox.critical(self, "Invalid Format", "Please enter HH:MM")


    def play_with_timer(self, player):
        player.stop()
        player.play()
        duration = player.duration()
        if duration <= 0:
            QTimer.singleShot(200, lambda: self.start_media_timer(player))
        else:
            self.start_media_timer(player)

    def start_media_timer(self, player):
        duration = player.duration()
        if duration > 0:
            self.remaining_ms = duration
            self.media_timer.start(1000)
            self.active_player = player

    def update_remaining_time(self):
        if not hasattr(self, "active_player"):
            return
        pos = self.active_player.position()
        dur = self.active_player.duration()
        if dur > 0:
            remaining = max(0, (dur - pos) // 1000)
            minutes, seconds = divmod(remaining, 60)
            self.time_remaining_label.setText(f"Time remaining: {minutes:02}:{seconds:02}")
        if pos >= dur:
            self.media_timer.stop()
            self.time_remaining_label.setText("Time remaining: --:--")

    def stop_all_local_media(self):
        for player in [self.goal_sound, self.pregame_mixtape, self.countdown, self.proleague_sound]:
            player.stop()
        self.media_timer.stop()
        self.time_remaining_label.setText("Time remaining: --:--")

    def open_spotify_app(self):
        try:
            subprocess.Popen(["spotify"])
        except FileNotFoundError:
            QMessageBox.critical(self, "Fout", "Spotify kon niet worden gevonden vanuit de Microsoft Store.")

        mogelijk_paden = [
            r"C:\\Users\\Ridepulse\\AppData\\Roaming\\Spotify\\Spotify.exe",
        ]
        for pad in mogelijk_paden:
            if os.path.exists(pad):
                try:
                    subprocess.Popen([pad])
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not open Spotify in AppData:\n{e}")
                    return

    def open_ledset_app(self):
        mogelijk_paden = [
            r"C:\\Program Files\\Linsn\\LedSet\\LedSet.exe",
        ]
        for pad in mogelijk_paden:
            if os.path.exists(pad):
                try:
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", pad, None, None, 1)
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not open LedSet as Administrator:\n{e}")
                    return
        QMessageBox.critical(self, "Error", "LedSet.exe was not found.")

    def add_sponsor_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Choose sponsors to add", "",
                                                "Media Files (*.jpg *.jpeg *.png *.mp4 *.avi *.mov)")
        if not files:
            return

        sponsor_folder = os.path.join(os.getcwd(), "Scorebord")
        if not os.path.exists(sponsor_folder):
            os.makedirs(sponsor_folder)

        copied = 0
        for file_path in files:
            try:
                filename = os.path.basename(file_path)
                target_path = os.path.join(sponsor_folder, filename)
                if not os.path.exists(target_path):
                    with open(file_path, "rb") as src, open(target_path, "wb") as dst:
                        dst.write(src.read())
                    copied += 1
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add {file_path} to the sponsor loop.:\n{str(e)}")

        self.start_sponsors_loop()

        QMessageBox.information(
            self,
            "Sponsors added",
            f"{copied} sponsorbestand{'en' if copied != 1 else ''} toegevoegd aan de map 'Scorebord'."
        )

    def remove_sponsor_files(self):
        folder = os.path.join(os.getcwd(), "Scorebord")
        archive_folder = os.path.join(os.getcwd(), "Scorebord_archive")

        if not os.path.exists(folder):
            QMessageBox.information(self, "Could not find", "Could not find the folder 'Scorebord'.")
            return

        if not os.path.exists(archive_folder):
            os.makedirs(archive_folder)

        files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mov"))]
        if not files:
            QMessageBox.information(self, "Could not find", "No sponsor files found.")
            return

        full_paths = [os.path.join(folder, f) for f in files]
        selected_files, _ = QFileDialog.getOpenFileNames(self, "Choose sponsors to remove", folder,
                                                         "Media Files (*.jpg *.jpeg *.png *.mp4 *.avi *.mov)")
        if not selected_files:
            return

        for source_path in selected_files:
            filename = os.path.basename(source_path)
            name, ext = os.path.splitext(filename)
            dest_path = os.path.join(archive_folder, filename)
            index = 1

            while os.path.exists(dest_path):
                dest_path = os.path.join(archive_folder, f"{name}({index}){ext}")
                index += 1

            try:
                os.rename(source_path, dest_path)
            except Exception as e:
                QMessageBox.critical(self, "Fout", f"Could not remove {filename}:\n{str(e)}")

        self.start_sponsors_loop()

        QMessageBox.information(self, "Sponsors successfully removed",
                                f"{len(selected_files)} sponsors are successfully removed and they are archived to 'Scorebord_archive'")

    def dummy_button(self):
        print("Dummy button hihi")

    def start_pregame_mixtape(self):
        playback = sp.current_playback()
        if playback and playback["is_playing"]:
            sp.pause_playback(device_id=device_id)
        else:
            pass
        self._play_local_media(self.pregame_mixtape)

    def start_countdown(self):
        self.pregame_mixtape.stop()
        playback = sp.current_playback()
        if playback and playback["is_playing"]:
            sp.pause_playback(device_id=device_id)
        else:
            pass
        self._play_local_media(self.countdown)

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
        self.spotify_timer.stop()
        self.current_spotify_track_id = None

    def play_spotify(self):
        playback = sp.current_playback()
        if playback and playback["is_playing"]:
            QMessageBox.warning(self, "Spotify", "Spotify is already playing.")
        else:
            sp.start_playback(device_id=device_id)
            self.spotify_timer.start()

    def start_baila(self, name):
        PLAYLIST_URI = "https://open.spotify.com/album/2ojXXfh1QKhimrvz4wt97G"
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)
        self.current_spotify_track_id = None
        self.spotify_timer.start()

    def start_euromir(self, name):
        PLAYLIST_URI = "https://open.spotify.com/album/1PrgiMlNc0fBtW0U9TdQFj"
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI, offset={"position": 1})
        self.current_spotify_track_id = None
        self.spotify_timer.start()

    def start_playlist_database(self):
        PLAYLIST_URI = DATABASE_URL
        sp.shuffle(state=True, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)
        self.current_spotify_track_id = None
        self.spotify_timer.start()

    def start_playlist_halftime(self):
        PLAYLIST_URI = HALFTIME_URL
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)
        self.current_spotify_track_id = None
        self.spotify_timer.start()
        self.halftime_dialog = CountdownDialog(15 * 60, self)
        self.halftime_dialog.show()

    def start_playlist_pregame(self):
        PLAYLIST_URI = PREGAME_URL
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)
        self.current_spotify_track_id = None
        self.spotify_timer.start()

    def start_synrise(self):
        self.pregame_mixtape.stop()
        PLAYLIST_URI = PREGAME_URL
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI, offset={"position": 4})
        self.current_spotify_track_id = None
        self.spotify_timer.start()

    def start_playlist_winst(self):
        PLAYLIST_URI = WIN_URL
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)
        self.current_spotify_track_id = None
        self.spotify_timer.start()

    def start_playlist_verlies(self):
        PLAYLIST_URI = LOSE_URL
        sp.shuffle(state=False, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)
        self.current_spotify_track_id = None
        self.spotify_timer.start()

    def exit_application(self):
        screens = QApplication.screens()
        if len(screens) >= 3:
            self.loop_window.close()
        self.display.close()
        self.close()
        QApplication.quit()

    def toggle_loop(self):
        self.loop_checkbox.setText("Loop AAN" if self.loop_checkbox.isChecked() else "Loop UIT")

    def toggle_fullscreen_playlist(self):
        self.playlist_fullscreen = self.fullscreen_checkbox.isChecked()
        if self.playlist_fullscreen:
            self.fullscreen_checkbox.setText("Fullscreen")
        else:
            self.fullscreen_checkbox.setText("Scorebord is visible")

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
        self._play_local_media(self.goal_sound)
        #self.goal_sound.stop()  # Ensures it replays properly
        #self.goal_sound.play()

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
            self.toggle_timer_btn.setText("Start Match")
        else:
            self.timer.start(1000)
            self.toggle_timer_btn.setText("Stop Match")
        self.timer_running = not self.timer_running

    def reset_timer_eerstehelft(self):
        self.timer.stop()
        self.toggle_timer_btn.setText("Start Match")
        self.timer_running = not self.timer_running
        self.elapsed_seconds = 0
        self.display.timer_label.setText("00:00")
        self.display.top_timer_label.setText("00:00")
        self.display.top2_timer_label.setText("00:00")

    def reset_timer_tweedehelft(self):
        self.timer.stop()
        self.toggle_timer_btn.setText("Start Match")
        self.timer_running = not self.timer_running
        self.elapsed_seconds = 45 * 60
        self.display.timer_label.setText("45:00")
        self.display.top_timer_label.setText("45:00")
        self.display.top2_timer_label.setText("45:00")

    def update_timer(self):
        self.elapsed_seconds += 1
        minutes, seconds = divmod(self.elapsed_seconds, 60)
        if self.elapsed_seconds == 240 and show_greg:
            self.show_greg_visual()

        self.display.timer_label.setText(f"{minutes:02}:{seconds:02}")
        self.display.top_timer_label.setText(f"{minutes:02}:{seconds:02}")
        self.display.top2_timer_label.setText(f"{minutes:02}:{seconds:02}")

    def show_greg_visual(self):
        image_path = os.path.join("Media", "greg.png")
        if not os.path.exists(image_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {image_path}")
            return

        self.display.greg_label.setPixmap(QPixmap(image_path).scaled(
            self.display.greg_label.size(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        ))

        self.display.stack.setCurrentIndex(2)
        QTimer.singleShot(60000, self.hide_greg_visual)

    def hide_greg_visual(self):
        self.display.greg_label.clear()
        self.display.stack.setCurrentIndex(0)


    def hide_lineup_visual(self):
        self.display.lineup_label.clear()
        self.display.lineup_label.hide()
        self.display.stack.setCurrentIndex(0)

    def update_timer_value(self):
        self.timer.stop()
        self.toggle_timer_btn.setText("Start Match")
        if self.timer_running == True:
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

    def start_sponsors_loop(self):

        try:
            self.image_timer.stop()
        except Exception:
            pass
        try:
            self.video_timer.stop()
        except Exception:
            pass
        try:
            self.qmedia_player.stop()
        except Exception:
            pass
        try:
            self.sponsor_watchdog.stop()
        except Exception:
            pass
        try:
            self.sponsor_player.stop()
        except Exception:
            pass

        folder_path = "Scorebord"
        if not os.path.isdir(folder_path):
            return

        self.sponsor_files = [
            os.path.join(folder_path, f) for f in sorted(os.listdir(folder_path))
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mov"))
        ]
        if not self.sponsor_files:
            return

        self.sponsor_index = 0
        self.show_next_sponsor()

    def show_next_sponsor(self):
        if not getattr(self, "sponsor_files", None):
            return

        file_path = self.sponsor_files[self.sponsor_index]
        self.sponsor_index = (self.sponsor_index + 1) % len(self.sponsor_files)
        ext = os.path.splitext(file_path)[1].lower()
        abs_path = os.path.abspath(file_path)

        if ext in [".png", ".jpg", ".jpeg"]:
            try:
                self.sponsor_watchdog.stop()
                self.sponsor_player.stop()
            except Exception:
                pass
            self.display.video_widget.hide()
            self.display.sponsor_label.show()
            pixmap = QPixmap(abs_path).scaled(
                self.display.sponsor_label.width(),
                self.display.sponsor_label.height(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            self.display.sponsor_label.setPixmap(pixmap)
            self.image_timer.start(sponsor_duration)
            return

        self.display.sponsor_label.hide()
        self.display.video_widget.show()
        self._start_sponsor_video(abs_path)

    def _start_sponsor_video(self, abs_path):
        try:
            self.sponsor_watchdog.stop()
            self.sponsor_player.stop()
        except Exception:
            pass

        self.display.sponsor_label.hide()
        self.display.video_widget.show()

        win_id = int(self.display.video_widget.winId())
        if sys.platform.startswith("linux"):
            self.sponsor_player.set_xwindow(win_id)
        else:
            self.sponsor_player.set_hwnd(win_id)

        media = self.sponsor_vlc_instance.media_new(abs_path)
        try:
            media.add_option(":no-video-title-show")
            media.add_option(":file-caching=300")
        except Exception:
            pass

        self.sponsor_player.set_media(media)
        self.sponsor_player.audio_set_mute(True)
        self._sp_last_ms = -1
        self._sp_frozen_for = 0
        self.sponsor_player.play()
        QTimer.singleShot(50, self._arm_sponsor_watchdog)

    def _arm_sponsor_watchdog(self):
        self._sp_last_ms = -1
        self._sp_frozen_for = 0
        self.sponsor_watchdog.start()

    def _disarm_sponsor_watchdog(self):
        try:
            self.sponsor_watchdog.stop()
        except Exception:
            pass
        self._sp_last_ms = -1
        self._sp_frozen_for = 0

    def _sponsor_watchdog_tick(self):
        try:
            length = self.sponsor_player.get_length()
            cur = self.sponsor_player.get_time()
            playing = self.sponsor_player.is_playing()
        except Exception:
            self._on_sponsor_end()
            return

        if length and length > 0 and cur and cur >= (length - 200):
            self._on_sponsor_end()
            return

        if playing:
            if cur == self._sp_last_ms:
                self._sp_frozen_for += self.sponsor_watchdog.interval()
                if self._sp_frozen_for >= 1000 and cur > 0:
                    self._on_sponsor_end()
                    return
            else:
                self._sp_last_ms = cur
                self._sp_frozen_for = 0
        else:
            if length and length > 0 and cur and cur >= (length - 200):
                self._on_sponsor_end()
                return

    def _on_sponsor_end(self):
        self._disarm_sponsor_watchdog()
        try:
            self.sponsor_player.stop()
        except Exception:
            pass
        QTimer.singleShot(10, self.show_next_sponsor)

    def start_video_timer(self):
        duration = self.media_player.get_length()
        if duration <= 0:
            duration = 1000
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
        self.display.lineup_label.clear()
        self.display.lineup_label.show()

        if sys.platform.startswith("linux"):
            self.lineup_video_player.set_xwindow(int(self.display.lineup_label.winId()))
        else:
            self.lineup_video_player.set_hwnd(int(self.display.lineup_label.winId()))
        self.play_next_lineup_video()

    def play_next_lineup_video(self):
        if self.lineup_index >= len(self.lineup_files):
            self.hide_lineup_visual()
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
        self.lineup_video_player.audio_set_mute(True)
        self.lineup_video_player.play()
        self.display.stack.setCurrentIndex(1)

        def check_duration_and_queue_next():
            duration = self.lineup_video_player.get_length()
            if duration > 0:
                QTimer.singleShot(duration, self.play_next_lineup_video)
                self.lineup_index += 1
            else:
                QTimer.singleShot(10, check_duration_and_queue_next)

        QTimer.singleShot(10, check_duration_and_queue_next)

    def play_proleague_hymne(self):
        playback = sp.current_playback()
        if playback and playback["is_playing"]:
            sp.pause_playback(device_id=device_id)
        else:
            pass
        self._play_local_media(self.proleague_sound)

    def play_goal_video(self):
        filename = self.goal_input.text().strip()
        if not filename:
            QMessageBox.warning(self, "No Input", "Please add a player number in the input field.")
            return

        video_path = os.path.join(os.getcwd(), video_path_goal, filename + ".mp4")
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "File not found", f"Could not find: {video_path}")
            return

        self.play_single_video(video_path)

    def play_single_video(self, video_path):
        self.display.lineup_label.show()

        if sys.platform.startswith("linux"):
            self.lineup_video_player.set_xwindow(int(self.display.lineup_label.winId()))
        else:
            self.lineup_video_player.set_hwnd(int(self.display.lineup_label.winId()))

        media = self.lineup_vlc_instance.media_new(video_path)
        self.lineup_video_player.set_media(media)
        self.lineup_video_player.audio_set_mute(True)
        self.lineup_video_player.play()
        QTimer.singleShot(100, lambda: self.display.stack.setCurrentIndex(1))


        def check_end():
            if not self.lineup_video_player.is_playing():
                self.display.stack.setCurrentIndex(0)
                self.lineup_video_player.stop()
                self.display.lineup_label.hide()
            else:
                QTimer.singleShot(300, check_end)

        QTimer.singleShot(500, check_end)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    display = ScoreboardDisplay()
    panel = ControlPanel(display)
    panel.update_match_time()
    display.show()
    panel.show()
    sys.exit(app.exec_())
