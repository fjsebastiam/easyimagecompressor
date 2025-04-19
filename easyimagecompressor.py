import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import threading
import os
import math
import sys
import ctypes 
myappid = 'easyimagecompressor.app.1.0' 
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

file_paths = []
selected_images = set()
image_labels = []
checkbox_vars = []
images_per_row = 7

def calculate_quality(percentage):
    return int(95 - (percentage * 0.94))

def format_bytes(size_in_bytes):
    kb, mb, gb = 1024, 1024 ** 2, 1024 ** 3
    if size_in_bytes >= gb:
        return f"{size_in_bytes / gb:.2f} GB"
    elif size_in_bytes >= mb:
        return f"{size_in_bytes / mb:.2f} MB"
    else:
        return f"{size_in_bytes / kb:.2f} KB"

def update_image_grid():
    for i, item in enumerate(image_labels):
        row, col = divmod(i, images_per_row)
        item.grid(row=row, column=col, padx=5, pady=5, sticky="w")

def check_compress_button_state():
    selected_images_paths = [file_paths[i] for i in selected_images if i < len(file_paths)]
    compress_button["state"] = "normal" if selected_images_paths and destination_folder else "disabled"
    selected_label.config(text=f"Seleccionadas: {len(selected_images)}")

def set_destination_folder():
    global destination_folder
    destination_folder = filedialog.askdirectory()
    check_compress_button_state()

def toggle_selection_by_path(path):
    try:
        index = file_paths.index(path)
        selected_images.symmetric_difference_update({index})
    except ValueError:
        pass
    check_compress_button_state()

def clear_preview():
    for label in image_labels:
        label.destroy()
    image_labels.clear()
    file_paths.clear()
    selected_images.clear()
    checkbox_vars.clear()
    check_compress_button_state()

def show_image_preview(file_path):
    global image_labels
    original_image = Image.open(file_path)
    resized_image = original_image.resize((100, 100))
    tk_image = ImageTk.PhotoImage(resized_image)

    frame = tk.Frame(frame_images_canvas, width=100, height=100)
    frame.grid_propagate(False)

    image_label = tk.Label(frame, image=tk_image, borderwidth=2, relief="solid")
    image_label.image = tk_image
    image_label.pack(fill="both", expand=True)

    def remove_image():
        if file_path in file_paths:
            idx = file_paths.index(file_path)
            file_paths.pop(idx)
            image_labels.pop(idx)
            var, _ = checkbox_vars.pop(idx)
            del var
            new_selected = set()
            for i in selected_images:
                if i < idx:
                    new_selected.add(i)
                elif i > idx:
                    new_selected.add(i - 1)
            selected_images.clear()
            selected_images.update(new_selected)
        frame.destroy()
        update_image_grid()
        check_compress_button_state()

    delete_button = tk.Button(frame, text="✖", command=remove_image, bg="red", fg="white",
                              bd=0, padx=2, pady=0, font=("Arial", 9, "bold"), cursor="hand2")
    delete_button.place(relx=1.0, rely=0.0, anchor="ne")

    var = tk.IntVar()
    checkbox = tk.Checkbutton(frame, variable=var, cursor="hand2", command=lambda: toggle_selection_by_path(file_path))
    checkbox.place(relx=1.0, rely=1.0, anchor="se")
    checkbox_vars.append((var, checkbox))
    image_labels.append(frame)
    update_image_grid()

def select_files():
    global file_paths
    new_file_paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
    file_paths.extend(new_file_paths)
    for path in new_file_paths:
        show_image_preview(path)
    check_compress_button_state()

def compress_image(input_path, output_path, compression_percentage):
    quality = calculate_quality(compression_percentage)
    image = Image.open(input_path)
    image.save(output_path, quality=quality, optimize=True)

