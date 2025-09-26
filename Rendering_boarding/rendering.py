import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import csv
import os
import threading


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

def edit_csv_file():
    edit_win = tk.Toplevel(root)
    edit_win.title("Sponsors Editor")
    edit_win.geometry("750x500")

    frame = ttk.Frame(edit_win, padding=10)
    frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(frame, columns=("filename",), show="headings")
    tree.heading("filename", text="Filename")
    tree.pack(fill="both", expand=True)

    try:
        with open(csv_file, newline="", mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                tree.insert("", "end", values=(row["filename"],))
    except FileNotFoundError:
        messagebox.showwarning("Error", "CSV file not found. Er wordt een lege lijst gestart.")

    def add_row():
        tree.insert("", "end", values=("nieuw_bestand.jpg",))

    def delete_row():
        selected = tree.selection()
        for sel in selected:
            tree.delete(sel)

    def edit_row(event=None):
        selected = tree.selection()
        if not selected:
            return
        item = selected[0]
        old_value = tree.item(item, "values")[0]

        edit_popup = tk.Toplevel(edit_win)
        edit_popup.title("Edit")
        edit_popup.geometry("300x120")

        tk.Label(edit_popup, text="Filename:").pack(pady=5)
        entry = tk.Entry(edit_popup, width=40)
        entry.insert(0, old_value)
        entry.pack(pady=5)

        def save_edit():
            new_value = entry.get().strip()
            if new_value:
                tree.item(item, values=(new_value,))
            edit_popup.destroy()

        ttk.Button(edit_popup, text="Save", command=save_edit).pack(pady=5)

    def save_csv():
        with open(csv_file, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["filename"])
            writer.writeheader()
            for row_id in tree.get_children():
                vals = tree.item(row_id, "values")
                writer.writerow({"filename": vals[0]})

        edit_win.destroy()
        start_rendering_with_progress()

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=10)

    ttk.Button(btn_frame, text="Add sponsor", command=add_row).grid(row=0, column=0, padx=5)
    ttk.Button(btn_frame, text="Remove sponsor", command=delete_row).grid(row=0, column=1, padx=5)
    ttk.Button(btn_frame, text="Save", command=save_csv).grid(row=0, column=3, padx=5)

    tree.bind("<Double-1>", edit_row)

def start_rendering_with_progress():
    progress_win = tk.Toplevel(root)
    progress_win.title("Rendering...")
    progress_win.geometry("400x140")

    tk.Label(progress_win, text="Rendering of sponsor loop...", font=("Arial", 12)).pack(pady=10)
    progress = ttk.Progressbar(progress_win, mode="determinate", maximum=100)
    progress.pack(fill="x", padx=20, pady=10)

    percent_label = tk.Label(progress_win, text="1% done")
    percent_label.pack()

    def update_progress(current, total):
        percent = int((current / total) * 100)
        progress["value"] = percent
        percent_label.config(text=f"{percent}% done")
        progress_win.update_idletasks()

    def run_rendering():
        try:
            choice = choice_var.get()
            fps = int(fps_var.get())
        except ValueError:
            messagebox.showerror("Error", "Choose a valid number of fps.")
            progress_win.destroy()
            return

        if choice in [1, 3]:
            media_files = read_media_from_csv(csv_file)
            print("Rendering Main Loop...")
            process_media_files(media_files, "Main.mp4", layout, fps,
                                progress_callback=update_progress)
        if choice in [2, 3]:
            print("Rendering Gameday Loop...")
            process_media_files([os.path.join(media_folder, "Gameday partner.mp4")],
                                "Gameday.mp4", layout, fps,
                                progress_callback=update_progress)

        progress_win.destroy()
        messagebox.showinfo("Klaar", "Rendering completed!")

    threading.Thread(target=run_rendering, daemon=True).start()


def start_rendering():
    if choice_var.get() == 0:
        messagebox.showerror("Error", "Select mode.")
        return
    edit_csv_file()

def process_media_files(media_files, output_video, layout, target_fps,
                        total_width=1920, total_height=1080, image_duration=10,
                        progress_callback=None):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, target_fps, (total_width, total_height))

    total_files = len(media_files)
    processed_files = 0

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

        processed_files += 1
        if progress_callback:
            progress_callback(processed_files, total_files)

    out.release()
    print("Media processing complete.")

root = tk.Tk()
root.title("Rendering Tool")
root.geometry("400x300")
root.resizable(False, False)

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)

ttk.Label(main_frame, text="Choose mode:", font=("Arial", 15)).pack(anchor="w", pady=10)

choice_var = tk.IntVar()
ttk.Radiobutton(main_frame, text="1 - Main loop", variable=choice_var, value=1).pack(anchor="w", pady=5)
ttk.Radiobutton(main_frame, text="2 - Gameday Partner loop", variable=choice_var, value=2).pack(anchor="w", pady=5)
ttk.Radiobutton(main_frame, text="3 - Both", variable=choice_var, value=3).pack(anchor="w", pady=5)

ttk.Label(main_frame, text="Number of FPS:", font=("Arial", 15)).pack(anchor="w", pady=(15, 5))
fps_var = tk.StringVar()
fps_entry = ttk.Entry(main_frame, textvariable=fps_var, width=10)
fps_entry.pack(pady=5)
fps_entry.insert(0, "60")

ttk.Button(main_frame, text="Start Rendering", command=start_rendering).pack(pady=5)

root.mainloop()
