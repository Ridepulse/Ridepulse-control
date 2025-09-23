import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import csv
import os

media_folder = "Media"
csv_file = os.path.join("sponsors.csv")
layout = [
    [(816, 96), (816, 96)],
    [(1200,96)],
    [(960, 96), (960, 96)],
    [(960, 96), (960, 96)],
    [(960, 96), (960, 96)],
    [(960, 96), (960, 96)],
    [(960, 96), (960, 96)],
    [(1488,96)],
    [(960,96)],
    [(1104, 96)],
]
fixed_image_path = os.path.join(media_folder, "Woonhoek.png")
fixed_image = cv2.imread(fixed_image_path)

def read_media_from_csv(csv_file):
    media_files = []
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            filename = os.path.join(media_folder, row['filename'])
            media_files.append(filename)
    return media_files

def generate_layout(layout, total_width, total_height, frame):
    canvas = np.zeros((total_height, total_width, 3), dtype=np.uint8)
    y_offset = 0
    for row_index, row in enumerate(layout):
        if row_index == 0:
            x_offset = 288
        elif row_index == 1:
            x_offset = 720
        else:
            x_offset = 0
        for module_index, (module_width, module_height) in enumerate(row):
            if module_width > 0 and module_height > 0:
                module_rect = (slice(y_offset, y_offset + module_height), slice(x_offset, x_offset + module_width))
                canvas[module_rect] = (50, 50, 50)
                if (row_index == 1 and module_index == 0) or (row_index == 9 and module_index == 0):
                    resized_image = cv2.resize(fixed_image, (module_width, module_height))
                    canvas[y_offset:y_offset + module_height, x_offset:x_offset + module_width] = resized_image
                elif frame is not None:
                    resized_frame = cv2.resize(frame, (module_width, module_height))
                    canvas[y_offset:y_offset + module_height, x_offset:x_offset + module_width] = resized_frame
            x_offset += module_width
        y_offset += module_height
    return canvas

def process_media_files(media_files, output_video, layout, target_fps, total_width=1920, total_height=1080, image_duration=10):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, target_fps, (total_width, total_height))
    for media_file in media_files:
        if media_file.lower().endswith(('.mp4', '.avi', '.mov')):
            cap = cv2.VideoCapture(media_file)
            if not cap.isOpened():
                print(f"Error: Unable to open video file {media_file}.")
                continue
            input_fps = cap.get(cv2.CAP_PROP_FPS)
            frame_multiplier = max(1, int(round(target_fps / input_fps))) if input_fps > 0 else 1
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                canvas = generate_layout(layout, total_width, total_height, frame)
                for _ in range(frame_multiplier):
                    out.write(canvas)
            cap.release()
        elif media_file.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            image = cv2.imread(media_file)
            if image is None:
                print(f"Error: Unable to open image file {media_file}.")
                continue
            canvas = generate_layout(layout, total_width, total_height, image)
            for _ in range(target_fps * image_duration):
                out.write(canvas)
    out.release()
    print("Media processing complete.")

def start_rendering():
    try:
        choice = choice_var.get()
        fps = int(fps_var.get())
    except ValueError:
        messagebox.showerror("Error", "Voer een geldig FPS-getal in.")
        return

    if choice == 0:
        messagebox.showerror("Error", "Selecteer een modus.")
        return

    root.destroy()

    if choice in [1, 3]:
        media_files = read_media_from_csv(csv_file)
        print("Rendering Main Loop...")
        process_media_files(media_files, "Main.mp4", layout, fps)
    if choice in [2, 3]:
        print("Rendering Gameday Loop...")
        process_media_files([os.path.join(media_folder, "Gameday partner.mp4")], "Gameday.mp4", layout, fps)

root = tk.Tk()
root.title("Rendering Tool")
root.geometry("400x300")
root.resizable(False, False)

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)

ttk.Label(main_frame, text="Kies een modus:", font=("Arial", 15)).pack(anchor="w", pady=10)

choice_var = tk.IntVar()
ttk.Radiobutton(main_frame, text="1 - Main loop", variable=choice_var, value=1).pack(anchor="w", pady=5)
ttk.Radiobutton(main_frame, text="2 - Gameday Partner loop", variable=choice_var, value=2).pack(anchor="w", pady=5)
ttk.Radiobutton(main_frame, text="3 - Beide", variable=choice_var, value=3).pack(anchor="w", pady=5)

ttk.Label(main_frame, text="Aantal FPS:", font=("Arial", 15)).pack(anchor="w", pady=(15, 5))
fps_var = tk.StringVar()
fps_entry = ttk.Entry(main_frame, textvariable=fps_var, width=10)
fps_entry.pack(pady=5)
fps_entry.insert(0, "60")

ttk.Button(main_frame, text="Start Rendering", command=start_rendering).pack(pady=5)

root.mainloop()
