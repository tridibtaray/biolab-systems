import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
from datetime import datetime, date
import logging
import re

# PDF Generation Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- Logging Configuration ---
# This ensures that all actions within this module are tracked for audit purposes.
logger = logging.getLogger(__name__)

class ChemicalUI:
    """
    A robust UI for Chemical Inventory management.
    Features: 
    - Input validation for scientific date formats.
    - Error handling for database and UI interactions.
    - Transaction logging for security and auditing.
    """
    def __init__(self, root, db, controller):
        self.root = root
        self.db = db
        self.controller = controller
        self.selected_id = None
        # Set to Full Screen / Maximized
        # 'zoomed' works for Windows; for Linux/Mac use self.root.attributes('-fullscreen', True)
        try:
            self.root.state('zoomed') 
        except:
            self.root.attributes('-fullscreen', True)        

        try:
            self.setup_ui()
            logger.info("ChemicalUI successfully initialized.")
        except Exception as e:
            logger.critical(f"Failed to initialize ChemicalUI: {str(e)}")
            messagebox.showerror("System Error", "The Chemical Module failed to load. Please contact the administrator.")

    def setup_ui(self):
        """Constructs the UI layout with a focus on usability and error prevention."""
        self.root.title("BioLab - Chemical Inventory")
        #self.root.geometry("1200x1200")

        # --- Header Section ---
        header = tb.Frame(self.root, bootstyle=SECONDARY)
        header.pack(fill=X, pady=5)
        
        tb.Label(header, text="CHEMICAL REAGENTS DATABASE", 
                 font=("Helvetica", 18, "bold"), bootstyle=INVERSE).pack(side=LEFT, padx=20, pady=15)
        
        # System Control Buttons
        tb.Button(header, text="✖ Exit System", bootstyle=DANGER, 
                  command=self.confirm_full_exit).pack(side=RIGHT, padx=20)
                  
        tb.Button(header, text="← Switch Module", bootstyle=INFO, 
                  command=self.back_to_hub).pack(side=RIGHT, padx=5)

        # --- Data Entry Form ---
        form = tb.LabelFrame(self.root, text="Material Specification & Safety Data", padding=15)
        form.pack(fill=X, padx=20, pady=10)

        # Configure 8 columns for responsive grid behavior
        for i in range(8): form.columnconfigure(i, weight=1)

        self.ents = {}

        # Row 0: Primary Identification Fields
        r0 = [("Chemical Name", "name"), ("Synonyms", "syn"), ("Chemical Class", "class")]
        for i, (lbl, key) in enumerate(r0):
            tb.Label(form, text=lbl).grid(row=0, column=i*2, padx=5, pady=5, sticky=W)
            self.ents[key] = tb.Entry(form)
            self.ents[key].grid(row=0, column=i*2+1, padx=5, pady=5, sticky=EW)

        # Row 1: Scientific Metadata (Formula, Quantity, GHS, Expiry)
        tb.Label(form, text="Formula/Wt:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        self.ents["mol"] = tb.Entry(form)
        self.ents["mol"].grid(row=1, column=1, padx=5, pady=5, sticky=EW)

        tb.Label(form, text="Current Qty:").grid(row=1, column=2, padx=5, pady=5, sticky=W)
        self.ents["qty"] = tb.Entry(form)
        self.ents["qty"].grid(row=1, column=3, padx=5, pady=5, sticky=EW)

        tb.Label(form, text="Hazard (GHS):").grid(row=1, column=4, padx=5, pady=5, sticky=W)
        self.ents["ghs"] = tb.Entry(form)
        self.ents["ghs"].grid(row=1, column=5, padx=5, pady=5, sticky=EW)

        tb.Label(form, text="Expiry (YYYY-MM-DD):").grid(row=1, column=6, padx=5, pady=5, sticky=W)
        self.ents["expiry"] = tb.Entry(form)
        self.ents["expiry"].grid(row=1, column=7, padx=5, pady=5, sticky=EW)
        self.ents["expiry"].insert(0, date.today().strftime("%Y-%m-%d"))

        # --- Action Buttons ---
        btn_f = tb.Frame(self.root)
        btn_f.pack(fill=X, padx=20, pady=5)
        
        tb.Button(btn_f, text="Add Chemical", bootstyle=SUCCESS, command=self.add_item).pack(side=LEFT, padx=5)
        tb.Button(btn_f, text="Update Record", bootstyle=WARNING, command=self.update_item).pack(side=LEFT, padx=5)
        tb.Button(btn_f, text="Delete", bootstyle=DANGER, command=self.delete_item).pack(side=LEFT, padx=5)
        # PDF Export Button Added Here
        tb.Button(btn_f, text="📄 Export to PDF", bootstyle=PRIMARY, 
                  command=self.export_to_pdf).pack(side=RIGHT, padx=5)
        tb.Button(btn_f, text="Clear Form", bootstyle=SECONDARY, command=self.clear_form).pack(side=RIGHT, padx=5)

        # --- Quad-Filter Search (Dynamic Filtering) ---
        search_f = tb.LabelFrame(self.root, text="Search & Filter", padding=15)
        search_f.pack(fill=X, padx=20, pady=10)
        
        for i in range(4): search_f.columnconfigure(i, weight=1)

        self.s_name = tb.Entry(search_f); self.s_name.grid(row=0, column=0, padx=10, sticky=EW)
        self.s_name.insert(0, "Filter Name...")
        
        self.s_class = tb.Entry(search_f); self.s_class.grid(row=0, column=1, padx=10, sticky=EW)
        self.s_class.insert(0, "Filter Class...")

        self.s_ghs = tb.Entry(search_f); self.s_ghs.grid(row=0, column=2, padx=10, sticky=EW)
        self.s_ghs.insert(0, "Filter Hazard...")

        self.s_date = tb.Entry(search_f); self.s_date.grid(row=0, column=3, padx=10, sticky=EW)
        self.s_date.insert(0, "Filter Year...")

        # Bind search events to inputs
        for s in [self.s_name, self.s_class, self.s_ghs, self.s_date]:
            s.bind("<KeyRelease>", lambda e: self.perform_search())
            s.bind("<FocusIn>", lambda e: e.widget.delete(0, END) if "Filter" in e.widget.get() else None)

        # --- Data Grid (Treeview) ---
        cols = ("ID", "Name", "Synonyms", "Class", "Mol. Wt", "Qty", "GHS", "Expiry")
        self.tree = tb.Treeview(self.root, columns=cols, show="headings", bootstyle=INFO)
        for c in cols: 
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor=CENTER, width=120)
        
        self.tree.pack(fill=BOTH, expand=True, padx=20, pady=10)
        # Configure the 'expired' tag with a high-contrast color
        self.tree.tag_configure("expired", background="#F08080", foreground="white")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.refresh()

    # --- Logic, Validation & Error Handling ---

    def is_valid_date(self, date_str):
        """Validates that a string follows ISO format YYYY-MM-DD."""
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def perform_search(self):
        """Performs a real-time multi-criteria search with safety checks."""
        try:
            def clean(e):
                v = e.get()
                return f"%{v}%" if v and "Filter" not in v else "%%"

            query = """SELECT id, name, synonyms, class, mol_info, quantity, ghs, expiry 
                       FROM chemicals WHERE name LIKE ? AND class LIKE ? 
                       AND ghs LIKE ? AND expiry LIKE ?"""
            params = (clean(self.s_name), clean(self.s_class), clean(self.s_ghs), clean(self.s_date))
            results = self.db.query(query, params)
            self.update_tree(results)
        except Exception as e:
            logger.error(f"Search filtering error: {str(e)}")

    def refresh(self):
        """Reloads the entire inventory from the database."""
        try:
            rows = self.db.query("SELECT id, name, synonyms, class, mol_info, quantity, ghs, expiry FROM chemicals")
            self.update_tree(rows)
        except Exception as e:
            logger.error(f"Failed to refresh data: {str(e)}")

    def update_tree(self, rows):
        """Repopulates the Treeview and applies expiration styling."""
        self.tree.delete(*self.tree.get_children())
        today = date.today()
        
        for r in rows:
            tag = ""
            try:
                # In your current SQL (id, name, syn, class, mol, qty, ghs, expiry)
                # the expiry date is at index 7.
                expiry_date_str = r[7] 
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                
                if expiry_date < today:
                    tag = "expired"
            except (ValueError, IndexError, TypeError):
                # If date is malformed or index is wrong, skip tagging
                tag = ""
                
            self.tree.insert("", END, values=r, tags=(tag,))

        # Force the tag configuration to ensure it persists after refresh
        self.tree.tag_configure("expired", background="#ffcccc", foreground="black")

    def add_item(self):
        """Processes the 'Add Chemical' request with validation."""
        name = self.ents["name"].get().strip()
        exp = self.ents["expiry"].get().strip()

        # Validation: Mandatory Fields
        if not name:
            messagebox.showwarning("Input Validation", "Chemical Name is mandatory.")
            return

        if not self.is_valid_date(exp):
            messagebox.showerror("Format Error", "Expiry must be in YYYY-MM-DD format.")
            return

        # Transaction Confirmation
        if messagebox.askyesno("Confirm Transaction", f"Confirm adding '{name}' to the database?"):
            data = (name, self.ents["syn"].get(), self.ents["class"].get(), 
                    self.ents["mol"].get(), self.ents["qty"].get(), 
                    self.ents["ghs"].get(), exp)
            
            success = self.db.execute("INSERT INTO chemicals (name, synonyms, class, mol_info, quantity, ghs, expiry) VALUES (?,?,?,?,?,?,?)", data)
            
            if success:
                logger.info(f"Inventory Add: {name} successfully created.")
                self.refresh()
                self.clear_form()
            else:
                logger.error(f"DB Error: Could not add chemical '{name}'")
                messagebox.showerror("Database Error", "The record could not be saved.")

    def update_item(self):
        """Updates the selected record with integrity checks."""
        if not self.selected_id:
            messagebox.showwarning("Selection Error", "Please select a record from the table to update.")
            return

        name = self.ents["name"].get().strip()
        exp = self.ents["expiry"].get().strip()

        if not self.is_valid_date(exp):
            messagebox.showerror("Format Error", "Expiry must be in YYYY-MM-DD format.")
            return

        if messagebox.askyesno("Confirm Update", f"Apply changes to '{name}' (ID: {self.selected_id})?"):
            data = (name, self.ents["syn"].get(), self.ents["class"].get(), 
                    self.ents["mol"].get(), self.ents["qty"].get(), 
                    self.ents["ghs"].get(), exp, self.selected_id)
            
            sql = "UPDATE chemicals SET name=?, synonyms=?, class=?, mol_info=?, quantity=?, ghs=?, expiry=? WHERE id=?"
            if self.db.execute(sql, data):
                logger.info(f"Inventory Update: Record ID {self.selected_id} modified.")
                self.refresh()
            else:
                messagebox.showerror("Update Failed", "Changes could not be saved to the database.")

    def delete_item(self):
        """Safely removes a record from the inventory."""
        if not self.selected_id:
            return
            
        if messagebox.askyesno("CRITICAL: Delete Record", "This action is permanent. Do you want to continue?"):
            try:
                success = self.db.execute("DELETE FROM chemicals WHERE id=?", (self.selected_id,))
                if success:
                    logger.warning(f"Inventory Delete: User removed record ID {self.selected_id}")
                    self.refresh()
                    self.clear_form()
            except Exception as e:
                logger.error(f"Critical error during deletion: {str(e)}")

    def on_select(self, e):
        """Handles record selection and populates form fields."""
        sel = self.tree.focus()
        if not sel: return
        
        try:
            v = self.tree.item(sel)['values']
            self.selected_id = v[0]
            # Map grid columns back to input boxes
            for i, k in enumerate(["name", "syn", "class", "mol", "qty", "ghs", "expiry"]):
                self.ents[k].delete(0, END)
                self.ents[k].insert(0, v[i+1])
        except Exception as e:
            logger.error(f"Error mapping table selection: {str(e)}")

    def clear_form(self):
        """Resets the input form to default states."""
        for e in self.ents.values(): e.delete(0, END)
        self.ents["expiry"].insert(0, date.today().strftime("%Y-%m-%d"))
        self.selected_id = None

    def back_to_hub(self):
        """Returns the user to the selection hub and closes current view."""
        logger.info("User navigating back to Selection Hub.")
        self.root.destroy()
        self.controller.start_selection_hub()

    def confirm_full_exit(self):
        """Prompts for a clean system shutdown."""
        if messagebox.askyesno("Exit BioLab", "Are you sure you want to terminate the session?"):
            logger.info("System shutdown initiated by user.")
            self.root.quit()
            self.root.destroy()

    def export_to_pdf(self):
        """Generates a professional PDF report from the current Treeview data."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Chemical_Inventory_{date.today()}.pdf"
        )
        if not file_path: return

        try:
            # Setup Document (Landscape A4 to fit 9 columns)
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
            elements = []
            styles = getSampleStyleSheet()

            # Title and Timestamp
            elements.append(Paragraph("Chemical Inventory Report", styles['Title']))
            elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 20))

            # Table Header and Data
            data = [["ID", "Name", "Synonyms", "Class", "Mol. Wt", "Qty", "GHS", "Expiry"]]
            
            # Get data currently visible in the Treeview (honors active filters)
            for child in self.tree.get_children():
                data.append(self.tree.item(child)["values"])

            # Create Table with Formatting
            table = Table(data, repeatRows=1)
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ])
            table.setStyle(style)

            elements.append(table)
            doc.build(elements)
            
            logger.info(f"PDF Exported: {file_path}")
            messagebox.showinfo("Export Successful", f"Report saved to:\n{file_path}")
        except Exception as e:
            logger.error(f"PDF Generation Failed: {e}")
            messagebox.showerror("Export Error", f"An error occurred while creating the PDF: {e}")
