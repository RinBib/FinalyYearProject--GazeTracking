import os
import sys
import shutil
from tkinter import filedialog, messagebox
import pandas as pd
import datetime
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk, ImageOps, ImageSequence, ImageDraw
from tkinter import BOTH, X, TOP, LEFT, RIGHT, END
from tkinter.ttk import Treeview
import tkinter.font as tkfont
from auth import register_user, verify_user, get_user_name
import tkinter.font as tkfont
import tkinter as tk



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from real_time import track_eye_activity, import_existing_data_and_generate_report


class LoginPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        
        style = tb.Style()
       
        style.map('Primary.TButton',
            background=[('active','#0b5ed7'),   
                        ('pressed','#0a58ca')], 
        )
        # Secondary button
        style.map('Secondary.TButton',
            background=[('active','#5c636a'),   
                        ('pressed','#4d5158')], 
        )

        
        self.email_var    = tk.StringVar()
        self.pw_var       = tk.StringVar()
        self.name_var     = tk.StringVar()
        self.remember_var = tk.BooleanVar(value=False)
        self.msg_var      = tk.StringVar()

        
        self.nb = tb.Notebook(self, bootstyle="secondary.TNotebook")
        self.nb.place(relx=0.5, rely=0.2, anchor='n', width=420, height=360)

       
        login_tab = tb.Frame(self.nb)
        self.nb.add(login_tab, text="Log In")
        self._build_login_grid(login_tab)

        signup_tab = tb.Frame(self.nb)
        self.nb.add(signup_tab, text="Sign Up")
        self._build_signup_grid(signup_tab)

        
        tb.Label(self,
                 textvariable=self.msg_var,
                 font=("Poppins",10),
                 foreground="red")\
          .place(relx=0.5, rely=0.8, anchor='center')

    def _build_login_grid(self, frame):
        frame.columnconfigure(0, weight=1, minsize=120)
        frame.columnconfigure(1, weight=2, minsize=240)

        tb.Label(frame, text="Email:", font=("Poppins",10))\
          .grid(row=0, column=0, sticky='e', pady=(20,5), padx=(10,5))
        tb.Entry(frame, textvariable=self.email_var, font=("Poppins",10))\
          .grid(row=0, column=1, sticky='we', pady=(20,5), padx=(5,10))

        tb.Label(frame, text="Password:", font=("Poppins",10))\
          .grid(row=1, column=0, sticky='e', pady=5, padx=(10,5))
        tb.Entry(frame, textvariable=self.pw_var, show="*", font=("Poppins",10))\
          .grid(row=1, column=1, sticky='we', pady=5, padx=(5,10))

        tk.Checkbutton(
            frame,
            text="Keep me logged in",
            variable=self.remember_var,
            font=("Poppins", 8),
            bg="#273746",
            fg="#ccd6f6",
            selectcolor="#0a192f",
            activebackground="#273746",
            activeforeground="#ccd6f6",
            borderwidth=0,
            highlightthickness=0
        ).grid(row=2, column=0, columnspan=2, pady=10)

        tb.Button(
            frame,
            text="Log In",
            bootstyle="dark",  # uses Primary.TButton
            width=20,
            command=self._on_login
        ).grid(row=3, column=0, columnspan=2, pady=(10,20))

    def _build_signup_grid(self, frame):
        frame.columnconfigure(0, weight=1, minsize=120)
        frame.columnconfigure(1, weight=2, minsize=240)

        tb.Label(frame, text="Name:", font=("Poppins",10))\
          .grid(row=0, column=0, sticky='e', pady=(20,5), padx=(10,5))
        tb.Entry(frame, textvariable=self.name_var, font=("Poppins",10))\
          .grid(row=0, column=1, sticky='we', pady=(20,5), padx=(5,10))

        tb.Label(frame, text="Email:", font=("Poppins",10))\
          .grid(row=1, column=0, sticky='e', pady=5, padx=(10,5))
        tb.Entry(frame, textvariable=self.email_var, font=("Poppins",10))\
          .grid(row=1, column=1, sticky='we', pady=5, padx=(5,10))

        tb.Label(frame, text="Password:", font=("Poppins",10))\
          .grid(row=2, column=0, sticky='e', pady=5, padx=(10,5))
        tb.Entry(frame, textvariable=self.pw_var, show="*", font=("Poppins",10))\
          .grid(row=2, column=1, sticky='we', pady=5, padx=(5,10))

        tk.Checkbutton(
            frame,
            text="Keep me logged in",
            variable=self.remember_var,
            font=("Poppins", 8),
            bg="#273746",
            fg="#ccd6f6",
            selectcolor="#0a192f",
            activebackground="#273746",
            activeforeground="#ccd6f6",
            borderwidth=0,
            highlightthickness=0
        ).grid(row=3, column=0, columnspan=2, pady=10)

        tb.Button(
            frame,
            text="Sign Up",
            bootstyle="dark",  # uses Secondary.TButton
            width=20,
            command=self._on_signup
        ).grid(row=4, column=0, columnspan=2, pady=(10,20))

    def _on_login(self):
        email = self.email_var.get().strip().lower()
        pw    = self.pw_var.get().strip()
        if verify_user(email, pw):
            name = get_user_name(email)
            # store in both the old attrs and your new StringVars
            self.controller.current_user_email      = email
            self.controller.current_user_name       = name
            user_folder = os.path.join("deterministic_model_test", name or email)
            os.makedirs(user_folder, exist_ok=True)
            self.controller.user_data_folder = user_folder

            self.controller.user_email_var.set(email)
            self.controller.user_name_var.set(name)
            self.controller.current_user_display_var.set(email)
            self.controller.user_password_var.set(pw)


            
            self.msg_var.set("")
            self.controller.show_frame("HomePage")
        else:
            self.msg_var.set("Invalid email or password.")

    def _on_signup(self):
        name  = self.name_var.get().strip()
        email = self.email_var.get().strip().lower()
        pw    = self.pw_var.get().strip()

        if not all((name, email, pw)):
            self.msg_var.set("All fields are required.")
        elif register_user(email, pw, name):
            self.msg_var.set("Account created! Please log in.")
            self.nb.select(0)
        else:
            self.msg_var.set("Email already registered.")



