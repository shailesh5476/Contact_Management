import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
from PIL import Image, ImageTk
import os
import shutil
from datetime import datetime

class ContactManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Contact Management System - FIXED")
        self.root.geometry("1200x700")
        self.root.state('zoomed')
        
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'Skg@5476',  # Your MySQL password
            'database': 'contact_manager'
        }
        self.conn = None
        self.cursor = None
        self.connect_db()
        
        self.image_dir = "contact_images"
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
        
        self.photo_reference = None
        self.setup_ui()
        self.load_contacts()
    
    def connect_db(self):
        try:
            self.conn = mysql.connector.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            
            # 🔥 CREATE TABLE IF NOT EXISTS
            create_table_query = """
            CREATE TABLE IF NOT EXISTS contacts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20),
                address TEXT,
                company VARCHAR(100),
                image_path VARCHAR(255),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.cursor.execute(create_table_query)
            self.conn.commit()
            
            print("✅ Database connected & table ready!")
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"❌ Connection failed:\n{str(e)}")
            print(f"Database error: {e}")
            self.root.quit()
    
    def setup_ui(self):
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title_label = ttk.Label(main_frame, text="📇 Contact Management System", font=('Arial', 24, 'bold'))
        title_label.pack(pady=(0, 20))
        
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 15))
        
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="➕ Add New Contact", command=self.add_contact).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="🗑️ Delete Selected", command=self.delete_contact).pack(side=tk.LEFT)
        
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.RIGHT)
        ttk.Label(search_frame, text="🔍 Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind('<KeyRelease>', self.search_contacts)
        ttk.Button(search_frame, text="✖ Clear", command=self.clear_search).pack(side=tk.LEFT)
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.contacts_frame = ttk.Frame(self.notebook)
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.contacts_frame, text="📋 All Contacts")
        self.notebook.add(self.details_frame, text="✏️ Edit Contact")
        
        self.setup_contacts_tab()
        self.setup_details_tab()
    
    def setup_contacts_tab(self):
        tree_frame = ttk.Frame(self.contacts_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('ID', 'Name', 'Email', 'Phone', 'Company')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=22)
        
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Email', text='Email')
        self.tree.heading('Phone', text='Phone')
        self.tree.heading('Company', text='Company')
        
        self.tree.column('ID', width=60)
        self.tree.column('Name', width=220)
        self.tree.column('Email', width=280)
        self.tree.column('Phone', width=140)
        self.tree.column('Company', width=220)
        
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_contact_select)
        self.tree.bind('<Double-1>', self.on_contact_double_click)
    
    def setup_details_tab(self):
        # Scrollable container
        scroll_container = ttk.Frame(self.details_frame)
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.form_canvas = tk.Canvas(scroll_container)
        v_scrollbar = ttk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=self.form_canvas.yview)
        self.form_canvas.configure(yscrollcommand=v_scrollbar.set)
        
        self.form_scroll_frame = ttk.Frame(self.form_canvas)
        self.form_scroll_frame.bind('<Configure>', lambda e: self.form_canvas.configure(scrollregion=self.form_canvas.bbox('all')))
        self.form_canvas.create_window((0, 0), window=self.form_scroll_frame, anchor='nw')
        
        self.form_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def _on_mousewheel(event):
            self.form_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
        self.form_canvas.bind('<MouseWheel>', _on_mousewheel)
        
        # Image
        img_frame = ttk.LabelFrame(self.form_scroll_frame, text="📸 Contact Photo", padding=10)
        img_frame.pack(fill=tk.X, padx=10, pady=(10, 10))
        
        self.canvas = tk.Canvas(img_frame, width=220, height=280, bg='lightgray', relief='sunken', bd=2)
        self.canvas.pack(pady=10)
        self.canvas.create_text(110, 140, text="No image\nselected", font=('Arial', 12))
        ttk.Button(img_frame, text="📁 Change Photo", command=self.change_photo).pack(pady=5)
        
        # Form
        form_frame = ttk.LabelFrame(self.form_scroll_frame, text="📝 Contact Information", padding=20)
        form_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 20))
        form_frame.grid_columnconfigure(1, weight=1)
        
        self.entries = {}
        fields = [
            ('👤 Name *', 'name'),
            ('📧 Email', 'email'),
            ('📞 Phone', 'phone'),
            ('🏢 Company', 'company'),
            ('🏠 Address', 'address')
        ]
        
        for i, (label, key) in enumerate(fields):
            ttk.Label(form_frame, text=label, font=('Arial', 10, 'bold')).grid(
                row=i//2, column=(i%2)*2, sticky='w', pady=8, padx=(0, 10))
            self.entries[key] = ttk.Entry(form_frame, width=35, font=('Arial', 10))
            self.entries[key].grid(row=i//2, column=(i%2)*2+1, sticky='ew', pady=8, padx=(10, 0))
        
        ttk.Label(form_frame, text="📄 Notes", font=('Arial', 10, 'bold')).grid(
            row=len(fields)//2, column=0, sticky='w', pady=(15, 5), padx=(0, 10))
        notes_widget = tk.Text(form_frame, height=6, width=70, font=('Arial', 10))
        notes_widget.grid(row=len(fields)//2, column=1, columnspan=2, sticky='ew', pady=(15, 10), padx=(10, 0))
        self.entries['notes'] = notes_widget
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=len(fields)//2 + 1, column=0, columnspan=3, pady=20)
        ttk.Button(btn_frame, text="💾 Save Contact", command=self.save_contact).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Button(btn_frame, text="🗑️ Clear Form", command=self.clear_form).pack(side=tk.LEFT)
    
    def load_contacts(self, search_term=""):
        """🔥 FIXED - Always refresh from DB"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            if search_term.strip():
                query = """
                    SELECT id, name, email, phone, company 
                    FROM contacts 
                    WHERE name LIKE %s OR email LIKE %s OR phone LIKE %s OR company LIKE %s
                    ORDER BY name
                """
                pattern = f"%{search_term}%"
                self.cursor.execute(query, (pattern, pattern, pattern, pattern))
            else:
                query = "SELECT id, name, email, phone, company FROM contacts ORDER BY name"
                self.cursor.execute(query)
            
            contacts = self.cursor.fetchall()
            
            for contact in contacts:
                self.tree.insert('', tk.END, values=contact)
            
            print(f"✅ Loaded {len(contacts)} contacts from DB")
            
        except Exception as e:
            print(f"❌ Load error: {e}")
            messagebox.showerror("Load Error", f"Cannot load contacts:\n{str(e)}")
    
    def search_contacts(self, event=None):
        self.load_contacts(self.search_var.get())
    
    def clear_search(self):
        self.search_var.set("")
        self.load_contacts()
    
    def add_contact(self):
        self.notebook.select(1)
        self.clear_form()
    
    def on_contact_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.load_contact_details(item['values'][0])
    
    def on_contact_double_click(self, event):
        self.notebook.select(1)
    
    def load_contact_details(self, contact_id):
        try:
            self.cursor.execute("SELECT * FROM contacts WHERE id = %s", (contact_id,))
            contact = self.cursor.fetchone()
            print(f"DEBUG: Contact loaded: {contact}")  # Debug
            
            if contact:
                self.current_contact_id = contact[0]
                
                # Exact DB field mapping
                self.entries['name'].delete(0, tk.END)
                self.entries['name'].insert(0, contact[1] or "")
                
                self.entries['email'].delete(0, tk.END)
                self.entries['email'].insert(0, contact[2] or "")
                
                self.entries['phone'].delete(0, tk.END)
                self.entries['phone'].insert(0, contact[3] or "")
                
                self.entries['address'].delete(0, tk.END)
                self.entries['address'].insert(0, contact[4] or "")
                
                self.entries['company'].delete(0, tk.END)
                self.entries['company'].insert(0, contact[5] or "")
                
                notes_widget = self.entries['notes']
                notes_widget.delete(1.0, tk.END)
                notes_widget.insert(1.0, contact[7] or "")
                
                self.load_contact_image(contact[6])
        except Exception as e:
            print(f"Load details error: {e}")
    
    def load_contact_image(self, image_path):
        self.canvas.delete("all")
        self.canvas.create_text(110, 140, text="No image\nselected", font=('Arial', 12), fill='gray')
        
        if image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img.thumbnail((200, 260))
                self.photo_reference = ImageTk.PhotoImage(img)
                self.canvas.create_image(110, 130, image=self.photo_reference)
            except:
                pass
    
    def change_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if file_path:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name = (self.entries['name'].get() or "contact")[:20].replace(" ", "_")
                new_path = os.path.join(self.image_dir, f"{name}_{timestamp}.jpg")
                shutil.copy2(file_path, new_path)
                self.load_contact_image(new_path)
                self.current_image_path = new_path
            except Exception as e:
                print(f"Photo error: {e}")
    
    def save_contact(self):
        """🔥 FIXED SAVE FUNCTION"""
        name = self.entries['name'].get().strip()
        if not name:
            messagebox.showwarning("Error", "Name is required!")
            return
        
        try:
            image_path = getattr(self, 'current_image_path', '')
            notes = self.entries['notes'].get(1.0, tk.END).strip()
            
            if hasattr(self, 'current_contact_id'):
                # UPDATE
                query = """
                    UPDATE contacts SET 
                    name = %s, email = %s, phone = %s, address = %s, 
                    company = %s, image_path = %s, notes = %s 
                    WHERE id = %s
                """
                self.cursor.execute(query, (
                    name, self.entries['email'].get().strip(),
                    self.entries['phone'].get().strip(),
                    self.entries['address'].get().strip(),
                    self.entries['company'].get().strip(),
                    image_path, notes, self.current_contact_id
                ))
                print(f"✅ Updated contact ID: {self.current_contact_id}")
            else:
                # INSERT
                query = """
                    INSERT INTO contacts (name, email, phone, address, company, image_path, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                self.cursor.execute(query, (
                    name, self.entries['email'].get().strip(),
                    self.entries['phone'].get().strip(),
                    self.entries['address'].get().strip(),
                    self.entries['company'].get().strip(),
                    image_path, notes
                ))
                print("✅ New contact created!")
            
            self.conn.commit()
            messagebox.showinfo("✅ Success", "Contact saved!")
            self.load_contacts()  # Refresh list
            self.notebook.select(0)
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            messagebox.showerror("Save Error", f"Failed to save:\n{str(e)}")
    
    def delete_contact(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        contact_id = item['values'][0]
        contact_name = item['values'][1]
        
        if messagebox.askyesno("Confirm", f"Delete '{contact_name}'?"):
            try:
                self.cursor.execute("SELECT image_path FROM contacts WHERE id=%s", (contact_id,))
                img = self.cursor.fetchone()
                if img and img[0] and os.path.exists(img[0]):
                    os.remove(img[0])
                
                self.cursor.execute("DELETE FROM contacts WHERE id=%s", (contact_id,))
                self.conn.commit()
                self.load_contacts()
                messagebox.showinfo("Success", "Deleted!")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def clear_form(self):
        for entry in self.entries.values():
            if isinstance(entry, tk.Text):
                entry.delete(1.0, tk.END)
            else:
                entry.delete(0, tk.END)
        self.load_contact_image(None)
        if hasattr(self, 'current_contact_id'):
            del self.current_contact_id
        self.current_image_path = None
    
    def __del__(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()

def main():
    root = tk.Tk()
    app = ContactManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()