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


class ImportPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Title
        tb.Label(self,
                 text="Import Existing Data",
                 font=("Poppins", 16),
                 foreground="#ccd6f6").pack(pady=(40,10))

        # Description
        tb.Label(self,
                 text="Select a folder containing CSV files\n(only .csv will be imported)",
                 font=("Poppins", 12),
                 foreground="#ccd6f6",
                 justify="center").pack(pady=(0,20))

        # Browse button
        tb.Button(self,
                  text="Choose Folder…",
                  bootstyle="dark",
                  width=20,
                  command=self._on_browse).pack(pady=10)

        # Feedback label
        self.msg = tb.Label(self,
                            text="",
                            font=("Poppins", 12),
                            foreground="lightgreen")
        self.msg.pack(pady=(20,0))
        
        
        # Shortcut to Imported-Data view
        tb.Button(
            self,
            text="View Imported Data",
            bootstyle="dark",
            width=20,
            command=self._goto_imported_tab
        ).pack(pady=(10,0))

    def _on_browse(self):
        
        folder = tk.filedialog.askdirectory(title="Select folder with CSV files")
        if not folder:
            return

        user = (
            self.controller.current_user_name
            or self.controller.current_user_email
            or "UnknownUser"
        )

        
        csvs = [f for f in os.listdir(folder) if f.lower().endswith(".csv")]
        if not csvs:
            tk.messagebox.showwarning(
                "No CSVs Found",
                "That folder contains no .csv files."
            )
            return

        if not self.controller.user_data_folder:
            print("User data folder not set!")
            return
        
        import_base = os.path.join(self.controller.user_data_folder, "imported")
        os.makedirs(import_base, exist_ok=True)

        
        existing = [
            d for d in os.listdir(import_base)
            if os.path.isdir(os.path.join(import_base, d))
        ]
        session_name = f"{user}{len(existing) + 1}"
        session_folder = os.path.join(import_base, session_name)
        os.makedirs(session_folder)

        
        for fname in csvs:
            shutil.copy(
                os.path.join(folder, fname),
                os.path.join(session_folder, fname)
            )

        
        import_existing_data_and_generate_report(user, session_folder)

        
        self.msg.config(text=f"Imported {len(csvs)} file(s) as session '{session_name}'")

        
        view_page = self.controller.frames["ViewDataPage"]
        view_page.show_imported_tab()

    def _goto_imported_tab(self):
        
        view = self.controller.frames["ViewDataPage"]
        view.show_imported_tab()                   
        self.controller.show_frame("ViewDataPage") 