# led_direct_play.py
"""
Direct LED Board Playback - Plays sponsor videos directly on the LED screen
No pre-rendering needed - videos play in their correct positions in real-time
"""

import sys
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional
import time

import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QSplitter, QGroupBox, QComboBox, QCheckBox,
    QLineEdit, QGridLayout, QSlider
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QRect
)
from PyQt5.QtGui import (
    QImage, QPainter, QColor, QFont, QPixmap
)


# ============================================================================
# LAYOUT DEFINITION - Exact match to rendering.py
# ============================================================================

def create_brickwall_layout(total_width: int = 2048) -> Dict[str, Dict]:
    """
    Creates the brick-wall layout from rendering.py
    Returns a dict with region info: position, size, and which part of the screen it covers
    """

    # Layout from rendering.py
    layout_rows = [
        [(1200, 96), (768, 96), (768, 96)],  # Row 0
        [(1056, 96), (768, 96)],  # Row 1
        [(768, 96), (576, 96)],  # Row 2
        [(960, 96), (960, 96), (960, 96)],  # Row 3
        [(960, 96), (960, 96)],  # Row 4
        [(960, 96), (960, 96)],  # Row 5
        [(960, 96), (960, 96)],  # Row 6
        [(960, 96)],  # Row 7
        [(864, 96), (1008, 96), (1008, 96)],  # Row 8
        [(1008, 96), (1008, 96)],  # Row 9
        [(1056, 96)]  # Row 10
    ]

    # Row offsets from rendering.py
    row_offsets = {
        0: 0, 1: 720, 2: 528, 3: 0, 4: 864,
        5: 768, 6: 672, 7: 576, 8: 0, 9: 864, 10: 864
    }

    regions = {}
    right_margin = 32
    row_heights = [max(h for _, h in row) for row in layout_rows]

    for row_idx, row_modules in enumerate(layout_rows):
        row_y = sum(row_heights[:row_idx])
        x_offset = row_offsets.get(row_idx, 0)
        curr_x = x_offset
        curr_row = row_idx
        curr_y = row_y

        for module_idx, (module_w, module_h) in enumerate(row_modules):
            remaining_w = module_w
            chunk_idx = 0

            while remaining_w > 0:
                available_w = (total_width - right_margin) - curr_x

                if available_w <= 0:
                    curr_row += 1
                    if curr_row < len(row_heights):
                        curr_y = sum(row_heights[:curr_row])
                    else:
                        curr_y += row_heights[curr_row - 1] if curr_row > 0 else 0
                    curr_x = 0
                    continue

                place_w = min(remaining_w, available_w)
                region_id = f"{row_idx}_{module_idx}_{chunk_idx}"

                regions[region_id] = {
                    'x': curr_x,
                    'y': curr_y,
                    'width': place_w,
                    'height': module_h,
                    'row': curr_row,
                    'col': module_idx,
                    'chunk': chunk_idx,
                    'original_width': module_w,
                    'original_height': module_h
                }

                curr_x += place_w
                remaining_w -= place_w
                chunk_idx += 1

                if curr_x >= total_width - right_margin:
                    curr_row += 1
                    if curr_row < len(row_heights):
                        curr_y = sum(row_heights[:curr_row])
                    else:
                        curr_y += row_heights[curr_row - 1] if curr_row > 0 else 0
                    curr_x = 0

    return regions


# ============================================================================
# VIDEO PLAYER - Plays videos in a region using OpenCV
# ============================================================================

