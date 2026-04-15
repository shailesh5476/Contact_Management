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
        self.root.title("Contact Management System v2.0")
        self.root.geometry("1100x750")
        self.root.configure(bg='#f0f0f0')
        
        # Database connection
        self.init_db()
        
        # Images directory
        self.images_dir = "contact_images"
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        
        self.current_image = None
        self.selected_contact_id = None
        self.setup_ui()
        self.load_contacts()
    
    def init_db(self):
        try:
            self.db = mysql.connector.connect(
                host='localhost',
                user='root',  # Change to your MySQL username
                password='Skg@5476',  # Change to your MySQL password (leave empty if no password)
                database='contact_management'
            )
            self.cursor = self.db.cursor()
            print("✅ Database connected successfully!")
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", 
                f"❌ Error connecting to database: {str(e)}\n\n"
                "📋 Please:\n"
                "1. Install & start MySQL Server\n"
                "2. Run the SQL script to create 'contact_management' database\n"
                "3. Update username/password in line 25-28")
            self.root.quit()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="👥 Contact Management System", 
                               font=('Segoe UI', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 25))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready", foreground='green')
        self.status_label.grid(row=0, column=1, columnspan=3, pady=(0, 25), sticky=tk.E)
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 15))
        
        ttk.Button(btn_frame, text="➕ Add Contact", command=self.add_contact).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="✏️ Edit Contact", command=self.edit_contact).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="🗑️ Delete Contact", command=self.delete_contact).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.load_contacts).pack(side=tk.LEFT, padx=4)
        
        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(search_frame, text="🔍 Search:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=35, font=('Segoe UI', 10))
        self.search_entry.pack(side=tk.LEFT, padx=(8, 8))
        self.search_entry.bind('<KeyRelease>', self.search_contacts)
        ttk.Button(search_frame, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=4)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0,10))
        
        # Contacts list tab
        self.contacts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.contacts_frame, text="📋 Contacts List")
        
        # Contact details tab
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text="👤 Contact Details")
        
        self.setup_contacts_tab()
        self.setup_details_tab()
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(3, weight=1)
    
    def setup_contacts_tab(self):
        # Treeview for contacts
        columns = ('ID', 'Name', 'Email', 'Phone', 'Company')
        self.tree = ttk.Treeview(self.contacts_frame, columns=columns, show='headings', height=22)
        
        # Define headings
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Email', text='Email')
        self.tree.heading('Phone', text='Phone')
        self.tree.heading('Company', text='Company')
        
        # Column widths
        self.tree.column('ID', width=60, anchor='center')
        self.tree.column('Name', width=180)
        self.tree.column('Email', width=250)
        self.tree.column('Phone', width=130, anchor='center')
        self.tree.column('Company', width=180)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(self.contacts_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self.contacts_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0,5))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.contacts_frame.columnconfigure(0, weight=1)
        self.contacts_frame.rowconfigure(0, weight=1)
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_contact_select)
    
    def setup_details_tab(self):
        # Left frame for image
        left_frame = ttk.Frame(self.details_frame)
        left_frame.grid(row=0, column=0, padx=15, pady=15, sticky=(tk.N, tk.S))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        img_container = ttk.LabelFrame(left_frame, text="📸 Photo", padding="15")
        img_container.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), pady=10)
        
        # FIXED: Use tk.Label for image display (ttk.Label doesn't support images well)
        self.image_label = tk.Label(img_container, text="No image selected\n\nClick 'Change Image'\nto add photo", 
                                   bg='white', width=28, height=18, relief='sunken', bd=2,
                                   font=('Segoe UI', 10))
        self.image_label.grid(row=0, column=0, pady=10)
        
        ttk.Button(img_container, text="📁 Change Image", command=self.change_image).grid(row=1, column=0, pady=10)
        
        # Right frame for details
        right_frame = ttk.Frame(self.details_frame)
        right_frame.grid(row=0, column=1, padx=15, pady=15, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        details_container = ttk.LabelFrame(right_frame, text="📝 Contact Information", padding="15")
        details_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Detail labels
        self.detail_labels = {}
        fields = [('👤', 'Name'), ('📧', 'Email'), ('📞', 'Phone'), ('🏢', 'Company'), 
                 ('📍', 'Address'), ('📝', 'Notes'), ('📅', 'Created')]
        
        for i, (icon, field) in enumerate(fields):
            frame = ttk.Frame(details_container)
            frame.grid(row=i//2, column=i%2, sticky=(tk.W, tk.E), padx=5, pady=5)
            
            ttk.Label(frame, text=f"{icon} {field}:", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
            self.detail_labels[field] = ttk.Label(frame, text="N/A", font=('Segoe UI', 9), 
                                                foreground='#2c3e50')
            self.detail_labels[field].pack(anchor='w', fill=tk.X)
        
        details_container.columnconfigure(1, weight=1)
    
    def load_contacts(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            query = "SELECT id, name, email, phone, company FROM contacts ORDER BY name"
            self.cursor.execute(query)
            contacts = self.cursor.fetchall()
            for row in contacts:
                self.tree.insert('', tk.END, values=row)
            self.status_label.config(text=f"Loaded {len(contacts)} contacts")
        except Exception as e:
            self.status_label.config(text="Error loading contacts", foreground='red')
            print(f"Load error: {e}")
    
    def search_contacts(self, event=None):
        search_term = self.search_var.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            query = """
            SELECT id, name, email, phone, company FROM contacts 
            WHERE LOWER(name) LIKE %s OR LOWER(email) LIKE %s OR LOWER(phone) LIKE %s OR LOWER(company) LIKE %s
            ORDER BY name
            """
            self.cursor.execute(query, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            contacts = self.cursor.fetchall()
            for row in contacts:
                self.tree.insert('', tk.END, values=row)
            self.status_label.config(text=f"Found {len(contacts)} contacts")
        except Exception as e:
            print(f"Search error: {e}")
    
    def clear_search(self):
        self.search_var.set('')
        self.load_contacts()
    
    def on_contact_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_contact_id = item['values'][0]
            self.load_contact_details(self.selected_contact_id)
    
    def load_contact_details(self, contact_id):
        try:
            query = "SELECT * FROM contacts WHERE id = %s"
            self.cursor.execute(query, (contact_id,))
            contact = self.cursor.fetchone()
            
            if contact:
                self.detail_labels['Name'].config(text=contact[1])
                self.detail_labels['Email'].config(text=contact[2] or 'N/A')
                self.detail_labels['Phone'].config(text=contact[3] or 'N/A')
                self.detail_labels['Company'].config(text=contact[5] or 'N/A')
                self.detail_labels['Address'].config(text=contact[4] or 'N/A')
                self.detail_labels['Notes'].config(text=contact[7] or 'N/A')
                self.detail_labels['Created'].config(text=contact[8].strftime('%Y-%m-%d %H:%M') if contact[8] else 'N/A')
                
                # Load image
                if contact[6] and os.path.exists(contact[6]):
                    self.load_image(contact[6])
                else:
                    self.image_label.config(image='', text="No image")
        except Exception as e:
            print(f"Details load error: {e}")
    
    def load_image(self, image_path):
        try:
            img = Image.open(image_path)
            # Resize maintaining aspect ratio
            img.thumbnail((220, 280), Image.Resampling.LANCZOS)
            self.current_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.current_image, text="")
        except Exception as e:
            self.image_label.config(image='', text="Image load error")
            print(f"Image load error: {e}")
    
    def change_image(self):
        filename = filedialog.askopenfilename(
            title="Select Contact Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp")]
        )
        if filename:
            try:
                # Copy image to our directory with unique name
                name = os.path.splitext(os.path.basename(filename))[0][:20]  # Limit filename length
                ext = os.path.splitext(filename)[1]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_path = os.path.join(self.images_dir, f"{name}_{timestamp}{ext}")
                shutil.copy2(filename, new_path)
                
                self.load_image(new_path)
                self.status_label.config(text=f"Image saved: {os.path.basename(new_path)}")
            except Exception as e:
                messagebox.showerror("Image Error", f"Failed to copy image: {str(e)}")
    
    def add_contact(self):
        self.contact_window('➕ Add New Contact', is_edit=False)
    
    def edit_contact(self):
        if self.selected_contact_id:
            self.contact_window('✏️ Edit Contact', is_edit=True, contact_id=self.selected_contact_id)
        else:
            messagebox.showwarning("⚠️ Warning", "Please select a contact from the list to edit")
    
    def delete_contact(self):
        if self.selected_contact_id:
            if messagebox.askyesno("🗑️ Confirm Delete", 
                                 f"Are you sure you want to delete this contact?\n\nThis action cannot be undone."):
                self.delete_selected_contact()
        else:
            messagebox.showwarning("⚠️ Warning", "Please select a contact from the list to delete")
    
    def delete_selected_contact(self):
        try:
            # Delete image if exists
            query = "SELECT image_path FROM contacts WHERE id = %s"
            self.cursor.execute(query, (self.selected_contact_id,))
            result = self.cursor.fetchone()
            if result and result[0] and os.path.exists(result[0]):
                os.remove(result[0])
            
            # Delete contact
            query = "DELETE FROM contacts WHERE id = %s"
            self.cursor.execute(query, (self.selected_contact_id,))
            self.db.commit()
            
            self.load_contacts()
            self.clear_details()
            self.selected_contact_id = None
            self.status_label.config(text="✅ Contact deleted successfully", foreground='green')
        except Exception as e:
            messagebox.showerror("❌ Delete Error", f"Error deleting contact:\n{str(e)}")
    
    def clear_details(self):
        for label in self.detail_labels.values():
            label.config(text='N/A')
        self.image_label.config(image='', text="No image selected")
    
    def contact_window(self, title, is_edit=False, contact_id=None):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("550x700")
        window.resizable(True, True)
        window.grab_set()
        window.transient(self.root)
        window.configure(bg='#f8f9fa')
        
        # Variables
        name_var = tk.StringVar()
        email_var = tk.StringVar()
        phone_var = tk.StringVar()
        company_var = tk.StringVar()
        image_path_var = tk.StringVar()
        
        if is_edit:
            query = "SELECT * FROM contacts WHERE id = %s"
            self.cursor.execute(query, (contact_id,))
            contact = self.cursor.fetchone()
            name_var.set(contact[1])
            email_var.set(contact[2] or '')
            phone_var.set(contact[3] or '')
            company_var.set(contact[5] or '')
            image_path_var.set(contact[6] or '')
        
        # Main container
        main_frame = ttk.Frame(window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form title
        ttk.Label(main_frame, text=title, font=('Segoe UI', 14, 'bold')).pack(pady=(0,20))
        
        # Name field (required)
        ttk.Label(main_frame, text="👤 Name *", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        name_entry = ttk.Entry(main_frame, textvariable=name_var, font=('Segoe UI', 10), width=40)
        name_entry.pack(fill=tk.X, pady=(0,15))
        
        # Email field
        ttk.Label(main_frame, text="📧 Email", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        ttk.Entry(main_frame, textvariable=email_var, font=('Segoe UI', 10), width=40).pack(fill=tk.X, pady=(0,15))
        
        # Phone field
        ttk.Label(main_frame, text="📞 Phone", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        ttk.Entry(main_frame, textvariable=phone_var, font=('Segoe UI', 10), width=40).pack(fill=tk.X, pady=(0,15))
        
        # Company field
        ttk.Label(main_frame, text="🏢 Company", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        ttk.Entry(main_frame, textvariable=company_var, font=('Segoe UI', 10), width=40).pack(fill=tk.X, pady=(0,15))
        
        # Address textarea
        ttk.Label(main_frame, text="📍 Address", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        address_frame = ttk.Frame(main_frame)
        address_frame.pack(fill=tk.X, pady=(0,15))
        address_text = tk.Text(address_frame, height=3, font=('Segoe UI', 10), wrap=tk.WORD, bg='white')
        address_scroll = ttk.Scrollbar(address_frame, orient=tk.VERTICAL, command=address_text.yview)
        address_text.configure(yscrollcommand=address_scroll.set)
        address_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        address_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Notes textarea
        ttk.Label(main_frame, text="📝 Notes", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        notes_frame = ttk.Frame(main_frame)
        notes_frame.pack(fill=tk.X, pady=(0,15))
        notes_text = tk.Text(notes_frame, height=4, font=('Segoe UI', 10), wrap=tk.WORD, bg='white')
        notes_scroll = ttk.Scroll