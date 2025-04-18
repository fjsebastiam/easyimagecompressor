import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import cv2
import threading
from PIL import Image, ImageTk
import os
import math

file_paths = []  # Variable global para almacenar las rutas de los archivos seleccionados
selected_images = set()  # Conjunto para rastrear las imágenes seleccionadas
image_labels = []  # Lista para almacenar las etiquetas de imagen
images_per_row = 7  # Número de imágenes por fila

def get_image_info(file_path):
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path) // 1024  # Convertir bytes a KB
    file_type = file_name.split('.')[-1]
    return file_name, file_size, file_type

def calculate_quality(percentage):
    # Ajustar el porcentaje a un valor de calidad de 1 a 95
    quality = int(95 - (percentage * 0.94))  # Escala el porcentaje entre 1 y 95
    return quality

def select_files():
    global file_paths  # Usar la variable global
    new_file_paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp")])
    file_paths.extend(new_file_paths)
    add_image_previews(new_file_paths)
    check_compress_button_state()

def add_image_previews(new_file_paths):
    for file_path in new_file_paths:
        show_image_preview(file_path)

def clear_preview():
    for label in image_labels:
        label.destroy()  # Destruir las etiquetas de imagen
    image_labels.clear()
    file_paths.clear()  # Limpiar la lista de rutas de archivos
    selected_images.clear()  # Limpiar las imágenes seleccionadas
    check_compress_button_state()

def toggle_image_selection(index):
    if index in selected_images:
        # Deseleccionar la imagen
        selected_images.remove(index)
    else:
        # Seleccionar la imagen
        selected_images.add(index)
    check_compress_button_state()

def show_image_preview(file_path):
    global image_labels  # Hacer que image_labels sea una variable global
    original_image = Image.open(file_path)
    resized_image = original_image.resize((100, 100))
    tk_image = ImageTk.PhotoImage(resized_image)

    # Crear una etiqueta para mostrar la imagen
    image_label = tk.Label(frame_images_canvas, image=tk_image, borderwidth=2, relief="solid", highlightbackground="black")
    image_label.image = tk_image

    # Crear una casilla de verificación (checkbox) para cada imagen
    var = tk.IntVar()
    checkbox = tk.Checkbutton(frame_images_canvas, variable=var, command=lambda i=len(image_labels): toggle_image_selection(i))
    
    # Colocar la imagen
    image_row = len(image_labels) // images_per_row
    image_column = len(image_labels) % images_per_row
    image_label.grid(row=image_row, column=image_column, padx=5, pady=5, sticky="w")
    
    # Colocar el checkbox sobre la imagen
    checkbox.place(in_=image_label, relx=0.5, rely=0.5, anchor="c")
    
    # Agregar la etiqueta e checkbox al frame
    image_labels.append(image_label)
    image_labels.append(checkbox)

    update_image_grid()

def update_image_grid():
    total_images = len(image_labels)
    for i, item in enumerate(image_labels):
        row, col = divmod(i, images_per_row)
        item.grid(row=row, column=col, padx=5, pady=5, sticky="w")

def check_compress_button_state():
    selected_images_paths = [file_paths[i] for i in selected_images if i < len(file_paths)]
    if selected_images_paths and destination_folder:
        compress_button["state"] = "normal"
    else:
        compress_button["state"] = "disabled"

def set_destination_folder():
    global destination_folder
    destination_folder = filedialog.askdirectory()
    check_compress_button_state()

