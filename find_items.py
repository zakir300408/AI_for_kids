import tkinter as tk
import random
import os
import requests
import zipfile
import pygame
import threading
import time
import tempfile
from pycocotools.coco import COCO
from PIL import Image, ImageTk, ImageDraw
from gtts import gTTS
import tkinter.messagebox as messagebox

# --------------------------
# COCO Dataset Configuration
# -------------------------- 
DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'coco_dataset')
COCO_ANNOTATION_FILE = os.path.join(DATASET_DIR, 'annotations/instances_val2017.json')
COCO_IMAGES_DIR = os.path.join(DATASET_DIR, 'val2017/')

COCO_ANNOTATIONS_URL = 'http://images.cocodataset.org/annotations/annotations_trainval2017.zip'
COCO_VAL_IMAGES_URL = 'http://images.cocodataset.org/zips/val2017.zip'

def download_file(url, target_path):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    response = requests.get(url, stream=True)
    with open(target_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

def extract_zip(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

def ensure_dataset_available():
    if os.path.exists(COCO_ANNOTATION_FILE) and os.path.exists(COCO_IMAGES_DIR):
        return True
    os.makedirs(DATASET_DIR, exist_ok=True)
    annotations_zip = os.path.join(DATASET_DIR, 'annotations.zip')
    try:
        if not os.path.exists(annotations_zip):
            download_file(COCO_ANNOTATIONS_URL, annotations_zip)
        extract_zip(annotations_zip, DATASET_DIR)
        val_images_zip = os.path.join(DATASET_DIR, 'val2017.zip')
        if not os.path.exists(val_images_zip):
            download_file(COCO_VAL_IMAGES_URL, val_images_zip)
        try:
            extract_zip(val_images_zip, DATASET_DIR)
        except zipfile.BadZipFile:
            os.remove(val_images_zip)
            download_file(COCO_VAL_IMAGES_URL, val_images_zip)
            extract_zip(val_images_zip, DATASET_DIR)
        return True
    except:
        return False

if not ensure_dataset_available():
    pass

try:
    coco = COCO(COCO_ANNOTATION_FILE)
except:
    coco = None

pygame.mixer.init()

def play_audio(word):
    try:
        tts = gTTS(text=word, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
        tts.save(temp_path)
        def play_in_thread():
            try:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            except:
                pass
        threading.Thread(target=play_in_thread, daemon=True).start()
    except:
        pass

class LevelSelectionScreen:
    def __init__(self, root, on_level_select):
        self.root = root
        self.on_level_select = on_level_select
        self.root.title("English Learning Game - Level Selection")
        self.root.geometry("500x700")
        self.root.resizable(False, False)
        tk.Label(
            root,
            text="Welcome to the English Learning Game!",
            font=("Comic Sans MS", 20, "bold"),
            fg="#1E90FF",
            wraplength=450,
            justify="center"
        ).pack(pady=(50, 20))
        tk.Label(
            root,
            text="Choose your difficulty level:",
            font=("Comic Sans MS", 16),
            fg="#333333"
        ).pack(pady=10)
        descriptions = [
            "Level 1: Beginner - One object per image",
            "Level 2: Intermediate - Up to two objects per image",
            "Level 3: Advanced - Up to three objects per image"
        ]
        for desc in descriptions:
            tk.Label(
                root,
                text=desc,
                font=("Comic Sans MS", 14),
                fg="#555555",
                justify="left"
            ).pack(pady=5, anchor="w", padx=50)
        button_frame = tk.Frame(root)
        button_frame.pack(pady=40)
        levels = [
            {"text": "Level 1", "color": "#90EE90", "max_objects": 1},
            {"text": "Level 2", "color": "#FFD700", "max_objects": 2},
            {"text": "Level 3", "color": "#FF9999", "max_objects": 3}
        ]
        for level in levels:
            btn = tk.Button(
                button_frame,
                text=level["text"],
                font=("Comic Sans MS", 16, "bold"),
                bg=level["color"],
                width=10,
                height=2,
                command=lambda max_obj=level["max_objects"]: self.select_level(max_obj)
            )
            btn.pack(side="left", padx=10)
        tk.Label(
            root,
            text="You can change the difficulty level later in the settings",
            font=("Comic Sans MS", 12, "italic"),
            fg="#888888"
        ).pack(pady=30)
    def select_level(self, max_objects):
        self.on_level_select(max_objects)

class EnglishLearningGUI:
    def __init__(self, root):
        self.root = root
        self.show_level_selection()
    def show_level_selection(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.level_screen = LevelSelectionScreen(self.root, self.start_game)
    def start_game(self, max_objects):
        self.max_instances = max_objects
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_game_interface()
        self.show_new_word()
    def setup_game_interface(self):
        self.root.title("Learn English Words with COCO Images!")
        self.root.geometry("500x700")
        self.root.resizable(False, False)
        if coco is None:
            messagebox.showerror("Error", "Could not initialize COCO API. Please check dataset availability.")
        self.level_indicator = tk.Label(
            self.root, 
            text=f"Level {self.max_instances}", 
            font=("Comic Sans MS", 12, "italic"),
            fg="#555555"
        )
        self.level_indicator.pack(anchor="ne", padx=10, pady=5)
        self.word_label = tk.Label(self.root, text="", font=("Comic Sans MS", 28, "bold"), fg="#1E90FF")
        self.word_label.pack(pady=10)
        self.definition_label = tk.Label(self.root, text="", font=("Comic Sans MS", 16), 
                                        wraplength=450, justify="center")
        self.definition_label.pack(pady=5)
        self.score_frame = tk.Frame(self.root)
        self.score_frame.pack(pady=5)
        self.score_label = tk.Label(self.score_frame, text="Score:", font=("Comic Sans MS", 16))
        self.score_label.pack(side="left")
        self.score_value = tk.Label(self.score_frame, text="0", font=("Comic Sans MS", 16, "bold"), fg="#228B22")
        self.score_value.pack(side="left", padx=10)
        self.detailed_score_frame = tk.Frame(self.root)
        self.detailed_score_frame.pack(pady=2)
        self.correct_label = tk.Label(self.detailed_score_frame, text="Correct:", font=("Comic Sans MS", 12))
        self.correct_label.pack(side="left", padx=2)
        self.correct_value = tk.Label(self.detailed_score_frame, text="0", font=("Comic Sans MS", 12, "bold"), fg="#228B22")
        self.correct_value.pack(side="left", padx=2)
        self.incorrect_label = tk.Label(self.detailed_score_frame, text="Incorrect:", font=("Comic Sans MS", 12))
        self.incorrect_label.pack(side="left", padx=10)
        self.incorrect_value = tk.Label(self.detailed_score_frame, text="0", font=("Comic Sans MS", 12, "bold"), fg="#FF0000")
        self.incorrect_value.pack(side="left", padx=2)
        self.avg_time_label = tk.Label(self.detailed_score_frame, text="Avg time:", font=("Comic Sans MS", 12))
        self.avg_time_label.pack(side="left", padx=10)
        self.avg_time_value = tk.Label(self.detailed_score_frame, text="0.0s", font=("Comic Sans MS", 12, "bold"), fg="#1E90FF")
        self.avg_time_value.pack(side="left", padx=2)
        self.feedback_label = tk.Label(self.root, text="", font=("Comic Sans MS", 18, "bold"))
        self.feedback_label.pack(pady=5)
        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(pady=10)
        self.image_label = tk.Label(self.image_frame)
        self.image_label.pack()
        self.image_label.bind("<Button-1>", self.check_click)
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        tk.Button(
            btn_frame,
            text="New Word",
            font=("Comic Sans MS", 14),
            command=self.show_new_word,
            bg="#FFD700",
            padx=10,
            pady=5
        ).pack(side="left", padx=10)
        tk.Button(
            btn_frame,
            text="Play Audio",
            font=("Comic Sans MS", 14),
            command=self.play_word_audio,
            bg="#90EE90",
            padx=10,
            pady=5
        ).pack(side="left", padx=10)
        self.show_answers_button = tk.Button(
            btn_frame,
            text="Show Answers",
            font=("Comic Sans MS", 14),
            command=self.show_answers,
            bg="#FF9999",
            padx=10,
            pady=5
        )
        tk.Button(
            btn_frame,
            text="Change Level",
            font=("Comic Sans MS", 14),
            command=self.show_level_selection,
            bg="#CCCCCC",
            padx=10,
            pady=5
        ).pack(side="left", padx=10)
        self.current_word = None
        self.current_category = None
        self.current_bboxes = []
        self.score = 0
        self.image_scale = (1, 1)
        self.last_pil_img = None
        self.correct_answers = 0
        self.incorrect_answers = 0
        self.response_times = []
        self.question_start_time = 0
        self.total_response_time = 0
        self.learning_mode = False
        self.repetitions_left = 0
        self.current_learning_category = None
        self.transitioning = False
        self.last_click_time = 0
        self.click_debounce_ms = 100
        self.min_bbox_size = 80
        self.min_multi_instance_size = 80
        self.max_small_instances = 3
        self.instances_found = set()
        self.total_instances = 0
        self.incorrect_clicks = []

    def show_new_word(self):
        self.transitioning = False
        self.feedback_label.config(text="")
        self.current_bboxes = []
        self.instances_found = set()
        self.total_instances = 0
        self.incorrect_clicks = []
        self.question_start_time = time.time()
        self.show_answers_button.pack_forget()
        if self.learning_mode and self.repetitions_left > 0:
            self.current_category = self.current_learning_category
            self.repetitions_left -= 1
            self.feedback_label.config(text=f"Learning '{self.current_word}' - {self.repetitions_left+1} remaining", fg="#1E90FF")
            if self.repetitions_left <= 0:
                self.learning_mode = False
        else:
            cat_ids = coco.getCatIds()
            if not cat_ids:
                self.image_label.config(text="No COCO categories available.", image="")
                return
            cats = coco.loadCats(cat_ids)
            random_cat = random.choice(cats)
            cat_name = random_cat['name']
            self.current_word = cat_name
            self.current_category = cat_name.lower()
        if not self.learning_mode:
            self.word_label.config(text=f"Find {self.current_category}")
        self.definition_label.config(text="Click on the image where you see the object")
        cat_ids = coco.getCatIds(catNms=[self.current_category])
        if not cat_ids:
            self.image_label.config(text=f"No COCO category named '{self.current_category}' found.", image="")
            return
        image_ids = coco.getImgIds(catIds=cat_ids)
        if not image_ids:
            self.image_label.config(text="No images available for this category.", image="")
            return
        max_attempts = 5
        for attempt in range(max_attempts):
            random_img_id = random.choice(image_ids)
            img_info = coco.loadImgs(random_img_id)[0]
            img_path = os.path.join(COCO_IMAGES_DIR, img_info['file_name'])
            try:
                pil_img = Image.open(img_path)
                orig_width, orig_height = pil_img.size
                ann_ids = coco.getAnnIds(imgIds=random_img_id, catIds=cat_ids, iscrowd=None)
                anns = coco.loadAnns(ann_ids)
                temp_bboxes = []
                small_instances_count = 0
                for ann in anns:
                    if ann['category_id'] in cat_ids:
                        bbox = ann['bbox']
                        x, y, w, h = [int(v) for v in bbox]
                        if w < self.min_multi_instance_size or h < self.min_multi_instance_size:
                            small_instances_count += 1
                        if w >= self.min_bbox_size and h >= self.min_bbox_size:
                            temp_bboxes.append((x, y, x+w, y+h))
                if len(temp_bboxes) > 1 and small_instances_count > self.max_small_instances:
                    continue
                if len(temp_bboxes) > self.max_instances:
                    continue
                if temp_bboxes:
                    self.current_bboxes = temp_bboxes
                    break
            except:
                pass
        if not self.current_bboxes:
            if not self.learning_mode:
                self.show_new_word()
                return
            else:
                self.image_label.config(text=f"No suitable images found for '{self.current_category}'.", image="")
                return
        self.total_instances = len(self.current_bboxes)
        if self.total_instances > 1:
            self.definition_label.config(text=f"Find ALL {self.total_instances} instances of this object!")
            self.show_answers_button.pack(side="left", padx=10)
        else:
            self.show_answers_button.pack_forget()
        display_width, display_height = 300, 300
        self.image_scale = (display_width / orig_width, display_height / orig_height)
        pil_img = pil_img.resize((display_width, display_height), Image.Resampling.LANCZOS)
        self.last_pil_img = pil_img.copy()
        self.photo = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=self.photo, text="")
        self.image_label.image = self.photo
        self.play_word_audio()

    def check_click(self, event):
        if not self.current_bboxes:
            return
        current_time = int(time.time() * 1000)
        if self.transitioning or (current_time - self.last_click_time < self.click_debounce_ms):
            return
        self.last_click_time = current_time
        x, y = event.x, event.y
        original_x = x / self.image_scale[0]
        original_y = y / self.image_scale[1]
        found_object = False
        for i, bbox in enumerate(self.current_bboxes):
            x1, y1, x2, y2 = bbox
            if x1 <= original_x <= x2 and y1 <= original_y <= y2:
                if i not in self.instances_found:
                    self.instances_found.add(i)
                    found_object = True
                    break
        if found_object:
            instances_found_count = len(self.instances_found)
            if self.last_pil_img:
                img_copy = self.last_pil_img.copy()
                draw = ImageDraw.Draw(img_copy)
                scale_x, scale_y = self.image_scale
                for i in self.instances_found:
                    x1, y1, x2, y2 = self.current_bboxes[i]
                    draw.rectangle(
                        [(x1 * scale_x, y1 * scale_y), (x2 * scale_x, y2 * scale_y)],
                        outline="green",
                        width=3
                    )
                for ix, iy in self.incorrect_clicks:
                    ix_display = ix * scale_x
                    iy_display = iy * scale_y
                    size = 5
                    draw.line([(ix_display-size, iy_display-size), (ix_display+size, iy_display+size)], fill="red", width=2)
                    draw.line([(ix_display-size, iy_display+size), (ix_display+size, iy_display-size)], fill="red", width=2)
                self.photo = ImageTk.PhotoImage(img_copy)
                self.image_label.config(image=self.photo)
                self.image_label.image = self.photo
            if instances_found_count < self.total_instances:
                self.feedback_label.config(
                    text=f"✓ Good job! Find {self.total_instances - instances_found_count} more!", 
                    fg="#008000"
                )
                play_audio("Good job! Find more!")
            else:
                response_time = time.time() - self.question_start_time
                if not self.learning_mode:
                    self.correct_answers += 1
                    self.response_times.append(response_time)
                    self.total_response_time += response_time
                    self.correct_value.config(text=str(self.correct_answers))
                    avg_time = self.total_response_time / len(self.response_times)
                    self.avg_time_value.config(text=f"{avg_time:.1f}s")
                    self.calculate_score()
                self.feedback_label.config(text="✓ Great! You found all of them!", fg="#008000")
                play_audio("Great! You found all of them!")
                self.transitioning = True
                self.root.after(1500, self.safe_show_new_word)
        else:
            self.incorrect_clicks.append((original_x, original_y))
            if not self.learning_mode:
                self.incorrect_answers += 1
                self.incorrect_value.config(text=str(self.incorrect_answers))
                self.calculate_score()
            if self.last_pil_img:
                img_copy = self.last_pil_img.copy()
                draw = ImageDraw.Draw(img_copy)
                scale_x, scale_y = self.image_scale
                for i in self.instances_found:
                    x1, y1, x2, y2 = self.current_bboxes[i]
                    draw.rectangle(
                        [(x1 * scale_x, y1 * scale_y), (x2 * scale_x, y2 * scale_y)], 
                        outline="green",
                        width=3
                    )
                for ix, iy in self.incorrect_clicks:
                    ix_display = ix * scale_x
                    iy_display = iy * scale_y
                    size = 5
                    draw.line([(ix_display-size, iy_display-size), (ix_display+size, iy_display+size)], fill="red", width=2)
                    draw.line([(ix_display-size, iy_display+size), (ix_display+size, iy_display-size)], fill="red", width=2)
                self.photo = ImageTk.PhotoImage(img_copy)
                self.image_label.config(image=self.photo)
                self.image_label.image = self.photo
            if len(self.incorrect_clicks) >= 3 and self.total_instances > 1:
                self.show_answers_button.config(bg="#FF6347")
            self.feedback_label.config(text="✗ Try again!", fg="#FF0000")
            play_audio("Try again")
            if not self.learning_mode and len(self.incorrect_clicks) >= 5:
                self.learning_mode = True
                self.repetitions_left = 3
                self.current_learning_category = self.current_category
                self.current_word = self.current_category.capitalize()

    def show_answers(self):
        if not self.learning_mode:
            missed_count = self.total_instances - len(self.instances_found)
            if missed_count > 0:
                self.incorrect_answers += missed_count
                self.incorrect_value.config(text=str(self.incorrect_answers))
                self.calculate_score()
        if self.last_pil_img:
            img_copy = self.last_pil_img.copy()
            draw = ImageDraw.Draw(img_copy)
            scale_x, scale_y = self.image_scale
            for i, (x1, y1, x2, y2) in enumerate(self.current_bboxes):
                color = "green" if i in self.instances_found else "red"
                draw.rectangle(
                    [(x1 * scale_x, y1 * scale_y), (x2 * scale_x, y2 * scale_y)],
                    outline=color,
                    width=3
                )
            for ix, iy in self.incorrect_clicks:
                ix_display = ix * scale_x
                iy_display = iy * scale_y
                size = 5
                draw.line([(ix_display-size, iy_display-size), (ix_display+size, iy_display+size)], fill="red", width=2)
                draw.line([(ix_display-size, iy_display+size), (ix_display+size, iy_display-size)], fill="red", width=2)
            self.photo = ImageTk.PhotoImage(img_copy)
            self.image_label.config(image=self.photo)
            self.image_label.image = self.photo
        missed_count = self.total_instances - len(self.instances_found)
        if missed_count > 0:
            self.feedback_label.config(
                text=f"You missed {missed_count} {self.current_category}(s)", 
                fg="#FF0000"
            )
            play_audio(f"You missed {missed_count} objects")
        if not self.learning_mode:
            self.learning_mode = True
            self.repetitions_left = 3
            self.current_learning_category = self.current_category
            self.current_word = self.current_category.capitalize()
        self.transitioning = True
        self.root.after(3000, self.safe_show_new_word)

    def safe_show_new_word(self):
        if self.transitioning:
            self.show_new_word()
    
    def play_word_audio(self):
        if self.current_word:
            play_audio(f"Find {self.current_word}")

    def calculate_score(self):
        if self.correct_answers == 0:
            self.score = 0
            self.score_value.config(text="0")
            return
        total_attempts = self.correct_answers + self.incorrect_answers
        accuracy = (self.correct_answers / total_attempts) * 100
        avg_time = self.total_response_time / len(self.response_times)
        speed_bonus = max(0, 50 - min(50, avg_time * 5))  
        self.score = int(accuracy + speed_bonus)
        self.score_value.config(text=str(self.score))

if __name__ == '__main__':
    root = tk.Tk()
    app = EnglishLearningGUI(root)
    root.mainloop()