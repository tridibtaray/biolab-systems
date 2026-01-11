import sqlite3
import logging

# Configure logger for the database module
logger = logging.getLogger(__name__)

class Database:
    """
    Handles all SQLite database persistence, table initialization, 
    and safe execution of SQL queries.
    """
    def __init__(self, db_name="biolab.db"):
        self.db_name = db_name
        self._create_tables()

    def _create_tables(self):
        """Initializes required tables if they do not exist."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                # Create Users, Chemicals, and Biologicals tables
                cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                               (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
                
                cursor.execute('''CREATE TABLE IF NOT EXISTS chemicals 
                                (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, synonyms TEXT, class TEXT, 
                                mol_info TEXT, quantity TEXT, ghs TEXT, expiry TEXT)''')
                
                cursor.execute("""CREATE TABLE IF NOT EXISTS biological 
                                (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, organism TEXT,
                                    medium TEXT, container TEXT, qty TEXT, bsl TEXT,expiry TEXT)""")
                conn.commit()
                logger.info("Database schema verified/created successfully.")
        except sqlite3.Error as e:
            logger.critical(f"Database Initialization Failed: {e}")
        self.show_schema('biolab.db', 'chemicals')
        self.show_schema('biolab.db', 'biologicals')
    
    def show_schema(self, db_path, table_name):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Fetch column info: id, name, type, notnull, default_value, pk
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema = cursor.fetchall()
        
        print(f"{'ID':<4} {'Column Name':<20} {'Type':<10} {'PK':<3}")
        print("-" * 40)
        for col in schema:
            print(f"{col[0]:<4} {col[1]:<20} {col[2]:<10} {col[5]:<3}")
        
        conn.close()
    
    def query(self, sql, params=()):
        """Executes a SELECT query and returns all matching rows."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"SQL Query Error: {e} | SQL: {sql}")
            return []

    def execute(self, sql, params=()):
        """Executes INSERT, UPDATE, or DELETE commands."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            logger.warning("Database Integrity Error: Duplicate entry or constraint violation.")
            return False
        except sqlite3.Error as e:
            logger.error(f"SQL Execution Error: {e}")
            return False
