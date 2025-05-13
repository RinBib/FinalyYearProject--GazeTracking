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


class LegalPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        tb.Label(self,
                 text="Where Your Data Goes",
                 font=("Poppins", 24, "bold"),
                 foreground="#ccd6f6")\
          .pack(pady=(40, 10))

        legal_text = (
            "All gaze‐tracking data you generate is stored locally on your machine\n"
            "in the folder:\n\n"
            "    deterministic_model_test/<your-email-or-name>/\n\n"
            "• CSV logs of every session\n"
            "• Weekly and monthly summary charts (PNG)\n"
            "• Optional PDF reports\n\n"
            "We do NOT transmit any data off-device without your explicit consent.\n"
            "You remain in full control of your files at all times."
        )

        tb.Label(self,
                 text=legal_text,
                 font=("Poppins", 12),
                 foreground="#ffffff",
                 background="#0a192f",
                 justify="left",
                 wraplength=750)\
          .pack(padx=40, pady=20)
     
     