class BasePage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        
        style = tb.Style()
        style.configure(
            'TransparentIcon.TButton',
            background='#0a192f',   
            borderwidth=0,
            relief='flat'
        )
        style.map(
            'TransparentIcon.TButton',
            background=[('active', '#1f2d47')], 
            relief=[('pressed','flat'), ('!pressed','flat')]
        )

        
        nav = tb.Frame(self)
        nav.pack(fill=X, side=TOP)

        
        burger_img = Image.open("GUI/burger.png") \
                          .resize((30,30)) \
                          .convert("RGBA")
        inv_b = ImageOps.invert(burger_img.convert("RGB"))
        burger_img = Image.merge(
            "RGBA",
            (*inv_b.split(), burger_img.split()[3])
        )
        self.menu_img = ImageTk.PhotoImage(burger_img)

        home_img = Image.open("GUI/home-icon-png-31.png") \
                        .resize((30,40)) \
                        .convert("RGBA")
        inv_h = ImageOps.invert(home_img.convert("RGB"))
        home_img = Image.merge(
            "RGBA",
            (*inv_h.split(), home_img.split()[3])
        )
        self.home_img = ImageTk.PhotoImage(home_img)

        
        btn_menu = tb.Button(
            nav,
            image=self.menu_img,
            command=controller.toggle_sidebar,
            style='TransparentIcon.TButton',
            takefocus=False
        )
        btn_menu.pack(side=LEFT, padx=5)

        btn_home = tb.Button(
            nav,
            image=self.home_img,
            command=lambda: controller.show_frame("HomePage"),
            style='TransparentIcon.TButton',
            takefocus=False
        )
        btn_home.pack(side=LEFT, padx=5)

