import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps

CONFIG_FILE = 'config.json'

class ImageAnnotator:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Annotator")
        self.root.state('zoomed')  # Start in full-screen mode

        self.image_folder = ""
        self.output_folder = ""
        self.json_file = ""
        self.image_list = []
        self.omitted_images = []
        self.omitted_reasons = {}
        self.current_image_index = -1
        self.annotations = {}

        self.create_widgets()
        self.load_config()
        self.populate_image_list()  # Populate the image list after loading config
        self.update_annotation_state()

        self.root.bind("<Configure>", self.on_resize)  # Bind the resize event

    def on_resize(self, event):
        self.options_frame.configure(scrollregion=self.options_frame.bbox("all"))

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                config = json.load(file)
                self.image_folder = config.get('image_folder', "")
                self.output_folder = config.get('output_folder', "")
                self.json_file = config.get('json_file', "")
                self.omitted_images = config.get('omitted_images', [])
                self.omitted_reasons = config.get('omitted_reasons', {})

                self.input_path_label.config(text=f"Input Folder: {self.image_folder if self.image_folder else 'No folder selected'}")
                self.output_path_label.config(text=f"Output Folder: {self.output_folder if self.output_folder else 'No folder selected'}")
                self.json_path_label.config(text=f"JSON File: {self.json_file if self.json_file else 'No JSON file selected'}")

                if self.json_file and os.path.exists(self.json_file):
                    self.load_annotations(from_startup=True)

    def save_config(self):
        config = {
            'image_folder': self.image_folder,
            'output_folder': self.output_folder,
            'json_file': self.json_file,
            'omitted_images': self.omitted_images,
            'omitted_reasons': self.omitted_reasons
        }
        with open(CONFIG_FILE, 'w') as file:
            json.dump(config, file)

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        self.create_welcome_page()
        self.create_annotation_page()
        self.create_omitted_page()
        self.create_statistics_page()

    def create_welcome_page(self):
        self.welcome_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.welcome_frame, text='Welcome')

        self.select_input_btn = ttk.Button(self.welcome_frame, text="Select Input Folder", command=self.select_image_folder)
        self.select_input_btn.pack(pady=10)

        self.input_path_label = ttk.Label(self.welcome_frame, text=f"Input Folder: {self.image_folder if self.image_folder else 'No folder selected'}")
        self.input_path_label.pack(pady=5)

        self.select_output_btn = ttk.Button(self.welcome_frame, text="Select Output Folder", command=self.select_output_folder)
        self.select_output_btn.pack(pady=10)

        self.output_path_label = ttk.Label(self.welcome_frame, text=f"Output Folder: {self.output_folder if self.output_folder else 'No folder selected'}")
        self.output_path_label.pack(pady=5)

        self.load_annotations_btn = ttk.Button(self.welcome_frame, text="Load JSON File", command=self.load_annotations)
        self.load_annotations_btn.pack(pady=10)

        self.json_path_label = ttk.Label(self.welcome_frame, text=f"JSON File: {self.json_file if self.json_file else 'No JSON file selected'}")
        self.json_path_label.pack(pady=5)

        self.start_annotation_btn = ttk.Button(self.welcome_frame, text="Start Annotation", command=self.start_annotation)
        self.start_annotation_btn.pack(pady=10)

        instructions_text = (
            "Instructions:\n"
            "\n1. Select an input folder containing the images you want to annotate.\n"
            "\n2. Select an output folder where the annotations will be saved.\n"
            "\n3. Optionally, load an existing JSON file to continue annotations.\n"
            "\n4. Click 'Start Annotation' to begin annotating the images."
        )
        self.instructions_label = ttk.Label(self.welcome_frame, text=instructions_text, font=("Helvetica", 10, "bold"))
        self.instructions_label.pack(pady=20)

    def create_annotation_page(self):
        self.annotation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.annotation_frame, text='Annotate')

        self.image_frame = ttk.Frame(self.annotation_frame)
        self.image_frame.pack(side='left', expand=True, fill='both', padx=10, pady=10)

        self.image_label = ttk.Label(self.image_frame, borderwidth=5, relief="solid")
        self.image_label.pack()

        self.not_annotated_label = ttk.Label(self.image_frame, text="", foreground="red")
        self.not_annotated_label.pack(pady=(10, 20))

        self.buttons_frame = ttk.Frame(self.image_frame)
        self.buttons_frame.pack(pady=10)

        self.save_btn = tk.Button(self.buttons_frame, text="Save Annotation", command=self.save_annotation, bg='green', fg='white')
        self.save_btn.pack(side='left', padx=5)

        self.prev_btn = tk.Button(self.buttons_frame, text="Previous Image", command=self.prev_image, bg='blue', fg='white')
        self.prev_btn.pack(side='left', padx=5)

        self.next_btn = tk.Button(self.buttons_frame, text="Next Image", command=self.next_image, bg='blue', fg='white')
        self.next_btn.pack(side='left', padx=5)

        self.omit_btn = tk.Button(self.buttons_frame, text="Omit Image", command=self.omit_image, bg='red', fg='white')
        self.omit_btn.pack(side='left', padx=5)

        self.omit_reason_label = ttk.Label(self.image_frame, text="Reason for omitting:")
        self.omit_reason_label.pack(pady=(10, 0))

        self.omit_reason_var = tk.StringVar()
        self.omit_reason_entry = ttk.Entry(self.image_frame, textvariable=self.omit_reason_var, width=50)
        self.omit_reason_entry.pack(pady=(0, 20))

        self.buttons_frame.pack(anchor='center')  # Center the buttons frame

        self.counter_label = ttk.Label(self.image_frame, text="", font=("Helvetica", 12, "bold"))
        self.counter_label.pack(pady=10)

        self.next_unannotated_btn = ttk.Button(self.image_frame, text="Next Unannotated Image", command=self.next_unannotated_image)
        self.next_unannotated_btn.pack(pady=10)

        self.search_frame = ttk.Frame(self.image_frame)
        self.search_frame.pack(pady=10)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind("<Return>", self.search_image)  # Bind Enter key to search function

        self.search_btn = ttk.Button(self.search_frame, text="Search Image", command=self.search_image)
        self.search_btn.pack(side='left', padx=5)

        # Create a frame to hold both scrollbars
        self.scrollbar_frame = ttk.Frame(self.annotation_frame)
        self.scrollbar_frame.pack(side='right', fill='y', padx=10, pady=10)

        self.v_scrollbar = ttk.Scrollbar(self.scrollbar_frame, orient="vertical")
        self.v_scrollbar.pack(side="right", fill="y")

        self.h_scrollbar = ttk.Scrollbar(self.scrollbar_frame, orient="horizontal")
        self.h_scrollbar.pack(side="top", fill="x")

        self.options_frame = tk.Canvas(self.annotation_frame, yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)  # Use tk.Canvas to add scrollbar
        self.options_frame.pack(side='right', fill='both', expand=True)

        self.options_frame.bind("<Configure>", self.on_options_frame_resize)  # Adjust scroll region on resize

        self.v_scrollbar.config(command=self.options_frame.yview)
        self.h_scrollbar.config(command=self.options_frame.xview)

        self.options_inner_frame = ttk.Frame(self.options_frame)
        self.options_frame.create_window((0, 0), window=self.options_inner_frame, anchor='nw')

        self.create_annotation_fields()

        # Bind mouse wheel to horizontal scrollbar
        self.options_frame.bind("<Enter>", self.bind_mousewheel)
        self.options_frame.bind("<Leave>", self.unbind_mousewheel)

    def create_omitted_page(self):
        self.omitted_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.omitted_frame, text='Omitted Images')

        self.omitted_listbox = tk.Listbox(self.omitted_frame)
        self.omitted_listbox.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        self.omitted_listbox.bind("<<ListboxSelect>>", self.display_omitted_image)

        self.omitted_image_label = ttk.Label(self.omitted_frame, borderwidth=5, relief="solid")
        self.omitted_image_label.pack(side='right', padx=10, pady=10)

    def create_statistics_page(self):
        self.statistics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.statistics_frame, text='Statistics')

        self.stats_label = ttk.Label(self.statistics_frame, text="", font=("Helvetica", 12, "bold"))
        self.stats_label.pack(pady=20)

        self.update_stats_button = ttk.Button(self.statistics_frame, text="Update Statistics", command=self.update_statistics)
        self.update_stats_button.pack(pady=10)

    def update_statistics(self):
        if not self.annotations:
            self.stats_label.config(text="No annotations available to display statistics.")
            return

        total = len(self.annotations)
        stats = {}

        for annotation in self.annotations.values():
            for key, value in annotation.items():
                if key not in ["id", "filename", "dimensions"]:
                    if isinstance(value, bool):
                        value = "yes" if value else "no"
                    if value not in stats:
                        stats[value] = 0
                    stats[value] += 1

        stats_text = "Statistics:\n\n"
        for key, count in stats.items():
            percentage = (count / total) * 100
            stats_text += f"{key.capitalize()}: {percentage:.2f}%\n"

        self.stats_label.config(text=stats_text)

    def bind_mousewheel(self, event):
        self.options_frame.bind_all("<MouseWheel>", self.on_mousewheel)
        self.options_frame.bind_all("<Shift-MouseWheel>", self.on_shift_mousewheel)

    def unbind_mousewheel(self, event):
        self.options_frame.unbind_all("<MouseWheel>")
        self.options_frame.unbind_all("<Shift-MouseWheel>")

    def on_mousewheel(self, event):
        self.options_frame.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_shift_mousewheel(self, event):
        self.options_frame.xview_scroll(int(-1*(event.delta/120)), "units")

    def on_options_frame_resize(self, event):
        self.options_frame.configure(scrollregion=self.options_frame.bbox("all"))

    def create_annotation_fields(self):
        # Metadata
        metadata_label = ttk.Label(self.options_inner_frame, text="Metadata", font=("Helvetica", 12, "bold"))
        metadata_label.pack(fill='x', pady=(10, 0))
        self.id_var = tk.StringVar()
        self.filename_var = tk.StringVar()
        self.dimensions_var = tk.StringVar()
        self.create_label_and_entry("ID:", self.id_var)
        self.create_label_and_entry("Filename:", self.filename_var)
        self.create_label_and_entry("Image Dimensions:", self.dimensions_var)

        # Divider
        self.create_divider()

        # Facial Features and Additional Features
        facial_features_label = ttk.Label(self.options_inner_frame, text="Facial Features", font=("Helvetica", 12, "bold"))
        facial_features_label.pack(fill='x', pady=(10, 0))

        # Hair Attributes
        hair_attributes_label = ttk.Label(self.options_inner_frame, text="Hair Attributes", font=("Helvetica", 10, "bold"))
        hair_attributes_label.pack(fill='x', pady=(5, 0))

        self.hair_color_var = tk.StringVar()
        self.create_label_and_radiobuttons("Hair Color:", self.hair_color_var, ["", "black", "brown", "blonde", "red", "gray",  "pink", "other"])

        self.hair_length_var = tk.StringVar()
        self.create_label_and_radiobuttons("Hair Length:", self.hair_length_var, ["", "short", "medium", "long"])

        self.hair_style_var = tk.StringVar()
        self.create_label_and_radiobuttons("Hair Style:", self.hair_style_var, ["", "straight", "wavy", "curly", "bald"])

        # Divider
        self.create_divider()

        # Eye Attributes
        eye_attributes_label = ttk.Label(self.options_inner_frame, text="Eye Attributes", font=("Helvetica", 10, "bold"))
        eye_attributes_label.pack(fill='x', pady=(5, 0))

        self.eye_color_var = tk.StringVar()
        self.create_label_and_radiobuttons("Eye Color:", self.eye_color_var, ["", "blue", "green", "brown", "gray","black", "other"])

        # Divider
        self.create_divider()

        # Glasses Attributes
        glasses_attributes_label = ttk.Label(self.options_inner_frame, text="Glasses Attributes", font=("Helvetica", 10, "bold"))
        glasses_attributes_label.pack(fill='x', pady=(5, 0))

        self.glasses_var = tk.BooleanVar()
        self.glasses_type_var = tk.StringVar()
        self.create_label_and_checkbutton("Glasses:", self.glasses_var)
        self.create_label_and_radiobuttons("Glasses Type:", self.glasses_type_var, ["", "reading glasses", "sunglasses", "other"])

        # Divider
        self.create_divider()

        # Hat Attributes
        hat_attributes_label = ttk.Label(self.options_inner_frame, text="Hat Attributes", font=("Helvetica", 10, "bold"))
        hat_attributes_label.pack(fill='x', pady=(5, 0))

        self.hat_var = tk.BooleanVar()
        self.hat_type_var = tk.StringVar()
        self.create_label_and_checkbutton("Wearing Hat:", self.hat_var)
        self.create_label_and_radiobuttons("Hat Type:", self.hat_type_var, ["", "cap", "beanie", "fedora", "other"])

        # Divider
        self.create_divider()

        # Facial Structure Attributes
        facial_structure_label = ttk.Label(self.options_inner_frame, text="Facial Structure", font=("Helvetica", 10, "bold"))
        facial_structure_label.pack(fill='x', pady=(5, 0))

        self.face_shape_var = tk.StringVar()
        self.create_label_and_radiobuttons("Face Shape:", self.face_shape_var, ["", "round", "oval", "square", "heart"])

        self.ethnicity_var = tk.StringVar()
        self.create_label_and_radiobuttons("Ethnicity:", self.ethnicity_var, ["", "asian", "black", "caucasian", "hispanic","indian",  "other"])

        # Divider
        self.create_divider()

        # Additional Attributes
        additional_attributes_label = ttk.Label(self.options_inner_frame, text="Additional Attributes", font=("Helvetica", 10, "bold"))
        additional_attributes_label.pack(fill='x', pady=(5, 0))

        self.age_var = tk.StringVar()
        self.create_label_and_radiobuttons("Age Range:", self.age_var, ["", "0-10", "11-20", "21-30", "31-40", "41-50", "51-60", "61-70", "71+"])

        self.gender_var = tk.StringVar()
        self.create_label_and_radiobuttons("Gender:", self.gender_var, ["", "male", "female"])

        self.expression_var = tk.StringVar()
        self.create_label_and_radiobuttons("Expression:", self.expression_var, ["", "happy", "sad", "neutral", "angry", "surprised", "confused", "disgusted", "fearful"])

        self.beard_var = tk.BooleanVar()
        self.mustache_var = tk.BooleanVar()
        self.create_label_and_checkbutton("Beard:", self.beard_var)
        self.create_label_and_checkbutton("Mustache:", self.mustache_var)

    def create_label_and_entry(self, text, variable):
        frame = ttk.Frame(self.options_inner_frame)
        frame.pack(fill='x', padx=10, pady=5)

        label = ttk.Label(frame, text=text, font=("Helvetica", 10, "bold"), width=20, anchor='w')
        label.pack(side='left')

        entry = ttk.Entry(frame, textvariable=variable, width=30)
        entry.pack(side='left')

    def create_label_and_checkbutton(self, text, variable):
        frame = ttk.Frame(self.options_inner_frame)
        frame.pack(fill='x', padx=10, pady=5)

        label = ttk.Label(frame, text=text, font=("Helvetica", 10, "bold"), width=20, anchor='w')
        label.pack(side='left')

        checkbutton = ttk.Checkbutton(frame, variable=variable)
        checkbutton.pack(side='left')

    def create_label_and_radiobuttons(self, text, variable, options):
        frame = ttk.Frame(self.options_inner_frame)
        frame.pack(fill='x', padx=10, pady=5)

        label = ttk.Label(frame, text=text, font=("Helvetica", 10, "bold"), width=20, anchor='w')
        label.pack(side='left')

        button_frame = ttk.Frame(frame)
        button_frame.pack(side='left')
        for option in options:
            radiobutton = ttk.Radiobutton(button_frame, text=option.capitalize() if option else "Uncheck", variable=variable, value=option)
            radiobutton.pack(side='left')

    def create_divider(self):
        divider = ttk.Separator(self.options_inner_frame, orient='horizontal')
        divider.pack(fill='x', pady=10)

    def select_image_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.image_folder = folder
            self.populate_image_list()
            self.input_path_label.config(text=f"Input Folder: {self.image_folder}")
            self.save_config()
            self.update_counter()
            self.update_annotation_state()
            self.update_omitted_list()  # Update omitted list after selecting folder

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            self.output_path_label.config(text=f"Output Folder: {self.output_folder}")
            self.save_config()
            self.update_annotation_state()

    def load_annotations(self, from_startup=False):
        if from_startup:
            file_path = self.json_file
        else:
            file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
            self.json_file = file_path

        if file_path:
            try:
                with open(file_path, 'r') as file:
                    self.annotations = json.load(file)
                    self.json_path_label.config(text=f"JSON File: {self.json_file}")
                    self.save_config()
                    self.update_counter()
                    print(f"Loaded annotations from {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load JSON file: {e}")

    def start_annotation(self):
        if self.image_folder and self.output_folder:
            self.update_counter()  # Update the counter immediately when starting annotation
            self.notebook.select(self.annotation_frame)
            self.next_image()
        else:
            messagebox.showerror("Error", "Please select both input and output folders.")

    def populate_image_list(self):
        if os.path.exists(self.image_folder):
            self.image_list = [f for f in os.listdir(self.image_folder) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
            self.current_image_index = -1
            # Remove omitted images from the image list
            self.image_list = [img for img in self.image_list if img not in self.omitted_images]
        else:
            self.image_list = []
            self.current_image_index = -1
            self.image_folder = ""
            self.input_path_label.config(text="Input Folder: No folder selected")

    def display_image(self):
        if self.current_image_index < 0 or self.current_image_index >= len(self.image_list):
            return

        image_path = os.path.join(self.image_folder, self.image_list[self.current_image_index])
        image = Image.open(image_path)
        image.thumbnail((500, 500))

        # Add a border around the image based on annotation status
        image_name = self.image_list[self.current_image_index]
        border_color = "green" if image_name in self.annotations else "red"
        image_with_border = ImageOps.expand(image, border=5, fill=border_color)

        photo = ImageTk.PhotoImage(image_with_border)

        self.image_label.config(image=photo)
        self.image_label.image = photo

        image_id = str(self.current_image_index + 1)
        dimensions = f"{image.width}x{image.height}"

        self.id_var.set(image_id)
        self.filename_var.set(image_name)
        self.dimensions_var.set(dimensions)

        if image_name in self.annotations:
            self.not_annotated_label.config(text="Annotated", foreground="green")
            self.load_annotation_fields(image_name)
        else:
            self.not_annotated_label.config(text="Not Annotated", foreground="red")
            self.clear_annotation_fields()

    def display_omitted_image(self, event):
        selected_index = self.omitted_listbox.curselection()
        if selected_index:
            image_name = self.omitted_listbox.get(selected_index[0]).split(" - ")[0]
            image_path = os.path.join(self.image_folder, image_name)
            if os.path.exists(image_path):
                image = Image.open(image_path)
                image.thumbnail((500, 500))

                photo = ImageTk.PhotoImage(image)

                self.omitted_image_label.config(image=photo)
                self.omitted_image_label.image = photo

    def load_annotation_fields(self, image_name):
        annotation = self.annotations.get(image_name, {})
        self.hair_color_var.set(annotation.get("hair_color", ""))
        self.hair_length_var.set(annotation.get("hair_length", ""))
        self.hair_style_var.set(annotation.get("hair_style", ""))
        self.eye_color_var.set(annotation.get("eye_color", ""))
        self.glasses_var.set(annotation.get("glasses", False))
        self.glasses_type_var.set(annotation.get("glasses_type", ""))
        self.hat_var.set(annotation.get("hat", False))
        self.hat_type_var.set(annotation.get("hat_type", ""))
        self.face_shape_var.set(annotation.get("face_shape", ""))
        self.ethnicity_var.set(annotation.get("ethnicity", ""))
        self.age_var.set(annotation.get("age", ""))
        self.gender_var.set(annotation.get("gender", ""))
        self.expression_var.set(annotation.get("expression", ""))
        self.beard_var.set(annotation.get("beard", False))
        self.mustache_var.set(annotation.get("mustache", False))

    def clear_annotation_fields(self):
        self.hair_color_var.set("")
        self.hair_length_var.set("")
        self.hair_style_var.set("")
        self.eye_color_var.set("")
        self.glasses_var.set(False)
        self.glasses_type_var.set("")
        self.hat_var.set(False)
        self.hat_type_var.set("")
        self.face_shape_var.set("")
        self.ethnicity_var.set("")
        self.age_var.set("")
        self.gender_var.set("")
        self.expression_var.set("")
        self.beard_var.set(False)
        self.mustache_var.set(False)

    def save_annotation(self):
        if self.current_image_index < 0 or self.current_image_index >= len(self.image_list):
            return

        image_name = self.image_list[self.current_image_index]
        annotation = {
            "id": self.id_var.get(),
            "filename": self.filename_var.get(),
            "dimensions": self.dimensions_var.get(),
            "hair_color": self.hair_color_var.get(),
            "hair_length": self.hair_length_var.get(),
            "hair_style": self.hair_style_var.get(),
            "eye_color": self.eye_color_var.get(),
            "glasses": self.glasses_var.get(),
            "glasses_type": self.glasses_type_var.get(),
            "hat": self.hat_var.get(),
            "hat_type": self.hat_type_var.get(),
            "face_shape": self.face_shape_var.get(),
            "ethnicity": self.ethnicity_var.get(),
            "age": self.age_var.get(),
            "gender": self.gender_var.get(),
            "expression": self.expression_var.get(),
            "beard": self.beard_var.get(),
            "mustache": self.mustache_var.get()
        }

        # Check if any annotation has been made
        if any(annotation[key] for key in annotation if key not in ["id", "filename", "dimensions"]):
            self.annotations[image_name] = annotation

            if self.output_folder:
                output_file = os.path.join(self.output_folder, "annotations.json")
                with open(output_file, 'w') as file:
                    json.dump(self.annotations, file, indent=4)

                # Save the JSON file path to config
                self.json_file = output_file
                self.json_path_label.config(text=f"JSON File: {self.json_file}")
                self.save_config()

            self.not_annotated_label.config(text="Annotated", foreground="green")
            self.update_counter()
            self.display_image()  # Update the border color immediately after saving

    def next_image(self):
        self.save_annotation()
        self.current_image_index += 1
        if self.current_image_index >= len(self.image_list):
            self.current_image_index = 0
        self.display_image()

    def prev_image(self):
        self.save_annotation()
        self.current_image_index -= 1
        if self.current_image_index < 0:
            self.current_image_index = len(self.image_list) - 1
        self.display_image()

    def omit_image(self):
        if self.current_image_index < 0 or self.current_image_index >= len(self.image_list):
            return

        image_name = self.image_list.pop(self.current_image_index)
        self.omitted_images.append(image_name)
        reason = self.omit_reason_var.get()
        self.omitted_reasons[image_name] = reason

        self.omit_reason_var.set("")  # Clear the reason entry field

        self.save_config()  # Save the omitted image and reason to config

        self.update_counter()
        self.update_omitted_list()
        self.next_image()

    def next_unannotated_image(self):
        start_index = self.current_image_index + 1
        for i in range(start_index, len(self.image_list)):
            if self.image_list[i] not in self.annotations:
                self.current_image_index = i
                self.display_image()
                return
        for i in range(0, start_index):
            if self.image_list[i] not in self.annotations:
                self.current_image_index = i
                self.display_image()
                return
        messagebox.showinfo("Info", "All images have been annotated.")

    def search_image(self, event=None):
        search_text = self.search_var.get().strip().lower()
        if not search_text:
            return

        for idx, image_name in enumerate(self.image_list):
            annotation = self.annotations.get(image_name, {})
            image_base_name = os.path.splitext(image_name)[0].lower()
            if search_text == image_base_name or search_text == annotation.get("id", "").lower():
                self.current_image_index = idx
                self.display_image()
                return

        messagebox.showinfo("Info", "Image not found.")

    def update_counter(self):
        total_images = len(self.image_list)
        annotated_images = len(self.annotations)
        unannotated_images = total_images - annotated_images
        self.counter_label.config(text=f"Annotated: {annotated_images} / Not Annotated: {unannotated_images}")

    def update_annotation_state(self):
        state = tk.NORMAL if self.image_folder and self.output_folder else tk.DISABLED

        self.save_btn.config(state=state)
        self.prev_btn.config(state=state)
        self.next_btn.config(state=state)
        self.omit_btn.config(state=state)
        self.omit_reason_entry.config(state=state)
        self.next_unannotated_btn.config(state=state)
        self.search_btn.config(state=state)
        self.search_entry.config(state=state)

        for widget in self.options_inner_frame.winfo_children():
            if isinstance(widget, (tk.Button, ttk.Checkbutton, ttk.Radiobutton, ttk.Entry)):
                widget.config(state=state)

    def update_omitted_list(self):
        self.omitted_listbox.delete(0, tk.END)
        for image_name in self.omitted_images:
            reason = self.omitted_reasons.get(image_name, "")
            self.omitted_listbox.insert(tk.END, f"{image_name} - {reason}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnnotator(root)
    root.mainloop()