def compress_selected_files():
    selected_images_paths = [file_paths[i] for i in selected_images if i < len(file_paths)]
    if not selected_images_paths or not destination_folder:
        messagebox.showwarning("Faltan datos", "Debes seleccionar archivos y una carpeta destino")
        return

    progress_var.set(0)
    total = len(selected_images_paths)
    total_original = sum(os.path.getsize(p) for p in selected_images_paths)
    progress_bar["maximum"] = total

    def on_done():
        total_compressed = sum(os.path.getsize(os.path.join(destination_folder, os.path.basename(p))) for p in selected_images_paths)
        saved = abs(total_original - total_compressed)
        saved_space_label.config(text=f"Espacio ahorrado: {format_bytes(saved)}")
        messagebox.showinfo("Completado", "Compresión realizada con éxito")
        clear_preview()

    def compress_and_track(p):
        out = os.path.join(destination_folder, os.path.basename(p))
        compress_image(p, out, compression_scale.get())
        root.after(0, update_progress)

    def update_progress():
        progress_var.set(progress_var.get() + 1)
        progress_bar["value"] = progress_var.get()
        if progress_var.get() == total:
            on_done()

    for path in selected_images_paths:
        threading.Thread(target=compress_and_track, args=(path,)).start()

def bind_shortcuts():
    def select_all(event=None):
        selected_images.clear()
        selected_images.update(range(len(file_paths)))
        for i, (var, _) in enumerate(checkbox_vars):
            var.set(1)
        check_compress_button_state()
        return "break"

    def deselect_all(event=None):
        selected_images.clear()
        for var, _ in checkbox_vars:
            var.set(0)
        check_compress_button_state()
        return "break"

    root.bind_all("<Control-a>", select_all)
    root.bind_all("<Control-A>", select_all)
    root.bind_all("<Control-x>", deselect_all)
    root.bind_all("<Control-X>", deselect_all)

root = tk.Tk()
root.iconbitmap(resource_path("easyImageCompressor.ico"))
root.title("EasyImageCompressor - Pillow Version")
root.geometry("850x500")
root.maxsize(850, 500)
destination_folder = None
progress_var = tk.IntVar()

frame_top_container = tk.Frame(root, bg="gray")
frame_top_container.pack(side=tk.TOP, fill=tk.X)

frame_buttons = tk.Frame(frame_top_container, bg="gray")
frame_buttons.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
for i in range(4): frame_buttons.columnconfigure(i, weight=1)

select_button = tk.Button(frame_buttons, text="Seleccionar archivos", command=select_files)
destination_button = tk.Button(frame_buttons, text="Seleccionar carpeta de destino", command=set_destination_folder)
select_all_button = tk.Button(frame_buttons, text="Seleccionar todo", command=lambda: root.event_generate('<Control-a>'))
deselect_all_button = tk.Button(frame_buttons, text="Deseleccionar todo", command=lambda: root.event_generate('<Control-x>'))

compression_label = tk.Label(frame_buttons, text="Porcentaje de compresión: 0%", bg="gray", fg="white")
compression_scale = ttk.Scale(frame_buttons, from_=0, to=100, orient=tk.HORIZONTAL, length=150,
                              command=lambda val: compression_label.config(text=f"Porcentaje de compresión: {math.ceil(float(val))}%"))

compress_button = tk.Button(frame_buttons, text="Comprimir seleccionados", command=compress_selected_files,
                            state="disabled", bg="#4CAF50", fg="white", relief="flat",
                            font=("Segoe UI", 9, "bold"), padx=10, pady=5, cursor="hand2")

select_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
destination_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
select_all_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
deselect_all_button.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
compression_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
compression_scale.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
compress_button.grid(row=1, column=3, padx=5, pady=5, sticky="e")

frame_images = tk.Frame(root)
frame_images.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
for i in range(images_per_row): frame_images.columnconfigure(i, weight=1)

canvas = tk.Canvas(frame_images)
canvas.pack(side="left", fill="both", expand=True)
scrollbar = ttk.Scrollbar(frame_images, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")
canvas.configure(yscrollcommand=scrollbar.set)

frame_images_canvas = tk.Frame(canvas)
canvas.create_window((0, 0), window=frame_images_canvas, anchor="nw")
frame_images_canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(side="top", fill="x")

bottom_status = tk.Frame(root, bg="gray")
bottom_status.pack(side="bottom", fill="x")

selected_label = tk.Label(bottom_status, text="Seleccionadas: 0", bg="gray", fg="white", anchor="w")
saved_space_label = tk.Label(bottom_status, text="Espacio ahorrado: N/A", bg="gray", fg="white", anchor="e")
selected_label.pack(side="left", padx=5)
saved_space_label.pack(side="right", padx=5)

bind_shortcuts()
root.mainloop()