class VideoRegionPlayer(QObject):
    """Plays a video in a specific screen region"""

    frame_ready = pyqtSignal(np.ndarray, str)

    def __init__(self, region_id: str, region_info: Dict):
        super().__init__()
        self.region_id = region_id
        self.region_info = region_info
        self.width = region_info['width']
        self.height = region_info['height']
        self.x = region_info['x']
        self.y = region_info['y']

        self.video_path: Optional[str] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_playing = False
        self.fps = 30
        self.total_frames = 0
        self.current_frame = 0
        self.frame_delay = 33  # ms
        self._frame_buffer: Optional[np.ndarray] = None
        self._lock = threading.Lock()

        # Placeholder frame
        self._create_placeholder()

        # Timer for video playback
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(self.frame_delay)

    def _create_placeholder(self):
        """Create a placeholder frame with region info"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Color based on region
        color = (hash(self.region_id) % 255,
                 (hash(self.region_id) * 7) % 255,
                 (hash(self.region_id) * 13) % 255)
        frame[:] = color

        # Add text
        cv2.putText(frame, self.region_id, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(frame, f"{self.width}x{self.height}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (200, 200, 200), 1)

        with self._lock:
            self._frame_buffer = frame

    def load_video(self, video_path: str) -> bool:
        """Load a video file"""
        if not os.path.exists(video_path):
            return False

        # Close existing video
        if self.cap:
            self.cap.release()

        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            self.cap = None
            return False

        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        self.frame_delay = int(1000 / self.fps)
        self.timer.setInterval(self.frame_delay)

        return True

    def play(self):
        """Start playback"""
        self.is_playing = True
        if self.cap:
            self.timer.start()

    def pause(self):
        """Pause playback"""
        self.is_playing = False
        self.timer.stop()

    def stop(self):
        """Stop playback"""
        self.is_playing = False
        self.timer.stop()
        self.current_frame = 0
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def _update_frame(self):
        """Update the current frame"""
        if not self.is_playing or not self.cap:
            return

        ret, frame = self.cap.read()

        if not ret:
            # Loop video
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

            if not ret:
                return

        # Resize frame to fit region
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))

        with self._lock:
            self._frame_buffer = frame

        self.frame_ready.emit(frame, self.region_id)

    def get_frame(self) -> Optional[np.ndarray]:
        """Get the current frame"""
        with self._lock:
            return self._frame_buffer.copy() if self._frame_buffer is not None else None

    def release(self):
        """Release resources"""
        if self.cap:
            self.cap.release()
            self.cap = None


# ============================================================================
# LED COMPOSITOR - Combines all regions into final display
# ============================================================================

class LEDCompositor(QWidget):
    """Combines all region videos into the final LED display"""

    def __init__(self, total_width=2048, total_height=1152):
        super().__init__()
        self.total_width = total_width
        self.total_height = total_height

        # Setup window for LED screen
        self.setWindowTitle("LED Board - Direct Play")
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Move to 3rd screen (index 2)
        screens = QApplication.screens()
        if len(screens) > 2:
            screen = screens[2]
            self.setGeometry(screen.geometry())
            self.showFullScreen()
        else:
            self.setGeometry(0, 0, total_width, total_height)

        self.setStyleSheet("background-color: black;")

        # Create layout
        self.regions = create_brickwall_layout(total_width)
        self.players: Dict[str, VideoRegionPlayer] = {}
        self._frame_buffer: Optional[np.ndarray] = None
        self._lock = threading.Lock()

        # Create players for each region
        for region_id, info in self.regions.items():
            player = VideoRegionPlayer(region_id, info)
            player.frame_ready.connect(self._on_frame_ready)
            self.players[region_id] = player

        # Timer for compositing
        self.composite_timer = QTimer()
        self.composite_timer.timeout.connect(self._composite)
        self.composite_timer.start(16)  # ~60fps

        # Create canvas
        self.canvas = np.zeros((total_height, total_width, 3), dtype=np.uint8)

        print(f"Initialized {len(self.players)} regions on LED screen")

    def _on_frame_ready(self, frame: np.ndarray, region_id: str):
        """Handle frame update from a region player"""
        pass  # Frames are stored in the player

    def _composite(self):
        """Composite all region frames"""
        # Clear canvas
        self.canvas[:] = (0, 0, 0)

        # Draw each region
        for region_id, player in self.players.items():
            frame = player.get_frame()
            if frame is not None:
                info = self.regions[region_id]
                try:
                    self.canvas[info['y']:info['y'] + info['height'],
                    info['x']:info['x'] + info['width']] = frame
                except Exception as e:
                    pass

        # Update display
        self.update()

    def paintEvent(self, event):
        """Paint the composited frame"""
        painter = QPainter(self)

        # Convert canvas to QImage
        h, w, ch = self.canvas.shape
        bytes_per_line = ch * w
        qimage = QImage(self.canvas.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # Scale to fit widget
        scaled = qimage.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Center
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2

        painter.drawImage(x, y, scaled)

    def load_video_to_region(self, region_id: str, video_path: str) -> bool:
        """Load a video to a specific region"""
        if region_id in self.players:
            return self.players[region_id].load_video(video_path)
        return False

    def play_all(self):
        """Play all regions"""
        for player in self.players.values():
            player.play()

    def pause_all(self):
        """Pause all regions"""
        for player in self.players.values():
            player.pause()

    def stop_all(self):
        """Stop all regions"""
        for player in self.players.values():
            player.stop()


# ============================================================================
# CONTROL PANEL
# ============================================================================

class ControlPanel(QMainWindow):
    """Control panel for the LED display"""

    def __init__(self, compositor: LEDCompositor):
        super().__init__()
        self.compositor = compositor
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("LED Control Panel")
        self.setGeometry(100, 100, 500, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Title
        title = QLabel("🎯 LED Board Direct Play")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Region selector
        region_layout = QHBoxLayout()
        region_layout.addWidget(QLabel("Region:"))
        self.region_combo = QComboBox()
        for region_id in sorted(self.compositor.regions.keys()):
            info = self.compositor.regions[region_id]
            self.region_combo.addItem(
                f"{region_id} ({info['width']}x{info['height']})",
                region_id
            )
        region_layout.addWidget(self.region_combo)
        layout.addLayout(region_layout)

        # Region info
        self.region_info = QLabel("x: 0, y: 0, w: 0, h: 0")
        self.region_info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.region_info)

        # Update region info on selection
        self.region_combo.currentIndexChanged.connect(self._update_region_info)
        self._update_region_info()

        # Playback controls
        controls_group = QGroupBox("Playback Controls")
        controls_layout = QHBoxLayout(controls_group)

        self.play_all_btn = QPushButton("▶ Play All")
        self.play_all_btn.clicked.connect(self.compositor.play_all)
        controls_layout.addWidget(self.play_all_btn)

        self.pause_all_btn = QPushButton("⏸ Pause All")
        self.pause_all_btn.clicked.connect(self.compositor.pause_all)
        controls_layout.addWidget(self.pause_all_btn)

        self.stop_all_btn = QPushButton("⏹ Stop All")
        self.stop_all_btn.clicked.connect(self.compositor.stop_all)
        controls_layout.addWidget(self.stop_all_btn)

        layout.addWidget(controls_group)

        # Video loading
        load_group = QGroupBox("Load Video to Region")
        load_layout = QVBoxLayout(load_group)

        self.load_btn = QPushButton("📁 Load Video")
        self.load_btn.clicked.connect(self._load_video)
        load_layout.addWidget(self.load_btn)

        self.current_video_label = QLabel("No video loaded")
        self.current_video_label.setStyleSheet("color: #888; font-size: 11px;")
        load_layout.addWidget(self.current_video_label)

        layout.addWidget(load_group)

        # Playlist
        playlist_group = QGroupBox("Playlist")
        playlist_layout = QVBoxLayout(playlist_group)

        self.playlist = QListWidget()
        self.playlist.itemDoubleClicked.connect(self._play_playlist_item)
        playlist_layout.addWidget(self.playlist)

        playlist_btns = QHBoxLayout()
        self.add_playlist_btn = QPushButton("Add Files")
        self.add_playlist_btn.clicked.connect(self._add_to_playlist)
        self.clear_playlist_btn = QPushButton("Clear")
        self.clear_playlist_btn.clicked.connect(self.playlist.clear)
        playlist_btns.addWidget(self.add_playlist_btn)
        playlist_btns.addWidget(self.clear_playlist_btn)
        playlist_layout.addLayout(playlist_btns)

        layout.addWidget(playlist_group)

        # Status
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #0f0; font-weight: bold;")
        layout.addWidget(self.status_label)

        # Set initial status
        self._update_region_info()

    def _update_region_info(self):
        """Update region info display"""
        region_id = self.region_combo.currentData()
        if region_id in self.compositor.regions:
            info = self.compositor.regions[region_id]
            self.region_info.setText(
                f"x: {info['x']}, y: {info['y']}, "
                f"w: {info['width']}, h: {info['height']}"
            )

    def _load_video(self):
        """Load a video to the selected region"""
        region_id = self.region_combo.currentData()

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm)"
        )

        if file_path:
            if self.compositor.load_video_to_region(region_id, file_path):
                self.current_video_label.setText(f"Loaded: {os.path.basename(file_path)}")
                self.status_label.setText(f"Status: Video loaded to {region_id}")
                # Auto-play
                self.compositor.players[region_id].play()
            else:
                QMessageBox.warning(self, "Error", "Failed to load video")

    def _add_to_playlist(self):
        """Add files to playlist"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Videos",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm)"
        )

        for file_path in files:
            item = QListWidgetItem(os.path.basename(file_path))
            item.setData(Qt.UserRole, file_path)
            self.playlist.addItem(item)

    def _play_playlist_item(self, item: QListWidgetItem):
        """Play a playlist item on the selected region"""
        region_id = self.region_combo.currentData()
        file_path = item.data(Qt.UserRole)

        if self.compositor.load_video_to_region(region_id, file_path):
            self.current_video_label.setText(f"Playing: {os.path.basename(file_path)}")
            self.status_label.setText(f"Status: Playing {region_id}")
            self.compositor.players[region_id].play()
        else:
            QMessageBox.warning(self, "Error", "Failed to load video")


# ============================================================================
# MAIN
# ============================================================================

def main():
    app = QApplication(sys.argv)

    # Create the LED compositor (on 3rd screen)
    compositor = LEDCompositor()
    compositor.show()

    # Create control panel
    control = ControlPanel(compositor)
    control.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()