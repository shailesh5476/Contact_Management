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
        self.root.title("Contact Management System")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Database connection
        self.init_db()
        
        # Images directory
        self.images_dir = "contact_images"
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        
        self.current_image = None
        self.setup_ui()
        self.load_contacts()
    
    def init_db(self):
        try:
            self.db = mysql.connector.connect(
                host='localhost',
                user='root',  # Change to your MySQL username
                password='your_password',  # Change to your MySQL password
                database='contact_management'
            )
            self.cursor = self.db.cursor()
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Error connecting to database: {str(e)}")
            self.root.quit()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Contact Management System", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Add Contact", command=self.add_contact, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Edit Contact", command=self.edit_contact).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Contact", command=self.delete_contact).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.load_contacts).pack(side=tk.LEFT, padx=5)
        
        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.search_entry.bind('<KeyRelease>', self.search_contacts)
        ttk.Button(search_frame, text="Clear", command=self.clear_search).pack(side=tk.LEFT)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Contacts list tab
        self.contacts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.contacts_frame, text="Contacts")
        
        # Contact details tab
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text="Details")
        
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
        self.tree = ttk.Treeview(self.contacts_frame, columns=columns, show='headings', height=20)
        
        # Define headings
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Email', text='Email')
        self.tree.heading('Phone', text='Phone')
        self.tree.heading('Company', text='Company')
        
        # Column widths
        self.tree.column('ID', width=50)
        self.tree.column('Name', width=150)
        self.tree.column('Email', width=200)
        self.tree.column('Phone', width=120)
        self.tree.column('Company', width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.contacts_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.contacts_frame.columnconfigure(0, weight=1)
        self.contacts_frame.rowconfigure(0, weight=1)
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_contact_select)
    
    def setup_details_tab(self):
        # Image display
        img_frame = ttk.LabelFrame(self.details_frame, text="Photo", padding="10")
        img_frame.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        self.image_label = ttk.Label(img_frame, text="No image", background='white', 
                                   width=20, height=15, relief='sunken')
        self.image_label.grid(row=0, column=0)
        
        ttk.Button(img_frame, text="Change Image", command=self.change_image).grid(row=1, column=0, pady=5)
        
        # Details frame
        details_frame = ttk.LabelFrame(self.details_frame, text="Contact Details", padding="10")
        details_frame.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Detail labels
        self.detail_labels = {}
        fields = ['Name', 'Email', 'Phone', 'Company', 'Address', 'Notes', 'Created']
        row = 0
        for field in fields:
            ttk.Label(details_frame, text=f"{field}:").grid(row=row, column=0, sticky=tk.W, pady=2)
            self.detail_labels[field] = ttk.Label(details_frame, text="", font=('Arial', 10))
            self.detail_labels[field].grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
            row += 1
        
        self.details_frame.columnconfigure(1, weight=1)
        self.details_frame.rowconfigure(0, weight=1)
    
    def load_contacts(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        query = "SELECT id, name, email, phone, company FROM contacts"
        self.cursor.execute(query)
        for row in self.cursor.fetchall():
            self.tree.insert('', tk.END, values=row)
    
    def search_contacts(self, event=None):
        search_term = self.search_var.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        query = """
        SELECT id, name, email, phone, company FROM contacts 
        WHERE name LIKE %s OR email LIKE %s OR phone LIKE %s OR company LIKE %s
        """
        self.cursor.execute(query, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        for row in self.cursor.fetchall():
            self.tree.insert('', tk.END, values=row)
    
    def clear_search(self):
        self.search_var.set('')
        self.load_contacts()
    
    def on_contact_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            contact_id = item['values'][0]
            self.load_contact_details(contact_id)
    
    def load_contact_details(self, contact_id):
        query = """
        SELECT * FROM contacts WHERE id = %s
        """
        self.cursor.execute(query, (contact_id,))
        contact = self.cursor.fetchone()
        
        if contact:
            self.detail_labels['Name'].config(text=contact[1])
            self.detail_labels['Email'].config(text=contact[2] or '')
            self.detail_labels['Phone'].config(text=contact[3] or '')
            self.detail_labels['Company'].config(text=contact[5] or '')
            self.detail_labels['Address'].config(text=contact[4] or '')
            self.detail_labels['Notes'].config(text=contact[7] or '')
            self.detail_labels['Created'].config(text=contact[8].strftime('%Y-%m-%d %H:%M'))
            
            # Load image
            if contact[6] and os.path.exists(contact[6]):
                self.load_image(contact[6])
    
    def load_image(self, image_path):
        try:
            img = Image.open(image_path)
            img = img.resize((200, 250), Image.Resampling.LANCZOS)
            self.current_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.current_image, text="")
        except:
            self.image_label.config(image='', text="Image not found")
    
    def change_image(self):
        filename = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if filename:
            # Copy image to our directory
            name = os.path.splitext(os.path.basename(filename))[0]
            ext = os.path.splitext(filename)[1]
            new_path = os.path.join(self.images_dir, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}")
            shutil.copy2(filename, new_path)
            
            self.load_image(new_path)
    
    def add_contact(self):
        self.contact_window('Add Contact', is_edit=False)
    
    def edit_contact(self):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            contact_id = item['values'][0]
            self.contact_window('Edit Contact', is_edit=True, contact_id=contact_id)
        else:
            messagebox.showwarning("Warning", "Please select a contact to edit")
    
    def delete_contact(self):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            contact_id = item['values'][0]
            
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this contact?"):
                try:
                    # Delete image if exists
                    query = "SELECT image_path FROM contacts WHERE id = %s"
                    self.cursor.execute(query, (contact_id,))
                    result = self.cursor.fetchone()
                    if result[0] and os.path.exists(result[0]):
                        os.remove(result[0])
                    
                    # Delete contact
                    query = "DELETE FROM contacts WHERE id = %s"
                    self.cursor.execute(query, (contact_id,))
                    self.db.commit()
                    self.load_contacts()
                    self.clear_details()
                    messagebox.showinfo("Success", "Contact deleted successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Error deleting contact: {str(e)}")
        else:
            messagebox.showwarning("Warning", "Please select a contact to delete")
    
    def contact_window(self, title, is_edit=False, contact_id=None):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("500x600")
        window.grab_set()
        
        # Variables
        name_var = tk.StringVar()
        email_var = tk.StringVar()
        phone_var = tk.StringVar()
        address_var = tk.StringVar()
        company_var = tk.StringVar()
        notes_var = tk.StringVar()
        image_path_var = tk.StringVar()
        
        if is_edit:
            query = "SELECT * FROM contacts WHERE id = %s"
            self.cursor.execute(query, (contact_id,))
            contact = self.cursor.fetchone()
            name_var.set(contact[1])
            email_var.set(contact[2] or '')
            phone_var.set(contact[3] or '')
            address_var.set(contact[4] or '')
            company_var.set(contact[5] or '')
            notes_var.set(contact[7] or '')
            image_path_var.set(contact[6] or '')
        
        # UI Elements
        ttk.Label(window, text="Name *").pack(pady=5)
        ttk.Entry(window, textvariable=name_var, font=('Arial', 10)).pack(pady=5, padx=20, fill=tk.X)
        
        ttk.Label(window, text="Email").pack(pady=5)
        ttk.Entry(window, textvariable=email_var, font=('Arial', 10)).pack(pady=5, padx=20, fill=tk.X)
        
        ttk.Label(window, text="Phone").pack(pady=5)
        ttk.Entry(window, textvariable=phone_var, font=('Arial', 10)).pack(pady=5, padx=20, fill=tk.X)
        
        ttk.Label(window, text="Company").pack(pady=5)
        ttk.Entry(window, textvariable=company_var, font=('Arial', 10)).pack(pady=5, padx=20, fill=tk.X)
        
        ttk.Label(window, text="Address").pack(pady=5)
        ttk.Text(window, height=4, font=('Arial', 10)).pack(pady=5, padx=20, fill=tk.X)
        address_text = ttk.Text(window, height=4, font=('Arial', 10))
        address_text.pack(pady=5, padx=20, fill=tk.X)
        if is_edit:
            address_text.insert('1.0', address_var.get())
        
        ttk.Label(window, text="Notes").pack(pady=5)
        notes_text = ttk.Text(window, height=4, font=('Arial', 10))
        notes_text.pack(pady=5, padx=20, fill=tk.X)
        if is_edit:
            notes_text.insert('1.0', notes_var.get())
        
        ttk.Label(window, text="Image Path").pack(pady=5)
        ttk.Entry(window, textvariable=image_path_var, state='readonly').pack(pady=5, padx=20, fill=tk.X)
        ttk.Button(window, text="Select Image", 
                  command=lambda: self.select_image(image_path_var)).pack(pady=5)
        
        def save_contact():
            if not name_var.get().strip():
                messagebox.showerror("Error", "Name is required!")
                return
            
            address = address_text.get('1.0', tk.END).strip()
            notes = notes_text.get('1.0', tk.END).strip()
            
            try:
                if is_edit:
                    query = """
                    UPDATE contacts SET name=%s, email=%s, phone=%s, address=%s, 
                    company=%s, image_path=%s, notes=%s WHERE id=%s
                    """
                    self.cursor.execute(query, (name_var.get(), email_var.get(), phone_var.get(),
                                              address, company_var.get(), image_path_var.get(),
                                              notes, contact_id))
                else:
                    query = """
                    INSERT INTO contacts (name, email, phone, address, company, image_path, notes) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    self.cursor.execute(query, (name_var.get(), email_var.get(), phone_var.get(),
                                              address, company_var.get(), image_path_var.get(), notes))
                
                self.db.commit()
                self.load_contacts()
                window.destroy()
                messagebox.showinfo("Success", "Contact saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving contact: {str(e)}")
        
        btn_frame = ttk.Frame(window)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Save", command=save_contact).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=window.destroy).pack(side=tk.LEFT)
    
    def select_image(self, var):
        filename = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if filename:
            name = os.path.splitext(os.path.basename(filename))[0]
            ext = os.path.splitext(filename)[1]
            new_path = os.path.join(self.images_dir, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}")
            shutil.copy2(filename, new_path)
            var.set(new_path)
    
    def clear_details(self):
        for label in self.detail_labels.values():
            label.config(text='')
        self.image_label.config(image='', text="No image")
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = ContactManager(root)
    root.mainloop()