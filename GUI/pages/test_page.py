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


class TestPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.controller = controller
        self.preview_size = (640, 480)

        # Use tk.Label so we can fine‐tune borders & highlight
        self.video_label = tk.Label(
            self,
            bg="black",
            borderwidth=0,
            highlightthickness=0,
            relief="flat"
        )
        self.video_label.place(
            relx=0.5, rely=0.5,
            width=self.preview_size[0],
            height=self.preview_size[1],
            anchor="center"
        )

    def begin_countdown(self, seconds=5):
        if seconds > 0:
            self.video_label.config(
                text=str(seconds),
                font=("Poppins", 72, "bold"),
                fg="white",
                image=""  # clear any old frame
            )
            self.after(1000, self.begin_countdown, seconds - 1)
        else:
            self.video_label.config(text="", image="")
            threading.Thread(target=self._run_full_test, daemon=True).start()

    def _update_frame(self, bgr_frame):
        now = time.time()
        if hasattr(self, "_last_update") and now - self._last_update < 1/20:
            return
        self._last_update = now

        w, h = self.preview_size
        frame = cv2.resize(bgr_frame, (w, h))
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        photo = ImageTk.PhotoImage(img)

        self.video_label.config(image=photo, text="")
        self.video_label.image = photo

    def _run_full_test(self):
        patient = self.controller.current_user_name or self.controller.current_user_email or "UnknownUser"
        folder = os.path.join("deterministic_model_test", patient)
        os.makedirs(folder, exist_ok=True)

        track_eye_activity(
            patient_name=patient,
            tracking_duration=10,
            frame_callback=self._update_frame
        )
        import_existing_data_and_generate_report(patient, folder)
        self.after(0, self._finish_test)

    def _finish_test(self):
        view = self.controller.frames["ViewDataPage"]
        view.refresh_all()
        roots = view.rt_tree.get_children()
        if roots:
            files = view.rt_tree.get_children(roots[0])
            if files:
                view.rt_tree.selection_set(files[-1])
                view._on_rt_select(None)

        self.controller.show_frame("ViewDataPage")
        view.notebook.select(view.rt_tab)