# led_direct_play.py - FIXED VERSION
"""
Direct LED Board Playback - Plays sponsor videos directly on the LED screen
Handles brick-wall layout where a single sponsor box is split across multiple rows
"""

import sys
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import json

import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QSplitter, QGroupBox, QComboBox, QCheckBox,
    QLineEdit, QGridLayout, QSlider, QTabWidget
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QRect
)
from PyQt5.QtGui import (
    QImage, QPainter, QColor, QFont, QPixmap
)


# ============================================================================
# LAYOUT DEFINITION - Exact match to rendering.py with box grouping
# ============================================================================

class LayoutManager:
    """Manages the brick-wall layout and maps sponsor boxes to screen regions"""

    def __init__(self, total_width: int = 2048):
        self.total_width = total_width
        self.right_margin = 32

        # Layout from rendering.py
        self.layout_rows = [
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
        self.row_offsets = {
            0: 0, 1: 720, 2: 528, 3: 0, 4: 864,
            5: 768, 6: 672, 7: 576, 8: 0, 9: 864, 10: 864
        }

        # Calculate row heights
        self.row_heights = [max(h for _, h in row) for row in self.layout_rows]

        # Build the layout
        self.boxes: Dict[int, Dict] = {}  # box_id -> {width, height, chunks: [{row, x, y, width}]}
        self.regions: Dict[str, Dict] = {}  # region_key -> {box_id, x, y, width, height, row}
        self.box_to_regions: Dict[int, List[str]] = {}  # box_id -> [region_keys]

        self._build_layout()

    def _build_layout(self):
        """Build the brick-wall layout with box grouping"""
        box_id = 0

        for row_idx, row_modules in enumerate(self.layout_rows):
            row_y = sum(self.row_heights[:row_idx])
            x_offset = self.row_offsets.get(row_idx, 0)
            curr_x = x_offset
            curr_row = row_idx
            curr_y = row_y

            for module_idx, (module_w, module_h) in enumerate(row_modules):
                remaining_w = module_w
                chunk_idx = 0
                chunks = []
                box_id += 1

                # Track the starting row for this box
                start_row = curr_row
                box_start_x = curr_x

                while remaining_w > 0:
                    available_w = (self.total_width - self.right_margin) - curr_x

                    if available_w <= 0:
                        curr_row += 1
                        if curr_row < len(self.row_heights):
                            curr_y = sum(self.row_heights[:curr_row])
                        else:
                            curr_y += self.row_heights[curr_row - 1] if curr_row > 0 else 0
                        curr_x = 0
                        continue

                    place_w = min(remaining_w, available_w)

                    # Create region for this chunk
                    region_key = f"r{curr_row}_m{module_idx}_c{chunk_idx}"
                    region_info = {
                        'box_id': box_id,
                        'x': curr_x,
                        'y': curr_y,
                        'width': place_w,
                        'height': module_h,
                        'row': curr_row,
                        'col': module_idx,
                        'chunk': chunk_idx,
                        'offset_x': curr_x - box_start_x  # Position within the full box
                    }
                    self.regions[region_key] = region_info

                    # Add to box's chunks
                    chunks.append({
                        'row': curr_row,
                        'x': curr_x,
                        'y': curr_y,
                        'width': place_w,
                        'height': module_h,
                        'region_key': region_key,
                        'offset_x': curr_x - box_start_x
                    })

                    curr_x += place_w
                    remaining_w -= place_w
                    chunk_idx += 1

                    if curr_x >= self.total_width - self.right_margin:
                        curr_row += 1
                        if curr_row < len(self.row_heights):
                            curr_y = sum(self.row_heights[:curr_row])
                        else:
                            curr_y += self.row_heights[curr_row - 1] if curr_row > 0 else 0
                        curr_x = 0

                # Store box info
                self.boxes[box_id] = {
                    'width': module_w,
                    'height': module_h,
                    'chunks': chunks,
                    'start_row': start_row,
                    'start_x': box_start_x
                }
                self.box_to_regions[box_id] = [chunk['region_key'] for chunk in chunks]

        print(f"Built layout: {len(self.boxes)} boxes, {len(self.regions)} regions")

    def get_box_count(self) -> int:
        """Get the total number of boxes"""
        return len(self.boxes)

    def get_box_info(self, box_id: int) -> Optional[Dict]:
        """Get info for a specific box"""
        return self.boxes.get(box_id)

    def get_region_info(self, region_key: str) -> Optional[Dict]:
        """Get info for a specific region"""
        return self.regions.get(region_key)

    def get_box_regions(self, box_id: int) -> List[str]:
        """Get all region keys for a box"""
        return self.box_to_regions.get(box_id, [])

    def get_all_boxes(self) -> List[int]:
        """Get all box IDs"""
        return list(self.boxes.keys())


# ============================================================================
# BOX PLAYER - Plays a video in a full box, splitting across regions
# ============================================================================

class BoxPlayer(QObject):
    """Plays a video in a full sponsor box, handling split across rows"""

    frame_ready = pyqtSignal(np.ndarray, int)  # frame, box_id

    def __init__(self, box_id: int, box_info: Dict, layout: LayoutManager):
        super().__init__()
        self.box_id = box_id
        self.box_info = box_info
        self.layout = layout
        self.full_width = box_info['width']
        self.full_height = box_info['height']
        self.chunks = box_info['chunks']
        self.start_x = box_info['start_x']

        self.video_path: Optional[str] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_playing = False
        self.fps = 30
        self.total_frames = 0
        self.current_frame = 0
        self.frame_delay = 33  # ms
        self._frame_buffer: Dict[str, np.ndarray] = {}  # region_key -> frame
        self._lock = threading.Lock()

        # Create placeholder frames for each chunk
        self._create_placeholders()

        # Timer for video playback
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(self.frame_delay)

    def _create_placeholders(self):
        """Create placeholder frames for each chunk"""
        for chunk in self.chunks:
            region_key = chunk['region_key']
            region_info = self.layout.get_region_info(region_key)
            if region_info:
                w = region_info['width']
                h = region_info['height']
                frame = np.zeros((h, w, 3), dtype=np.uint8)

                # Color based on box ID (BGR format)
                color_b = (self.box_id * 50 + 100) % 255
                color_g = (self.box_id * 80 + 150) % 255
                color_r = (self.box_id * 120 + 50) % 255
                frame[:] = (color_b, color_g, color_r)

                # Add text
                cv2.putText(frame, f"Box {self.box_id}", (5, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                cv2.putText(frame, f"{w}x{h}", (5, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.3, (200, 200, 200), 1)

                with self._lock:
                    self._frame_buffer[region_key] = frame

    def load_video(self, video_path: str) -> bool:
        """Load a video file for this box"""
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

        # Initialize with first frame
        self._update_frame()

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
        """Update the current frame and split it across regions"""
        if not self.is_playing or not self.cap:
            return

        ret, full_frame = self.cap.read()

        if not ret:
            # Loop video
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, full_frame = self.cap.read()

            if not ret:
                return

        # IMPORTANT: Resize full frame to the box size, preserving aspect ratio
        # but filling the entire box (stretch to fit)
        if full_frame.shape[1] != self.full_width or full_frame.shape[0] != self.full_height:
            full_frame = cv2.resize(full_frame, (self.full_width, self.full_height),
                                    interpolation=cv2.INTER_LANCZOS4)

        # Split the frame into chunks
        with self._lock:
            for chunk in self.chunks:
                region_key = chunk['region_key']
                region_info = self.layout.get_region_info(region_key)

                if region_info:
                    # Calculate the portion of the full frame to extract
                    # offset_x is the position within the full box
                    offset_x = chunk['offset_x']
                    chunk_width = chunk['width']
                    chunk_height = chunk['height']

                    # Extract the correct portion from the full frame
                    # x: offset_x, y: 0 (since all chunks are the same height)
                    chunk_frame = full_frame[0:chunk_height, offset_x:offset_x + chunk_width].copy()

                    # Ensure the chunk is the right size (should be, but just in case)
                    if chunk_frame.shape[1] != chunk_width or chunk_frame.shape[0] != chunk_height:
                        chunk_frame = cv2.resize(chunk_frame, (chunk_width, chunk_height))

                    self._frame_buffer[region_key] = chunk_frame

        self.frame_ready.emit(full_frame, self.box_id)

    def get_chunk_frame(self, region_key: str) -> Optional[np.ndarray]:
        """Get the frame for a specific chunk/region"""
        with self._lock:
            frame = self._frame_buffer.get(region_key)
            if frame is not None:
                return frame.copy()
            return None

    def release(self):
        """Release resources"""
        if self.cap:
            self.cap.release()
            self.cap = None


# ============================================================================
# LED COMPOSITOR - Combines all box videos into final display
# ============================================================================

class LEDCompositor(QWidget):
    """Combines all box videos into the final LED display"""

    def __init__(self, total_width=2048, total_height=1152):
        super().__init__()
        self.total_width = total_width
        self.total_height = total_height
        self.layout = LayoutManager(total_width)

        # Setup window for LED screen (3rd screen = index 2)
        self.setWindowTitle("LED Board - Direct Play")
        self.setWindowFlags(Qt.FramelessWindowHint)

        screens = QApplication.screens()
        if len(screens) > 2:
            screen = screens[2]
            self.setGeometry(screen.geometry())
            self.showFullScreen()
        else:
            self.setGeometry(0, 0, total_width, total_height)

        self.setStyleSheet("background-color: black;")

        # Create box players
        self.box_players: Dict[int, BoxPlayer] = {}
        for box_id in self.layout.get_all_boxes():
            box_info = self.layout.get_box_info(box_id)
            if box_info:
                player = BoxPlayer(box_id, box_info, self.layout)
                player.frame_ready.connect(self._on_frame_ready)
                self.box_players[box_id] = player

        self._lock = threading.Lock()

        # Timer for compositing
        self.composite_timer = QTimer()
        self.composite_timer.timeout.connect(self._composite)
        self.composite_timer.start(16)  # ~60fps

        # Create canvas
        self.canvas = np.zeros((total_height, total_width, 3), dtype=np.uint8)
        self.canvas.fill(0)  # Black background

        print(f"Initialized {len(self.box_players)} boxes on LED screen")

    def _on_frame_ready(self, frame: np.ndarray, box_id: int):
        """Handle frame update from a box player"""
        pass  # Frames are stored in the player

    def _composite(self):
        """Composite all box frames"""
        # Clear canvas to black
        self.canvas.fill(0)

        for box_id, player in self.box_players.items():
            # Get all regions for this box
            region_keys = self.layout.get_box_regions(box_id)

            for region_key in region_keys:
                chunk_frame = player.get_chunk_frame(region_key)
                if chunk_frame is not None:
                    region_info = self.layout.get_region_info(region_key)
                    if region_info:
                        try:
                            x = region_info['x']
                            y = region_info['y']
                            w = region_info['width']
                            h = region_info['height']

                            # Ensure the chunk frame is the right size
                            if chunk_frame.shape[1] != w or chunk_frame.shape[0] != h:
                                chunk_frame = cv2.resize(chunk_frame, (w, h))

                            self.canvas[y:y + h, x:x + w] = chunk_frame
                        except Exception as e:
                            pass

        self.update()

    def paintEvent(self, event):
        """Paint the composited frame"""
        painter = QPainter(self)

        # Convert canvas to QImage (BGR to RGB)
        h, w, ch = self.canvas.shape
        bytes_per_line = ch * w

        # Convert BGR to RGB for display
        display_frame = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2RGB)

        qimage = QImage(display_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # Scale to fit widget
        scaled = qimage.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Center
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2

        painter.drawImage(x, y, scaled)

        # Draw region borders for debugging
        painter.setPen(QColor(255, 255, 255, 20))
        for region_key, region_info in self.layout.regions.items():
            scale_x = scaled.width() / self.total_width
            scale_y = scaled.height() / self.total_height
            rx = x + region_info['x'] * scale_x
            ry = y + region_info['y'] * scale_y
            rw = region_info['width'] * scale_x
            rh = region_info['height'] * scale_y
            painter.drawRect(int(rx), int(ry), int(rw), int(rh))

    def load_video_to_box(self, box_id: int, video_path: str) -> bool:
        """Load a video to a specific box"""
        if box_id in self.box_players:
            return self.box_players[box_id].load_video(video_path)
        return False

    def play_all(self):
        """Play all boxes"""
        for player in self.box_players.values():
            player.play()

    def pause_all(self):
        """Pause all boxes"""
        for player in self.box_players.values():
            player.pause()

    def stop_all(self):
        """Stop all boxes"""
        for player in self.box_players.values():
            player.stop()

    def play_box(self, box_id: int):
        """Play a specific box"""
        if box_id in self.box_players:
            self.box_players[box_id].play()

    def pause_box(self, box_id: int):
        """Pause a specific box"""
        if box_id in self.box_players:
            self.box_players[box_id].pause()

    def stop_box(self, box_id: int):
        """Stop a specific box"""
        if box_id in self.box_players:
            self.box_players[box_id].stop()


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
        self.setWindowTitle("LED Control Panel - Direct Play")
        self.setGeometry(100, 100, 600, 700)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Title
        title = QLabel("🎯 LED Board Direct Play - Brick Wall Layout")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()

        # === Tab 1: Playback Control ===
        playback_tab = QWidget()
        playback_layout = QVBoxLayout(playback_tab)

        # Box selector
        box_layout = QHBoxLayout()
        box_layout.addWidget(QLabel("Box:"))
        self.box_combo = QComboBox()
        for box_id in self.compositor.layout.get_all_boxes():
            box_info = self.compositor.layout.get_box_info(box_id)
            chunks = len(box_info['chunks'])
            self.box_combo.addItem(
                f"Box {box_id} ({box_info['width']}x{box_info['height']}, {chunks} chunks)",
                box_id
            )
        box_layout.addWidget(self.box_combo)
        playback_layout.addLayout(box_layout)

        # Box info
        self.box_info_label = QLabel("Width: 0, Height: 0, Chunks: 0")
        self.box_info_label.setStyleSheet("color: #888; font-size: 11px;")
        playback_layout.addWidget(self.box_info_label)

        # Update box info on selection
        self.box_combo.currentIndexChanged.connect(self._update_box_info)
        self._update_box_info()

        # Playback controls
        controls_group = QGroupBox("Playback Controls")
        controls_layout = QGridLayout(controls_group)

        self.play_all_btn = QPushButton("▶ Play All")
        self.play_all_btn.clicked.connect(self.compositor.play_all)
        controls_layout.addWidget(self.play_all_btn, 0, 0)

        self.pause_all_btn = QPushButton("⏸ Pause All")
        self.pause_all_btn.clicked.connect(self.compositor.pause_all)
        controls_layout.addWidget(self.pause_all_btn, 0, 1)

        self.stop_all_btn = QPushButton("⏹ Stop All")
        self.stop_all_btn.clicked.connect(self.compositor.stop_all)
        controls_layout.addWidget(self.stop_all_btn, 0, 2)

        self.play_box_btn = QPushButton("▶ Play Box")
        self.play_box_btn.clicked.connect(self._play_selected_box)
        controls_layout.addWidget(self.play_box_btn, 1, 0)

        self.pause_box_btn = QPushButton("⏸ Pause Box")
        self.pause_box_btn.clicked.connect(self._pause_selected_box)
        controls_layout.addWidget(self.pause_box_btn, 1, 1)

        self.stop_box_btn = QPushButton("⏹ Stop Box")
        self.stop_box_btn.clicked.connect(self._stop_selected_box)
        controls_layout.addWidget(self.stop_box_btn, 1, 2)

        playback_layout.addWidget(controls_group)

        # Video loading
        load_group = QGroupBox("Load Video to Box")
        load_layout = QVBoxLayout(load_group)

        self.load_btn = QPushButton("📁 Load Video")
        self.load_btn.clicked.connect(self._load_video)
        load_layout.addWidget(self.load_btn)

        self.current_video_label = QLabel("No video loaded")
        self.current_video_label.setStyleSheet("color: #888; font-size: 11px;")
        load_layout.addWidget(self.current_video_label)

        playback_layout.addWidget(load_group)

        tabs.addTab(playback_tab, "Playback")

        # === Tab 2: Playlist ===
        playlist_tab = QWidget()
        playlist_layout = QVBoxLayout(playlist_tab)

        # Playlist controls
        pl_controls = QHBoxLayout()
        self.add_playlist_btn = QPushButton("Add Files")
        self.add_playlist_btn.clicked.connect(self._add_to_playlist)
        self.clear_playlist_btn = QPushButton("Clear")
        self.clear_playlist_btn.clicked.connect(self._clear_playlist)
        self.play_playlist_btn = QPushButton("▶ Play Playlist")
        self.play_playlist_btn.clicked.connect(self._play_playlist)
        pl_controls.addWidget(self.add_playlist_btn)
        pl_controls.addWidget(self.clear_playlist_btn)
        pl_controls.addWidget(self.play_playlist_btn)
        playlist_layout.addLayout(pl_controls)

        # Playlist display
        self.playlist = QListWidget()
        self.playlist.itemDoubleClicked.connect(self._play_playlist_item)
        playlist_layout.addWidget(self.playlist)

        # Playlist status
        self.playlist_status = QLabel("0 files in playlist")
        self.playlist_status.setStyleSheet("color: #888; font-size: 11px;")
        playlist_layout.addWidget(self.playlist_status)

        # Playlist assignment
        assign_layout = QHBoxLayout()
        assign_layout.addWidget(QLabel("Assign to box:"))
        self.assign_box_combo = QComboBox()
        for box_id in self.compositor.layout.get_all_boxes():
            self.assign_box_combo.addItem(f"Box {box_id}", box_id)
        assign_layout.addWidget(self.assign_box_combo)
        self.assign_btn = QPushButton("Assign")
        self.assign_btn.clicked.connect(self._assign_to_box)
        assign_layout.addWidget(self.assign_btn)
        playlist_layout.addLayout(assign_layout)

        tabs.addTab(playlist_tab, "Playlist")

        # === Tab 3: System ===
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)

        info_group = QGroupBox("System Information")
        info_layout = QGridLayout(info_group)

        info_layout.addWidget(QLabel("Total Resolution:"), 0, 0)
        info_layout.addWidget(QLabel(f"{self.compositor.total_width} x {self.compositor.total_height}"), 0, 1)

        info_layout.addWidget(QLabel("Total Boxes:"), 1, 0)
        info_layout.addWidget(QLabel(str(len(self.compositor.box_players))), 1, 1)

        info_layout.addWidget(QLabel("Total Regions:"), 2, 0)
        info_layout.addWidget(QLabel(str(len(self.compositor.layout.regions))), 2, 1)

        info_layout.addWidget(QLabel("Layout:"), 3, 0)
        info_layout.addWidget(QLabel("Brick Wall (wrapping)"), 3, 1)

        system_layout.addWidget(info_group)

        system_controls = QGroupBox("System Controls")
        sys_layout = QVBoxLayout(system_controls)

        reset_btn = QPushButton("🔄 Reset All")
        reset_btn.clicked.connect(self.compositor.stop_all)
        sys_layout.addWidget(reset_btn)

        layout_btn = QPushButton("📐 Show Layout")
        layout_btn.clicked.connect(self._show_layout)
        sys_layout.addWidget(layout_btn)

        system_layout.addWidget(system_controls)

        tabs.addTab(system_tab, "System")

        main_layout.addWidget(tabs)

        # Status
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #0f0; font-weight: bold;")
        main_layout.addWidget(self.status_label)

        # Playlist storage
        self.playlist_items: List[Dict] = []  # [{'box_id': box_id, 'path': path}]

    def _update_box_info(self):
        """Update box info display"""
        box_id = self.box_combo.currentData()
        if box_id in self.compositor.layout.boxes:
            info = self.compositor.layout.boxes[box_id]
            self.box_info_label.setText(
                f"Width: {info['width']}, Height: {info['height']}, "
                f"Chunks: {len(info['chunks'])}"
            )

    def _play_selected_box(self):
        """Play the selected box"""
        box_id = self.box_combo.currentData()
        self.compositor.play_box(box_id)
        self.status_label.setText(f"Status: Playing Box {box_id}")

    def _pause_selected_box(self):
        """Pause the selected box"""
        box_id = self.box_combo.currentData()
        self.compositor.pause_box(box_id)
        self.status_label.setText(f"Status: Paused Box {box_id}")

    def _stop_selected_box(self):
        """Stop the selected box"""
        box_id = self.box_combo.currentData()
        self.compositor.stop_box(box_id)
        self.status_label.setText(f"Status: Stopped Box {box_id}")

    def _load_video(self):
        """Load a video to the selected box"""
        box_id = self.box_combo.currentData()

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm)"
        )

        if file_path:
            if self.compositor.load_video_to_box(box_id, file_path):
                self.current_video_label.setText(f"Loaded: {os.path.basename(file_path)}")
                self.status_label.setText(f"Status: Video loaded to Box {box_id}")
                # Auto-play
                self.compositor.play_box(box_id)
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
            # Default to first box
            box_id = self.assign_box_combo.currentData()
            self.playlist_items.append({'box_id': box_id, 'path': file_path})
            item = QListWidgetItem(f"Box {box_id}: {os.path.basename(file_path)}")
            item.setData(Qt.UserRole, {'box_id': box_id, 'path': file_path})
            self.playlist.addItem(item)

        self.playlist_status.setText(f"{len(self.playlist_items)} files in playlist")

    def _clear_playlist(self):
        """Clear the playlist"""
        self.playlist_items.clear()
        self.playlist.clear()
        self.playlist_status.setText("0 files in playlist")

    def _play_playlist(self):
        """Play all items in the playlist"""
        for item_data in self.playlist_items:
            box_id = item_data['box_id']
            path = item_data['path']
            self.compositor.load_video_to_box(box_id, path)
            self.compositor.play_box(box_id)
        self.status_label.setText(f"Status: Playing playlist ({len(self.playlist_items)} items)")

    def _play_playlist_item(self, item: QListWidgetItem):
        """Play a playlist item"""
        data = item.data(Qt.UserRole)
        box_id = data['box_id']
        path = data['path']

        if self.compositor.load_video_to_box(box_id, path):
            self.compositor.play_box(box_id)
            self.status_label.setText(f"Status: Playing Box {box_id}: {os.path.basename(path)}")
        else:
            QMessageBox.warning(self, "Error", "Failed to load video")

    def _assign_to_box(self):
        """Assign selected playlist items to a box"""
        box_id = self.assign_box_combo.currentData()
        selected = self.playlist.selectedIndexes()

        for idx in selected:
            item = self.playlist.item(idx.row())
            data = item.data(Qt.UserRole)
            data['box_id'] = box_id
            item.setText(f"Box {box_id}: {os.path.basename(data['path'])}")
            item.setData(Qt.UserRole, data)

            # Update stored data
            for stored in self.playlist_items:
                if stored['path'] == data['path']:
                    stored['box_id'] = box_id

        self.status_label.setText(f"Status: Assigned to Box {box_id}")

    def _show_layout(self):
        """Show layout information"""
        info = f"Total Resolution: {self.compositor.total_width}x{self.compositor.total_height}\n"
        info += f"Total Boxes: {len(self.compositor.box_players)}\n"
        info += f"Total Regions: {len(self.compositor.layout.regions)}\n\n"
        info += "Box Layout:\n"
        info += "-" * 50 + "\n"

        for box_id, box_info in self.compositor.layout.boxes.items():
            info += f"\nBox {box_id}: {box_info['width']}x{box_info['height']}\n"
            for chunk in box_info['chunks']:
                info += f"  Region {chunk['region_key']}: x={chunk['x']}, y={chunk['y']}, w={chunk['width']}\n"

        QMessageBox.information(self, "Layout Information", info)


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