class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Load GIF frames
        self.gif_frames = []
        gif = Image.open("GUI/fractal-tree-transparent.gif")
        for frame in ImageSequence.Iterator(gif):
            f = frame.convert("RGBA")\
                     .resize((300,300), Image.LANCZOS)
            self.gif_frames.append(ImageTk.PhotoImage(f))

        # GIF label 
        self.gif_label = tb.Label(self)
        self.gif_label.pack(pady=(30, 10))
        self.animate_gif(0)

        # Title under GIF
        tb.Label(self,
                 text="Cognitive Eye Tracker",
                 font=("Poppins", 24, "bold"),
                 foreground="#ccd6f6").pack(pady=(0, 20))

        # Start / Exit
        tb.Button(self,
                  text="Start",
                  command=lambda: controller.show_frame("InstructionPage"),
                  bootstyle="success-outline",
                  takefocus=False,
                  width=20,
                  padding=30).place(relx=0.1, rely=0.85, anchor='w')
        
        tb.Button(self,
                  text="Exit",
                  command=controller.quit,
                  bootstyle="danger-outline",
                  takefocus=False,
                  width=20,
                  padding=30).place(relx=0.9, rely=0.85, anchor='e')

    def animate_gif(self, idx):
        self.gif_label.config(image=self.gif_frames[idx])
        self.after(100, self.animate_gif, (idx+1) % len(self.gif_frames))





class InstructionPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Instruction box 
        instr_box = tb.Frame(self, style='Instr.TFrame', width=300, height=250)
        instr_box.place(relx=0.1, rely=0.5, anchor='w')
        tb.Label(
            instr_box,
            text=(
                "1. Keep your head inside the oval.\n"
                "2. Follow the moving dot with your eyes for 10 seconds.\n"
                "3. If box turns red, reposition head inside oval.\n\n"
                "Click Begin Test when ready."
            ),
            font=("Poppins", 12),
            foreground="#ccd6f6",
            background='#223344',
            wraplength=280,
            justify="left"
        ).place(x=10, y=10)

        # Helpers to draw the oval and dot
        def make_oval_img(w, h, outline, width):
            img = Image.new("RGBA", (w, h), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            inset = width/2
            draw.ellipse((inset, inset, w-inset, h-inset), outline=outline, width=width)
            return ImageTk.PhotoImage(img)

        def make_dot_img(r, fill):
            d = r*2
            img = Image.new("RGBA", (d, d), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((0,0,d,d), fill=fill)
            return ImageTk.PhotoImage(img)

        # Build once
        oval_w, oval_h = 200, 300
        dot_r, border_w = 20, 4
        dot_d = dot_r*2
        self.oval_img = make_oval_img(oval_w, oval_h, 'red', border_w)
        self.dot_img  = make_dot_img(dot_r, 'yellow')

        # Container for dot + oval
        container_h = dot_d + oval_h
        ovbox = tb.Frame(self, width=oval_w, height=container_h, style='TFrame')
        ovbox.place(relx=0.5, rely=0.5, anchor='center')

        # Place the dot at the top
        lbl_dot = tb.Label(ovbox, image=self.dot_img, background='#0a192f', borderwidth=0)
        lbl_dot.place(x=(oval_w - dot_d)/2, y=0, width=dot_d, height=dot_d)

        # Place the oval below it
        lbl_oval = tb.Label(ovbox, image=self.oval_img, background='#0a192f', borderwidth=0)
        lbl_oval.place(x=0, y=dot_d, width=oval_w, height=oval_h)

        # Begin Test button
        tb.Button(
            self,
            text="Begin Test",
            bootstyle="success-outline",
            takefocus=False,
            command=self._start_test
        ).place(
            relx=0.85, rely=0.5, anchor='e',
            width=260, height=80
        )

    def _start_test(self):
        

        
        patient_name = (
            self.controller.current_user_name
            or self.controller.current_user_email
            or "UnknownUser"
        )

        
        user_folder = os.path.join("deterministic_model_test", patient_name)
        os.makedirs(user_folder, exist_ok=True)

       
        track_eye_activity(patient_name, tracking_duration=10)

        
        import_existing_data_and_generate_report(patient_name, user_folder)

        
        view_page = self.controller.frames["ViewDataPage"]
        view_page._populate_rt()
        roots = view_page.rt_tree.get_children()
        if roots:
            files = view_page.rt_tree.get_children(roots[0])
            if files:
                view_page.rt_tree.selection_set(files[-1])
                view_page._on_rt_select(None)

        #  switch to the Real-Time tab
        self.controller.show_frame("ViewDataPage")


class TestPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        # placeholder
        tb.Label(
            self,
            text="Running the test…",
            font=("Poppins", 18),
            foreground="#ccd6f6"
        ).pack(pady=200)

        
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

    def _on_browse(self):
        # 1️⃣ let the user pick a folder of CSVs
        folder = tk.filedialog.askdirectory(title="Select folder with CSV files")
        if not folder:
            return

        user = (
            self.controller.current_user_name
            or self.controller.current_user_email
            or "UnknownUser"
        )

        # 2️⃣ collect only the .csv files
        csvs = [f for f in os.listdir(folder) if f.lower().endswith(".csv")]
        if not csvs:
            tk.messagebox.showwarning(
                "No CSVs Found",
                "That folder contains no .csv files."
            )
            return

        # 3️⃣ ensure the per-user imported/ base exists
        import_base = os.path.join(self.controller.user_data_folder, "imported")
        os.makedirs(import_base, exist_ok=True)

        # 4️⃣ pick a new session name (User1, User2, …)
        existing = [
            d for d in os.listdir(import_base)
            if os.path.isdir(os.path.join(import_base, d))
        ]
        session_name = f"{user}{len(existing) + 1}"
        session_folder = os.path.join(import_base, session_name)
        os.makedirs(session_folder)

        # 5️⃣ copy CSVs into that session
        for fname in csvs:
            shutil.copy(
                os.path.join(folder, fname),
                os.path.join(session_folder, fname)
            )

        # 6️⃣ process & report on *this* session
        import_existing_data_and_generate_report(user, session_folder)

        # 7️⃣ give feedback
        self.msg.config(text=f"Imported {len(csvs)} file(s) as session '{session_name}'")

        # 8️⃣ show the Imported Data tab (ViewDataPage)
        view_page = self.controller.frames["ViewDataPage"]
        view_page.show_imported_tab()


        
        

class SettingsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        
        nb = tb.Notebook(self, bootstyle="secondary.TNotebook")
        nb.pack(fill=BOTH, expand=True, padx=100, pady=100)

        
        profile_tab = tb.Frame(nb)
        nb.add(profile_tab, text="Profile")
        
         
        tb.Label(profile_tab,
                 text="Name:",
                 font=("Poppins", 12),
                 foreground="#ccd6f6")\
          .grid(row=0, column=0, sticky="w", padx=10, pady=(10,5))

        tb.Label(profile_tab,
                textvariable=controller.user_name_var,
                font=("Poppins",12,"bold"),
                foreground="#ffffff")\
            .grid(row=0, column=1, padx=10, pady=(10,5))
            
        
        
        tb.Label(profile_tab,
                 text="Email:",
                 font=("Poppins", 12),
                 foreground="#ccd6f6")\
          .grid(row=1, column=0, sticky="w", padx=10, pady=5)
              

        tb.Label(profile_tab,
                textvariable=controller.user_email_var,
                font=("Poppins",12,"bold"),
                foreground="#ffffff")\
            .grid(row=1, column=1, padx=10, pady=5)


        
        tb.Label(profile_tab, text="Password:", font=("Poppins",12), foreground="#ccd6f6")\
          .grid(row=2, column=0, sticky="w", padx=10, pady=5)

        pwd_entry = tb.Entry(profile_tab,
                             textvariable=controller.user_password_var,
                             font=("Poppins",12),
                             show="*",
                             state="readonly")
        pwd_entry.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        def toggle_password():
            if pwd_entry.cget("show") == "":
                pwd_entry.config(show="*")
                btn_toggle.config(text="Show")
            else:
                pwd_entry.config(show="")
                btn_toggle.config(text="Hide")

        btn_toggle = tb.Button(profile_tab,
                               text="Show",
                               width=5,
                               bootstyle="secondary",
                               command=toggle_password)
        btn_toggle.grid(row=2, column=2, padx=(5,10), pady=5)

        # (placeholder)
        other_tab = tb.Frame(nb)
        nb.add(other_tab, text="Other")
        tb.Label(other_tab,
                 text="TBC",
                 font=("Poppins", 14),
                 foreground="#888888")\
          .pack(expand=True)

        # (placeholder)
        other_tab = tb.Frame(nb)
        nb.add(other_tab, text="Other")
        tb.Label(other_tab,
                 text="TBC",
                 font=("Poppins", 14),
                 foreground="#888888")\
          .pack(expand=True)
          
        # (placeholder)
        other_tab = tb.Frame(nb)
        nb.add(other_tab, text="Other")
        tb.Label(other_tab,
                 text="TBC",
                 font=("Poppins", 14),
                 foreground="#888888")\
          .pack(expand=True)


        
        btn = tb.Button(self,
                        text="Save Settings",
                        bootstyle="success-outline",
                        command=lambda: tb.messagebox.showinfo("Settings", "Saved!"))
        btn.pack(pady=10)
        
      
        
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
            "............................\n\n"
            "............................\n\n"
            "............................\n\n"
            "............................\n\n"
            "© 2025 All rights reserved."
        )
        tb.Label(self,
                 text=about_text,
                 font=("Poppins", 12),
                 foreground="#ffffff",
                 background="#0a192f",
                 justify="center",
                 wraplength=500)\
          .pack(padx=40, pady=20)
     
     




class ViewDataPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.controller.imported_folder = None

        # Notebook tabs
        self.notebook = tb.Notebook(self, bootstyle="secondary.TNotebook")
        self.notebook.pack(fill=BOTH, expand=True, padx=20, pady=20)

        self.rt_tab  = tb.Frame(self.notebook)
        self.imp_tab = tb.Frame(self.notebook)
        self.notebook.add(self.rt_tab,  text="Real-Time Data")
        self.notebook.add(self.imp_tab, text="Imported Data")

        # Build both panes
        self._build_rt_pane()
        self._build_imp_pane()

    def _build_rt_pane(self):
        paned = tk.PanedWindow(self.rt_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=BOTH, expand=True)

        
        lf = tb.Frame(paned, width=300)
        lf.pack_propagate(False)
        paned.add(lf, stretch="always", minsize=300)

        self.rt_tree = Treeview(lf, show="tree")
        self.rt_tree.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.rt_tree.bind("<<TreeviewSelect>>", self._on_rt_select)
        

        
        rf = tb.Frame(paned)
        paned.add(rf, stretch="always")

        self.rt_text   = tk.Text(rf, wrap="none")
        self.rt_text.pack(fill=X, padx=5, pady=(5,0))
        self.rt_graphs = tb.Frame(rf)
        self.rt_graphs.pack(fill=BOTH, expand=True, padx=5, pady=(5,0))

        # force sash at 300px
        paned.update_idletasks()
        paned.sash_place(0, 300, 0)

        self._populate_rt()

    def _populate_rt(self):
        # Clear
        for iid in self.rt_tree.get_children():  
            self.rt_tree.delete(iid)

        # nothing until user logs in
        user = self.controller.current_user_name or self.controller.current_user_email
        if not user:  
            return

        base = self.controller.user_data_folder
        if os.path.isdir(base):
            root = self.rt_tree.insert("", "end", text=user, open=True)
            for fn in sorted(os.listdir(base)):
                if fn.lower().endswith(".csv"):
                    self.rt_tree.insert(root, "end", text=fn)

    def _on_rt_select(self, _evt):
        sel = self.rt_tree.selection()
        if not sel: return
        item = sel[0]
        if self.rt_tree.parent(item) == "":  
            return
        fn = self.rt_tree.item(item, "text")
        user = self.controller.current_user_name or self.controller.current_user_email
        base = os.path.join("deterministic_model_test", user)

        # load CSV
        df = pd.read_csv(os.path.join(base, fn))
        self.rt_text.delete("1.0", END)
        self.rt_text.insert(END, df.head(20).to_string(index=False))

        # load graphs
        for w in self.rt_graphs.winfo_children():
            w.destroy()
        rootname, _ = os.path.splitext(fn)
        imgs = []
        for img in sorted(os.listdir(base)):
            if img.startswith(rootname) and img.lower().endswith(".png"):
                path = os.path.join(base, img)
                im = Image.open(path).resize((180,180), Image.LANCZOS)
                imgs.append(ImageTk.PhotoImage(im))
        for i,photo in enumerate(imgs):
            lbl = tk.Label(self.rt_graphs, image=photo)
            lbl.image = photo
            lbl.grid(row=i//3, column=i%3, padx=5, pady=5)

    def _build_imp_pane(self):
        paned = tk.PanedWindow(self.imp_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=BOTH, expand=True)

        
        lf = tb.Frame(paned, width=300)
        lf.pack_propagate(False)
        paned.add(lf, stretch="always", minsize=300)

        self.imp_tree = Treeview(lf, show="tree")
        self.imp_tree.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.imp_tree.bind("<<TreeviewSelect>>", self._on_imp_select)

        
        rf = tb.Frame(paned)
        paned.add(rf, stretch="always")
        


        self.imp_text = tk.Text(rf, wrap="none")
        self.imp_text.pack(fill=BOTH, expand=True, padx=5, pady=(5,0))

        paned.update_idletasks()
        paned.sash_place(0, 300, 0)

    def _populate_imp(self):
        # clear tree
        for iid in self.imp_tree.get_children():
            self.imp_tree.delete(iid)

        user = self.controller.current_user_name or self.controller.current_user_email
        if not user:
            return

        base = os.path.join(self.controller.user_data_folder, "imported")
        if not os.path.isdir(base):
            return

        # one root per session folder
        for session in sorted(os.listdir(base)):
            session_path = os.path.join(base, session)
            if not os.path.isdir(session_path):
                continue
            sid = self.imp_tree.insert("", "end", text=session, open=True)
            # list every CSV, PNG, PDF, JPG
            for fn in sorted(os.listdir(session_path)):
                if fn.lower().endswith((".csv", ".png", ".jpg", ".jpeg", ".pdf")):
                    self.imp_tree.insert(sid, "end", text=fn)

    def _on_imp_select(self, _evt):
        sel = self.imp_tree.selection()
        if not sel:
            return
        item   = sel[0]
        parent = self.imp_tree.parent(item)

        # if they clicked the session name itself, show its latest summary
        if parent == "":
            session     = self.imp_tree.item(item, "text")
            session_dir = os.path.join(self.controller.user_data_folder, "imported", session)
            summary_csv = os.path.join(session_dir, "weekly_summary.csv")

            self.imp_text.delete("1.0", END)
            if os.path.exists(summary_csv):
                df = pd.read_csv(summary_csv)
                last = df.iloc[-1]
                self.imp_text.insert(END,
                    f"Session: {session}\n\n"
                    f"Latest Weekly Summary:\n"
                    f"  Week {int(last['Week'])}: {last['Prediction']}"
                )
            else:
                self.imp_text.insert(END,
                    f"Session: {session}\n\n"
                    "No weekly_summary.csv found."
                )
            return

        # otherwise they clicked a file under a session
        fn      = self.imp_tree.item(item, "text")
        session = self.imp_tree.item(parent, "text")
        path    = os.path.join(self.controller.user_data_folder, "imported", session, fn)
        ext     = os.path.splitext(fn)[1].lower()

        self.imp_text.delete("1.0", END)

        if ext == ".csv":
            df = pd.read_csv(path)
            self.imp_text.insert(END, df.head(50).to_string(index=False))

        elif ext in (".png", ".jpg", ".jpeg"):
            img = Image.open(path).resize((300, 300), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            # clear previous image refs
            self.imp_text.image = photo
            self.imp_text.image_create("1.0", image=photo)

        elif ext == ".pdf":
            self.imp_text.insert(END, f"PDF report saved at:\n{path}")

        else:
            self.imp_text.insert(END, f"Cannot preview this file type:\n{fn}")


    def show_imported_tab(self):
        self.notebook.select(self.imp_tab)
        self._populate_imp()
        
        
    def refresh_all(self):
        
        self._populate_rt()
        self._populate_imp()    


class EyeTrackingApp(tb.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        
        
        self.current_user_email = None
        self.current_user_name = None
        self.user_data_folder       = None
        self.imported_folder = None
        self.current_user_display_var = tk.StringVar(value="")
        self.user_name_var  = tk.StringVar(value="")
        self.user_email_var = tk.StringVar(value="")
        self.user_password_var = tk.StringVar()



        self.configure(background='#0a192f')

        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Poppins", size=20)
        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(family="Poppins", size=20)
        heading_font = tkfont.nametofont("TkHeadingFont")
        heading_font.configure(family="Poppins", size=20)

        self.geometry("1200x680")
        self.resizable(False, False)

        style = tb.Style()
        style.configure('TFrame',                        background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('TLabel',                        background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('dark.TFrame',                   background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('dark.TLabel',                   background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('dark.TButton',                  background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('inverse-dark.TLabel',           background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('Outline.Success.TButton',       background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('Outline.Danger.TButton',        background='#0a192f', focusthickness=0, focuscolor='')
        style.configure('Instr.TFrame',                  background='#223344', focusthickness=0, focuscolor='')
        style.configure('OvalBox.TFrame',                background='#273746', focusthickness=0, focuscolor='')
        style.configure('round-toggle.TCheckbutton', font=('Poppins', 8))
        
        style.configure(
            'Sidebar.TButton',
            font=('Poppins', 14),         
            background='#0a192f',         
            bordercolor='#ccd6f6',        
            foreground='#ccd6f6',
            borderwidth=1,
            relief='flat'
        )
        
        style.map(
            'Sidebar.TButton',
            background=[('active', '#0a192f')],     
            bordercolor=[('active','#ffffff')],     
            foreground=[('active','#77e4e5')]      
        )

        self.sidebar_visible = False
        self.sidebar_frame = None

        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=True)

        self.frames = {}
        for F in (LoginPage, HomePage, InstructionPage, ViewDataPage, ImportPage, SettingsPage, AboutPage):
            frame = F(parent=self.main_frame, controller=self)
            self.frames[F.__name__] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("LoginPage")
        

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "refresh_all"):
            frame.refresh_all()


    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.destroy()
        else:
            # same width/height as before
            self.sidebar_frame = tb.Frame(self, bootstyle="dark")
            self.sidebar_frame.place(
                x=0, y=50,
                width=200,
                height=self.winfo_height() - 50
            )

            
            tb.Label(
                self.sidebar_frame,
                text="Menu",
                font=("Poppins", 24),
                foreground="#ccd6f6",
                background="#0a192f"
            ).pack(pady=(15, 10))

            
            for text, action in [
                ("Home",              lambda: self.show_frame("HomePage")),
                ("Start Test",       lambda: self.show_frame("InstructionPage")),
                ("Import Data",       lambda: self.show_frame("ImportPage")),
                ("View Data Files", lambda: self.show_frame("ViewDataPage")),
                ("Settings", lambda: self.show_frame("SettingsPage")),
                ("About", lambda: self.show_frame("AboutPage")),
                ("Log Out",           self.logout),
                ("Exit",              self.quit)
            ]:
                btn = tb.Button(
                    self.sidebar_frame,
                    text=text,
                    style='Sidebar.TButton',
                    takefocus=False,
                    command=action
                )
                
                btn.pack(fill=X, padx=10, pady=6)

        self.sidebar_visible = not self.sidebar_visible

    def view_data(self):
        tb.messagebox.showinfo("Data Folders", "Feature to view data folders coming soon!")

    def add_hover(self, widget):
        widget.bind("<Enter>", lambda e: widget.configure(bootstyle="primary"))
        widget.bind(
            "<Leave>",
            lambda e: widget.configure(
                bootstyle="danger" if widget.cget("text") == "Exit" else "secondary"
            )
        )
        
    def logout(self):
        # hide the sidebar if it's open
        if self.sidebar_visible:
            self.sidebar_frame.destroy()
            self.sidebar_visible = False
        # clear user info
        self.current_user_email = None
        self.current_user_name  = None
        self.current_user_display_var.set("")
        self.user_password_var.set("")

        # go back to login
        self.show_frame("LoginPage")




if __name__ == "__main__":
    app = EyeTrackingApp()
    app.mainloop()