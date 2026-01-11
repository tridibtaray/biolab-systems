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

logger = logging.getLogger(__name__)

class BiologicalUI:
    def __init__(self, root, db, controller):
        self.root = root
        self.db = db
        self.controller = controller
        self.selected_id = None
        
        try:
            self.root.state('zoomed') 
        except:
            self.root.attributes('-fullscreen', True)        

        try:
            self.setup_ui()
            logger.info("BiologicalUI initialized.")
        except Exception as e:
            logger.critical(f"Initialization error: {e}")

    def setup_ui(self):
        self.root.title("BioLab - Biological Sample Inventory")

        # --- Header Section ---
        header = tb.Frame(self.root, bootstyle=SECONDARY)
        header.pack(fill=X, pady=5)
        
        tb.Label(header, text="BIOLOGICAL SAMPLES DATABASE", 
                 font=("Helvetica", 18, "bold"), bootstyle=INVERSE).pack(side=LEFT, padx=20, pady=15)
        
        tb.Button(header, text="✖ Exit System", bootstyle=DANGER, 
                  command=self.confirm_full_exit).pack(side=RIGHT, padx=20)
        tb.Button(header, text="← Switch Module", bootstyle=INFO, 
                  command=self.back_to_hub).pack(side=RIGHT, padx=5)

        # --- Data Entry Form (Fields same as previous) ---
        form = tb.LabelFrame(self.root, text="Sample Specification", padding=15)
        form.pack(fill=X, padx=20, pady=10)
        for i in range(8): form.columnconfigure(i, weight=1)

        self.ents = {}
        r0 = [("Sample Name", "name"), ("Sample Type", "type"), 
              ("Source Organism", "source"), ("Preservative/Medium", "medium")]
        for i, (lbl, key) in enumerate(r0):
            tb.Label(form, text=lbl).grid(row=0, column=i*2, padx=5, pady=5, sticky=W)
            self.ents[key] = tb.Entry(form)
            self.ents[key].grid(row=0, column=i*2+1, padx=5, pady=5, sticky=EW)

        r1 = [("Container Type", "container"), ("Vol / Qty", "qty"), 
              ("BSL Level", "bsl"), ("Expiry (YYYY-MM-DD)", "expiry")]
        for i, (lbl, key) in enumerate(r1):
            tb.Label(form, text=lbl).grid(row=1, column=i*2, padx=5, pady=5, sticky=W)
            self.ents[key] = tb.Entry(form)
            self.ents[key].grid(row=1, column=i*2+1, padx=5, pady=5, sticky=EW)
        self.ents["expiry"].insert(0, date.today().strftime("%Y-%m-%d"))

        # --- Action Buttons ---
        btn_f = tb.Frame(self.root); btn_f.pack(fill=X, padx=20, pady=5)
        
        tb.Button(btn_f, text="Add Sample", bootstyle=SUCCESS, command=self.add_item).pack(side=LEFT, padx=5)
        tb.Button(btn_f, text="Update Record", bootstyle=WARNING, command=self.update_item).pack(side=LEFT, padx=5)
        tb.Button(btn_f, text="Delete", bootstyle=DANGER, command=self.delete_item).pack(side=LEFT, padx=5)
        
        # PDF Export Button Added Here
        tb.Button(btn_f, text="📄 Export to PDF", bootstyle=PRIMARY, 
                  command=self.export_to_pdf).pack(side=RIGHT, padx=5)
        tb.Button(btn_f, text="Clear Form", bootstyle=SECONDARY, command=self.clear_form).pack(side=RIGHT, padx=5)

        # --- Search & Filter ---
        search_f = tb.LabelFrame(self.root, text="Advanced Filter (Name, Type, BSL, Expiry Year)", padding=15)
        search_f.pack(fill=X, padx=20, pady=10)
        
        for i in range(4): search_f.columnconfigure(i, weight=1)

        self.s_name = tb.Entry(search_f); self.s_name.grid(row=0, column=0, padx=10, sticky=EW)
        self.s_name.insert(0, "Filter Name...")
        
        self.s_type = tb.Entry(search_f); self.s_type.grid(row=0, column=1, padx=10, sticky=EW)
        self.s_type.insert(0, "Filter Type...")

        self.s_bsl = tb.Entry(search_f); self.s_bsl.grid(row=0, column=2, padx=10, sticky=EW)
        self.s_bsl.insert(0, "Filter BSL...")

        self.s_date = tb.Entry(search_f); self.s_date.grid(row=0, column=3, padx=10, sticky=EW)
        self.s_date.insert(0, "Filter Expiry...")

        for s in [self.s_name, self.s_type, self.s_bsl, self.s_date]:
            s.bind("<KeyRelease>", lambda e: self.perform_search())
            s.bind("<FocusIn>", lambda e: e.widget.delete(0, END) if "Filter" in e.widget.get() else None)

        # --- Treeview ---
        cols = ("ID", "Name", "Type", "Organism", "Medium", "Container", "Qty", "BSL", "Expiry")
        self.tree = tb.Treeview(self.root, columns=cols, show="headings", bootstyle=INFO)
        for c in cols: 
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor=CENTER, width=110)
        
        self.tree.pack(fill=BOTH, expand=True, padx=20, pady=10)
        self.tree.tag_configure("expired", background="#ffcccc", foreground="black") 
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.refresh()

    def export_to_pdf(self):
        """Generates a professional PDF report from the current Treeview data."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Biological_Inventory_{date.today()}.pdf"
        )
        if not file_path: return

        try:
            # Setup Document (Landscape A4 to fit 9 columns)
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
            elements = []
            styles = getSampleStyleSheet()

            # Title and Timestamp
            elements.append(Paragraph("Biological Samples Inventory Report", styles['Title']))
            elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 20))

            # Table Header and Data
            data = [["ID", "Name", "Type", "Source", "Medium", "Container", "Qty", "BSL", "Expiry"]]
            
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

    def is_valid_date(self, date_str):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str): return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError: return False

    def perform_search(self):
        try:
            def clean(e):
                v = e.get()
                return f"%{v}%" if v and "Filter" not in v else "%%"

            query = """SELECT * FROM biological WHERE name LIKE ? AND type LIKE ? 
                       AND bsl LIKE ? AND expiry LIKE ?"""
            params = (clean(self.s_name), clean(self.s_type), clean(self.s_bsl), clean(self.s_date))
            self.update_tree(self.db.query(query, params))
        except Exception as e: logger.error(f"Search error: {e}")

    def refresh(self):
        try:
            rows = self.db.query("SELECT * FROM biological")
            self.update_tree(rows)
        except Exception as e: logger.error(f"Refresh error: {e}")

    def update_tree(self, rows):
        self.tree.delete(*self.tree.get_children())
        today = date.today()
        for r in rows:
            tag = ""
            try:
                # Expiry is at index 8 for Biological Table
                if datetime.strptime(r[8], "%Y-%m-%d").date() < today:
                    tag = "expired"
            except: pass
            self.tree.insert("", END, values=r, tags=(tag,))
        self.tree.tag_configure("expired", background="#ffcccc", foreground="black")

    def add_item(self):
        name = self.ents["name"].get().strip()
        exp = self.ents["expiry"].get().strip()
        if not name or not self.is_valid_date(exp):
            messagebox.showerror("Error", "Check Name and Expiry (YYYY-MM-DD)")
            return

        if messagebox.askyesno("Confirm", f"Add Biological Sample '{name}'?"):
            data = (name, self.ents["type"].get(), self.ents["source"].get(), 
                    self.ents["medium"].get(), self.ents["container"].get(),
                    self.ents["qty"].get(), self.ents["bsl"].get(), exp)
            
            sql = "INSERT INTO biological (name, type, organism, medium, container, qty, bsl, expiry) VALUES (?,?,?,?,?,?,?,?)"
            if self.db.execute(sql, data):
                logger.info(f"Bio Sample Added: {name}")
                self.refresh(); self.clear_form()

    def update_item(self):
        if not self.selected_id: return
        exp = self.ents["expiry"].get().strip()
        if not self.is_valid_date(exp): return

        data = (self.ents["name"].get(), self.ents["type"].get(), self.ents["source"].get(), 
                self.ents["medium"].get(), self.ents["container"].get(),
                self.ents["qty"].get(), self.ents["bsl"].get(), exp, self.selected_id)
        
        sql = "UPDATE biological SET name=?, type=?, organism=?, medium=?, container=?, qty=?, bsl=?, expiry=? WHERE id=?"
        if self.db.execute(sql, data):
            logger.info(f"Bio Sample Updated ID: {self.selected_id}")
            self.refresh()

    def delete_item(self):
        if self.selected_id and messagebox.askyesno("Delete", "Delete sample permanently?"):
            if self.db.execute("DELETE FROM biological WHERE id=?", (self.selected_id,)):
                logger.warning(f"Bio Sample Deleted ID: {self.selected_id}")
                self.refresh(); self.clear_form()

    def on_select(self, e):
        sel = self.tree.focus()
        if not sel: return
        v = self.tree.item(sel)['values']
        self.selected_id = v[0]
        # Map values back to entries
        keys = ["name", "type", "source", "medium", "container", "qty", "bsl", "expiry"]
        for i, k in enumerate(keys):
            self.ents[k].delete(0, END)
            self.ents[k].insert(0, v[i+1])

    def clear_form(self):
        for e in self.ents.values(): e.delete(0, END)
        self.ents["expiry"].insert(0, date.today().strftime("%Y-%m-%d"))
        self.selected_id = None

    def back_to_hub(self):
        self.root.destroy()
        self.controller.start_selection_hub()

    def confirm_full_exit(self):
        if messagebox.askyesno("Exit", "Close System?"):
            self.root.quit()
            self.root.destroy()