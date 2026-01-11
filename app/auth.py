import hashlib
import logging
from tkinter import messagebox

logger = logging.getLogger(__name__)

class AuthManager:
    """Handles user security, password hashing, and session validation."""
    def __init__(self, db):
        self.db = db

    def hash_password(self, password):
        """Hashes plain text password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username, password):
        """Validates credentials against the database."""
        if not username or not password:
            return False
        
        hashed = self.hash_password(password)
        res = self.db.query("SELECT * FROM users WHERE username=? AND password=?", (username, hashed))
        
        if res:
            logger.info(f"AUDIT: Successful login for user '{username}'")
            return True
        
        logger.warning(f"SECURITY: Failed login attempt for '{username}'")
        return False

    def register(self, username, password):
        """Creates a new user account with a hashed password."""
        if not username or not password:
            messagebox.showwarning("Input Error", "Username and Password cannot be empty.")
            return False
            
        hashed = self.hash_password(password)
        if self.db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed)):
            logger.info(f"AUDIT: Registered new user '{username}'")
            messagebox.showinfo("Success", "Account created successfully!")
            return True
        
        messagebox.showerror("Error", "Username already exists.")
        return False