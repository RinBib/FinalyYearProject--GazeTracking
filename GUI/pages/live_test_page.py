from .base_page import BasePage
import os
import sys
import shutil
from tkinter import filedialog, messagebox
import pandas as pd
import datetime
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk, ImageOps, ImageSequence, ImageDraw
from tkinter import BOTH, X, Y, TOP, LEFT, RIGHT, END
from tkinter.ttk import Treeview
import tkinter.font as tkfont
from auth import register_user, verify_user, get_user_name
import tkinter.font as tkfont
import tkinter as tk
import threading
import cv2
import time
from tkinter import Toplevel
from tkinter.ttk import Scrollbar



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from real_time import track_eye_activity, import_existing_data_and_generate_report
from GUI.auth import register_user, verify_user, get_user_name


class LiveTestPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        # Label text
        tb.Label(self, text="Running test...", font=("Poppins", 18), foreground="#ccd6f6")\
          .pack(pady=10)

        # Canvas to draw video frames
        self.canvas = tk.Canvas(self, width=640, height=480)
        self.canvas.pack()
        self.photo_image = None  

    def on_show(self):
        # Called every time this page is raised
        user = self.controller.current_user_name or self.controller.current_user_email
        # threading of window
        threading.Thread(target=self._run_test, args=(user,), daemon=True).start()

    def _run_test(self, patient_name):
        # Run tracking test
        def _frame_callback(cv_frame):
            # convert BGR to PIL image
            rgb = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img = img.resize((640,480), Image.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(img)
            # update canvas on the main thread
            self.canvas.after(0, lambda: self.canvas.create_image(0,0,anchor="nw",image=self.photo_image))

        # calling track_eye_activity
        track_eye_activity(patient_name,
                           tracking_duration=10,
                           frame_callback=_frame_callback)

        # after complete, geenrate report (if possible)
        session_folder = os.path.join("deterministic_model_test", patient_name)
        import_existing_data_and_generate_report(patient_name, session_folder)

        # navigate to view data page - real-time tab
        self.after(0, lambda: self.controller.show_frame("ViewDataPage"))