def compress_image(input_path, output_path, compression_percentage, progress_var, progress_label_top):
    # Obtener el tipo de archivo
    _, file_extension = os.path.splitext(input_path)
    file_extension = file_extension.lower()  # Convertir la extensión a minúsculas

    quality = calculate_quality(compression_percentage)

    if file_extension == '.jpg' or file_extension == '.jpeg':
        image = cv2.imread(input_path)
        cv2.imwrite(output_path, image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    elif file_extension == '.png':
        image = cv2.imread(input_path)
        cv2.imwrite(output_path, image, [int(cv2.IMWRITE_PNG_COMPRESSION), quality])
    # Agregar más formatos de imagen si es necesario

    # Actualizar la etiqueta de progreso con el porcentaje
    progress_var.set(progress_var.get() + 1)
    max_value = progress_var.get()  # Obtener el valor máximo de la barra de progreso
    progress_label_top["text"] = f"Progreso: {int((progress_var.get() / max_value) * 100)}%"

def compress_selected_files(progress_label_top):
    selected_images_paths = [file_paths[i] for i in selected_images if i < len(file_paths)]
    if not selected_images_paths or not destination_folder:
        return
    
    progress_var = tk.IntVar()
    compression_percentage = compression_scale.get()

    progress_label_top["text"] = "Progreso: 0%"

    for input_path in selected_images_paths:
        _, file_name = os.path.split(input_path)
        output_path = os.path.join(destination_folder, file_name)
        thread = threading.Thread(target=compress_image, args=(input_path, output_path, compression_percentage, progress_var, progress_label_top))
        thread.start()

# Crear la ventana principal
root = tk.Tk()
root.title("Compresor de Imágenes")
root.geometry("850x500")  # Ancho de 850 píxeles
root.maxsize(850, 500)  # Establecer el tamaño máximo

# Crear un Frame para los botones
frame_buttons = tk.Frame(root)
frame_buttons.pack(side=tk.TOP, fill=tk.X)

# Crear y configurar elementos de la interfaz con estilo en el Frame de botones
select_button = tk.Button(frame_buttons, text="Seleccionar archivos", command=select_files, relief="solid")
destination_button = tk.Button(frame_buttons, text="Seleccionar carpeta de destino", command=set_destination_folder, relief="solid")
compress_button = tk.Button(frame_buttons, text="Comprimir seleccionados", command=lambda: compress_selected_files(progress_label_top), state="disabled", relief="solid")

def update_compression_label(value):
    rounded_value = math.ceil(float(value))
    compression_label["text"] = f"Porcentaje de compresión: {rounded_value}%"

compression_scale = ttk.Scale(frame_buttons, from_=0, to=100, orient=tk.HORIZONTAL, length=200, command=lambda value: update_compression_label(value))
compression_label = tk.Label(frame_buttons, text="Porcentaje de compresión: 0%")

# Posicionar elementos en el Frame de botones
select_button.pack(side=tk.LEFT, padx=5, pady=10)
destination_button.pack(side=tk.LEFT, padx=5, pady=10)
compression_label.pack(side=tk.LEFT, padx=5, pady=5)
compression_scale.pack(side=tk.LEFT, padx=5, pady=5)
compress_button.pack(side=tk.LEFT, padx=5, pady=10)

destination_folder = None  # Variable global para la carpeta de destino

# Crear un Frame para las imágenes dentro del lienzo
frame_images = tk.Frame(root)
frame_images.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Configurar las columnas para que tengan el mismo tamaño
for i in range(images_per_row):
    frame_images.columnconfigure(i, weight=1)

# Agregar un lienzo para permitir el desplazamiento vertical
canvas = tk.Canvas(frame_images)
canvas.pack(side="left", fill="both", expand=True)

# Agregar una barra de desplazamiento vertical
scrollbar = ttk.Scrollbar(frame_images, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")

# Configurar el lienzo para que funcione con la barra de desplazamiento
canvas.configure(yscrollcommand=scrollbar.set)

# Crear un nuevo Frame para las imágenes dentro del lienzo
frame_images_canvas = tk.Frame(canvas)
canvas.create_window((0, 0), window=frame_images_canvas, anchor="nw")

# Ajustar el lienzo para que expanda horizontalmente
frame_images_canvas.bind("<Configure>", lambda event, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all")))

# Crear una Label en la parte superior para mostrar el progreso
progress_label_top = tk.Label(root, text="Progreso: 0%", bg="gray", fg="white", anchor="w", padx=5)
progress_label_top.pack(side="top", fill="x")

# Iniciar la ventana
root.mainloop()