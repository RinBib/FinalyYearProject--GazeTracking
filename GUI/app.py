import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import os, sys

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from real_time import track_eye_activity, import_existing_data_and_generate_report

class EyeTrackingApp(tb.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        self.title("Cognitive Eye Tracker")
        self.geometry("800x480")  # Wider for sidebar space

        self.sidebar_visible = False  # Sidebar toggle state
        self.sidebar_frame = None

        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=True)

        self.frames = {}
        for F in (HomePage, TestPage, ImportPage):
            page_name = F.__name__
            frame = F(parent=self.main_frame, controller=self)
            self.frames[page_name] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("HomePage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.destroy()
            self.sidebar_visible = False
        else:
            self.sidebar_frame = tb.Frame(self, bootstyle="dark")
            self.sidebar_frame.place(x=0, y=50, width=200, height=430)  # Adjusted height for nav bar space

            tb.Label(self.sidebar_frame, text="Options", font=("Helvetica", 14), bootstyle="inverse-dark", takefocus=False).pack(fill=X, pady=10)

            section1 = tb.Label(self.sidebar_frame, text="View Data Folders", font=("Helvetica", 12), bootstyle="secondary", takefocus=False)
            section1.pack(fill=X, pady=5, padx=10)
            section1.bind("<Button-1>", lambda e: self.view_data())
            self.add_hover(section1)

            section2 = tb.Label(self.sidebar_frame, text="Settings", font=("Helvetica", 12), bootstyle="secondary", takefocus=False)
            section2.pack(fill=X, pady=5, padx=10)
            self.add_hover(section2)

            section3 = tb.Label(self.sidebar_frame, text="Exit", font=("Helvetica", 12), bootstyle="danger", takefocus=False)
            section3.pack(fill=X, pady=5, padx=10)
            section3.bind("<Button-1>", lambda e: self.quit())
            self.add_hover(section3)

            self.sidebar_visible = True

    def view_data(self):
        tb.messagebox.showinfo("Data Folders", "Feature to view data folders coming soon!")

    def add_hover(self, widget):
        widget.bind("<Enter>", lambda e: widget.configure(bootstyle="primary"))
        widget.bind("<Leave>", lambda e: widget.configure(bootstyle="secondary" if "Exit" not in widget.cget("text") else "danger"))

class BasePage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Top Navigation Bar
        nav_frame = tb.Frame(self, bootstyle="dark")
        nav_frame.pack(fill=X, side=TOP)

        # Images
        self.menu_img = ImageTk.PhotoImage(Image.open("GUI/burger.png").resize((30, 30)))
        self.home_img = ImageTk.PhotoImage(Image.open("GUI/home-icon-png-31.png").resize((30, 40)))

        # Burger (left)
        menu_button = tb.Button(nav_frame, image=self.menu_img, command=controller.toggle_sidebar, bootstyle="dark", takefocus=False)
        menu_button.pack(side=LEFT, padx=10)
        self.add_hover(menu_button)

        # Home (right)
        home_button = tb.Button(nav_frame, image=self.home_img, command=lambda: controller.show_frame("HomePage"), bootstyle="dark", takefocus=False)
        home_button.pack(side=RIGHT, padx=10)
        self.add_hover(home_button)

    def add_hover(self, button):
        button.bind("<Enter>", lambda e: button.configure(bootstyle="secondary"))
        button.bind("<Leave>", lambda e: button.configure(bootstyle="dark"))

class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        tb.Label(self, text="Welcome to Cognitive Eye Tracker", font=("Helvetica", 16), takefocus=False).pack(pady=100)
        tb.Button(self, text="Start Test", command=lambda: controller.show_frame("TestPage"), bootstyle="success-outline", takefocus=False).pack(pady=10)
        tb.Button(self, text="Import Data", command=lambda: controller.show_frame("ImportPage"), bootstyle="info-outline", takefocus=False).pack(pady=10)
        tb.Button(self, text="Exit", command=controller.quit, bootstyle="danger-outline", takefocus=False).pack(pady=10)

class TestPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        tb.Label(self, text="Test Page (Webcam)", font=("Helvetica", 16), takefocus=False).pack(pady=20)

class ImportPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        tb.Label(self, text="Import Data Page", font=("Helvetica", 16), takefocus=False).pack(pady=20)

if __name__ == "__main__":
    app = EyeTrackingApp()
    app.mainloop()
