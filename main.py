import ttkbootstrap as tb
from ttkbootstrap.constants import * # Defines INFO, OUTLINE, etc.
import logging
import sys
from app.database import Database
from app.auth import AuthManager
from app.ui_chemical import ChemicalUI
from app.ui_biological import BiologicalUI

# Professional Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("biolab.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("BioLabMain")

class BioLabController:
    """Orchestrates the application flow between Login, Hub, and Inventories."""
    def __init__(self):
        logger.info("BioLab System starting up...")
        self.db = Database()
        self.auth = AuthManager(self.db)
        self.show_login()

    def show_login(self):
        """Initial login interface."""
        self.login_root = tb.Window(themename="flatly", title="BIOLAB Security Login")
        self.login_root.geometry("400x450")
        f = tb.Frame(self.login_root, padding=30); f.pack(expand=True, fill='both')
        
        tb.Label(f, text="BIOLAB LOGIN", font=("Helvetica", 18, "bold")).pack(pady=20)
        # --- Username Field ---
        u = tb.Entry(f)
        u.insert(0, "Username")
        u.bind('<FocusIn>', lambda e: self.on_entry_click(e, u, "Username"))
        u.bind('<FocusOut>', lambda e: self.on_focusout(e, u, "Username"))
        u.pack(pady=10, fill='x')

        # --- Password Field ---
        p = tb.Entry(f)
        p.insert(0, "Password")
        # We don't set show="*" yet, so the user can read the word "Password"
        p.bind('<FocusIn>', lambda e: self.on_entry_click(e, p, "Password"))
        p.bind('<FocusOut>', lambda e: self.on_focusout(e, p, "Password"))
        p.pack(pady=10, fill='x')
        
        tb.Button(f, text="Login", command=lambda: self.attempt(u.get(), p.get())).pack(pady=10, fill='x')
        tb.Button(f, text="Register", bootstyle=OUTLINE, 
                  command=lambda: self.auth.register(u.get(), p.get())).pack(fill='x')
        self.login_root.mainloop()

    def attempt(self, user, pw):
        """Attempts to log in and transitions to Selection Hub."""
        if self.auth.login(user, pw):
            self.login_root.destroy()
            self.start_selection_hub()
        else:
            from tkinter import messagebox
            messagebox.showerror("Access Denied", "Invalid Username or Password.")

    def start_selection_hub(self):
        """Allows user to choose between Chemical or Biological inventories."""
        self.hub = tb.Window(themename="flatly", title="BIOLAB Module Selection")
        self.hub.geometry("500x350")
        f = tb.Frame(self.hub, padding=40); f.pack(expand=True)
        
        tb.Label(f, text="SELECT INVENTORY MODULE", font=("Helvetica", 14, "bold")).pack(pady=20)
        tb.Button(f, text="Chemical Inventory", width=30, bootstyle=INFO, 
                  command=lambda: self.launch("Chemical")).pack(pady=10)
        tb.Button(f, text="Biological Inventory", width=30, bootstyle=SUCCESS, 
                  command=lambda: self.launch("Biological")).pack(pady=10)
        self.hub.mainloop()

    def launch(self, lab_type):
        """Launches the specific inventory dashboard."""
        self.hub.destroy()
        main_root = tb.Window(themename="flatly")
        
        if lab_type == "Chemical":
            ChemicalUI(main_root, self.db, self)
        else:
            BiologicalUI(main_root, self.db, self)
            
        main_root.mainloop()

    def on_entry_click(self,event, entry, default_text):
        """Function to clear placeholder on click"""
        if entry.get() == default_text:
            entry.delete(0, "end")
            entry.insert(0, "")
            # If it's the password field, turn on masking when user types
            if default_text == "Password":
                entry.config(show="*")

    def on_focusout(self, event, entry, default_text):
        """Function to restore placeholder if empty"""
        if entry.get() == "":
            entry.insert(0, default_text)
            # If it's the password field, remove masking so we can see the word "Password"
            if default_text == "Password":
                entry.config(show="")

if __name__ == "__main__":
    try:
        BioLabController()
    except Exception as e:
        logger.critical(f"Unhandled system error: {e}", exc_info=True)