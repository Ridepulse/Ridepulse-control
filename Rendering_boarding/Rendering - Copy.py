import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import csv
import os
import threading
media_folder = "Media"
csv_file = "sponsors.csv"

if not os.path.exists(csv_file):
    alt_path = os.path.join("Rendering_boarding", "sponsors.csv")
    if os.path.exists(alt_path):
        csv_file = alt_path

if not os.path.exists(media_folder):
    alt_path = os.path.join("Rendering_boarding", "Media")
    if os.path.exists(alt_path):
        media_folder = alt_path

layout = [
    [(1200, 96), (816, 96)],
    [(816, 96), (1056,96), (816, 96)],
    [(816, 96), (576, 96)],
    [(960, 96), (960, 96)],
    [(960, 96), (960, 96)],
    [(960, 96), (960, 96)],
    [(960, 96), (960, 96)],
    [(960, 96), (960, 96)],
    [(1008,96), (1008,96)],
    [(1008,96), (1008,96)],
    [(1056,96)]
]

fixed_image_path = os.path.join(media_folder, "Woonhoek.png")
fixed_image = None
if os.path.exists(fixed_image_path):
    fixed_image = cv2.imread(fixed_image_path)

def read_media_from_csv(csv_file):
    media_files = []
    try:
        with open(csv_file, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                filename = os.path.join(media_folder, row['filename'])
                media_files.append(filename)
    except FileNotFoundError:
        pass
    return media_files

def _compute_row_heights(layout):
    return [max((h for (_, h) in row), default=0) for row in layout]

def generate_layout(layout, total_width, total_height, frame):
    canvas = np.zeros((total_height, total_width, 3), dtype=np.uint8)
    canvas[:] = (30, 30, 30)

    row_heights = [max(h for (w, h) in row) for row in layout]
    y_offsets = []
    y = 0
    for h in row_heights:
        y_offsets.append(y)
        y += h

    if frame is not None:
        src = frame.copy()
    else:
        src = fixed_image.copy() if fixed_image is not None else np.zeros((100, 100, 3), dtype=np.uint8)

    for row_idx, row in enumerate(layout):
        row_y = y_offsets[row_idx]
        row_h = row_heights[row_idx]
        if row_idx == 9:
            x_offset = 96
        elif row_idx == 10:
            x_offset = 192
        elif row_idx == 2:
            x_offset = 640   #672-32
        else:
            x_offset = 0

        for module_idx, (module_w, module_h) in enumerate(row):
            if fixed_image is not None and ((row_idx == 0 and module_idx == 0) or (row_idx == 10 and module_idx == 0)):
                full_module = cv2.resize(fixed_image, (module_w, module_h))
            else:
                full_module = cv2.resize(src, (module_w, module_h))
            remaining = module_w
            placed = 0
            curr_row = row_idx
            curr_x = x_offset
            while remaining > 0 and curr_row < len(layout):
                available = total_width - curr_x
                if available <= 0:
                    curr_row += 1
                    curr_x = 0
                    continue

                place_w = min(remaining, available)
                chunk = full_module[:, placed:placed + place_w]
                target_row_y = y_offsets[curr_row]
                target_row_h = row_heights[curr_row]
                y_place = target_row_y + (target_row_h - module_h) // 2
                canvas[y_place:y_place + module_h, curr_x:curr_x + place_w] = chunk
                remaining -= place_w
                placed += place_w
                curr_x += place_w
                if curr_x >= total_width:
                    curr_row += 1
                    curr_x = 0

            x_offset += module_w
            if x_offset >= total_width:
                x_offset = total_width

    return canvas

def process_media_files(media_files, output_video, layout, target_fps,
                        total_width=2048, total_height=1152, image_duration=10,
                        progress_callback=None):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, target_fps, (total_width, total_height))

    total_files = max(1, len(media_files))
    processed_files = 0

    for media_file in media_files:
        if not os.path.exists(media_file):
            print(f"Warning: {media_file} not found, skipping.")
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files)
            continue

        if media_file.lower().endswith(('.mp4', '.avi', '.mov')):
            cap = cv2.VideoCapture(media_file)
            if not cap.isOpened():
                print(f"Error: Unable to open video file {media_file}.")
                processed_files += 1
                if progress_callback:
                    progress_callback(processed_files, total_files)
                continue

            input_fps = cap.get(cv2.CAP_PROP_FPS) or target_fps
            frame_multiplier = max(1, int(round(target_fps / input_fps))) if input_fps > 0 else 1

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame.ndim == 2:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                canvas = generate_layout(layout, total_width, total_height, frame)
                for _ in range(frame_multiplier):
                    out.write(canvas)
            cap.release()

        elif media_file.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            image = cv2.imread(media_file)
            if image is None:
                print(f"Error: Unable to open image file {media_file}.")
                processed_files += 1
                if progress_callback:
                    progress_callback(processed_files, total_files)
                continue
            canvas = generate_layout(layout, total_width, total_height, image)
            for _ in range(target_fps * image_duration):
                out.write(canvas)

        else:
            print(f"Skipping unsupported file: {media_file}")

        processed_files += 1
        if progress_callback:
            progress_callback(processed_files, total_files)

    out.release()
    print("Media processing complete.")

def edit_csv_file(root, on_save_callback):
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
        pass

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
        on_save_callback()

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=10)

    ttk.Button(btn_frame, text="Add sponsor", command=add_row).grid(row=0, column=0, padx=5)
    ttk.Button(btn_frame, text="Remove sponsor", command=delete_row).grid(row=0, column=1, padx=5)
    ttk.Button(btn_frame, text="Save", command=save_csv).grid(row=0, column=3, padx=5)

    tree.bind("<Double-1>", edit_row)


def start_rendering_with_progress(root):
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
            gameday_path = os.path.join(media_folder, "1gameday.mp4")
            process_media_files([gameday_path], "Gameday.mp4", layout, fps,
                                progress_callback=update_progress)

        progress_win.destroy()
        messagebox.showinfo("Klaar", "Rendering completed!")

    threading.Thread(target=run_rendering, daemon=True).start()

def start_rendering(root):
    if choice_var.get() == 0:
        messagebox.showerror("Error", "Select mode.")
        return
    edit_csv_file(root, lambda: start_rendering_with_progress(root))


# MAIN
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

ttk.Button(main_frame, text="Start Rendering", command=lambda: start_rendering(root)).pack(pady=5)

root.mainloop()
