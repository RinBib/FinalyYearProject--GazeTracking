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


class AboutPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Page title
        tb.Label(self,
                 text="About This App",
                 font=("Poppins", 24, "bold"),
                 foreground="#ccd6f6")\
          .pack(pady=(40, 10))

        # About text
        about_text = (
            "Cognitive Eye Tracker v1.0\n\n"
            "Dementia is a progressive neurological condition where there is\n"
            "loss of intellectual function, memory impairment, behavioural changes and\n"
            "astract reasoning, usually stemmed from disease of the brain.\n\n"
            "Recent research demonstrates, subbtle changes in eye movement, such as:\n"
            "fixations, blink patterns, saccades and speed, can detect early cognitive\n"
            "symptoms. By continuously gathering gaze metrics, this app seeks trends, weekly\n"
            "and monthly, that may flag early signs of cognitive decline.\n\n"
            "Our intention is to create a non-invasive, secure and age inclusive approach,\n"
            "which offers caregivers, parents and clinicians insights to a users long-term cognitive health\n\n"
            "© 2025 All rights reserved."
        )
        tb.Label(self,
                 text=about_text,
                 font=("Poppins", 12),
                 foreground="#ffffff",
                 background="#0a192f",
                 justify="center",
                 wraplength=750)\
          .pack(padx=40, pady=20)