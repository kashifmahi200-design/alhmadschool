     import os
import sqlite3
import re
import json
import webbrowser
import shutil
from datetime import datetime, timedelta
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.selectioncontrol import MDSwitch
import urllib.request

# Register Urdu font if available
try:
    LabelBase.register(name='JameelNooriNastaleeq', fn_regular='assets/fonts/JameelNooriNastaleeq.ttf')
    URDU_FONT_AVAILABLE = True
except:
    URDU_FONT_AVAILABLE = False

# PDF generation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

DB_NAME = "alhamd_school.db"
PROFILE_PICS_DIR = "profile_pics"

# ---------------------------- INTERNET CHECK ----------------------------
def is_connected():
    try:
        urllib.request.urlopen('https://www.google.com', timeout=3)
        return True
    except:
        return False

# ---------------------------- DATABASE SETUP ----------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        status TEXT DEFAULT 'Pending',
        name TEXT,
        class_name TEXT,
        gender TEXT,
        contact TEXT,
        address TEXT,
        last_active TEXT DEFAULT '',
        profile_pic TEXT DEFAULT ''
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS school_settings (
        key TEXT PRIMARY KEY, value TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS heads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, gender TEXT, qualification TEXT, experience TEXT, designation TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, contact TEXT, address TEXT, gender TEXT,
        assigned_class TEXT, class_strength TEXT, username TEXT, password TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, contact TEXT, class_name TEXT, address TEXT,
        gender TEXT, username TEXT, password TEXT,
        father_name TEXT, cnic TEXT, dob TEXT,
        is_deleted INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS fee_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT, student_username TEXT, class_name TEXT,
        total_fee INTEGER DEFAULT 0, paid_amount INTEGER DEFAULT 0,
        remaining INTEGER DEFAULT 0, status TEXT DEFAULT 'Pending',
        month_year TEXT,
        carried_over INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_username TEXT,
        receiver_username TEXT,
        message TEXT,
        timestamp TEXT,
        is_read INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS student_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_username TEXT,
        class_name TEXT,
        term_name TEXT,
        subject TEXT,
        total_marks INTEGER DEFAULT 0,
        obtained_marks INTEGER DEFAULT 0,
        percentage REAL DEFAULT 0,
        grade TEXT DEFAULT '',
        UNIQUE(student_username, term_name, subject)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS date_sheets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT,
        term_name TEXT,
        data TEXT,
        updated_by TEXT,
        timestamp TEXT,
        UNIQUE(class_name, term_name)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS timetables (
        class_name TEXT PRIMARY KEY,
        data TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT,
        date TEXT,
        slot TEXT,
        teacher_username TEXT,
        attendance_data TEXT,
        total_present INTEGER,
        total_absent INTEGER,
        total_students INTEGER
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS student_change_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        student_username TEXT,
        action TEXT,
        status TEXT DEFAULT 'Pending',
        timestamp TEXT,
        viewed INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS teacher_change_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_name TEXT,
        teacher_username TEXT,
        action TEXT,
        status TEXT DEFAULT 'Pending',
        timestamp TEXT,
        viewed INTEGER DEFAULT 0
    )''')
    
    # Notification table
    cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_username TEXT,
        title TEXT,
        message TEXT,
        timestamp TEXT,
        is_read INTEGER DEFAULT 0,
        type TEXT
    )''')
    
    # Add status column if missing
    try:
        cursor.execute("ALTER TABLE student_change_logs ADD COLUMN status TEXT DEFAULT 'Pending'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE teacher_change_logs ADD COLUMN status TEXT DEFAULT 'Pending'")
    except sqlite3.OperationalError:
        pass
    
    # Insert default data
    cursor.execute("SELECT * FROM users WHERE username='kashif'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role, status) VALUES (?, ?, ?, ?)",
                       ('kashif', 'admin123', 'Admin', 'Approved'))
        cursor.execute("INSERT INTO users (username, password, role, status, name) VALUES (?, ?, ?, ?, ?)",
                       ('principal1', 'principal123', 'Principal', 'Approved', 'Mr. Principal'))
        cursor.execute("INSERT INTO users (username, password, role, status, name) VALUES (?, ?, ?, ?, ?)",
                       ('head1', 'head123', 'Head', 'Approved', 'Mr. Head'))
    
    cursor.execute("INSERT OR IGNORE INTO school_settings (key, value) VALUES (?, ?)",
                   ('principal_message', 'Welcome to Al-Hamd Cadet School.'))
    cursor.execute("INSERT OR IGNORE INTO school_settings (key, value) VALUES (?, ?)",
                   ('principal_name', 'Mr. Khuda Dad'))
    cursor.execute("INSERT OR IGNORE INTO school_settings (key, value) VALUES (?, ?)",
                   ('school_name', 'Al-Hamd Cadet School'))
    cursor.execute("INSERT OR IGNORE INTO school_settings (key, value) VALUES (?, ?)",
                   ('app_locked', 'False'))
    
    cursor.execute("SELECT * FROM heads")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO heads (name, gender, qualification, experience, designation) VALUES (?, ?, ?, ?, ?)",
                       ('Kashif Ali', 'Male', 'BS Mathematics', '6', 'Head SSC'))
        cursor.execute("INSERT INTO heads (name, gender, qualification, experience, designation) VALUES (?, ?, ?, ?, ?)",
                       ('Fatima Ahmed', 'Female', 'Masters in Education', '8', 'Vice Principal'))
    
    cursor.execute("SELECT * FROM teachers")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role, status, name, class_name, gender, contact, address, last_active) VALUES (?, ?, ?, 'Approved', ?, ?, ?, ?, ?, ?)",
                       ('Ahmed Khan', 'teacher123', 'Teacher', 'Ahmed Khan', 'Class 5', 'Male', '0300-1111111', 'Lahore', ''))
        cursor.execute("INSERT INTO teachers (name, contact, address, gender, assigned_class, username, password, class_strength) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ('Ahmed Khan', '0300-1111111', 'Lahore', 'Male', 'Class 5', 'Ahmed Khan', 'teacher123', '25'))
        
        cursor.execute("INSERT INTO users (username, password, role, status, name, class_name, gender, contact, address, last_active) VALUES (?, ?, ?, 'Approved', ?, ?, ?, ?, ?, ?)",
                       ('Sara Ali', 'teacher123', 'Teacher', 'Sara Ali', 'Class 8', 'Female', '0300-2222222', 'Karachi', ''))
        cursor.execute("INSERT INTO teachers (name, contact, address, gender, assigned_class, username, password, class_strength) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ('Sara Ali', '0300-2222222', 'Karachi', 'Female', 'Class 8', 'Sara Ali', 'teacher123', '30'))
        
        cursor.execute("INSERT INTO users (username, password, role, status, name, class_name, gender, contact, address, last_active) VALUES (?, ?, ?, 'Approved', ?, ?, ?, ?, ?, ?)",
                       ('Shahid Rasheed', 'teacher123', 'Teacher', 'Shahid Rasheed', 'Class 6', 'Male', '0300-3333333', 'Islamabad', ''))
        cursor.execute("INSERT INTO teachers (name, contact, address, gender, assigned_class, username, password, class_strength) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ('Shahid Rasheed', '0300-3333333', 'Islamabad', 'Male', 'Class 6', 'Shahid Rasheed', 'teacher123', '28'))
    
    cursor.execute("SELECT * FROM students")
    if not cursor.fetchone():
        sample_bform = '12345-1234567-8'
        cursor.execute("INSERT INTO users (username, password, role, status, name, class_name, gender, contact, address) VALUES (?, ?, ?, 'Approved', ?, ?, ?, ?, ?)",
                       (sample_bform, 'student123', 'Student', 'Ali Raza', 'Class 5', 'Male', '0300-1234567', 'Lahore'))
        cursor.execute("INSERT INTO students (name, contact, class_name, address, gender, username, password, father_name, cnic, dob, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                       ('Ali Raza', '0300-1234567', 'Class 5', 'Lahore', 'Male', sample_bform, 'student123', 'Ahmed Raza', '12345-1234567-8', '01-01-2010', 0))
        total_fee = get_fee_by_class('Class 5')
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute("INSERT INTO fee_records (student_name, student_username, class_name, total_fee, paid_amount, remaining, status, month_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ('Ali Raza', sample_bform, 'Class 5', total_fee, 0, total_fee, 'Less Paid', current_month))
        
        for i in range(2, 6):
            bform = f'12345-1234567-{i}'
            cursor.execute("INSERT INTO users (username, password, role, status, name, class_name, gender, contact, address) VALUES (?, ?, ?, 'Approved', ?, ?, ?, ?, ?)",
                           (bform, 'student123', 'Student', f'Student {i}', 'Class 5', 'Male', f'0300-00000{i}', 'Lahore'))
            cursor.execute("INSERT INTO students (name, contact, class_name, address, gender, username, password, father_name, cnic, dob, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                           (f'Student {i}', f'0300-00000{i}', 'Class 5', 'Lahore', 'Male', bform, 'student123', f'Father {i}', bform, '01-01-2010', 0))
            cursor.execute("INSERT INTO fee_records (student_name, student_username, class_name, total_fee, paid_amount, remaining, status, month_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (f'Student {i}', bform, 'Class 5', total_fee, 0, total_fee, 'Less Paid', current_month))
        
        bform8 = '87654-9876543-1'
        cursor.execute("INSERT INTO users (username, password, role, status, name, class_name, gender, contact, address) VALUES (?, ?, ?, 'Approved', ?, ?, ?, ?, ?)",
                       (bform8, 'student123', 'Student', 'Fatima', 'Class 8', 'Female', '0300-8888888', 'Karachi'))
        cursor.execute("INSERT INTO students (name, contact, class_name, address, gender, username, password, father_name, cnic, dob, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                       ('Fatima', '0300-8888888', 'Class 8', 'Karachi', 'Female', bform8, 'student123', 'Ali', '87654-9876543-1', '10-05-2012', 0))
        total_fee8 = get_fee_by_class('Class 8')
        cursor.execute("INSERT INTO fee_records (student_name, student_username, class_name, total_fee, paid_amount, remaining, status, month_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ('Fatima', bform8, 'Class 8', total_fee8, 0, total_fee8, 'Less Paid', current_month))
        
        bform6 = '11111-2222222-3'
        cursor.execute("INSERT INTO users (username, password, role, status, name, class_name, gender, contact, address) VALUES (?, ?, ?, 'Approved', ?, ?, ?, ?, ?)",
                       (bform6, 'student123', 'Student', 'Bilal', 'Class 6', 'Male', '0300-9999999', 'Islamabad'))
        cursor.execute("INSERT INTO students (name, contact, class_name, address, gender, username, password, father_name, cnic, dob, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                       ('Bilal', '0300-9999999', 'Class 6', 'Islamabad', 'Male', bform6, 'student123', 'Khalid', '11111-2222222-3', '15-03-2011', 0))
        total_fee6 = get_fee_by_class('Class 6')
        cursor.execute("INSERT INTO fee_records (student_name, student_username, class_name, total_fee, paid_amount, remaining, status, month_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ('Bilal', bform6, 'Class 6', total_fee6, 0, total_fee6, 'Less Paid', current_month))
    
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role, status, name, class_name, gender, contact, address) VALUES (?, ?, ?, 'Pending', ?, ?, ?, ?, ?)",
                   ('test_pending', 'pass123', 'Student', 'Test Student', 'Class 5', 'Male', '0300-8888888', 'Test Address'))
    
    classes = get_all_classes()
    default_timetable = json.dumps([{"time": "", "subject": "", "teacher": ""} for _ in range(8)])
    default_datesheet = json.dumps([{"date": "", "day": "", "subject": ""} for _ in range(8)])
    for cls in classes:
        cursor.execute("INSERT OR IGNORE INTO timetables (class_name, data) VALUES (?, ?)", (cls, default_timetable))
        cursor.execute("INSERT OR IGNORE INTO date_sheets (class_name, term_name, data) VALUES (?, ?, ?)", (cls, 'Term 1', default_datesheet))
    
    cursor.execute("INSERT OR IGNORE INTO school_settings (key, value) VALUES (?, ?)", ('language', 'english'))
    cursor.execute("INSERT OR IGNORE INTO school_settings (key, value) VALUES (?, ?)", ('theme', 'light'))
    
    conn.commit()
    conn.close()

def get_all_classes():
    return ['Nursery', 'Play', 'Prep', 'Class 1', 'Class 2', 'Class 3', 'Class 4', 
            'Class 5', 'Class 6', 'Class 7', 'Class 8', 'Class 9', 'Class 10']

def get_fee_by_class(class_name):
    fee = {'Nursery':5000,'Play':5500,'Prep':6000,'Class 1':6500,'Class 2':7000,
           'Class 3':7500,'Class 4':8000,'Class 5':8500,'Class 6':9000,
           'Class 7':9500,'Class 8':10000,'Class 9':11000,'Class 10':12000}
    return fee.get(class_name, 8000)

def get_class_color(class_name):
    # Return a distinct pastel color for each class
    colors = [(0.85,0.95,0.85,1), (0.95,0.85,0.95,1), (0.85,0.85,0.95,1),
              (0.95,0.95,0.85,1), (0.95,0.85,0.85,1), (0.85,0.95,0.95,1),
              (0.95,0.9,0.8,1), (0.9,0.95,0.8,1), (0.8,0.9,0.95,1),
              (0.95,0.8,0.9,1), (0.9,0.8,0.95,1), (0.8,0.95,0.9,1)]
    idx = hash(class_name) % len(colors)
    return colors[idx]

def block_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET status='Blocked' WHERE username=?", (username,))
    c.execute("UPDATE students SET is_deleted=1 WHERE username=?", (username,))
    conn.commit()
    conn.close()

def unblock_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET status='Approved' WHERE username=?", (username,))
    c.execute("UPDATE students SET is_deleted=0 WHERE username=?", (username,))
    conn.commit()
    conn.close()

def is_username_blocked(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT status FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == 'Blocked'

def get_documents_path():
    if platform == 'android':
        return '/sdcard/Documents/'
    else:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        documents = os.path.join(os.path.expanduser("~"), "Documents")
        if os.path.exists(documents):
            return documents
        elif os.path.exists(desktop):
            return desktop
        else:
            return os.getcwd()

def validate_bform(value):
    pattern = r'^\d{5}-\d{7}-\d{1}$'
    return re.match(pattern, value) is not None

def is_admin_or_principal_or_head(role):
    return role in ['Admin', 'Principal', 'Head']

def is_teacher(role):
    return role == 'Teacher'

def is_student(role):
    return role == 'Student'

def is_principal_active():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE role='Principal' AND status='Approved' LIMIT 1")
    exists = c.fetchone() is not None
    conn.close()
    return exists

def set_app_lock(locked):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO school_settings (key, value) VALUES (?, ?)", ('app_locked', str(locked)))
    conn.commit()
    conn.close()

def get_app_lock():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM school_settings WHERE key='app_locked'")
    row = c.fetchone()
    conn.close()
    return row and row[0] == 'True'

def enforce_principal_lock(app_instance, screen_manager, current_username, current_role):
    if current_role != 'Admin' and not is_principal_active():
        if hasattr(app_instance, 'lock_dialog_shown') and app_instance.lock_dialog_shown:
            return False
        app_instance.lock_dialog_shown = True
        def logout(*args):
            app_instance.lock_dialog_shown = False
            screen_manager.current = 'login'
        dialog = MDDialog(title="App Locked", text="The principal account has been removed. The app is temporarily disabled. Please contact the administrator.",
                          buttons=[MDFlatButton(text="OK", on_release=lambda x: (x.dismiss(), logout()))])
        dialog.open()
        return False
    return True

def show_month_year_dialog(callback):
    current_year = datetime.now().year
    current_month_num = datetime.now().month
    selected_year = current_year
    selected_month_num = current_month_num
    
    def update_month_grid():
        month_grid.clear_widgets()
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for i, month_name in enumerate(months, 1):
            month_num = i
            card = MDCard(
                orientation='vertical',
                size_hint_x=1,
                size_hint_y=None,
                height=dp(70),
                radius=12,
                elevation=3,
                md_bg_color=(1,1,1,1),
                padding=8
            )
            card.add_widget(MDLabel(
                text=f"{month_name}\n{selected_year}",
                halign='center',
                valign='middle',
                bold=True,
                theme_text_color="Custom",
                text_color=(0.05,0.28,0.63,1),
                font_style="Body1"
            ))
            card.bind(on_release=lambda x, y=selected_year, m=month_num: callback(f"{y}-{m:02d}"))
            month_grid.add_widget(card)
    
    content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None)
    content.bind(minimum_height=content.setter('height'))
    
    year_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=10)
    prev_btn = MDRaisedButton(text="◀", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.2)
    year_label = MDLabel(text=str(selected_year), halign='center', valign='middle', font_style="H5", bold=True, size_hint_x=0.6)
    next_btn = MDRaisedButton(text="▶", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.2)
    
    def prev_year(x):
        nonlocal selected_year
        selected_year -= 1
        year_label.text = str(selected_year)
        update_month_grid()
    
    def next_year(x):
        nonlocal selected_year
        selected_year += 1
        year_label.text = str(selected_year)
        update_month_grid()
    
    prev_btn.bind(on_release=prev_year)
    next_btn.bind(on_release=next_year)
    year_layout.add_widget(prev_btn)
    year_layout.add_widget(year_label)
    year_layout.add_widget(next_btn)
    content.add_widget(year_layout)
    
    month_grid = GridLayout(cols=3, spacing=10, size_hint_y=None)
    month_grid.bind(minimum_height=month_grid.setter('height'))
    content.add_widget(month_grid)
    
    update_month_grid()
    
    dialog = MDDialog(title="Select Month & Year", type="custom", content_cls=content,
                      buttons=[MDFlatButton(text="Cancel", on_release=lambda x: x.dismiss())])
    dialog.open()

def add_student_change_log(student_name, student_username, action, status='Pending'):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO student_change_logs (student_name, student_username, action, status, timestamp, viewed) VALUES (?, ?, ?, ?, ?, 0)",
              (student_name, student_username, action, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_unviewed_change_logs():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, student_name, student_username, action, status, timestamp FROM student_change_logs WHERE viewed=0 ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def mark_logs_viewed(log_ids):
    if not log_ids:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"UPDATE student_change_logs SET viewed=1 WHERE id IN ({','.join('?'*len(log_ids))})", log_ids)
    conn.commit()
    conn.close()

def get_all_change_logs():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, student_name, student_username, action, status, timestamp FROM student_change_logs ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_student_permanently(student_username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM fee_records WHERE student_username=?", (student_username,))
    c.execute("DELETE FROM student_results WHERE student_username=?", (student_username,))
    c.execute("DELETE FROM chat_messages WHERE sender_username=? OR receiver_username=?", (student_username, student_username))
    c.execute("DELETE FROM student_change_logs WHERE student_username=?", (student_username,))
    c.execute("DELETE FROM students WHERE username=?", (student_username,))
    c.execute("DELETE FROM users WHERE username=?", (student_username,))
    conn.commit()
    conn.close()

def add_teacher_change_log(teacher_name, teacher_username, action, status='Pending'):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO teacher_change_logs (teacher_name, teacher_username, action, status, timestamp, viewed) VALUES (?, ?, ?, ?, ?, 0)",
              (teacher_name, teacher_username, action, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_unviewed_teacher_logs():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, teacher_name, teacher_username, action, status, timestamp FROM teacher_change_logs WHERE viewed=0 ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def mark_teacher_logs_viewed(log_ids):
    if not log_ids:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"UPDATE teacher_change_logs SET viewed=1 WHERE id IN ({','.join('?'*len(log_ids))})", log_ids)
    conn.commit()
    conn.close()

def get_all_teacher_logs():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, teacher_name, teacher_username, action, status, timestamp FROM teacher_change_logs ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_teacher_permanently(teacher_username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM teachers WHERE username=?", (teacher_username,))
    c.execute("DELETE FROM chat_messages WHERE sender_username=? OR receiver_username=?", (teacher_username, teacher_username))
    c.execute("DELETE FROM teacher_change_logs WHERE teacher_username=?", (teacher_username,))
    c.execute("DELETE FROM users WHERE username=?", (teacher_username,))
    conn.commit()
    conn.close()

def restore_teacher(teacher_username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET status='Approved' WHERE username=?", (teacher_username,))
    c.execute("SELECT name, contact, address, gender, assigned_class, password FROM teachers WHERE username=?", (teacher_username,))
    row = c.fetchone()
    if row:
        name, contact, address, gender, assigned_class, password = row
        c.execute("INSERT OR IGNORE INTO teachers (name, contact, address, gender, assigned_class, username, password, class_strength) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (name, contact, address, gender, assigned_class, teacher_username, password, '0'))
    conn.commit()
    conn.close()

def save_profile_picture(username, source_path):
    if not os.path.exists(PROFILE_PICS_DIR):
        os.makedirs(PROFILE_PICS_DIR)
    ext = os.path.splitext(source_path)[1]
    dest = os.path.join(PROFILE_PICS_DIR, f"{username}{ext}")
    shutil.copyfile(source_path, dest)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET profile_pic=? WHERE username=?", (dest, username))
    conn.commit()
    conn.close()
    return dest

def get_profile_pic(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT profile_pic FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] and os.path.exists(row[0]):
        return row[0]
    return None

# ---------- NOTIFICATION FUNCTIONS ----------
def add_notification(recipient_username, title, message, type_):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO notifications (recipient_username, title, message, timestamp, is_read, type) VALUES (?, ?, ?, ?, 0, ?)",
              (recipient_username, title, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), type_))
    conn.commit()
    conn.close()

def get_unread_notifications_count(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM notifications WHERE recipient_username=? AND is_read=0", (username,))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_notifications(username, limit=50):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, title, message, timestamp, is_read, type FROM notifications WHERE recipient_username=? ORDER BY timestamp DESC LIMIT ?", (username, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_notifications_read(notif_ids):
    if not notif_ids:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"UPDATE notifications SET is_read=1 WHERE id IN ({','.join('?'*len(notif_ids))})", notif_ids)
    conn.commit()
    conn.close()

def notify_all_students_and_teachers(title, message, type_):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE role='Student' AND status='Approved'")
    students = c.fetchall()
    c.execute("SELECT username FROM users WHERE role='Teacher' AND status='Approved'")
    teachers = c.fetchall()
    conn.close()
    for (uname,) in students:
        add_notification(uname, title, message, type_)
    for (uname,) in teachers:
        add_notification(uname, title, message, type_)

def notify_teachers(title, message, type_):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE role='Teacher' AND status='Approved'")
    teachers = c.fetchall()
    conn.close()
    for (uname,) in teachers:
        add_notification(uname, title, message, type_)

def notify_student(student_username, title, message, type_):
    add_notification(student_username, title, message, type_)

# ---------------------------- KV STRING (UPDATED with new cards and icons) ----------------------------
KV = '''
ScreenManager:
    LoginScreen:
    RegisterScreen:
    DashboardScreen:
    PrincipalPanelScreen:
    PrincipalDateSheetsScreen:
    PrincipalTimetablesScreen:
    PrincipalAttendanceScreen:
    PrincipalFeeScreen:
    PrincipalStudentResultsScreen:
    HeadsPanelScreen:
    TeachersPanelScreen:
    StudentsPanelScreen:
    FeeLedgerScreen:
    FeeDetailScreen:
    ClassPanelScreen:
    StudentEditScreen:
    ChangePasswordScreen:
    TimetableScreen:
    DateSheetScreen:
    ResultsAnnouncementScreen:
    StudentResultViewScreen:
    StudentResultAccessScreen:
    SettingsScreen:
    AttendanceViewScreen:
    StudentChangeLogsScreen:
    TeacherChangeLogsScreen:
    NotificationsScreen:

<LoginScreen>:
    name: 'login'
    md_bg_color: 0.9,0.92,0.96,1
    ScrollView:
        do_scroll_y: True
        scroll_type: ['bars', 'content']
        bar_width: dp(6)
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: "20dp"
            Widget:
                size_hint_y: None
                height: "60dp"
            MDCard:
                orientation: 'vertical'
                size_hint_x: 0.88
                size_hint_y: None
                height: "480dp"
                padding: "24dp"
                spacing: "16dp"
                radius: [20,20,20,20]
                md_bg_color: 1,1,1,1
                elevation: 4
                pos_hint: {"center_x": 0.5}
                MDLabel:
                    text: "AL-HAMD CADET SCHOOL"
                    font_style: "H5"
                    bold: True
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.05,0.28,0.63,1
                    size_hint_y: None
                    height: "40dp"
                MDLabel:
                    text: "PORTAL LOGIN"
                    font_style: "Button"
                    bold: True
                    halign: "center"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: "20dp"
                MDTextField:
                    id: user_input
                    hint_text: "B-FORM / USERNAME"
                    icon_right: "account"
                    mode: "rectangle"
                MDTextField:
                    id: pass_input
                    hint_text: "PASSWORD"
                    icon_right: "key"
                    password: True
                    mode: "rectangle"
                MDFillRoundFlatButton:
                    text: "LOGIN"
                    md_bg_color: 0.05,0.28,0.63,1
                    size_hint_x: 1
                    on_release: root.process_login()
                MDFlatButton:
                    text: "CREATE NEW ACCOUNT"
                    theme_text_color: "Custom"
                    text_color: 0.05,0.28,0.63,1
                    pos_hint: {"center_x":0.5}
                    on_release: root.manager.current = 'register'
                MDLabel:
                    text: "CREATED BY KASHIF ALI (0344-7344008)"
                    font_style: "Caption"
                    bold: True
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.02,0.18,0.45,0.7
                    size_hint_y: None
                    height: "30dp"
            Widget:
                size_hint_y: None
                height: "60dp"

<RegisterScreen>:
    name: 'register'
    md_bg_color: 0.9,0.92,0.96,1
    ScrollView:
        do_scroll_y: True
        scroll_type: ['bars', 'content']
        bar_width: dp(6)
        MDBoxLayout:
            orientation: 'vertical'
            padding: "16dp"
            spacing: "10dp"
            size_hint_y: None
            height: self.minimum_height
            MDLabel:
                text: "CREATE NEW ACCOUNT"
                font_style: "H5"
                bold: True
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.05,0.28,0.63,1
                size_hint_y: None
                height: "50dp"
            MDCard:
                orientation: 'vertical'
                size_hint_x: 0.92
                size_hint_y: None
                height: "800dp"
                padding: "18dp"
                spacing: "12dp"
                radius: [20,20,20,20]
                md_bg_color: 1,1,1,1
                elevation: 4
                pos_hint: {"center_x": 0.5}
                MDLabel:
                    text: "SELECT YOUR ROLE"
                    font_style: "Caption"
                    bold: True
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: "20dp"
                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: "55dp"
                    spacing: "12dp"
                    MDRaisedButton:
                        id: student_role_btn
                        text: "STUDENT"
                        md_bg_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.5
                        on_release: root.set_role("Student")
                    MDRaisedButton:
                        id: teacher_role_btn
                        text: "TEACHER"
                        md_bg_color: 0.7,0.7,0.7,1
                        size_hint_x: 0.5
                        on_release: root.set_role("Teacher")
                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: "70dp"
                    spacing: "10dp"
                    MDTextField:
                        id: reg_name
                        hint_text: "FULL NAME *"
                        mode: "rectangle"
                        size_hint_x: 0.9
                        size_hint_y: None
                        height: "48dp"
                    MDIconButton:
                        id: profile_icon
                        icon: "camera"
                        theme_icon_color: "Custom"
                        icon_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.1
                        on_release: root.select_profile_pic()
                MDTextField:
                    id: reg_contact
                    hint_text: "CONTACT NUMBER *"
                    mode: "rectangle"
                    size_hint_y: None
                    height: "48dp"
                MDTextField:
                    id: reg_class
                    hint_text: "CLASS (Nursery/Play/Prep/Class 1-10) *"
                    mode: "rectangle"
                    size_hint_y: None
                    height: "48dp"
                MDTextField:
                    id: reg_bform
                    hint_text: "B-FORM (12345-1234567-8) *"
                    mode: "rectangle"
                    size_hint_y: None
                    height: "48dp"
                MDTextField:
                    id: reg_password
                    hint_text: "CREATE PASSWORD *"
                    password: True
                    mode: "rectangle"
                    size_hint_y: None
                    height: "48dp"
                MDLabel:
                    text: "GENDER"
                    font_style: "Caption"
                    bold: True
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: "18dp"
                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: "48dp"
                    spacing: "12dp"
                    MDRaisedButton:
                        id: male_btn
                        text: "MALE"
                        md_bg_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.5
                        on_release: root.set_gender("Male")
                    MDRaisedButton:
                        id: female_btn
                        text: "FEMALE"
                        md_bg_color: 0.7,0.7,0.7,1
                        size_hint_x: 0.5
                        on_release: root.set_gender("Female")
                MDFillRoundFlatButton:
                    text: "SUBMIT FOR APPROVAL"
                    md_bg_color: 0.05,0.28,0.63,1
                    size_hint_x: 1
                    size_hint_y: None
                    height: "48dp"
                    on_release: root.process_register()
                MDFlatButton:
                    text: "BACK TO LOGIN"
                    theme_text_color: "Custom"
                    text_color: 0.05,0.28,0.63,1
                    pos_hint: {"center_x":0.5}
                    size_hint_y: None
                    height: "35dp"
                    on_release: root.manager.current = 'login'
            Widget:
                size_hint_y: None
                height: "30dp"

<DashboardScreen>:
    name: 'dashboard'
    md_bg_color: 0.95,0.96,0.98,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            id: toolbar
            title: "AL-HAMD DASHBOARD"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["menu", lambda x: root.toggle_drawer()]]
            right_action_items: [["logout", lambda x: root.logout()]]
        MDScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                padding: "10dp"
                spacing: "8dp"
                size_hint_y: None
                height: self.minimum_height
                # Notifications card
                MDCard:
                    id: notif_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 0.95,0.95,0.9,1
                    on_release: root.open_notifications()
                    MDIcon:
                        icon: "bell"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        id: notif_label
                        text: "Notifications"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: principal_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 0.9,0.95,1,1
                    on_release: root.manager.current = 'principal_panel'
                    MDIcon:
                        icon: "school"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Principal Panel"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: heads_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 0.95,0.9,1,1
                    on_release: root.manager.current = 'heads_panel'
                    MDIcon:
                        icon: "account-tie"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Heads Panel"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: teachers_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 1,0.95,0.9,1
                    on_release: root.manager.current = 'teachers_panel'
                    MDIcon:
                        icon: "account-multiple"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Teachers Panel"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: students_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 0.9,1,0.95,1
                    on_release: root.manager.current = 'students_panel'
                    MDIcon:
                        icon: "account-school"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Students Panel"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: fee_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 1,0.9,0.9,1
                    on_release: root.manager.current = 'fee_ledger'
                    MDIcon:
                        icon: "cash"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Fee Ledger"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: class_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 0.9,0.9,1,1
                    on_release: root.manager.current = 'class_panel'
                    MDIcon:
                        icon: "google-classroom"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Class Panel"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: date_sheet_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 1,0.95,0.85,1
                    on_release: root.open_date_sheet()
                    MDIcon:
                        icon: "calendar"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Date Sheet"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: timetable_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 0.85,1,0.85,1
                    on_release: root.open_timetable()
                    MDIcon:
                        icon: "clock-outline"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Timetable Center"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: my_result_access_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 0.8,1,0.8,1
                    on_release: root.open_my_result_access()
                    MDIcon:
                        icon: "clipboard-list"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "My Result"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: ai_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 0.95,0.85,1,1
                    on_release: root.open_ai_dialog()
                    MDIcon:
                        icon: "robot"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Chat AI"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: settings_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 0.85,0.85,0.95,1
                    on_release: root.open_settings()
                    MDIcon:
                        icon: "cog"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Settings"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: change_pwd_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 1,0.85,0.85,1
                    on_release: root.manager.current = 'change_password'
                    MDIcon:
                        icon: "key"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Change Admin Password"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Primary"
                MDCard:
                    id: manage_principal_dash_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 1,0.8,0.8,1
                    on_release: root.manage_principal()
                    MDIcon:
                        icon: "account-cog"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "Manage Principal (Admin Only)"
                        font_style: "Button"
                        size_hint_x: 0.6
                        theme_text_color: "Custom"
                        text_color: 0.8,0.2,0.2,1
                MDCard:
                    id: my_class_label_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    radius: 12
                    md_bg_color: 1,1,1,1
                    MDLabel:
                        id: my_class_label
                        text: "Your Class: Not Available"
                        bold: True
                        font_style: "Button"
                        halign: "center"
                        valign: "middle"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1

<StudentResultAccessScreen>:
    name: 'student_result_access'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "STUDENT RESULT ACCESS"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
        MDScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                padding: "30dp"
                spacing: "20dp"
                size_hint_y: None
                height: self.minimum_height
                MDCard:
                    orientation: 'vertical'
                    padding: "14dp"
                    spacing: "15dp"
                    size_hint_y: None
                    height: dp(350)
                    radius: 16
                    md_bg_color: 1,1,1,1
                    elevation: 4
                    MDLabel:
                        text: "VIEW YOUR RESULT"
                        font_style: "H5"
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_y: None
                        height: "50dp"
                    MDTextField:
                        id: access_bform
                        hint_text: "B-FORM (12345-1234567-8)"
                        mode: "rectangle"
                        size_hint_y: None
                        height: "60dp"
                    MDTextField:
                        id: access_class
                        hint_text: "CLASS (e.g., Class 5)"
                        mode: "rectangle"
                        size_hint_y: None
                        height: "60dp"
                    MDTextField:
                        id: access_term
                        hint_text: "TERM (e.g., Term 1, Mid Term)"
                        mode: "rectangle"
                        size_hint_y: None
                        height: "60dp"
                    MDRaisedButton:
                        text: "SHOW RESULT"
                        md_bg_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.6
                        pos_hint: {"center_x": 0.5}
                        on_release: root.verify_and_show_result()

<SettingsScreen>:
    name: 'settings'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Settings"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
        MDScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                padding: "16dp"
                spacing: "20dp"
                size_hint_y: None
                height: self.minimum_height
                MDCard:
                    orientation: 'vertical'
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(420)
                    padding: "16dp"
                    spacing: "12dp"
                    radius: 14
                    elevation: 3
                    md_bg_color: 1,1,1,1
                    MDLabel:
                        text: "Privacy"
                        bold: True
                        font_style: "H6"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_y: None
                        height: dp(35)
                    MDLabel:
                        text: "[list]Data is stored locally in SQLite database only on device.[/list]"
                        markup: True
                        size_hint_y: None
                        height: dp(40)
                    MDLabel:
                        text: "[list]Passwords are stored as plain text (can be improved with hashing).[/list]"
                        markup: True
                        size_hint_y: None
                        height: dp(40)
                    MDLabel:
                        text: "[list]Users must be approved by Admin before access.[/list]"
                        markup: True
                        size_hint_y: None
                        height: dp(40)
                    MDLabel:
                        text: "[list]Blocked users lose all access.[/list]"
                        markup: True
                        size_hint_y: None
                        height: dp(40)
                    MDLabel:
                        text: "[list]Chat messages are visible only to sender and receiver.[/list]"
                        markup: True
                        size_hint_y: None
                        height: dp(40)
                    MDLabel:
                        text: "[list]No external data sharing or cloud storage.[/list]"
                        markup: True
                        size_hint_y: None
                        height: dp(40)
                MDCard:
                    orientation: 'horizontal'
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    padding: "10dp"
                    spacing: "10dp"
                    radius: 14
                    elevation: 3
                    md_bg_color: 1,1,1,1
                    MDLabel:
                        text: "Language"
                        bold: True
                        font_style: "H6"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.3
                        size_hint_y: None
                        height: dp(30)
                    MDBoxLayout:
                        orientation: 'horizontal'
                        spacing: 10
                        size_hint_x: 0.7
                        size_hint_y: None
                        height: dp(40)
                        MDRaisedButton:
                            id: english_btn
                            text: "English"
                            md_bg_color: 0.05,0.28,0.63,1
                            size_hint_x: 0.5
                            on_release: root.set_language('english')
                        MDRaisedButton:
                            id: urdu_btn
                            text: "Urdu"
                            md_bg_color: 0.7,0.7,0.7,1
                            size_hint_x: 0.5
                            on_release: root.set_language('urdu')
                MDCard:
                    orientation: 'horizontal'
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(60)
                    padding: "10dp"
                    spacing: "10dp"
                    radius: 14
                    elevation: 3
                    md_bg_color: 1,1,1,1
                    MDLabel:
                        text: "Themes"
                        bold: True
                        font_style: "H6"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.3
                        size_hint_y: None
                        height: dp(30)
                    MDBoxLayout:
                        orientation: 'horizontal'
                        spacing: 10
                        size_hint_x: 0.7
                        size_hint_y: None
                        height: dp(40)
                        MDRaisedButton:
                            id: light_btn
                            text: "Light"
                            md_bg_color: 0.05,0.28,0.63,1
                            size_hint_x: 0.5
                            on_release: root.set_theme('light')
                        MDRaisedButton:
                            id: dark_btn
                            text: "Dark"
                            md_bg_color: 0.7,0.7,0.7,1
                            size_hint_x: 0.5
                            on_release: root.set_theme('dark')

<ChangePasswordScreen>:
    name: 'change_password'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "CHANGE ADMIN PASSWORD"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
        MDScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                padding: "20dp"
                spacing: "20dp"
                size_hint_y: None
                height: self.minimum_height
                MDCard:
                    orientation: "vertical"
                    padding: "20dp"
                    spacing: "15dp"
                    size_hint_y: None
                    height: dp(400)
                    radius: 16
                    md_bg_color: 1,1,1,1
                    elevation: 3
                    MDLabel:
                        text: "CHANGE PASSWORD"
                        font_style: "H5"
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_y: None
                        height: "40dp"
                    MDTextField:
                        id: old_pass
                        hint_text: "OLD PASSWORD"
                        password: True
                        mode: "rectangle"
                        size_hint_y: None
                        height: "50dp"
                    MDTextField:
                        id: new_pass
                        hint_text: "NEW PASSWORD"
                        password: True
                        mode: "rectangle"
                        size_hint_y: None
                        height: "50dp"
                    MDTextField:
                        id: confirm_pass
                        hint_text: "CONFIRM PASSWORD"
                        password: True
                        mode: "rectangle"
                        size_hint_y: None
                        height: "50dp"
                    MDRaisedButton:
                        text: "UPDATE PASSWORD"
                        md_bg_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.6
                        pos_hint: {"center_x": 0.5}
                        on_release: root.update_password()

<PrincipalPanelScreen>:
    name: 'principal_panel'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "PRINCIPAL PANEL"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
            right_action_items: [["refresh", lambda x: root.load_notifications()]]
        MDScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                padding: "16dp"
                spacing: "12dp"
                size_hint_y: None
                height: self.minimum_height
                MDCard:
                    orientation: "vertical"
                    padding: "12dp"
                    spacing: "8dp"
                    size_hint_y: None
                    height: dp(220)
                    radius: 16
                    md_bg_color: 0.91,0.94,0.98,1
                    elevation: 3
                    MDBoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: dp(80)
                        padding: "10dp"
                        spacing: "10dp"
                        Image:
                            id: principal_profile
                            source: "assets/default_avatar.png"
                            size_hint_x: None
                            width: dp(70)
                            height: dp(70)
                            allow_stretch: True
                        MDLabel:
                            text: "Principal's Profile"
                            font_style: "H6"
                            bold: True
                            halign: "left"
                            valign: "middle"
                            theme_text_color: "Custom"
                            text_color: 0.05,0.28,0.63,1
                    MDLabel:
                        text: "Principal Name"
                        font_style: "H6"
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_y: None
                        height: dp(30)
                    MDTextField:
                        id: principal_name
                        hint_text: "Principal Name"
                        mode: "rectangle"
                        size_hint_y: None
                        height: dp(45)
                        text: ""
                        disabled: True
                        icon_right: "account"
                    MDRaisedButton:
                        text: "SAVE NAME"
                        md_bg_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.6
                        pos_hint: {"center_x":0.5}
                        size_hint_y: None
                        height: dp(35)
                        on_release: root.save_principal_name()
                MDCard:
                    orientation: "vertical"
                    padding: "12dp"
                    spacing: "8dp"
                    size_hint_y: None
                    height: dp(320)
                    radius: 16
                    md_bg_color: 0.98,0.94,0.96,1
                    elevation: 3
                    MDLabel:
                        text: "Principal's Message"
                        font_style: "H6"
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_y: None
                        height: dp(30)
                    MDTextField:
                        id: message_box
                        hint_text: "Edit your message here..."
                        mode: "rectangle"
                        multiline: True
                        size_hint_y: None
                        height: dp(180)
                        text: ""
                    MDRaisedButton:
                        text: "SAVE MESSAGE"
                        md_bg_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.6
                        pos_hint: {"center_x":0.5}
                        size_hint_y: None
                        height: dp(35)
                        on_release: root.save_principal_message()
                MDCard:
                    id: teacher_change_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(50)
                    padding: "10dp"
                    radius: 12
                    md_bg_color: 0.96,0.96,0.92,1
                    elevation: 3
                    on_release: root.open_teacher_change_logs()
                    MDIcon:
                        icon: "account-switch"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        id: teacher_change_label
                        text: "TEACHER CHANGE REQUESTS (0)"
                        bold: True
                        font_style: "Button"
                        halign: "center"
                        valign: "middle"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.8
                MDCard:
                    id: notification_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(50)
                    padding: "10dp"
                    radius: 12
                    md_bg_color: 0.92,0.96,0.92,1
                    elevation: 3
                    on_release: root.open_change_logs()
                    MDIcon:
                        icon: "bell-ring"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "STUDENT CHANGE REQUESTS (0)"
                        bold: True
                        font_style: "Button"
                        halign: "center"
                        valign: "middle"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.8
                MDCard:
                    id: manage_principal_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(50)
                    padding: "10dp"
                    radius: 12
                    md_bg_color: 0.98,0.92,0.92,1
                    elevation: 3
                    on_release: root.manage_principal()
                    MDIcon:
                        icon: "account-cog"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "MANAGE PRINCIPAL (Admin Only)"
                        bold: True
                        font_style: "Button"
                        halign: "center"
                        valign: "middle"
                        theme_text_color: "Custom"
                        text_color: 0.8,0.2,0.2,1
                        size_hint_x: 0.8
                MDCard:
                    id: date_sheets_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(50)
                    padding: "10dp"
                    radius: 12
                    md_bg_color: 0.94,0.94,0.98,1
                    elevation: 3
                    on_release: root.view_date_sheets()
                    MDIcon:
                        icon: "calendar"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "VIEW DATE SHEETS"
                        bold: True
                        font_style: "Button"
                        halign: "center"
                        valign: "middle"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.8
                MDCard:
                    id: timetables_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(50)
                    padding: "10dp"
                    radius: 12
                    md_bg_color: 0.96,0.94,0.90,1
                    elevation: 3
                    on_release: root.view_timetables()
                    MDIcon:
                        icon: "clock-outline"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "VIEW TIMETABLES"
                        bold: True
                        font_style: "Button"
                        halign: "center"
                        valign: "middle"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.8
                MDCard:
                    id: attendance_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(50)
                    padding: "10dp"
                    radius: 12
                    md_bg_color: 0.90,0.96,0.94,1
                    elevation: 3
                    on_release: root.view_attendance()
                    MDIcon:
                        icon: "clipboard-check"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "VIEW ATTENDANCE"
                        bold: True
                        font_style: "Button"
                        halign: "center"
                        valign: "middle"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.8
                MDCard:
                    id: fee_records_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(50)
                    padding: "10dp"
                    radius: 12
                    md_bg_color: 0.98,0.96,0.90,1
                    elevation: 3
                    on_release: root.view_fee_records()
                    MDIcon:
                        icon: "cash"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "VIEW FEE RECORDS"
                        bold: True
                        font_style: "Button"
                        halign: "center"
                        valign: "middle"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.8
                MDCard:
                    id: student_results_card
                    orientation: "horizontal"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(50)
                    padding: "10dp"
                    radius: 12
                    md_bg_color: 0.94,0.92,0.96,1
                    elevation: 3
                    on_release: root.view_student_results()
                    MDIcon:
                        icon: "clipboard-list"
                        size_hint_x: 0.2
                        pos_hint: {"center_y":0.5}
                    MDLabel:
                        text: "VIEW STUDENT RESULTS"
                        bold: True
                        font_style: "Button"
                        halign: "center"
                        valign: "middle"
                        theme_text_color: "Custom"
                        text_color: 0.05,0.28,0.63,1
                        size_hint_x: 0.8

<PrincipalDateSheetsScreen>:
    name: 'principal_date_sheets'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "VIEW DATE SHEETS"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_principal()]]
            right_action_items: [["refresh", lambda x: root.load_cards()], ["calendar", lambda x: root.show_term_picker()]]
        MDScrollView:
            MDBoxLayout:
                id: datesheet_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "10dp"
                size_hint_y: None
                height: self.minimum_height

<PrincipalTimetablesScreen>:
    name: 'principal_timetables'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "VIEW TIMETABLES"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_principal()]]
            right_action_items: [["refresh", lambda x: root.load_cards()]]
        MDScrollView:
            MDBoxLayout:
                id: timetable_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "10dp"
                size_hint_y: None
                height: self.minimum_height

<PrincipalAttendanceScreen>:
    name: 'principal_attendance'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "VIEW ATTENDANCE RECORDS"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_principal()]]
            right_action_items: [["refresh", lambda x: root.load_attendance()], ["calendar", lambda x: root.show_month_picker()]]
        MDScrollView:
            MDBoxLayout:
                id: attendance_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "12dp"
                size_hint_y: None
                height: self.minimum_height

<PrincipalFeeScreen>:
    name: 'principal_fee'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "VIEW FEE RECORDS"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_principal()]]
            right_action_items: [["refresh", lambda x: root.load_classes()], ["🗓️", lambda x: root.show_month_picker()]]
        MDScrollView:
            MDBoxLayout:
                id: fee_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "10dp"
                size_hint_y: None
                height: self.minimum_height

<PrincipalStudentResultsScreen>:
    name: 'principal_student_results'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "STUDENT RESULTS"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_principal()]]
            right_action_items: [["refresh", lambda x: root.load_data()], ["calendar", lambda x: root.show_term_picker()]]
        MDScrollView:
            MDBoxLayout:
                id: results_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "12dp"
                size_hint_y: None
                height: self.minimum_height

<HeadsPanelScreen>:
    name: 'heads_panel'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "HEADS PANEL"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
            right_action_items: [["refresh", lambda x: root.load_heads_list()]]
        MDBoxLayout:
            orientation: "vertical"
            padding: "10dp"
            spacing: "8dp"
            MDLabel:
                text: "ALL HEADS RECORDS"
                font_style: "H6"
                bold: True
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.05,0.28,0.63,1
                size_hint_y: None
                height: "40dp"
            ScrollView:
                do_scroll_x: False
                bar_width: dp(5)
                MDBoxLayout:
                    id: heads_container
                    orientation: "vertical"
                    spacing: "12dp"
                    size_hint_y: None
                    height: self.minimum_height
                    padding: "5dp"
            MDBoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: "65dp"
                padding: "10dp"
                MDRaisedButton:
                    text: "+ ADD NEW HEAD"
                    icon: "plus"
                    md_bg_color: 0.05,0.28,0.63,1
                    size_hint_x: 0.5
                    pos_hint: {"center_x":0.5}
                    on_release: root.open_add_head_dialog()

<TeachersPanelScreen>:
    name: 'teachers_panel'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "TEACHERS PANEL"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
            right_action_items: [["refresh", lambda x: root.load_teachers_list()]]
        MDBoxLayout:
            orientation: "vertical"
            padding: "10dp"
            spacing: "8dp"
            MDLabel:
                text: "ALL TEACHERS RECORDS"
                font_style: "H6"
                bold: True
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.05,0.28,0.63,1
                size_hint_y: None
                height: "40dp"
            ScrollView:
                do_scroll_x: False
                bar_width: dp(5)
                MDBoxLayout:
                    id: teachers_container
                    orientation: "vertical"
                    spacing: "12dp"
                    size_hint_y: None
                    height: self.minimum_height
                    padding: "5dp"
            MDBoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: "65dp"
                padding: "10dp"
                MDRaisedButton:
                    text: "+ ADD NEW TEACHER"
                    icon: "plus"
                    md_bg_color: 0.05,0.28,0.63,1
                    size_hint_x: 0.5
                    pos_hint: {"center_x":0.5}
                    on_release: root.open_add_teacher_dialog()

<StudentsPanelScreen>:
    name: 'students_panel'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "STUDENTS PANEL"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
            right_action_items: [["refresh", lambda x: root.load_students_list()]]
        MDBoxLayout:
            orientation: "vertical"
            padding: "10dp"
            spacing: "8dp"
            MDLabel:
                text: "ALL STUDENTS RECORDS"
                font_style: "H6"
                bold: True
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.05,0.28,0.63,1
                size_hint_y: None
                height: "40dp"
            ScrollView:
                do_scroll_x: False
                bar_width: dp(5)
                MDBoxLayout:
                    id: students_container
                    orientation: "vertical"
                    spacing: "12dp"
                    size_hint_y: None
                    height: self.minimum_height
                    padding: "5dp"
            MDBoxLayout:
                id: add_student_btn_layout
                orientation: "horizontal"
                size_hint_y: None
                height: "65dp"
                padding: "10dp"
                MDRaisedButton:
                    text: "+ ADD NEW STUDENT"
                    icon: "plus"
                    md_bg_color: 0.05,0.28,0.63,1
                    size_hint_x: 0.5
                    pos_hint: {"center_x":0.5}
                    on_release: root.open_add_student_dialog()

<ClassPanelScreen>:
    name: 'class_panel'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "CLASS PANEL"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
            right_action_items: [["refresh", lambda x: root.refresh_classes()]]
        MDScrollView:
            MDBoxLayout:
                id: classes_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "14dp"
                size_hint_y: None
                height: self.minimum_height

<StudentEditScreen>:
    name: 'student_edit'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            id: edit_toolbar
            title: "EDIT STUDENTS"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_class_panel()]]
            right_action_items: [["refresh", lambda x: root.load_students()], ["clipboard-account", lambda x: root.generate_pdf_report()]]
        MDScrollView:
            MDBoxLayout:
                id: edit_container
                orientation: "vertical"
                padding: "10dp"
                spacing: "15dp"
                size_hint_y: None
                height: self.minimum_height

<FeeLedgerScreen>:
    name: 'fee_ledger'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "FEE LEDGER"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
            right_action_items: [["refresh", lambda x: root.load_classes()], ["🗓️", lambda x: root.show_month_picker()]]
        MDScrollView:
            MDBoxLayout:
                id: fee_classes_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "14dp"
                size_hint_y: None
                height: self.minimum_height

<FeeDetailScreen>:
    name: 'fee_detail'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            id: toolbar
            title: "FEE DETAILS"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_ledger()]]
            right_action_items: [["refresh", lambda x: root.load_fee_data()], ["arrow-down", lambda x: root.generate_fee_pdf()]]
        MDScrollView:
            MDBoxLayout:
                id: fee_detail_container
                orientation: "vertical"
                padding: "10dp"
                spacing: "10dp"
                size_hint_y: None
                height: self.minimum_height

<TimetableScreen>:
    name: 'timetable'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "TIMETABLE CENTER"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
        MDScrollView:
            MDBoxLayout:
                id: timetable_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "14dp"
                size_hint_y: None
                height: self.minimum_height

<DateSheetScreen>:
    name: 'date_sheet'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "DATE SHEET"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
            right_action_items: [["plus", lambda x: root.add_term()], ["refresh", lambda x: root.load_terms()]]
        MDScrollView:
            MDBoxLayout:
                id: datesheet_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "14dp"
                size_hint_y: None
                height: self.minimum_height

<ResultsAnnouncementScreen>:
    name: 'results_announcement'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "RESULTS MANAGEMENT"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
            right_action_items: [["plus", lambda x: root.add_term()], ["refresh", lambda x: root.load_classes()]]
        MDScrollView:
            MDBoxLayout:
                id: results_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "14dp"
                size_hint_y: None
                height: self.minimum_height

<StudentResultViewScreen>:
    name: 'student_result_view'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "MY RESULT"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
            right_action_items: [["refresh", lambda x: root.load_result()]]
        MDScrollView:
            MDBoxLayout:
                id: result_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "12dp"
                size_hint_y: None
                height: self.minimum_height

<AttendanceViewScreen>:
    name: 'attendance_view'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Daily Attendance Records"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_principal()]]
        MDScrollView:
            MDBoxLayout:
                id: attendance_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "12dp"
                size_hint_y: None
                height: self.minimum_height

<StudentChangeLogsScreen>:
    name: 'student_change_logs'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Student Change Logs"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_principal()]]
            right_action_items: [["refresh", lambda x: root.load_logs()]]
        MDScrollView:
            MDBoxLayout:
                id: logs_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "12dp"
                size_hint_y: None
                height: self.minimum_height

<TeacherChangeLogsScreen>:
    name: 'teacher_change_logs'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Teacher Change Logs"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_principal()]]
            right_action_items: [["refresh", lambda x: root.load_logs()]]
        MDScrollView:
            MDBoxLayout:
                id: logs_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "12dp"
                size_hint_y: None
                height: self.minimum_height

<NotificationsScreen>:
    name: 'notifications'
    md_bg_color: 0.9,0.92,0.96,1
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Notifications"
            bold: True
            background_color: 0.05,0.28,0.63,1
            left_action_items: [["arrow-left", lambda x: root.back_to_dashboard()]]
            right_action_items: [["refresh", lambda x: root.load_notifications()]]
        MDScrollView:
            MDBoxLayout:
                id: notif_container
                orientation: "vertical"
                padding: "16dp"
                spacing: "12dp"
                size_hint_y: None
                height: self.minimum_height
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "60dp"
            padding: "10dp"
            MDRaisedButton:
                text: "Mark All as Read"
                md_bg_color: 0.05,0.28,0.63,1
                on_release: root.mark_all_read()
'''

# ---------------------------- SCREEN CLASSES (UPDATED with notifications and icons) ----------------------------
class LoginScreen(Screen):
    def process_login(self):
        u = self.ids.user_input.text.strip()
        p = self.ids.pass_input.text.strip()
        if not u or not p:
            self.show_dialog("Error", "Please enter B-Form/Username and password!")
            return
        if is_username_blocked(u):
            self.show_dialog("Blocked", "Your account has been blocked. Contact admin.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT role, status, gender FROM users WHERE username=? AND password=?", (u, p))
        user = c.fetchone()
        conn.close()
        if user:
            role, status, gender = user
            if status == 'Approved':
                app = MDApp.get_running_app()
                if role != 'Admin' and not is_principal_active():
                    self.show_dialog("App Locked", "The principal account has been removed. The app is temporarily disabled. Please contact the administrator.")
                    return
                app.username = u
                app.role = role
                app.user_gender = gender
                if role == 'Student':
                    conn2 = sqlite3.connect(DB_NAME)
                    cur = conn2.cursor()
                    cur.execute("SELECT class_name FROM users WHERE username=?", (u,))
                    row = cur.fetchone()
                    app.student_class = row[0] if row else None
                    conn2.close()
                conn3 = sqlite3.connect(DB_NAME)
                c3 = conn3.cursor()
                c3.execute("UPDATE users SET last_active=? WHERE username=?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), u))
                conn3.commit()
                conn3.close()
                self.manager.current = 'dashboard'
                self.manager.get_screen('dashboard').load_user_role(role)
                if role == 'Principal':
                    principal_screen = self.manager.get_screen('principal_panel')
                    pic = get_profile_pic(u)
                    if pic:
                        principal_screen.ids.principal_profile.source = pic
                    else:
                        principal_screen.ids.principal_profile.source = "assets/default_avatar.png"
                    principal_screen.ids.principal_profile.reload()
            else:
                self.show_dialog("Pending Approval", "Your account is pending approval by the admin.")
        else:
            self.show_dialog("Error", "Invalid B-Form/Username or password!")
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_gender = "Male"
        self.selected_role = "Student"
        self.selected_pic_path = None
        self.file_manager = None
    def set_role(self, role):
        self.selected_role = role
        if role == "Student":
            self.ids.student_role_btn.md_bg_color = (0.05,0.28,0.63,1)
            self.ids.teacher_role_btn.md_bg_color = (0.7,0.7,0.7,1)
            self.ids.reg_class.opacity = 1
            self.ids.reg_class.disabled = False
            self.ids.reg_bform.opacity = 1
            self.ids.reg_bform.disabled = False
        else:
            self.ids.student_role_btn.md_bg_color = (0.7,0.7,0.7,1)
            self.ids.teacher_role_btn.md_bg_color = (0.05,0.28,0.63,1)
            self.ids.reg_class.opacity = 0.3
            self.ids.reg_class.disabled = True
            self.ids.reg_class.text = ""
            self.ids.reg_bform.opacity = 0.3
            self.ids.reg_bform.disabled = True
            self.ids.reg_bform.text = ""
    def set_gender(self, g):
        self.selected_gender = g
        if g == "Male":
            self.ids.male_btn.md_bg_color = (0.05,0.28,0.63,1)
            self.ids.female_btn.md_bg_color = (0.7,0.7,0.7,1)
        else:
            self.ids.male_btn.md_bg_color = (0.7,0.7,0.7,1)
            self.ids.female_btn.md_bg_color = (0.05,0.28,0.63,1)
    def select_profile_pic(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=self.on_pic_selected,
            preview=True,
        )
        self.file_manager.show(os.path.expanduser("~"))
    def exit_file_manager(self, *args):
        if self.file_manager:
            self.file_manager.close()
    def on_pic_selected(self, path):
        self.exit_file_manager()
        if path and os.path.exists(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                self.selected_pic_path = path
                self.ids.profile_icon.icon_color = (0.2,0.7,0.3,1)
            else:
                self.show_dialog("Error", "Please select a JPG or PNG image.")
    def process_register(self):
        name = self.ids.reg_name.text.strip()
        contact = self.ids.reg_contact.text.strip()
        username = self.ids.reg_bform.text.strip()
        password = self.ids.reg_password.text.strip()
        gender = self.selected_gender
        role = self.selected_role
        if not all([name, contact, username, password]):
            self.show_dialog("Error", "All fields required!")
            return
        if self.selected_pic_path is None:
            self.show_dialog("Error", "Profile picture is required! Click the camera icon to upload.")
            return
        if role == "Student":
            class_name = self.ids.reg_class.text.strip()
            if not class_name:
                self.show_dialog("Error", "Class is required!")
                return
            if not validate_bform(username):
                self.show_dialog("Error", "B-Form must be in format: 12345-1234567-8")
                return
            address = "N/A"
        else:
            class_name = "N/A"
            address = "N/A"
            username = name
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, role, status, name, class_name, gender, contact, address) VALUES (?,?,?, 'Pending', ?, ?, ?, ?, ?)",
                      (username, password, role, name, class_name, gender, contact, address))
            if self.selected_pic_path:
                save_profile_picture(username, self.selected_pic_path)
            conn.commit()
            conn.close()
            self.show_dialog("Success", "Registration submitted! Wait for admin approval.")
            self.clear_fields()
            self.manager.current = 'login'
        except sqlite3.IntegrityError:
            self.show_dialog("Error", "Username already exists!")
    def clear_fields(self):
        self.ids.reg_name.text = ""
        self.ids.reg_contact.text = ""
        self.ids.reg_class.text = ""
        self.ids.reg_bform.text = ""
        self.ids.reg_password.text = ""
        self.selected_gender = "Male"
        self.selected_role = "Student"
        self.selected_pic_path = None
        self.ids.profile_icon.icon_color = (0.05,0.28,0.63,1)
        self.ids.male_btn.md_bg_color = (0.05,0.28,0.63,1)
        self.ids.female_btn.md_bg_color = (0.7,0.7,0.7,1)
        self.ids.student_role_btn.md_bg_color = (0.05,0.28,0.63,1)
        self.ids.teacher_role_btn.md_bg_color = (0.7,0.7,0.7,1)
        self.ids.reg_class.opacity = 1
        self.ids.reg_class.disabled = False
        self.ids.reg_bform.opacity = 1
        self.ids.reg_bform.disabled = False
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_manager = None
    def on_enter(self):
        app = MDApp.get_running_app()
        if app.role != 'Admin' and not is_principal_active():
            self.show_dialog("App Locked", "The principal account has been removed. The app is temporarily disabled. Please contact the administrator.")
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'login'), 0.5)
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET last_active=? WHERE username=?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), app.username))
        conn.commit()
        conn.close()
        if hasattr(self, 'user_role'):
            self.load_user_role(self.user_role)
        if app.role == 'Student' and app.student_class:
            self.ids.my_class_label.text = f"Your Class: {app.student_class}"
            self.ids.my_class_label_card.opacity = 1
            self.ids.my_class_label_card.disabled = False
        else:
            self.ids.my_class_label_card.opacity = 0
            self.ids.my_class_label_card.disabled = True
        # Update notification count badge
        notif_count = get_unread_notifications_count(app.username)
        self.ids.notif_label.text = f"Notifications ({notif_count})" if notif_count > 0 else "Notifications"
    def load_user_role(self, role):
        self.user_role = role
        cards = {
            'principal_card': True,
            'heads_card': True,
            'teachers_card': True,
            'students_card': True,
            'fee_card': True,
            'class_card': True,
            'date_sheet_card': True,
            'timetable_card': True,
            'my_result_access_card': True,
            'ai_card': True,
            'settings_card': True,
            'change_pwd_card': (role == 'Admin'),
            'manage_principal_dash_card': (role == 'Admin')
        }
        if role == 'Student':
            for card_id in ['principal_card','heads_card','teachers_card','class_card','timetable_card','ai_card','settings_card','change_pwd_card','manage_principal_dash_card']:
                if card_id in cards:
                    cards[card_id] = False
            cards['students_card'] = True
            cards['fee_card'] = True
            cards['date_sheet_card'] = True
            cards['my_result_access_card'] = True
        elif role == 'Teacher':
            cards['change_pwd_card'] = False
            cards['manage_principal_dash_card'] = False
        for card_id, visible in cards.items():
            if hasattr(self.ids, card_id):
                if visible:
                    self.ids[card_id].opacity = 1
                    self.ids[card_id].disabled = False
                else:
                    self.ids[card_id].opacity = 0
                    self.ids[card_id].disabled = True
    def logout(self):
        self.manager.current = 'login'
    def open_date_sheet(self):
        self.manager.current = 'date_sheet'
    def open_timetable(self):
        self.manager.current = 'timetable'
    def open_my_result(self):
        self.manager.current = 'student_result_view'
        self.manager.get_screen('student_result_view').load_result()
    def open_my_result_access(self):
        self.manager.current = 'student_result_access'
    def open_ai_dialog(self):
        content = MDBoxLayout(orientation='vertical', spacing=20, padding=20, size_hint_y=None, height=400)
        chatgpt_card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=80, radius=14, elevation=4, md_bg_color=(1,1,1,1), padding=10)
        chatgpt_card.add_widget(MDLabel(text="ChatGPT", halign="center", valign="middle", font_style="H5", bold=True, theme_text_color="Custom", text_color=(0.05,0.28,0.63,1), size_hint=(1,1)))
        chatgpt_card.bind(on_release=lambda x: self.open_app_store('chatgpt'))
        content.add_widget(chatgpt_card)
        gemini_card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=80, radius=14, elevation=4, md_bg_color=(1,1,1,1), padding=10)
        gemini_card.add_widget(MDLabel(text="Gemini", halign="center", valign="middle", font_style="H5", bold=True, theme_text_color="Custom", text_color=(0.05,0.28,0.63,1), size_hint=(1,1)))
        gemini_card.bind(on_release=lambda x: self.open_app_store('gemini'))
        content.add_widget(gemini_card)
        deepseek_card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=80, radius=14, elevation=4, md_bg_color=(1,1,1,1), padding=10)
        deepseek_card.add_widget(MDLabel(text="DeepSeek", halign="center", valign="middle", font_style="H5", bold=True, theme_text_color="Custom", text_color=(0.05,0.28,0.63,1), size_hint=(1,1)))
        deepseek_card.bind(on_release=lambda x: self.open_app_store('deepseek'))
        content.add_widget(deepseek_card)
        dialog = MDDialog(title="Select AI Assistant", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="Close", on_release=lambda x: x.dismiss())])
        dialog.open()
    def open_app_store(self, app_name):
        packages = {'deepseek': 'com.deepseek.chat', 'gemini': 'com.google.android.apps.bard', 'chatgpt': 'com.openai.chatgpt'}
        if platform == 'android':
            pkg = packages.get(app_name)
            if pkg:
                webbrowser.open(f'market://details?id={pkg}')
            else:
                self.show_dialog("Error", "App not found in store.")
        elif platform == 'ios':
            urls = {'deepseek': 'https://apps.apple.com/app/deepseek/id1660393232', 'gemini': 'https://apps.apple.com/app/google-gemini/id6477794871', 'chatgpt': 'https://apps.apple.com/app/chatgpt/id6448311069'}
            url = urls.get(app_name)
            if url:
                webbrowser.open(url)
            else:
                self.show_dialog("Error", "App not found in store.")
        else:
            self.show_dialog("Info", "Please install the app from official store on your mobile device.")
    def open_settings(self):
        self.manager.current = 'settings'
    def open_notifications(self):
        self.manager.current = 'notifications'
        self.manager.get_screen('notifications').load_notifications()
    def manage_principal(self):
        app = MDApp.get_running_app()
        if app.role != 'Admin':
            self.show_dialog("Access Denied", "Only Admin can manage principal.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT username, name, role FROM users WHERE role != 'Admin' AND status='Approved' ORDER BY name")
        users = c.fetchall()
        conn.close()
        if not users:
            self.show_dialog("Info", "No eligible users found to assign as principal.")
            return
        current_principal = None
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT username, name FROM users WHERE role='Principal' AND status='Approved'")
        row = c.fetchone()
        current_principal = row[0] if row else None
        conn.close()
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=(20,12,20,20), size_hint_y=None, height=700)
        content.add_widget(MDLabel(text="Current Principal:", font_style="H6", bold=True, size_hint_y=None, height=30))
        content.add_widget(MDLabel(text=current_principal if current_principal else "None", size_hint_y=None, height=30))
        content.add_widget(Widget(size_hint_y=None, height=10))
        content.add_widget(MDLabel(text="Select new principal:", font_style="H6", bold=True, size_hint_y=None, height=30))
        user_list = GridLayout(cols=1, spacing=10, size_hint_y=None)
        user_list.bind(minimum_height=user_list.setter('height'))
        for uname, name, role in users:
            btn = MDRaisedButton(text=f"{name} ({uname}) - {role}", size_hint_x=1, height=dp(50), md_bg_color=(0.05,0.28,0.63,1))
            btn.bind(on_release=lambda x, u=uname, n=name: (self.set_principal(u), setattr(self.manager.get_screen('principal_panel').ids.principal_name, 'text', n)))
            user_list.add_widget(btn)
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False)
        scroll.add_widget(user_list)
        content.add_widget(scroll)
        dlg = MDDialog(title="Manage Principal", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="Close", on_release=lambda x: x.dismiss()),
                                MDRaisedButton(text="Remove Principal", md_bg_color=(0.8,0.2,0.2,1), on_release=lambda x: self.remove_principal(dlg))])
        dlg.open()
    def set_principal(self, username):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET role='User' WHERE role='Principal'")
        c.execute("UPDATE users SET role='Principal' WHERE username=?", (username,))
        conn.commit()
        conn.close()
        set_app_lock(False)
        self.show_dialog("Success", f"{username} is now the Principal. App is unlocked for all staff.")
        self.manager.current = 'principal_panel'
    def remove_principal(self, dialog):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET role='User' WHERE role='Principal'")
        conn.commit()
        conn.close()
        set_app_lock(True)
        dialog.dismiss()
        self.show_dialog("Principal Removed", "Principal has been removed. App is now locked. Only Admin can assign a new principal.")
        self.manager.current = 'dashboard'
    def toggle_drawer(self):
        pass
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class NotificationsScreen(Screen):
    def load_notifications(self):
        container = self.ids.notif_container
        container.clear_widgets()
        app = MDApp.get_running_app()
        notifs = get_notifications(app.username)
        if not notifs:
            container.add_widget(MDLabel(text="No notifications yet.", halign="center", theme_text_color="Secondary"))
            return
        for nid, title, msg, ts, is_read, typ in notifs:
            card = MDCard(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=dp(120), radius=12, elevation=3, md_bg_color=(1,1,1,0.9) if is_read else (1,1,0.9,1))
            card.add_widget(MDLabel(text=title, bold=True, size_hint_y=None, height=dp(30)))
            card.add_widget(MDLabel(text=msg, size_hint_y=None, height=dp(40)))
            card.add_widget(MDLabel(text=ts, size_hint_y=None, height=dp(20), theme_text_color="Secondary"))
            if not is_read:
                mark_btn = MDRaisedButton(text="Mark as Read", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.4, pos_hint={'center_x':0.5},
                                          on_release=lambda x, nid=nid: self.mark_read(nid))
                card.add_widget(mark_btn)
            container.add_widget(card)
    def mark_read(self, notif_id):
        mark_notifications_read([notif_id])
        self.load_notifications()
        self.manager.get_screen('dashboard').on_enter()
    def mark_all_read(self):
        app = MDApp.get_running_app()
        notifs = get_notifications(app.username)
        ids = [n[0] for n in notifs if not n[4]]
        if ids:
            mark_notifications_read(ids)
        self.load_notifications()
        self.manager.get_screen('dashboard').on_enter()
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'

class StudentResultAccessScreen(Screen):
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'
    
    def verify_and_show_result(self):
        bform = self.ids.access_bform.text.strip()
        class_name = self.ids.access_class.text.strip()
        term = self.ids.access_term.text.strip()
        
        if not bform or not class_name or not term:
            self.show_dialog("Error", "Please fill all fields (B-Form, Class, Term).")
            return
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT u.name, u.class_name, s.father_name, s.cnic, u.username FROM users u JOIN students s ON u.username = s.username WHERE u.username=? AND u.class_name=? AND u.role='Student' AND u.status='Approved' AND s.is_deleted=0", (bform, class_name))
        student = c.fetchone()
        conn.close()
        
        if not student:
            self.show_dialog("Login Failed", "Invalid B-Form or Class. Please check and try again.")
            return
        
        student_name, found_class, father_name, cnic, uname = student
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT subject, total_marks, obtained_marks, percentage, grade FROM student_results WHERE student_username=? AND term_name=?", (uname, term))
        results = c.fetchall()
        conn.close()
        
        if not results:
            self.show_dialog("No Results", f"No results found for term '{term}'. Please check term spelling or contact teacher.")
            return
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT value FROM school_settings WHERE key='school_name'")
        school_row = c.fetchone()
        school_name = school_row[0] if school_row else "Al-Hamd Cadet School"
        conn.close()
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT student_username, SUM(obtained_marks) as total_obtained, SUM(total_marks) as total_marks
            FROM student_results WHERE class_name=? AND term_name=?
            GROUP BY student_username
        """, (found_class, term))
        all_students = c.fetchall()
        conn.close()
        
        rank = 1
        for idx, (uname2, obtained, total) in enumerate(sorted(all_students, key=lambda x: (x[1]/x[2]) if x[2]>0 else 0, reverse=True)):
            if uname2 == uname:
                rank = idx + 1
                break
        
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
        main_box = MDBoxLayout(orientation='vertical', spacing=15, size_hint_y=None, padding=20, width=Window.width-dp(40))
        main_box.bind(minimum_height=main_box.setter('height'))
        
        main_box.add_widget(MDLabel(text=school_name, font_style="H4", bold=True, halign='center', size_hint_y=None, height=dp(50)))
        main_box.add_widget(MDLabel(text="ACADEMIC RESULT CARD", font_style="H5", bold=True, halign='center', size_hint_y=None, height=dp(40)))
        main_box.add_widget(Widget(size_hint_y=None, height=dp(10)))
        
        info_card = MDCard(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=dp(180), radius=12, elevation=2, md_bg_color=(1,1,1,1))
        info_card.add_widget(MDLabel(text=f"Name: {student_name}", bold=True, size_hint_y=None, height=dp(30)))
        info_card.add_widget(MDLabel(text=f"B-Form: {bform}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"Father Name: {father_name}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"CNIC: {cnic if cnic else 'N/A'}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"Class: {found_class}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"Term: {term}", size_hint_y=None, height=dp(25)))
        main_box.add_widget(info_card)
        
        main_box.add_widget(MDLabel(text="Subject-wise Marks", bold=True, font_style="H6", size_hint_y=None, height=dp(40)))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=10)
        header.add_widget(MDLabel(text="Subject", bold=True, size_hint_x=0.4))
        header.add_widget(MDLabel(text="Total", bold=True, size_hint_x=0.3))
        header.add_widget(MDLabel(text="Obtained", bold=True, size_hint_x=0.3))
        main_box.add_widget(header)
        
        total_marks = 0
        total_obtained = 0
        for subj, tot, obt, perc, grade in results:
            row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=10)
            row_box.add_widget(MDLabel(text=subj, size_hint_x=0.4))
            row_box.add_widget(MDLabel(text=str(tot), size_hint_x=0.3))
            row_box.add_widget(MDLabel(text=str(obt), size_hint_x=0.3))
            main_box.add_widget(row_box)
            total_marks += tot
            total_obtained += obt
        
        main_box.add_widget(Widget(size_hint_y=None, height=dp(10)))
        percentage = (total_obtained / total_marks * 100) if total_marks > 0 else 0
        if percentage >= 80: grade = "A+"
        elif percentage >= 70: grade = "A"
        elif percentage >= 60: grade = "B"
        elif percentage >= 50: grade = "C"
        elif percentage >= 40: grade = "D"
        else: grade = "F" if total_marks > 0 else "N/A"
        
        summary_card = MDCard(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=dp(140), radius=12, elevation=2, md_bg_color=(1,1,1,1))
        summary_card.add_widget(MDLabel(text=f"Total Marks: {total_obtained} / {total_marks}", bold=True, size_hint_y=None, height=dp(30)))
        summary_card.add_widget(MDLabel(text=f"Percentage: {percentage:.2f}%", bold=True, size_hint_y=None, height=dp(30)))
        summary_card.add_widget(MDLabel(text=f"Grade: {grade}", bold=True, size_hint_y=None, height=dp(30)))
        summary_card.add_widget(MDLabel(text=f"Position: {rank} / {len(all_students)}", bold=True, size_hint_y=None, height=dp(30)))
        main_box.add_widget(summary_card)
        
        scroll.add_widget(main_box)
        
        paper_card = MDCard(orientation='horizontal', size_hint_y=None, height=dp(50), radius=12, elevation=3, md_bg_color=(0.05,0.28,0.63,1), padding=10)
        paper_card.add_widget(MDLabel(text="Paper Generate", bold=True, font_style="Button", halign="center", valign="middle", theme_text_color="Custom", text_color=(1,1,1,1)))
        paper_card.bind(on_release=lambda x: self.generate_result_pdf(school_name, student_name, bform, father_name, cnic, found_class, term, results, all_students, rank))
        
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=10, size_hint_y=None, height=dp(350))
        content.add_widget(scroll)
        content.add_widget(paper_card)
        
        dialog = MDDialog(title=f"Result - {term}", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: x.dismiss())])
        dialog.open()
    
    def generate_result_pdf(self, school_name, student_name, bform, father_name, cnic, class_name, term, results, all_students, rank):
        if not REPORTLAB_AVAILABLE:
            self.show_dialog("Error", "ReportLab not installed. Please install it using: pip install reportlab")
            return
        save_path = get_documents_path()
        if not os.path.exists(save_path):
            save_path = os.getcwd()
        filename = os.path.join(save_path, f"Result_{student_name}_{term}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm, leftMargin=15*mm, rightMargin=15*mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=12)
        story = []
        story.append(Paragraph(f"{school_name}", title_style))
        story.append(Paragraph(f"ACADEMIC RESULT CARD - {term}", title_style))
        story.append(Spacer(1, 10))
        info_data = [['Name:', student_name], ['B-Form:', bform], ['Father Name:', father_name], ['CNIC:', cnic if cnic else 'N/A'], ['Class:', class_name]]
        info_table = Table(info_data, colWidths=[50*mm, 100*mm])
        info_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('FONTNAME', (0,0), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,0), (-1,-1), 10)]))
        story.append(info_table)
        story.append(Spacer(1, 10))
        table_data = [['Subject', 'Total', 'Obtained', 'Percentage', 'Grade']]
        total_marks = 0
        total_obtained = 0
        for subj, tot, obt, perc, grade in results:
            table_data.append([subj, str(tot), str(obt), f"{perc:.1f}%", grade])
            total_marks += tot
            total_obtained += obt
        table_data.append(['TOTAL', str(total_marks), str(total_obtained), '', ''])
        col_widths = [40*mm, 20*mm, 20*mm, 25*mm, 15*mm]
        table = Table(table_data, repeatRows=1, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 10))
        percentage = (total_obtained / total_marks * 100) if total_marks > 0 else 0
        if percentage >= 80: grade = "A+"
        elif percentage >= 70: grade = "A"
        elif percentage >= 60: grade = "B"
        elif percentage >= 50: grade = "C"
        elif percentage >= 40: grade = "D"
        else: grade = "F"
        summary_data = [['Total Percentage:', f"{percentage:.2f}%"], ['Grade:', grade], ['Position:', f"{rank} / {len(all_students)}"]]
        summary_table = Table(summary_data, colWidths=[50*mm, 100*mm])
        summary_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('FONTNAME', (0,0), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,0), (-1,-1), 10), ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold')]))
        story.append(summary_table)
        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(A4[0]/2, 15*mm, f"Page {page_num}")
            canvas.restoreState()
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        self.show_dialog("Success", f"PDF saved at:\n{filename}")
    
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class SettingsScreen(Screen):
    def on_enter(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT value FROM school_settings WHERE key='language'")
        lang_row = c.fetchone()
        c.execute("SELECT value FROM school_settings WHERE key='theme'")
        theme_row = c.fetchone()
        conn.close()
        current_lang = lang_row[0] if lang_row else 'english'
        current_theme = theme_row[0] if theme_row else 'light'
        if current_lang == 'english':
            self.ids.english_btn.md_bg_color = (0.05,0.28,0.63,1)
            self.ids.urdu_btn.md_bg_color = (0.7,0.7,0.7,1)
        else:
            self.ids.english_btn.md_bg_color = (0.7,0.7,0.7,1)
            self.ids.urdu_btn.md_bg_color = (0.05,0.28,0.63,1)
        if current_theme == 'light':
            self.ids.light_btn.md_bg_color = (0.05,0.28,0.63,1)
            self.ids.dark_btn.md_bg_color = (0.7,0.7,0.7,1)
        else:
            self.ids.light_btn.md_bg_color = (0.7,0.7,0.7,1)
            self.ids.dark_btn.md_bg_color = (0.05,0.28,0.63,1)
    def set_language(self, lang):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO school_settings (key, value) VALUES (?, ?)", ('language', lang))
        conn.commit()
        conn.close()
        if lang == 'english':
            self.ids.english_btn.md_bg_color = (0.05,0.28,0.63,1)
            self.ids.urdu_btn.md_bg_color = (0.7,0.7,0.7,1)
        else:
            self.ids.english_btn.md_bg_color = (0.7,0.7,0.7,1)
            self.ids.urdu_btn.md_bg_color = (0.05,0.28,0.63,1)
            if URDU_FONT_AVAILABLE:
                MDApp.get_running_app().user_font = 'JameelNooriNastaleeq'
            else:
                self.show_dialog("Font Missing", "Urdu font not found. Using default.")
        self.show_dialog("Language", f"Language set to {lang}. Restart app for full effect.")
    def set_theme(self, theme):
        app = MDApp.get_running_app()
        if theme == 'light':
            app.theme_cls.theme_style = 'Light'
            self.ids.light_btn.md_bg_color = (0.05,0.28,0.63,1)
            self.ids.dark_btn.md_bg_color = (0.7,0.7,0.7,1)
        else:
            app.theme_cls.theme_style = 'Dark'
            self.ids.light_btn.md_bg_color = (0.7,0.7,0.7,1)
            self.ids.dark_btn.md_bg_color = (0.05,0.28,0.63,1)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO school_settings (key, value) VALUES (?, ?)", ('theme', theme))
        conn.commit()
        conn.close()
        self.show_dialog("Theme", f"Theme set to {theme}.")
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'

class ChangePasswordScreen(Screen):
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'
    def update_password(self):
        old = self.ids.old_pass.text.strip()
        new = self.ids.new_pass.text.strip()
        confirm = self.ids.confirm_pass.text.strip()
        if not old or not new or not confirm:
            self.show_dialog("Error", "All fields required!")
            return
        if new != confirm:
            self.show_dialog("Error", "New password and confirm password do not match!")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username='kashif'")
        current = c.fetchone()
        if not current or current[0] != old:
            self.show_dialog("Error", "Old password is incorrect!")
            conn.close()
            return
        c.execute("UPDATE users SET password=? WHERE username='kashif'", (new,))
        conn.commit()
        conn.close()
        self.show_dialog("Success", "Password updated successfully!")
        self.manager.current = 'dashboard'
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class PrincipalPanelScreen(Screen):
    def on_enter(self):
        app = MDApp.get_running_app()
        if is_student(app.role):
            self.show_dialog("Access Denied", "You do not have permission to access the Principal Panel.")
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'dashboard'), 0.5)
            return
        if app.role != 'Admin' and not is_principal_active():
            self.show_dialog("App Locked", "The principal account has been removed. The app is temporarily disabled.")
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'dashboard'), 0.5)
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT value FROM school_settings WHERE key='principal_name'")
        r1 = c.fetchone()
        c.execute("SELECT value FROM school_settings WHERE key='principal_message'")
        r2 = c.fetchone()
        if app.role == 'Principal':
            pic = get_profile_pic(app.username)
            if pic:
                self.ids.principal_profile.source = pic
            else:
                self.ids.principal_profile.source = "assets/default_avatar.png"
            self.ids.principal_profile.reload()
        conn.close()
        if r1: self.ids.principal_name.text = r1[0]
        if r2: self.ids.message_box.text = r2[0]
        show_cards = is_admin_or_principal_or_head(app.role) or is_teacher(app.role)
        management_cards = ['date_sheets_card', 'timetables_card', 'attendance_card', 'fee_records_card', 'student_results_card']
        for card_id in management_cards:
            if hasattr(self.ids, card_id):
                if show_cards:
                    self.ids[card_id].opacity = 1
                    self.ids[card_id].disabled = False
                else:
                    self.ids[card_id].opacity = 0
                    self.ids[card_id].disabled = True
        if app.role == 'Admin':
            self.ids.manage_principal_card.opacity = 1
            self.ids.manage_principal_card.disabled = False
        else:
            self.ids.manage_principal_card.opacity = 0
            self.ids.manage_principal_card.disabled = True
        self.load_notifications()
        self.load_teacher_change_count()
    def load_teacher_change_count(self):
        logs = get_unviewed_teacher_logs()
        self.ids.teacher_change_label.text = f"TEACHER CHANGE REQUESTS ({len(logs)})"
    def load_notifications(self):
        logs = get_unviewed_change_logs()
        self.ids.notification_card.children[1].text = f"STUDENT CHANGE REQUESTS ({len(logs)})"
    def open_teacher_change_logs(self):
        self.manager.current = 'teacher_change_logs'
        self.manager.get_screen('teacher_change_logs').load_logs()
        logs = get_unviewed_teacher_logs()
        if logs:
            mark_teacher_logs_viewed([l[0] for l in logs])
            self.load_teacher_change_count()
    def open_change_logs(self):
        self.manager.current = 'student_change_logs'
        self.manager.get_screen('student_change_logs').load_logs()
        logs = get_unviewed_change_logs()
        if logs:
            mark_logs_viewed([l[0] for l in logs])
            self.load_notifications()
    def save_principal_name(self):
        pname = self.ids.principal_name.text
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO school_settings (key, value) VALUES (?,?)", ('principal_name', pname))
        conn.commit()
        conn.close()
        self.show_dialog("Success", "Principal name updated!")
    def save_principal_message(self):
        msg = self.ids.message_box.text
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO school_settings (key, value) VALUES (?,?)", ('principal_message', msg))
        conn.commit()
        conn.close()
        self.show_dialog("Success", "Message updated!")
    def manage_principal(self):
        app = MDApp.get_running_app()
        if app.role != 'Admin':
            self.show_dialog("Access Denied", "Only Admin can manage principal.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT username, name, role FROM users WHERE role != 'Admin' AND status='Approved' ORDER BY name")
        users = c.fetchall()
        conn.close()
        if not users:
            self.show_dialog("Info", "No eligible users found to assign as principal.")
            return
        current_principal = None
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT username, name FROM users WHERE role='Principal' AND status='Approved'")
        row = c.fetchone()
        current_principal = row[0] if row else None
        conn.close()
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=(20,12,20,20), size_hint_y=None, height=700)
        content.add_widget(MDLabel(text="Current Principal:", font_style="H6", bold=True, size_hint_y=None, height=30))
        content.add_widget(MDLabel(text=current_principal if current_principal else "None", size_hint_y=None, height=30))
        content.add_widget(Widget(size_hint_y=None, height=10))
        content.add_widget(MDLabel(text="Select new principal:", font_style="H6", bold=True, size_hint_y=None, height=30))
        user_list = GridLayout(cols=1, spacing=10, size_hint_y=None)
        user_list.bind(minimum_height=user_list.setter('height'))
        for uname, name, role in users:
            btn = MDRaisedButton(text=f"{name} ({uname}) - {role}", size_hint_x=1, height=dp(50), md_bg_color=(0.05,0.28,0.63,1))
            btn.bind(on_release=lambda x, u=uname, n=name: (self.set_principal(u), setattr(self.ids.principal_name, 'text', n)))
            user_list.add_widget(btn)
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False)
        scroll.add_widget(user_list)
        content.add_widget(scroll)
        dlg = MDDialog(title="Manage Principal", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="Close", on_release=lambda x: x.dismiss()),
                                MDRaisedButton(text="Remove Principal", md_bg_color=(0.8,0.2,0.2,1), on_release=lambda x: self.remove_principal(dlg))])
        dlg.open()
    def set_principal(self, username):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET role='User' WHERE role='Principal'")
        c.execute("UPDATE users SET role='Principal' WHERE username=?", (username,))
        conn.commit()
        conn.close()
        set_app_lock(False)
        self.show_dialog("Success", f"{username} is now the Principal. App is unlocked for all staff.")
        self.manager.current = 'principal_panel'
    def remove_principal(self, dialog):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET role='User' WHERE role='Principal'")
        conn.commit()
        conn.close()
        set_app_lock(True)
        dialog.dismiss()
        self.show_dialog("Principal Removed", "Principal has been removed. App is now locked. Only Admin can assign a new principal.")
        self.manager.current = 'dashboard'
    def view_date_sheets(self):
        self.manager.current = 'principal_date_sheets'
        self.manager.get_screen('principal_date_sheets').load_cards()
    def view_timetables(self):
        self.manager.current = 'principal_timetables'
        self.manager.get_screen('principal_timetables').load_cards()
    def view_attendance(self):
        self.manager.current = 'principal_attendance'
        self.manager.get_screen('principal_attendance').load_attendance()
    def view_fee_records(self):
        self.manager.current = 'principal_fee'
        self.manager.get_screen('principal_fee').load_classes()
    def view_student_results(self):
        self.manager.current = 'principal_student_results'
        self.manager.get_screen('principal_student_results').load_data()
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class StudentChangeLogsScreen(Screen):
    def load_logs(self):
        container = self.ids.logs_container
        container.clear_widgets()
        app = MDApp.get_running_app()
        all_logs = get_all_change_logs()

        if is_student(app.role):
            all_logs = [log for log in all_logs if log[2] == app.username]

        if not all_logs:
            container.add_widget(MDLabel(text="No change logs found.", halign="center", theme_text_color="Secondary"))
            return

        for idx, log in enumerate(all_logs, 1):
            lid, s_name, s_uname, action, status, ts = log
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT is_deleted FROM students WHERE username=?", (s_uname,))
            row = c.fetchone()
            is_deleted = row[0] if row else None
            conn.close()
            card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(160),
                          radius=12, elevation=3, md_bg_color=(1,1,1,1), padding=12, spacing=8)
            card.add_widget(MDLabel(text=f"{idx}. Student: {s_name} ({s_uname})", bold=True, size_hint_y=None, height=dp(30)))
            card.add_widget(MDLabel(text=f"Action: {action} at {ts}", theme_text_color="Secondary", size_hint_y=None, height=dp(25)))
            card.add_widget(MDLabel(text=f"Status: {status}", bold=True, size_hint_y=None, height=dp(25)))
            btn_layout = MDBoxLayout(orientation='horizontal', spacing=12, size_hint_y=None, height=dp(45))

            if is_admin_or_principal_or_head(app.role):
                if status == 'Pending':
                    approve_btn = MDRaisedButton(text="Approve", md_bg_color=(0.2,0.7,0.3,1), size_hint_x=0.5,
                                                  on_release=lambda x, uname=s_uname, name=s_name: self.approve_student(uname, name))
                    reject_btn = MDRaisedButton(text="Reject", md_bg_color=(0.8,0.2,0.2,1), size_hint_x=0.5,
                                                  on_release=lambda x, uname=s_uname: self.reject_student(uname))
                    btn_layout.add_widget(approve_btn)
                    btn_layout.add_widget(reject_btn)
                elif action == 'Deleted' and is_deleted is not None:
                    add_back_btn = MDRaisedButton(text="Add Back", md_bg_color=(0.2,0.7,0.3,1), size_hint_x=0.5,
                                                  on_release=lambda x, uname=s_uname: self.add_back_student(uname))
                    del_perm_btn = MDRaisedButton(text="Delete Permanently", md_bg_color=(0.8,0.2,0.2,1), size_hint_x=0.5,
                                                  on_release=lambda x, uname=s_uname: self.confirm_delete_permanent(uname))
                    btn_layout.add_widget(add_back_btn)
                    btn_layout.add_widget(del_perm_btn)
                else:
                    btn_layout.add_widget(Widget(size_hint_x=1))
            else:
                btn_layout.add_widget(Widget(size_hint_x=1))

            card.add_widget(btn_layout)
            container.add_widget(card)

    def approve_student(self, student_username, student_name):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET status='Approved' WHERE username=?", (student_username,))
        c.execute("UPDATE student_change_logs SET status='Approved' WHERE student_username=?", (student_username,))
        c.execute("SELECT id FROM students WHERE username=?", (student_username,))
        if not c.fetchone():
            c.execute("SELECT class_name, gender, contact, address, password FROM users WHERE username=?", (student_username,))
            row = c.fetchone()
            if row:
                class_name, gender, contact, address, password = row
                total_fee = get_fee_by_class(class_name)
                current_month = datetime.now().strftime('%Y-%m')
                c.execute("INSERT INTO students (name, contact, class_name, address, gender, username, password, father_name, cnic, dob, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                          (student_name, contact, class_name, address, gender, student_username, password, '', '', ''))
                c.execute("INSERT INTO fee_records (student_name, student_username, class_name, total_fee, paid_amount, remaining, status, month_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          (student_name, student_username, class_name, total_fee, 0, total_fee, 'Less Paid', current_month))
        conn.commit()
        conn.close()
        self.load_logs()
        self.show_dialog("Success", f"Student {student_name} approved and added to class.")
        # Notification to student and teachers
        notify_student(student_username, "Account Approved", f"Your account has been approved by admin. You can now login.", "approval")
        notify_teachers("New Student Approved", f"Student {student_name} has been approved and added to class {class_name}.", "student_approval")

    def reject_student(self, student_username):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE username=?", (student_username,))
        c.execute("DELETE FROM student_change_logs WHERE student_username=?", (student_username,))
        conn.commit()
        conn.close()
        self.load_logs()
        self.show_dialog("Success", f"Student {student_username} rejected and removed.")

    def add_back_student(self, student_username):
        def confirm(instance):
            unblock_user(student_username)
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT class_name FROM students WHERE username=?", (student_username,))
            row = c.fetchone()
            if row:
                class_name = row[0]
                current_month = datetime.now().strftime('%Y-%m')
                c.execute("SELECT id FROM fee_records WHERE student_username=? AND month_year=?", (student_username, current_month))
                if not c.fetchone():
                    total_fee = get_fee_by_class(class_name)
                    c.execute("INSERT INTO fee_records (student_name, student_username, class_name, total_fee, paid_amount, remaining, status, month_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                              (student_username, student_username, class_name, total_fee, 0, total_fee, 'Less Paid', current_month))
            conn.commit()
            conn.close()
            self.show_dialog("Success", f"Student {student_username} has been restored.")
            self.load_logs()
            principal = self.manager.get_screen('principal_panel')
            principal.load_notifications()
            dlg.dismiss()
            # Notification
            notify_student(student_username, "Account Restored", "Your account has been restored by admin.", "restore")
            notify_teachers("Student Restored", f"Student {student_username} has been restored.", "student_restore")
        dlg = MDDialog(title="Confirm Restore", text=f"Are you sure you want to restore student {student_username}?",
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="RESTORE", md_bg_color=(0.2,0.7,0.3,1), on_release=confirm)])
        dlg.open()

    def confirm_delete_permanent(self, student_username):
        def confirm(instance):
            delete_student_permanently(student_username)
            self.show_dialog("Success", f"Student {student_username} permanently deleted.")
            self.load_logs()
            principal = self.manager.get_screen('principal_panel')
            principal.load_notifications()
            dlg.dismiss()
            notify_teachers("Student Deleted Permanently", f"Student {student_username} has been permanently deleted.", "student_delete")
        dlg = MDDialog(title="Confirm Permanent Deletion", 
                       text=f"WARNING: This will permanently delete {student_username} from all records (fees, results, chat, logs). This action cannot be undone.\n\nAre you sure?",
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="DELETE PERMANENTLY", md_bg_color=(0.8,0.2,0.2,1), on_release=confirm)])
        dlg.open()

    def back_to_principal(self):
        self.manager.current = 'principal_panel'
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class TeacherChangeLogsScreen(Screen):
    def load_logs(self):
        container = self.ids.logs_container
        container.clear_widgets()
        app = MDApp.get_running_app()
        all_logs = get_all_teacher_logs()

        if not all_logs:
            container.add_widget(MDLabel(text="No teacher change logs found.", halign="center", theme_text_color="Secondary"))
            return

        for idx, log in enumerate(all_logs, 1):
            lid, t_name, t_uname, action, status, ts = log
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT status FROM users WHERE username=?", (t_uname,))
            row = c.fetchone()
            is_blocked = (row and row[0] == 'Blocked') if row else False
            conn.close()
            card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(160),
                          radius=12, elevation=3, md_bg_color=(1,1,1,1), padding=12, spacing=8)
            card.add_widget(MDLabel(text=f"{idx}. Teacher: {t_name} ({t_uname})", bold=True, size_hint_y=None, height=dp(30)))
            card.add_widget(MDLabel(text=f"Action: {action} at {ts}", theme_text_color="Secondary", size_hint_y=None, height=dp(25)))
            card.add_widget(MDLabel(text=f"Status: {status}", bold=True, size_hint_y=None, height=dp(25)))
            btn_layout = MDBoxLayout(orientation='horizontal', spacing=12, size_hint_y=None, height=dp(45))

            if is_admin_or_principal_or_head(app.role):
                if status == 'Pending':
                    approve_btn = MDRaisedButton(text="Approve", md_bg_color=(0.2,0.7,0.3,1), size_hint_x=0.5,
                                                  on_release=lambda x, uname=t_uname, name=t_name: self.approve_teacher(uname, name))
                    reject_btn = MDRaisedButton(text="Reject", md_bg_color=(0.8,0.2,0.2,1), size_hint_x=0.5,
                                                  on_release=lambda x, uname=t_uname: self.reject_teacher(uname))
                    btn_layout.add_widget(approve_btn)
                    btn_layout.add_widget(reject_btn)
                elif action == 'Deleted' and is_blocked:
                    add_back_btn = MDRaisedButton(text="Add Back", md_bg_color=(0.2,0.7,0.3,1), size_hint_x=0.5,
                                                  on_release=lambda x, uname=t_uname: self.restore_teacher(uname))
                    del_perm_btn = MDRaisedButton(text="Delete Permanently", md_bg_color=(0.8,0.2,0.2,1), size_hint_x=0.5,
                                                  on_release=lambda x, uname=t_uname: self.confirm_delete_permanent(uname))
                    btn_layout.add_widget(add_back_btn)
                    btn_layout.add_widget(del_perm_btn)
                else:
                    btn_layout.add_widget(Widget(size_hint_x=1))
            else:
                btn_layout.add_widget(Widget(size_hint_x=1))

            card.add_widget(btn_layout)
            container.add_widget(card)

    def approve_teacher(self, teacher_username, teacher_name):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET status='Approved' WHERE username=?", (teacher_username,))
        c.execute("UPDATE teacher_change_logs SET status='Approved' WHERE teacher_username=?", (teacher_username,))
        c.execute("SELECT id FROM teachers WHERE username=?", (teacher_username,))
        if not c.fetchone():
            c.execute("SELECT assigned_class, gender, contact, address, password FROM users WHERE username=?", (teacher_username,))
            row = c.fetchone()
            if row:
                assigned_class, gender, contact, address, password = row
                c.execute("INSERT INTO teachers (name, contact, address, gender, assigned_class, username, password, class_strength) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          (teacher_name, contact, address, gender, assigned_class, teacher_username, password, '0'))
        conn.commit()
        conn.close()
        self.load_logs()
        self.show_dialog("Success", f"Teacher {teacher_name} approved.")
        # Notification to teacher
        notify_student(teacher_username, "Account Approved", f"Your teacher account has been approved.", "approval")
        notify_teachers("New Teacher Approved", f"Teacher {teacher_name} has been approved.", "teacher_approval")

    def reject_teacher(self, teacher_username):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE username=?", (teacher_username,))
        c.execute("DELETE FROM teacher_change_logs WHERE teacher_username=?", (teacher_username,))
        conn.commit()
        conn.close()
        self.load_logs()
        self.show_dialog("Success", f"Teacher {teacher_username} rejected and removed.")

    def restore_teacher(self, teacher_username):
        def confirm(instance):
            restore_teacher(teacher_username)
            self.show_dialog("Success", f"Teacher {teacher_username} has been restored.")
            self.load_logs()
            principal = self.manager.get_screen('principal_panel')
            principal.load_teacher_change_count()
            dlg.dismiss()
            # Notification
            notify_student(teacher_username, "Account Restored", "Your teacher account has been restored.", "restore")
            notify_teachers("Teacher Restored", f"Teacher {teacher_username} has been restored.", "teacher_restore")
        dlg = MDDialog(title="Confirm Restore", text=f"Are you sure you want to restore teacher {teacher_username}?",
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="RESTORE", md_bg_color=(0.2,0.7,0.3,1), on_release=confirm)])
        dlg.open()

    def confirm_delete_permanent(self, teacher_username):
        def confirm(instance):
            delete_teacher_permanently(teacher_username)
            self.show_dialog("Success", f"Teacher {teacher_username} permanently deleted.")
            self.load_logs()
            principal = self.manager.get_screen('principal_panel')
            principal.load_teacher_change_count()
            dlg.dismiss()
            notify_teachers("Teacher Deleted Permanently", f"Teacher {teacher_username} has been permanently deleted.", "teacher_delete")
        dlg = MDDialog(title="Confirm Permanent Deletion", 
                       text=f"WARNING: This will permanently delete {teacher_username} from all records (teacher data, chat, logs). This action cannot be undone.\n\nAre you sure?",
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="DELETE PERMANENTLY", md_bg_color=(0.8,0.2,0.2,1), on_release=confirm)])
        dlg.open()

    def back_to_principal(self):
        self.manager.current = 'principal_panel'
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class PrincipalDateSheetsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_term = "Term 1"
        self.terms_list = []
    def on_enter(self):
        self.load_terms()
    def load_terms(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT DISTINCT term_name FROM date_sheets ORDER BY term_name")
        terms = c.fetchall()
        conn.close()
        self.terms_list = [t[0] for t in terms] if terms else ["Term 1"]
        self.load_cards()
    def show_term_picker(self):
        if not self.terms_list:
            self.show_dialog("Info", "No terms available.")
            return
        def on_select(selected_term):
            self.current_term = selected_term
            self.load_cards()
        MDDialog(title="Select Term", text="", 
                 buttons=[MDFlatButton(text=t, on_release=lambda x, term=t: on_select(term)) for t in self.terms_list] + 
                 [MDFlatButton(text="Cancel", on_release=lambda x: x.dismiss())]).open()
    def load_cards(self):
        container = self.ids.datesheet_container
        container.clear_widgets()
        term_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=10, padding=[10,5])
        term_label = MDLabel(text="Select Term:", size_hint_x=0.3, font_style="H6")
        term_spinner = MDTextField(hint_text="Term", text=self.current_term, mode="rectangle", size_hint_x=0.5, on_focus=self.on_term_focus)
        term_layout.add_widget(term_label)
        term_layout.add_widget(term_spinner)
        container.add_widget(term_layout)
        classes = get_all_classes()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        for class_name in classes:
            c.execute("SELECT data FROM date_sheets WHERE class_name=? AND term_name=?", (class_name, self.current_term))
            row = c.fetchone()
            data = json.loads(row[0]) if row else [{"date":"","day":"","subject":""} for _ in range(8)]
            preview = "No entries"
            for entry in data:
                if entry.get("date") and entry.get("subject"):
                    preview = f"{entry['date']} - {entry['subject']}"
                    break
            color = get_class_color(class_name)
            card = MDCard(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=dp(55),
                          radius=12, elevation=3, md_bg_color=(1,1,1,1), padding=[12,5], spacing=10)
            label = MDLabel(text=class_name, bold=True, font_style="H6", 
                            halign='left', valign='middle', size_hint_x=0.7,
                            theme_text_color="Custom", text_color=(0.05,0.28,0.63,1))
            label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
            view_btn = MDRaisedButton(text="VIEW", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.25, height=dp(40),
                                      on_release=lambda x, cn=class_name: self.view_datesheet(cn))
            card.add_widget(label)
            card.add_widget(view_btn)
            container.add_widget(card)
        conn.close()
    def on_term_focus(self, instance, focus):
        if focus:
            self.show_term_picker()
    def view_datesheet(self, class_name):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT data FROM date_sheets WHERE class_name=? AND term_name=?", (class_name, self.current_term))
        row = c.fetchone()
        data = json.loads(row[0]) if row else [{"date":"","day":"","subject":""} for _ in range(8)]
        conn.close()
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
        main_box = MDBoxLayout(orientation='vertical', spacing=12, size_hint_y=None, width=Window.width-dp(80))
        main_box.bind(minimum_height=main_box.setter('height'))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
        header.add_widget(MDLabel(text="Date", bold=True, size_hint_x=0.30))
        header.add_widget(MDLabel(text="Day", bold=True, size_hint_x=0.30))
        header.add_widget(MDLabel(text="Subject", bold=True, size_hint_x=0.40))
        main_box.add_widget(header)
        for entry in data:
            row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
            row_box.add_widget(MDLabel(text=entry.get("date",""), size_hint_x=0.30, shorten=True))
            row_box.add_widget(MDLabel(text=entry.get("day",""), size_hint_x=0.30, shorten=True))
            row_box.add_widget(MDLabel(text=entry.get("subject",""), size_hint_x=0.40, shorten=True))
            main_box.add_widget(row_box)
        scroll.add_widget(main_box)
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=dp(450))
        content.add_widget(MDLabel(text=f"Date Sheet - {class_name} ({self.current_term})", font_style="H6", bold=True, halign="center", size_hint_y=None, height=40))
        content.add_widget(scroll)
        MDDialog(title="", type="custom", content_cls=content,
                 buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: x.dismiss())]).open()
    def back_to_principal(self):
        self.manager.current = 'principal_panel'
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class PrincipalTimetablesScreen(Screen):
    def load_cards(self):
        container = self.ids.timetable_container
        container.clear_widgets()
        classes = get_all_classes()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        for class_name in classes:
            c.execute("SELECT data FROM timetables WHERE class_name=?", (class_name,))
            row = c.fetchone()
            data = json.loads(row[0]) if row else [{"time":"","subject":"","teacher":""} for _ in range(8)]
            preview = "No entries"
            for entry in data:
                if entry.get("time") and entry.get("subject"):
                    preview = f"{entry['time']} - {entry['subject']}"
                    break
            card = MDCard(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=dp(55),
                          radius=12, elevation=3, md_bg_color=(1,1,1,1), padding=[12,5], spacing=10)
            label = MDLabel(text=class_name, bold=True, font_style="H6", 
                            halign='left', valign='middle', size_hint_x=0.7,
                            theme_text_color="Custom", text_color=(0.05,0.28,0.63,1))
            label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
            view_btn = MDRaisedButton(text="VIEW", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.25, height=dp(40),
                                      on_release=lambda x, cn=class_name: self.view_timetable(cn))
            card.add_widget(label)
            card.add_widget(view_btn)
            container.add_widget(card)
        conn.close()
    def view_timetable(self, class_name):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT data FROM timetables WHERE class_name=?", (class_name,))
        row = c.fetchone()
        data = json.loads(row[0]) if row else [{"time":"","subject":"","teacher":""} for _ in range(8)]
        conn.close()
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
        main_box = MDBoxLayout(orientation='vertical', spacing=12, size_hint_y=None, width=Window.width-dp(80))
        main_box.bind(minimum_height=main_box.setter('height'))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
        header.add_widget(MDLabel(text="Time", bold=True, size_hint_x=0.35))
        header.add_widget(MDLabel(text="Subject", bold=True, size_hint_x=0.35))
        header.add_widget(MDLabel(text="Teacher", bold=True, size_hint_x=0.30))
        main_box.add_widget(header)
        for entry in data:
            row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
            row_box.add_widget(MDLabel(text=entry.get("time",""), size_hint_x=0.35, shorten=True))
            row_box.add_widget(MDLabel(text=entry.get("subject",""), size_hint_x=0.35, shorten=True))
            row_box.add_widget(MDLabel(text=entry.get("teacher",""), size_hint_x=0.30, shorten=True))
            main_box.add_widget(row_box)
        scroll.add_widget(main_box)
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=dp(450))
        content.add_widget(MDLabel(text=f"Timetable - {class_name}", font_style="H6", bold=True, halign="center", size_hint_y=None, height=40))
        content.add_widget(scroll)
        MDDialog(title="", type="custom", content_cls=content,
                 buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: x.dismiss())]).open()
    def back_to_principal(self):
        self.manager.current = 'principal_panel'

class PrincipalAttendanceScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_month = datetime.now().strftime('%Y-%m')
    def show_month_picker(self):
        def on_month_selected(month_year):
            self.current_month = month_year
            self.load_attendance()
        show_month_year_dialog(on_month_selected)
    def load_attendance(self):
        container = self.ids.attendance_container
        container.clear_widgets()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if self.current_month:
            c.execute("SELECT date, class_name, slot, teacher_username, total_present, total_absent, total_students FROM attendance WHERE strftime('%Y-%m', date) = ? ORDER BY date DESC, slot DESC", (self.current_month,))
        else:
            c.execute("SELECT date, class_name, slot, teacher_username, total_present, total_absent, total_students FROM attendance ORDER BY date DESC, slot DESC")
        records = c.fetchall()
        conn.close()
        if not records:
            container.add_widget(MDLabel(text="No attendance records found for selected month.", halign="center", theme_text_color="Secondary", size_hint_y=None, height=50))
        for rec in records:
            date, cls, slot, teacher, present, absent, total = rec
            card = MDCard(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=160, radius=12, elevation=3, md_bg_color=(1,1,1,1))
            card.add_widget(MDLabel(text=f"Date: {date}  |  Class: {cls}", bold=True, size_hint_y=None, height=30))
            card.add_widget(MDLabel(text=f"Slot: {slot}  |  Teacher: {teacher}", size_hint_y=None, height=25))
            card.add_widget(MDLabel(text=f"Present: {present}  |  Absent: {absent}  |  Total: {total}", size_hint_y=None, height=25))
            container.add_widget(card)
    def back_to_principal(self):
        self.manager.current = 'principal_panel'
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class PrincipalFeeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_month = datetime.now().strftime('%Y-%m')
    def show_month_picker(self):
        def on_month_selected(month_year):
            self.current_month = month_year
            self.load_classes()
        show_month_year_dialog(on_month_selected)
    def load_classes(self):
        container = self.ids.fee_container
        container.clear_widgets()
        classes = get_all_classes()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        month_card = MDCard(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=dp(50), radius=12, elevation=2, md_bg_color=(1,1,1,1), padding=8)
        month_card.add_widget(MDLabel(text=f"Selected Month: {self.current_month}", bold=True, font_style="H6", halign="center", theme_text_color="Custom", text_color=(0.05,0.28,0.63,1)))
        container.add_widget(month_card)
        for class_name in classes:
            c.execute("SELECT COUNT(*) FROM fee_records fr JOIN students s ON fr.student_username = s.username WHERE fr.class_name=? AND fr.month_year=? AND s.is_deleted=0", (class_name, self.current_month))
            count = c.fetchone()[0]
            color = get_class_color(class_name)
            card = MDCard(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=dp(55),
                          radius=12, elevation=3, md_bg_color=(1,1,1,1), padding=[12,5], spacing=10)
            label = MDLabel(text=class_name, bold=True, font_style="H6", 
                            halign='left', valign='middle', size_hint_x=0.6,
                            theme_text_color="Custom", text_color=(0.05,0.28,0.63,1))
            label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
            view_btn = MDRaisedButton(text="VIEW DETAILS", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.35, height=dp(40),
                                      on_release=lambda x, cn=class_name: self.view_fee_detail(cn))
            card.add_widget(label)
            card.add_widget(view_btn)
            container.add_widget(card)
        conn.close()
    def view_fee_detail(self, class_name):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT fr.student_name, fr.student_username, fr.total_fee, fr.paid_amount, fr.remaining, fr.status FROM fee_records fr JOIN students s ON fr.student_username = s.username WHERE fr.class_name=? AND fr.month_year=? AND s.is_deleted=0 ORDER BY fr.student_name", (class_name, self.current_month))
        records = c.fetchall()
        conn.close()
        if not records:
            self.show_dialog("Info", "No fee records found for this class.")
            return
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
        main_box = MDBoxLayout(orientation='vertical', spacing=12, size_hint_y=None, width=Window.width-dp(80))
        main_box.bind(minimum_height=main_box.setter('height'))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=8)
        header.add_widget(MDLabel(text="Student", bold=True, size_hint_x=0.25))
        header.add_widget(MDLabel(text="B-Form", bold=True, size_hint_x=0.25))
        header.add_widget(MDLabel(text="Total", bold=True, size_hint_x=0.15))
        header.add_widget(MDLabel(text="Paid", bold=True, size_hint_x=0.15))
        header.add_widget(MDLabel(text="Remaining", bold=True, size_hint_x=0.20))
        main_box.add_widget(header)
        for rec in records:
            name, uname, total, paid, remaining, status = rec
            row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=8)
            row_box.add_widget(MDLabel(text=name[:20], size_hint_x=0.25, shorten=True))
            row_box.add_widget(MDLabel(text=uname, size_hint_x=0.25, shorten=True))
            row_box.add_widget(MDLabel(text=str(total), size_hint_x=0.15))
            row_box.add_widget(MDLabel(text=str(paid), size_hint_x=0.15))
            row_box.add_widget(MDLabel(text=str(remaining), size_hint_x=0.20, bold=True if remaining>0 else False, 
                                       theme_text_color="Custom", text_color=(0.8,0.2,0.2,1) if remaining>0 else (0.2,0.7,0.3,1)))
            main_box.add_widget(row_box)
        scroll.add_widget(main_box)
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=dp(450))
        content.add_widget(MDLabel(text=f"Fee Details - {class_name} ({self.current_month})", font_style="H6", bold=True, halign="center", size_hint_y=None, height=40))
        content.add_widget(scroll)
        MDDialog(title="", type="custom", content_cls=content,
                 buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: x.dismiss())]).open()
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()
    def back_to_principal(self):
        self.manager.current = 'principal_panel'

class PrincipalStudentResultsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_class = None
        self.selected_term = None
        self.classes = get_all_classes()
        self.terms_list = []
    def load_data(self):
        self.load_terms()
        self.load_ui()
    def load_terms(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT DISTINCT term_name FROM student_results ORDER BY term_name")
        terms = c.fetchall()
        conn.close()
        self.terms_list = [t[0] for t in terms] if terms else []
    def show_term_picker(self):
        if not self.terms_list:
            self.show_dialog("Info", "No terms available.")
            return
        def on_select(term):
            self.selected_term = term
            self.load_ui()
        MDDialog(title="Select Term", text="", 
                 buttons=[MDFlatButton(text=t, on_release=lambda x, term=t: on_select(term)) for t in self.terms_list] + 
                 [MDFlatButton(text="Cancel", on_release=lambda x: x.dismiss())]).open()
    def load_ui(self):
        container = self.ids.results_container
        container.clear_widgets()
        container.add_widget(MDLabel(text="SELECT CLASS", bold=True, font_style="H6", halign="center", size_hint_y=None, height=dp(40)))
        other_classes = [c for c in self.classes if c != 'Class 10']
        class_grid = GridLayout(cols=3, spacing=dp(12), size_hint_y=None)
        class_grid.bind(minimum_height=class_grid.setter('height'))
        for cls in other_classes:
            color = get_class_color(cls)
            card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(120),
                          radius=12, elevation=2, md_bg_color=(1,1,1,1), padding=8)
            label = MDLabel(text=cls, bold=True, halign='center', valign='middle',
                            theme_text_color="Custom", text_color=(0.05,0.28,0.63,1))
            card.add_widget(label)
            if self.selected_class == cls:
                card.md_bg_color = (0.2, 0.8, 0.2, 1)
            card.bind(on_release=lambda x, c=cls: self.select_class(c))
            class_grid.add_widget(card)
        container.add_widget(class_grid)
        if 'Class 10' in self.classes:
            class10_card = MDCard(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=dp(120),
                                  radius=12, elevation=2, md_bg_color=(1,1,1,1), padding=8)
            label = MDLabel(text="Class 10", bold=True, halign='center', valign='middle',
                            theme_text_color="Custom", text_color=(0.05,0.28,0.63,1))
            class10_card.add_widget(label)
            if self.selected_class == 'Class 10':
                class10_card.md_bg_color = (0.2, 0.8, 0.2, 1)
            class10_card.bind(on_release=lambda x, c='Class 10': self.select_class(c))
            container.add_widget(class10_card)
        if not self.selected_class:
            return
        container.add_widget(Widget(size_hint_y=None, height=dp(20)))
        container.add_widget(MDLabel(text="SELECT TERM", bold=True, font_style="H6", halign="center", size_hint_y=None, height=dp(40)))
        if not self.terms_list:
            container.add_widget(MDLabel(text="No terms available. Please add terms in Results Management.", halign="center", theme_text_color="Secondary"))
        else:
            term_grid = GridLayout(cols=3, spacing=dp(12), size_hint_y=None)
            term_grid.bind(minimum_height=term_grid.setter('height'))
            for term in self.terms_list:
                card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(80),
                              radius=12, elevation=2, md_bg_color=(1,1,1,1), padding=8)
                label = MDLabel(text=term, bold=True, halign='center', valign='middle',
                                theme_text_color="Custom", text_color=(0.05,0.28,0.63,1))
                card.add_widget(label)
                if self.selected_term == term:
                    card.md_bg_color = (0.2, 0.8, 0.2, 1)
                card.bind(on_release=lambda x, t=term: self.select_term(t))
                term_grid.add_widget(card)
            container.add_widget(term_grid)
        if not self.selected_term:
            return
        container.add_widget(Widget(size_hint_y=None, height=dp(20)))
        container.add_widget(MDLabel(text=f"STUDENTS - {self.selected_class} ({self.selected_term})", bold=True, font_style="H6", halign="center", size_hint_y=None, height=dp(40)))
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT name, username FROM students WHERE class_name=? AND is_deleted=0 ORDER BY name", (self.selected_class,))
        students = c.fetchall()
        conn.close()
        if not students:
            container.add_widget(MDLabel(text="No students in this class", halign="center", theme_text_color="Secondary"))
            return
        for student_name, student_username in students:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT total_marks, obtained_marks FROM student_results WHERE student_username=? AND term_name=?", (student_username, self.selected_term))
            results = c.fetchall()
            conn.close()
            total_obtained = sum(r[1] for r in results)
            total_marks = sum(r[0] for r in results)
            if total_marks > 0:
                percentage = (total_obtained / total_marks) * 100
                if percentage >= 80: grade = "A+"
                elif percentage >= 70: grade = "A"
                elif percentage >= 60: grade = "B"
                elif percentage >= 50: grade = "C"
                elif percentage >= 40: grade = "D"
                else: grade = "F"
                preview = f"Total: {total_obtained}/{total_marks} | {percentage:.1f}% | Grade: {grade}"
            else:
                preview = "No results entered"
            card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(100),
                          radius=12, elevation=3, md_bg_color=(1,1,1,1), padding=10, spacing=6)
            card.add_widget(MDLabel(text=student_name, bold=True, font_style="H6", halign="center", size_hint_y=None, height=dp(30)))
            card.add_widget(MDLabel(text=preview, font_style="Caption", theme_text_color="Secondary", halign="center", size_hint_y=None, height=dp(30)))
            view_btn = MDRaisedButton(text="VIEW RESULT", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5, pos_hint={'center_x':0.5}, height=dp(35),
                                      on_release=lambda x, uname=student_username: self.view_student_result(uname))
            card.add_widget(view_btn)
            container.add_widget(card)
    def select_class(self, cls):
        self.selected_class = cls
        self.selected_term = None
        self.load_ui()
    def select_term(self, term):
        self.selected_term = term
        self.load_ui()
    def view_student_result(self, student_username):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT name, father_name, cnic, username, class_name FROM students WHERE username=?", (student_username,))
        student = c.fetchone()
        if not student:
            conn.close()
            return
        student_name, father_name, cnic, bform, class_name = student
        c.execute("SELECT value FROM school_settings WHERE key='school_name'")
        school_row = c.fetchone()
        school_name = school_row[0] if school_row else "Al-Hamd Cadet School"
        c.execute("SELECT subject, total_marks, obtained_marks, percentage, grade FROM student_results WHERE student_username=? AND term_name=?", (student_username, self.selected_term))
        results = c.fetchall()
        conn.close()
        if not results:
            self.show_dialog("Info", "No results found for this student.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT student_username, SUM(obtained_marks) as total_obtained, SUM(total_marks) as total_marks
            FROM student_results WHERE class_name=? AND term_name=?
            GROUP BY student_username
        """, (class_name, self.selected_term))
        all_students = c.fetchall()
        conn.close()
        rank = 1
        for idx, (uname, obtained, total) in enumerate(sorted(all_students, key=lambda x: (x[1]/x[2]) if x[2]>0 else 0, reverse=True)):
            if uname == student_username:
                rank = idx + 1
                break
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
        main_box = MDBoxLayout(orientation='vertical', spacing=15, size_hint_y=None, padding=20, width=Window.width-dp(40))
        main_box.bind(minimum_height=main_box.setter('height'))
        main_box.add_widget(MDLabel(text=school_name, font_style="H4", bold=True, halign='center', size_hint_y=None, height=dp(50)))
        main_box.add_widget(MDLabel(text="ACADEMIC RESULT CARD", font_style="H5", bold=True, halign='center', size_hint_y=None, height=dp(40)))
        main_box.add_widget(Widget(size_hint_y=None, height=dp(10)))
        info_card = MDCard(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=dp(180), radius=12, elevation=2, md_bg_color=(1,1,1,1))
        info_card.add_widget(MDLabel(text=f"Name: {student_name}", bold=True, size_hint_y=None, height=dp(30)))
        info_card.add_widget(MDLabel(text=f"B-Form: {bform}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"Father Name: {father_name}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"CNIC: {cnic if cnic else 'N/A'}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"Class: {class_name}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"Term: {self.selected_term}", size_hint_y=None, height=dp(25)))
        main_box.add_widget(info_card)
        main_box.add_widget(MDLabel(text="Subject-wise Marks", bold=True, font_style="H6", size_hint_y=None, height=dp(40)))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=10)
        header.add_widget(MDLabel(text="Subject", bold=True, size_hint_x=0.4))
        header.add_widget(MDLabel(text="Total", bold=True, size_hint_x=0.3))
        header.add_widget(MDLabel(text="Obtained", bold=True, size_hint_x=0.3))
        main_box.add_widget(header)
        total_marks = 0
        total_obtained = 0
        for subj, tot, obt, perc, grade in results:
            row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=10)
            row_box.add_widget(MDLabel(text=subj, size_hint_x=0.4))
            row_box.add_widget(MDLabel(text=str(tot), size_hint_x=0.3))
            row_box.add_widget(MDLabel(text=str(obt), size_hint_x=0.3))
            main_box.add_widget(row_box)
            total_marks += tot
            total_obtained += obt
        main_box.add_widget(Widget(size_hint_y=None, height=dp(10)))
        percentage = (total_obtained / total_marks * 100) if total_marks > 0 else 0
        if percentage >= 80: grade = "A+"
        elif percentage >= 70: grade = "A"
        elif percentage >= 60: grade = "B"
        elif percentage >= 50: grade = "C"
        elif percentage >= 40: grade = "D"
        else: grade = "F" if total_marks > 0 else "N/A"
        summary_card = MDCard(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=dp(140), radius=12, elevation=2, md_bg_color=(1,1,1,1))
        summary_card.add_widget(MDLabel(text=f"Total Marks: {total_obtained} / {total_marks}", bold=True, size_hint_y=None, height=dp(30)))
        summary_card.add_widget(MDLabel(text=f"Percentage: {percentage:.2f}%", bold=True, size_hint_y=None, height=dp(30)))
        summary_card.add_widget(MDLabel(text=f"Grade: {grade}", bold=True, size_hint_y=None, height=dp(30)))
        summary_card.add_widget(MDLabel(text=f"Position: {rank} / {len(all_students)}", bold=True, size_hint_y=None, height=dp(30)))
        main_box.add_widget(summary_card)
        scroll.add_widget(main_box)
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=10, size_hint_y=None, height=dp(650))
        content.add_widget(scroll)
        dialog = MDDialog(title="", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: x.dismiss())])
        dialog.open()
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()
    def back_to_principal(self):
        self.manager.current = 'principal_panel'

class HeadsPanelScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_gender = "Male"
    def on_enter(self):
        self.load_heads_list()
    def load_heads_list(self):
        self.ids.heads_container.clear_widgets()
        app = MDApp.get_running_app()
        if is_student(app.role):
            if app.user_gender == 'Male':
                gender_filter = 'Male'
            else:
                gender_filter = 'Female'
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, name, gender, qualification, experience, designation FROM heads WHERE gender=?", (gender_filter,))
            heads = c.fetchall()
            conn.close()
        else:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, name, gender, qualification, experience, designation FROM heads")
            heads = c.fetchall()
            conn.close()
        if not heads:
            card = MDCard(orientation='vertical', padding=30, spacing=10, size_hint_y=None, height=150, radius=15, elevation=2, md_bg_color=(1,1,1,1))
            card.add_widget(MDLabel(text="No Heads Added Yet", halign="center", theme_text_color="Secondary", font_style="H5"))
            card.add_widget(MDLabel(text="Click '+' to add a new head", halign="center", theme_text_color="Secondary"))
            self.ids.heads_container.add_widget(card)
        else:
            can_edit = is_admin_or_principal_or_head(app.role)
            for idx, h in enumerate(heads, 1):
                hid, name, gender, qual, exp, desig = h
                color = (0.05,0.28,0.63,1) if gender=='Male' else (0.8,0.2,0.5,1)
                pic_path = get_profile_pic(name)  # Heads don't have separate users, using default
                card = MDCard(orientation='vertical', padding=15, spacing=0, size_hint_y=None, height=450, radius=15, elevation=4, md_bg_color=(1,1,1,1))
                header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=70, padding=[10,0,0,0], spacing=10)
                avatar = Image(source="assets/default_avatar.png", size_hint_x=None, width=60, height=60, allow_stretch=True)
                header.add_widget(avatar)
                name_label = MDLabel(text=f"{idx}. {name}", bold=True, theme_text_color="Custom", text_color=color, font_style="H6", valign='middle', size_hint_x=0.8)
                name_label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
                header.add_widget(name_label)
                card.add_widget(header)
                card.add_widget(MDBoxLayout(size_hint_y=None, height=2, md_bg_color=(0.85,0.85,0.85,1)))
                card.add_widget(Widget(size_hint_y=None, height=14))
                card.add_widget(MDLabel(text=f"  Qualification: {qual}", size_hint_y=None, height=40, font_style="Body1"))
                card.add_widget(Widget(size_hint_y=None, height=14))
                card.add_widget(MDLabel(text=f"  Experience: {exp} years", size_hint_y=None, height=40, font_style="Body1"))
                card.add_widget(Widget(size_hint_y=None, height=14))
                card.add_widget(MDLabel(text=f"  Designation: {desig}", size_hint_y=None, height=40, font_style="Body1"))
                card.add_widget(Widget(size_hint_y=None, height=14))
                card.add_widget(MDLabel(text=f"  Gender: {gender}", size_hint_y=None, height=40, font_style="Body1"))
                card.add_widget(Widget())
                card.add_widget(Widget(size_hint_y=None, height=8))
                if can_edit:
                    btn_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=48, spacing=12, padding=[15,0,15,8])
                    edit_btn = MDRaisedButton(text="EDIT", md_bg_color=(0.2,0.7,0.3,1), size_hint_x=0.5,
                                              on_release=lambda x, hid=hid, name=name, gender=gender, qual=qual, exp=exp, desig=desig: self.open_edit_head_dialog(hid, name, gender, qual, exp, desig))
                    btn_box.add_widget(edit_btn)
                    delete_btn = MDRaisedButton(text="DELETE", md_bg_color=(0.8,0.2,0.2,1), size_hint_x=0.5,
                                               on_release=lambda x, hid=hid: self.delete_head(hid))
                    btn_box.add_widget(delete_btn)
                    card.add_widget(btn_box)
                self.ids.heads_container.add_widget(card)
    def open_edit_head_dialog(self, hid, name, gender, qual, exp, desig):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can edit heads.")
            return
        content = MDBoxLayout(orientation='vertical', spacing=12, padding=20, size_hint_y=None, height=650)
        content.add_widget(MDLabel(text="EDIT HEAD INFORMATION", font_style="H5", bold=True, halign="center", 
                                   theme_text_color="Custom", text_color=(0.05,0.28,0.63,1), size_hint_y=None, height=40))
        name_f = MDTextField(hint_text="Head Name *", mode="rectangle", text=name, size_hint_y=None, height=30)
        content.add_widget(name_f)
        qual_f = MDTextField(hint_text="Qualification *", mode="rectangle", text=qual, size_hint_y=None, height=30)
        content.add_widget(qual_f)
        exp_f = MDTextField(hint_text="Experience (years) *", mode="rectangle", text=exp, size_hint_y=None, height=30)
        content.add_widget(exp_f)
        desig_f = MDTextField(hint_text="Designation *", mode="rectangle", text=desig, size_hint_y=None, height=30)
        content.add_widget(desig_f)
        content.add_widget(Widget(size_hint_y=None, height=25))
        gbox = MDBoxLayout(orientation='horizontal', spacing=12, size_hint_y=None, height=35)
        mb = MDRaisedButton(text="MALE", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5)
        fb = MDRaisedButton(text="FEMALE", md_bg_color=(0.7,0.7,0.7,1), size_hint_x=0.5)
        edit_gender = {"value": gender}
        def set_g(g):
            edit_gender["value"] = g
            mb.md_bg_color = (0.05,0.28,0.63,1) if g=='Male' else (0.7,0.7,0.7,1)
            fb.md_bg_color = (0.7,0.7,0.7,1) if g=='Male' else (0.05,0.28,0.63,1)
        mb.bind(on_release=lambda x: set_g("Male"))
        fb.bind(on_release=lambda x: set_g("Female"))
        gbox.add_widget(mb)
        gbox.add_widget(fb)
        content.add_widget(gbox)
        content.add_widget(Widget(size_hint_y=None, height=10))
        dlg = MDDialog(title="", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="UPDATE", md_bg_color=(0.2,0.7,0.3,1),
                                               on_release=lambda x: self.update_head(hid, name_f.text, edit_gender["value"], qual_f.text, exp_f.text, desig_f.text, dlg))])
        dlg.open()
    def update_head(self, hid, name, gender, qual, exp, desig, dlg):
        if not all([name.strip(), qual.strip(), exp.strip(), desig.strip()]):
            self.show_dialog("Error", "All fields required!")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE heads SET name=?, gender=?, qualification=?, experience=?, designation=? WHERE id=?",
                  (name.strip(), gender, qual.strip(), exp.strip(), desig.strip(), hid))
        conn.commit()
        conn.close()
        dlg.dismiss()
        self.load_heads_list()
        self.show_dialog("Success", "Head updated!")
    def open_add_head_dialog(self):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can add heads.")
            return
        content = MDBoxLayout(orientation='vertical', spacing=12, padding=20, size_hint_y=None, height=650)
        content.add_widget(MDLabel(text="ADD NEW HEAD", font_style="H5", bold=True, halign="center", 
                                   theme_text_color="Custom", text_color=(0.05,0.28,0.63,1), size_hint_y=None, height=40))
        name_f = MDTextField(hint_text="Head Name *", mode="rectangle", size_hint_y=None, height=30)
        content.add_widget(name_f)
        qual_f = MDTextField(hint_text="Qualification *", mode="rectangle", size_hint_y=None, height=30)
        content.add_widget(qual_f)
        exp_f = MDTextField(hint_text="Experience (years) *", mode="rectangle", size_hint_y=None, height=30)
        content.add_widget(exp_f)
        desig_f = MDTextField(hint_text="Designation *", mode="rectangle", size_hint_y=None, height=30)
        content.add_widget(desig_f)
        content.add_widget(Widget(size_hint_y=None, height=25))
        gbox = MDBoxLayout(orientation='horizontal', spacing=12, size_hint_y=None, height=35)
        mb = MDRaisedButton(text="MALE", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5)
        fb = MDRaisedButton(text="FEMALE", md_bg_color=(0.7,0.7,0.7,1), size_hint_x=0.5)
        def set_g(gender):
            self.selected_gender = gender
            mb.md_bg_color = (0.05,0.28,0.63,1) if gender=='Male' else (0.7,0.7,0.7,1)
            fb.md_bg_color = (0.7,0.7,0.7,1) if gender=='Male' else (0.05,0.28,0.63,1)
        mb.bind(on_release=lambda x: set_g("Male"))
        fb.bind(on_release=lambda x: set_g("Female"))
        gbox.add_widget(mb)
        gbox.add_widget(fb)
        content.add_widget(gbox)
        content.add_widget(Widget(size_hint_y=None, height=10))
        self.selected_gender = "Male"
        dlg = MDDialog(title="", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="ADD", md_bg_color=(0.05,0.28,0.63,1),
                                               on_release=lambda x: self.add_head(name_f.text, self.selected_gender, qual_f.text, exp_f.text, desig_f.text, dlg))])
        dlg.open()
    def add_head(self, name, gender, qual, exp, desig, dlg):
        if not all([name.strip(), qual.strip(), exp.strip(), desig.strip()]):
            self.show_dialog("Error", "All fields required!")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO heads (name, gender, qualification, experience, designation) VALUES (?,?,?,?,?)",
                  (name.strip(), gender, qual.strip(), exp.strip(), desig.strip()))
        conn.commit()
        conn.close()
        dlg.dismiss()
        self.load_heads_list()
        self.show_dialog("Success", f"Head '{name}' added!")
    def delete_head(self, hid):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can delete heads.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM heads WHERE id=?", (hid,))
        conn.commit()
        conn.close()
        self.load_heads_list()
        self.show_dialog("Success", "Head deleted!")
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class TeachersPanelScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_gender = "Male"
        self.file_manager = None
    def on_enter(self):
        self.load_teachers_list()
    def load_teachers_list(self):
        self.ids.teachers_container.clear_widgets()
        app = MDApp.get_running_app()
        if is_student(app.role):
            if app.user_gender == 'Male':
                gender_filter = 'Male'
            else:
                gender_filter = 'Female'
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT t.id, t.name, t.contact, t.address, t.gender, t.assigned_class, t.username, u.status FROM teachers t JOIN users u ON t.username = u.username WHERE u.status='Approved' AND t.gender=? ORDER BY t.id", (gender_filter,))
            teachers = c.fetchall()
            conn.close()
        else:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT t.id, t.name, t.contact, t.address, t.gender, t.assigned_class, t.username, u.status FROM teachers t JOIN users u ON t.username = u.username WHERE u.status='Approved' ORDER BY t.id")
            teachers = c.fetchall()
            conn.close()
        if not teachers:
            card = MDCard(orientation='vertical', padding=30, spacing=10, size_hint_y=None, height=150,
                          radius=15, elevation=2, md_bg_color=(1,1,1,1))
            card.add_widget(MDLabel(text="No Teachers Added Yet", halign="center",
                                    theme_text_color="Secondary", font_style="H5"))
            card.add_widget(MDLabel(text="Click '+' to add a new teacher", halign="center",
                                    theme_text_color="Secondary"))
            self.ids.teachers_container.add_widget(card)
        else:
            current_user = MDApp.get_running_app().username
            app = MDApp.get_running_app()
            can_edit = is_admin_or_principal_or_head(app.role)
            for idx, t in enumerate(teachers, 1):
                tid, name, contact, address, gender, assigned_class, username, status = t
                color = (0.05,0.28,0.63,1) if gender=='Male' else (0.9,0.2,0.5,1)
                pic_path = get_profile_pic(username)
                card = MDCard(orientation='vertical', padding=15, spacing=0,
                              size_hint_y=None, height=500, radius=15,
                              elevation=4, md_bg_color=(1,1,1,1))
                header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=[10,0,0,0], spacing=10)
                avatar = Image(source=pic_path if pic_path else "assets/default_avatar.png", size_hint_x=None, width=50, height=50, allow_stretch=True)
                avatar.bind(on_touch_down=lambda instance, touch, un=username: self.open_profile_pic_dialog(un) if instance.collide_point(*touch.pos) else None)
                header.add_widget(avatar)
                name_label = MDLabel(text=f"{idx}. {name}", bold=True, theme_text_color="Custom",
                                     text_color=color, font_style="H6", valign='middle', size_hint_x=0.8)
                name_label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
                header.add_widget(name_label)
                card.add_widget(header)
                card.add_widget(MDBoxLayout(size_hint_y=None, height=2, md_bg_color=(0.85,0.85,0.85,1)))
                card.add_widget(Widget(size_hint_y=None, height=6))
                card.add_widget(MDLabel(text=f"  Username: {username}", size_hint_y=None,
                                        height=40, font_style="Body1"))
                card.add_widget(Widget(size_hint_y=None, height=6))
                show_contact = True
                if app.role == 'Student':
                    if app.student_gender == 'Female':
                        show_contact = True
                    else:
                        show_contact = False
                if show_contact:
                    card.add_widget(MDLabel(text=f"  Contact: {contact}", size_hint_y=None,
                                            height=40, font_style="Body1"))
                else:
                    card.add_widget(MDLabel(text=f"  Contact: [Hidden]", size_hint_y=None,
                                            height=40, font_style="Body1", markup=True))
                card.add_widget(Widget(size_hint_y=None, height=6))
                card.add_widget(MDLabel(text=f"  Address: {address}", size_hint_y=None,
                                        height=40, font_style="Body1"))
                card.add_widget(Widget(size_hint_y=None, height=6))
                card.add_widget(MDLabel(text=f"  Class: {assigned_class}", size_hint_y=None,
                                        height=40, font_style="Body1"))
                card.add_widget(Widget(size_hint_y=None, height=6))
                card.add_widget(MDLabel(text=f"  Gender: {gender}", size_hint_y=None,
                                        height=40, font_style="Body1"))
                card.add_widget(Widget(size_hint_y=None, height=48))
                btn_box = MDBoxLayout(orientation='horizontal', size_hint_y=None,
                                      height=48, spacing=12, padding=[15,0,15,8])
                if can_edit:
                    if app.role == 'Admin':
                        make_principal_btn = MDRaisedButton(text="Make Principal", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.24,
                                                            on_release=lambda x, uname=username: self.make_principal(uname))
                        btn_box.add_widget(make_principal_btn)
                    edit_btn = MDRaisedButton(text="EDIT", md_bg_color=(0.2,0.7,0.3,1), size_hint_x=0.24,
                                              on_release=lambda x, tid=tid, name=name, contact=contact,
                                                             address=address, gender=gender,
                                                             assigned_class=assigned_class,
                                                             username=username:
                                              self.open_edit_teacher_dialog(tid, name, contact, address,
                                                                            gender, assigned_class, username))
                    btn_box.add_widget(edit_btn)
                    delete_btn = MDRaisedButton(text="DELETE", md_bg_color=(0.8,0.2,0.2,1), size_hint_x=0.24,
                                                on_release=lambda x, username=username: self.delete_teacher(username))
                    btn_box.add_widget(delete_btn)
                atten_btn = MDRaisedButton(text="Atten", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.28,
                                           on_release=lambda x, t_username=username, t_class=assigned_class: self.open_teacher_attendance(t_username, t_class))
                if current_user != username and not (is_admin_or_principal_or_head(app.role)):
                    atten_btn.disabled = True
                    atten_btn.md_bg_color = (0.5,0.5,0.5,1)
                btn_box.add_widget(atten_btn)
                card.add_widget(btn_box)
                self.ids.teachers_container.add_widget(card)
    def open_profile_pic_dialog(self, username):
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=200)
        content.add_widget(MDLabel(text="Change Profile Picture", font_style="H6", halign="center", size_hint_y=None, height=40))
        content.add_widget(Widget(size_hint_y=None, height=20))
        btn_layout = MDBoxLayout(orientation='horizontal', spacing=20, size_hint_y=None, height=50)
        upload_btn = MDRaisedButton(text="Upload", md_bg_color=(0.05,0.28,0.63,1), on_release=lambda x: self.select_teacher_pic(username, dlg))
        remove_btn = MDRaisedButton(text="Remove", md_bg_color=(0.8,0.2,0.2,1), on_release=lambda x: self.remove_teacher_pic(username, dlg))
        btn_layout.add_widget(upload_btn)
        btn_layout.add_widget(remove_btn)
        content.add_widget(btn_layout)
        dlg = MDDialog(title="", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="Cancel", on_release=lambda x: dlg.dismiss())])
        dlg.open()
    def select_teacher_pic(self, username, dialog):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=lambda path: self.save_teacher_pic(username, path, dialog),
            preview=True,
        )
        self.file_manager.show(os.path.expanduser("~"))
    def save_teacher_pic(self, username, path, dialog):
        self.exit_file_manager()
        if path and os.path.exists(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                save_profile_picture(username, path)
                dialog.dismiss()
                self.load_teachers_list()
                self.show_dialog("Success", "Profile picture updated!")
            else:
                self.show_dialog("Error", "Please select a JPG or PNG image.")
    def remove_teacher_pic(self, username, dialog):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET profile_pic='' WHERE username=?", (username,))
        conn.commit()
        conn.close()
        dialog.dismiss()
        self.load_teachers_list()
        self.show_dialog("Success", "Profile picture removed.")
    def make_principal(self, username):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET role='User' WHERE role='Principal'")
        c.execute("UPDATE users SET role='Principal' WHERE username=?", (username,))
        conn.commit()
        conn.close()
        set_app_lock(False)
        self.show_dialog("Success", f"{username} is now the Principal. App is unlocked.")
        self.load_teachers_list()
    def open_teacher_attendance(self, teacher_username, class_name):
        app = MDApp.get_running_app()
        if app.role == 'Teacher' and app.username != teacher_username:
            self.show_dialog("Access Denied", "You can only mark your own attendance.")
            return
        now = datetime.now()
        current_time = now.time()
        morning_start = datetime.strptime("07:30", "%H:%M").time()
        morning_end = datetime.strptime("09:00", "%H:%M").time()
        afternoon_start = datetime.strptime("13:00", "%H:%M").time()
        afternoon_end = datetime.strptime("14:30", "%H:%M").time()
        slot = None
        if morning_start <= current_time <= morning_end:
            slot = "Morning"
        elif afternoon_start <= current_time <= afternoon_end:
            slot = "Afternoon"
        else:
            self.show_dialog("Time Error", "Attendance can only be marked between 7:30-9:00 AM or 1:00-2:30 PM.")
            return
        today = now.strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM attendance WHERE class_name=? AND date=? AND slot=? AND teacher_username=?", (class_name, today, slot, teacher_username))
        if c.fetchone():
            conn.close()
            self.show_dialog("Error", f"You have already marked {slot} attendance for today.")
            return
        c.execute("SELECT username, name FROM students WHERE class_name=? AND is_deleted=0", (class_name,))
        students = c.fetchall()
        conn.close()
        if not students:
            self.show_dialog("Info", "No students in this class.")
            return
        scroll = ScrollView(size_hint=(1, 0.8))
        main_box = MDBoxLayout(orientation='vertical', spacing=15, size_hint_y=None, padding=20)
        main_box.bind(minimum_height=main_box.setter('height'))
        main_box.add_widget(MDLabel(text=f"Mark Attendance - {class_name} ({slot} slot)", font_style="H6", halign="center", size_hint_y=None, height=40))
        student_status = {}
        for s_username, s_name in students:
            row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
            row.add_widget(MDLabel(text=s_name, size_hint_x=0.7))
            sw = MDSwitch(size_hint_x=0.3, active=False)
            row.add_widget(sw)
            main_box.add_widget(row)
            student_status[s_username] = sw
        total_label = MDLabel(text="Present: 0  |  Absent: 0  |  Total: 0", size_hint_y=None, height=40, bold=True)
        main_box.add_widget(total_label)
        def update_counts(*args):
            present = sum(1 for sw in student_status.values() if sw.active)
            absent = len(student_status) - present
            total_label.text = f"Present: {present}  |  Absent: {absent}  |  Total: {len(student_status)}"
        for sw in student_status.values():
            sw.bind(active=update_counts)
        scroll.add_widget(main_box)
        content = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=500)
        content.add_widget(scroll)
        btn_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10, padding=20)
        btn_layout.add_widget(Widget(size_hint_x=0.2))
        submit_btn = MDRaisedButton(text="Submit", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.6)
        btn_layout.add_widget(submit_btn)
        btn_layout.add_widget(Widget(size_hint_x=0.2))
        content.add_widget(btn_layout)
        dialog = MDDialog(title="", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="Cancel", on_release=lambda x: x.dismiss())])
        submit_btn.bind(on_release=lambda x: self.save_teacher_attendance(class_name, today, slot, teacher_username, student_status, dialog))
        dialog.open()
    def save_teacher_attendance(self, class_name, date, slot, teacher_username, student_status, dialog):
        attendance_data = {}
        present_count = 0
        for s_username, sw in student_status.items():
            status = "Present" if sw.active else "Absent"
            attendance_data[s_username] = status
            if status == "Present":
                present_count += 1
        total_students = len(student_status)
        absent_count = total_students - present_count
        data_json = json.dumps(attendance_data)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""INSERT INTO attendance (class_name, date, slot, teacher_username, attendance_data, total_present, total_absent, total_students)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (class_name, date, slot, teacher_username, data_json, present_count, absent_count, total_students))
        conn.commit()
        conn.close()
        dialog.dismiss()
        self.show_dialog("Success", f"Attendance for {class_name} ({slot}) saved.")
    def open_edit_teacher_dialog(self, tid, name, contact, address, gender, assigned_class, username):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can edit teachers.")
            return
        content = MDBoxLayout(orientation='vertical', spacing=12, padding=20, size_hint_y=None, height=650)
        content.add_widget(MDLabel(text="EDIT TEACHER INFORMATION", font_style="H5", bold=True, halign="center", 
                                   theme_text_color="Custom", text_color=(0.05,0.28,0.63,1), size_hint_y=None, height=40))
        name_f = MDTextField(hint_text="Teacher Name *", mode="rectangle", text=name, size_hint_y=None, height=30)
        content.add_widget(name_f)
        contact_f = MDTextField(hint_text="Contact *", mode="rectangle", text=contact, size_hint_y=None, height=30)
        content.add_widget(contact_f)
        address_f = MDTextField(hint_text="Address *", mode="rectangle", text=address, size_hint_y=None, height=30)
        content.add_widget(address_f)
        class_f = MDTextField(hint_text="Assigned Class *", mode="rectangle", text=assigned_class, size_hint_y=None, height=30)
        content.add_widget(class_f)
        content.add_widget(Widget(size_hint_y=None, height=25))
        gbox = MDBoxLayout(orientation='horizontal', spacing=12, size_hint_y=None, height=35)
        mb = MDRaisedButton(text="MALE", md_bg_color=(0.05,0.28,0.63,1) if gender=='Male' else (0.7,0.7,0.7,1), size_hint_x=0.5)
        fb = MDRaisedButton(text="FEMALE", md_bg_color=(0.05,0.28,0.63,1) if gender=='Female' else (0.7,0.7,0.7,1), size_hint_x=0.5)
        edit_gender = {"value": gender}
        def set_g(g):
            edit_gender["value"] = g
            mb.md_bg_color = (0.05,0.28,0.63,1) if g=='Male' else (0.7,0.7,0.7,1)
            fb.md_bg_color = (0.7,0.7,0.7,1) if g=='Male' else (0.05,0.28,0.63,1)
        mb.bind(on_release=lambda x: set_g("Male"))
        fb.bind(on_release=lambda x: set_g("Female"))
        gbox.add_widget(mb)
        gbox.add_widget(fb)
        content.add_widget(gbox)
        content.add_widget(Widget(size_hint_y=None, height=10))
        dlg = MDDialog(title="", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="UPDATE", md_bg_color=(0.2,0.7,0.3,1),
                                               on_release=lambda x: self.update_teacher(tid, name_f.text, contact_f.text, address_f.text, edit_gender["value"], class_f.text, dlg))])
        dlg.open()
    def update_teacher(self, tid, name, contact, address, gender, assigned_class, dlg):
        if not all([name.strip(), contact.strip(), address.strip(), assigned_class.strip()]):
            self.show_dialog("Error", "All fields required!")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE teachers SET name=?, contact=?, address=?, gender=?, assigned_class=? WHERE id=?",
                  (name.strip(), contact.strip(), address.strip(), gender, assigned_class.strip(), tid))
        c.execute("UPDATE users SET name=?, username=? WHERE username=(SELECT username FROM teachers WHERE id=?)", (name.strip(), name.strip(), tid))
        conn.commit()
        conn.close()
        dlg.dismiss()
        self.load_teachers_list()
        self.show_dialog("Success", "Teacher updated!")
        # Notification to teacher
        notify_student(name.strip(), "Profile Updated", "Your teacher profile has been updated.", "profile_update")
        notify_teachers("Teacher Profile Updated", f"Teacher {name}'s profile has been updated.", "profile_update")
    def open_add_teacher_dialog(self):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can add teachers.")
            return
        scroll = ScrollView(size_hint=(1, None), height=Window.height*0.8)
        box = MDBoxLayout(orientation='vertical', spacing=12, padding=20, size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        title_label = MDLabel(text="ADD NEW TEACHER", font_style="H5", bold=True, halign="center",
                              theme_text_color="Custom", text_color=(0.05,0.28,0.63,1), size_hint_y=None, height=40)
        box.add_widget(title_label)
        box.add_widget(Widget(size_hint_y=None, height=10))
        avatar_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=20, padding=[20,0,20,0])
        avatar_image = Image(source="assets/default_avatar.png", size_hint_x=None, width=60, height=60, allow_stretch=True)
        avatar_layout.add_widget(Widget(size_hint_x=0.2))
        avatar_layout.add_widget(avatar_image)
        avatar_layout.add_widget(Widget(size_hint_x=0.2))
        box.add_widget(avatar_layout)
        change_avatar_btn = MDRaisedButton(text="Upload Profile Picture", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.6, pos_hint={'center_x':0.5})
        box.add_widget(change_avatar_btn)
        box.add_widget(Widget(size_hint_y=None, height=10))
        name_f = MDTextField(hint_text="Teacher Name *", mode="rectangle", size_hint_y=None, height=48)
        box.add_widget(name_f)
        contact_f = MDTextField(hint_text="Contact Number *", mode="rectangle", size_hint_y=None, height=48)
        box.add_widget(contact_f)
        address_f = MDTextField(hint_text="Address *", mode="rectangle", size_hint_y=None, height=48)
        box.add_widget(address_f)
        class_f = MDTextField(hint_text="Assigned Class *", mode="rectangle", size_hint_y=None, height=48)
        box.add_widget(class_f)
        pwd_f = MDTextField(hint_text="Password *", password=True, mode="rectangle", size_hint_y=None, height=48)
        box.add_widget(pwd_f)
        box.add_widget(Widget(size_hint_y=None, height=20))
        gbox = MDBoxLayout(orientation='horizontal', spacing=12, size_hint_y=None, height=50)
        mb = MDRaisedButton(text="MALE", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5)
        fb = MDRaisedButton(text="FEMALE", md_bg_color=(0.7,0.7,0.7,1), size_hint_x=0.5)
        def set_g(gender):
            self.selected_gender = gender
            mb.md_bg_color = (0.05,0.28,0.63,1) if gender=='Male' else (0.7,0.7,0.7,1)
            fb.md_bg_color = (0.7,0.7,0.7,1) if gender=='Male' else (0.05,0.28,0.63,1)
        mb.bind(on_release=lambda x: set_g("Male"))
        fb.bind(on_release=lambda x: set_g("Female"))
        gbox.add_widget(mb)
        gbox.add_widget(fb)
        box.add_widget(gbox)
        box.add_widget(Widget(size_hint_y=None, height=20))
        scroll.add_widget(box)
        self.selected_gender = "Male"
        self.new_teacher_pic_path = None
        def on_pic_select(instance):
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            file_manager = MDFileManager(
                exit_manager=lambda *args: None,
                select_path=lambda path: select_pic(path),
                preview=True,
            )
            file_manager.show(os.path.expanduser("~"))
            def select_pic(path):
                if path and os.path.exists(path):
                    ext = os.path.splitext(path)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png']:
                        self.new_teacher_pic_path = path
                        avatar_image.source = path
                        avatar_image.reload()
                        file_manager.close()
                    else:
                        self.show_dialog("Error", "Please select a JPG or PNG image.")
                else:
                    file_manager.close()
        change_avatar_btn.bind(on_release=on_pic_select)
        dlg = MDDialog(
            title="",
            type="custom",
            content_cls=scroll,
            size_hint=(0.9, None),
            height=Window.height*0.9,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                MDRaisedButton(
                    text="ADD",
                    md_bg_color=(0.05,0.28,0.63,1),
                    on_release=lambda x: self.add_teacher(
                        name_f.text, contact_f.text, address_f.text,
                        self.selected_gender, class_f.text, pwd_f.text, dlg
                    )
                )
            ]
        )
        dlg.open()
    def add_teacher(self, name, contact, address, gender, assigned_class, pwd, dlg):
        if not all([name.strip(), contact.strip(), address.strip(), assigned_class.strip(), pwd.strip()]):
            self.show_dialog("Error", "All fields required!")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            uname = name.strip()
            c.execute("INSERT INTO users (username, password, role, status, name, class_name, gender, contact, address) VALUES (?,?,?, 'Pending', ?, ?, ?, ?, ?)",
                      (uname, pwd.strip(), 'Teacher', name.strip(), assigned_class.strip(), gender, contact.strip(), address.strip()))
            if self.new_teacher_pic_path:
                save_profile_picture(uname, self.new_teacher_pic_path)
            c.execute("INSERT INTO teachers (name, contact, address, gender, assigned_class, username, password, class_strength) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (name.strip(), contact.strip(), address.strip(), gender, assigned_class.strip(), uname, pwd.strip(), '0'))
            conn.commit()
            dlg.dismiss()
            self.load_teachers_list()
            self.show_dialog("Success", f"Teacher '{name}' added!")
            # Notification to all teachers
            notify_teachers("New Teacher Added", f"A new teacher '{name}' has been added and pending approval.", "teacher_add")
        except sqlite3.IntegrityError:
            self.show_dialog("Error", "Username already exists!")
        conn.close()
    def delete_teacher(self, username):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can delete teachers.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT name FROM teachers WHERE username=?", (username,))
        row = c.fetchone()
        teacher_name = row[0] if row else username
        conn.close()
        block_user(username)
        add_teacher_change_log(teacher_name, username, "Deleted")
        self.load_teachers_list()
        self.show_dialog("Success", "Teacher blocked and removed from panel. Payment records remain in fee ledger.")
        # Notification
        notify_teachers("Teacher Deleted", f"Teacher {teacher_name} has been blocked/deleted.", "teacher_delete")
    def exit_file_manager(self, *args):
        if self.file_manager:
            self.file_manager.close()
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'

class StudentsPanelScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_gender = "Male"
        self.file_manager = None
    def on_enter(self):
        self.load_students_list()
    def load_students_list(self):
        self.ids.students_container.clear_widgets()
        app = MDApp.get_running_app()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if is_student(app.role):
            c.execute("SELECT s.id, s.name, s.contact, s.class_name, s.address, s.gender, s.username, u.status FROM students s JOIN users u ON s.username = u.username WHERE s.is_deleted=0 AND u.status='Approved' AND s.gender=? ORDER BY s.class_name, s.name", (app.user_gender,))
        else:
            c.execute("SELECT s.id, s.name, s.contact, s.class_name, s.address, s.gender, s.username, u.status FROM students s JOIN users u ON s.username = u.username WHERE s.is_deleted=0 AND u.status='Approved' ORDER BY s.class_name, s.name")
        students = c.fetchall()
        conn.close()
        if not students:
            card = MDCard(orientation='vertical', padding=30, spacing=10, size_hint_y=None, height=150, radius=15, elevation=2, md_bg_color=(1,1,1,1))
            card.add_widget(MDLabel(text="No Students Added Yet", halign="center", theme_text_color="Secondary", font_style="H5"))
            card.add_widget(MDLabel(text="Click '+' to add a new student", halign="center", theme_text_color="Secondary"))
            self.ids.students_container.add_widget(card)
        else:
            for idx, s in enumerate(students, 1):
                sid, name, contact, class_name, address, gender, username, status = s
                color = (0.05,0.28,0.63,1) if gender=='Male' else (0.9,0.2,0.5,1)
                pic_path = get_profile_pic(username)
                card = MDCard(orientation='vertical', padding=15, spacing=0, size_hint_y=None, height=440, radius=15, elevation=4, md_bg_color=(1,1,1,1))
                header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=[10,0,0,0], spacing=10)
                avatar = Image(source=pic_path if pic_path else "assets/default_avatar.png", size_hint_x=None, width=50, height=50, allow_stretch=True)
                avatar.bind(on_touch_down=lambda instance, touch, un=username: self.open_profile_pic_dialog(un) if instance.collide_point(*touch.pos) else None)
                header.add_widget(avatar)
                name_label = MDLabel(text=f"{idx}. {name}", bold=True, theme_text_color="Custom", text_color=color, font_style="H6", valign='middle', size_hint_x=0.8)
                name_label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
                header.add_widget(name_label)
                card.add_widget(header)
                card.add_widget(MDBoxLayout(size_hint_y=None, height=2, md_bg_color=(0.85,0.85,0.85,1)))
                card.add_widget(Widget(size_hint_y=None, height=12))
                card.add_widget(MDLabel(text=f"  B-Form: {username}", size_hint_y=None, height=40, font_style="Body1"))
                card.add_widget(Widget(size_hint_y=None, height=12))
                card.add_widget(MDLabel(text=f"  Class: {class_name}", size_hint_y=None, height=40, font_style="Body1"))
                card.add_widget(Widget(size_hint_y=None, height=12))
                if not is_student(app.role) or sid == self.get_own_student_id():
                    card.add_widget(MDLabel(text=f"  Contact: {contact}", size_hint_y=None, height=40, font_style="Body1"))
                else:
                    card.add_widget(MDLabel(text=f"  Contact: [Hidden]", size_hint_y=None, height=40, font_style="Body1", markup=True))
                card.add_widget(Widget(size_hint_y=None, height=12))
                card.add_widget(MDLabel(text=f"  Address: {address}", size_hint_y=None, height=40, font_style="Body1"))
                card.add_widget(Widget(size_hint_y=None, height=12))
                card.add_widget(MDLabel(text=f"  Gender: {gender}", size_hint_y=None, height=40, font_style="Body1"))
                card.add_widget(Widget(size_hint_y=None, height=20))
                card.add_widget(Widget())
                card.add_widget(Widget(size_hint_y=None, height=8))
                allow_edit = False
                if is_admin_or_principal_or_head(app.role):
                    allow_edit = True
                elif is_teacher(app.role):
                    conn_teach = sqlite3.connect(DB_NAME)
                    cur = conn_teach.cursor()
                    cur.execute("SELECT assigned_class FROM teachers WHERE username=?", (app.username,))
                    teach_row = cur.fetchone()
                    conn_teach.close()
                    if teach_row and teach_row[0] == class_name:
                        allow_edit = True
                elif is_student(app.role) and sid == self.get_own_student_id():
                    allow_edit = True
                if allow_edit:
                    btn_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=48, spacing=12, padding=[15,0,15,8])
                    edit_btn = MDRaisedButton(text="EDIT", md_bg_color=(0.2,0.7,0.3,1), size_hint_x=0.5,
                                              on_release=lambda x, sid=sid, name=name, gender=gender, contact=contact, address=address, class_name=class_name, username=username: self.open_edit_student_dialog(sid, name, gender, contact, address, class_name, username))
                    btn_box.add_widget(edit_btn)
                    if is_admin_or_principal_or_head(app.role):
                        delete_btn = MDRaisedButton(text="DELETE", md_bg_color=(0.8,0.2,0.2,1), size_hint_x=0.5,
                                                   on_release=lambda x, username=username: self.delete_student(username))
                        btn_box.add_widget(delete_btn)
                    card.add_widget(btn_box)
                self.ids.students_container.add_widget(card)
        if is_student(app.role):
            self.ids.add_student_btn_layout.opacity = 0
            self.ids.add_student_btn_layout.disabled = True
    def open_profile_pic_dialog(self, username):
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=200)
        content.add_widget(MDLabel(text="Change Profile Picture", font_style="H6", halign="center", size_hint_y=None, height=40))
        content.add_widget(Widget(size_hint_y=None, height=20))
        btn_layout = MDBoxLayout(orientation='horizontal', spacing=20, size_hint_y=None, height=50)
        upload_btn = MDRaisedButton(text="Upload", md_bg_color=(0.05,0.28,0.63,1), on_release=lambda x: self.select_student_pic(username, dlg))
        remove_btn = MDRaisedButton(text="Remove", md_bg_color=(0.8,0.2,0.2,1), on_release=lambda x: self.remove_student_pic(username, dlg))
        btn_layout.add_widget(upload_btn)
        btn_layout.add_widget(remove_btn)
        content.add_widget(btn_layout)
        dlg = MDDialog(title="", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="Cancel", on_release=lambda x: dlg.dismiss())])
        dlg.open()
    def select_student_pic(self, username, dialog):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=lambda path: self.save_student_pic(username, path, dialog),
            preview=True,
        )
        self.file_manager.show(os.path.expanduser("~"))
    def save_student_pic(self, username, path, dialog):
        self.exit_file_manager()
        if path and os.path.exists(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                save_profile_picture(username, path)
                dialog.dismiss()
                self.load_students_list()
                self.show_dialog("Success", "Profile picture updated!")
            else:
                self.show_dialog("Error", "Please select a JPG or PNG image.")
    def remove_student_pic(self, username, dialog):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET profile_pic='' WHERE username=?", (username,))
        conn.commit()
        conn.close()
        dialog.dismiss()
        self.load_students_list()
        self.show_dialog("Success", "Profile picture removed.")
    def get_own_student_id(self):
        app = MDApp.get_running_app()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM students WHERE username=?", (app.username,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    def open_edit_student_dialog(self, sid, name, gender, contact, address, class_name, username):
        app = MDApp.get_running_app()
        allow = False
        if is_admin_or_principal_or_head(app.role):
            allow = True
        elif is_teacher(app.role):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT assigned_class FROM teachers WHERE username=?", (app.username,))
            row = c.fetchone()
            conn.close()
            if row and row[0] == class_name:
                allow = True
        elif is_student(app.role) and sid == self.get_own_student_id():
            allow = True
        if not allow:
            self.show_dialog("Access Denied", "You don't have permission to edit this student.")
            return
        scroll = ScrollView(size_hint=(1, None), height=Window.height*0.8)
        box = MDBoxLayout(orientation='vertical', spacing=10, padding=[30,20,20,20], size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        box.add_widget(MDLabel(text="EDIT STUDENT INFORMATION", font_style="H5", bold=True, halign="center", 
                               theme_text_color="Custom", text_color=(0.05,0.28,0.63,1), size_hint_y=None, height=35))
        box.add_widget(Widget(size_hint_y=None, height=10))
        name_f = MDTextField(hint_text="Student Name *", mode="rectangle", text=name, size_hint_y=None, height=28)
        box.add_widget(name_f)
        class_f = MDTextField(hint_text="Class *", mode="rectangle", text=class_name, size_hint_y=None, height=28)
        box.add_widget(class_f)
        contact_f = MDTextField(hint_text="Contact *", mode="rectangle", text=contact, size_hint_y=None, height=28)
        box.add_widget(contact_f)
        address_f = MDTextField(hint_text="Address *", mode="rectangle", text=address, size_hint_y=None, height=28)
        box.add_widget(address_f)
        # B-Form field: if student editing own profile, make readonly
        bform_field = MDTextField(text=username, hint_text="B-Form (12345-1234567-8)", mode="rectangle", size_hint_y=None, height=28)
        if is_student(app.role) and sid == self.get_own_student_id():
            bform_field.disabled = True
        box.add_widget(bform_field)
        # DOB field with dd-mm-yyyy format
        conn_dob = sqlite3.connect(DB_NAME)
        cur_dob = conn_dob.cursor()
        cur_dob.execute("SELECT dob FROM students WHERE id=?", (sid,))
        dob_row = cur_dob.fetchone()
        conn_dob.close()
        current_dob = dob_row[0] if dob_row else ""
        dob_field = MDTextField(text=current_dob, hint_text="Date of Birth (dd-mm-yyyy)", mode="rectangle", size_hint_y=None, height=28)
        box.add_widget(dob_field)
        box.add_widget(Widget(size_hint_y=None, height=45))
        gbox = MDBoxLayout(orientation='horizontal', spacing=12, size_hint_y=None, height=30)
        mb = MDRaisedButton(text="MALE", md_bg_color=(0.05,0.28,0.63,1) if gender=='Male' else (0.7,0.7,0.7,1), size_hint_x=0.5)
        fb = MDRaisedButton(text="FEMALE", md_bg_color=(0.05,0.28,0.63,1) if gender=='Female' else (0.7,0.7,0.7,1), size_hint_x=0.5)
        edit_gender = {"value": gender}
        def set_g(g):
            edit_gender["value"] = g
            mb.md_bg_color = (0.05,0.28,0.63,1) if g=='Male' else (0.7,0.7,0.7,1)
            fb.md_bg_color = (0.7,0.7,0.7,1) if g=='Male' else (0.05,0.28,0.63,1)
        mb.bind(on_release=lambda x: set_g("Male"))
        fb.bind(on_release=lambda x: set_g("Female"))
        gbox.add_widget(mb)
        gbox.add_widget(fb)
        box.add_widget(gbox)
        box.add_widget(Widget(size_hint_y=None, height=10))
        scroll.add_widget(box)
        dlg = MDDialog(title="", type="custom", content_cls=scroll,
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="UPDATE", md_bg_color=(0.2,0.7,0.3,1),
                                               on_release=lambda x: self.update_student(sid, name_f.text, edit_gender["value"], contact_f.text, address_f.text, class_f.text, bform_field.text, dob_field.text, dlg))])
        dlg.open()
    def update_student(self, sid, name, gender, contact, address, class_name, bform, dob, dlg):
        if not all([name.strip(), contact.strip(), address.strip(), class_name.strip(), bform.strip()]):
            self.show_dialog("Error", "All fields required!")
            return
        if bform and not validate_bform(bform):
            self.show_dialog("Error", "B-Form must be in format: 12345-1234567-8")
            return
        # Validate date format dd-mm-yyyy
        if dob.strip():
            try:
                datetime.strptime(dob.strip(), "%d-%m-%Y")
            except ValueError:
                self.show_dialog("Error", "Date of Birth must be in dd-mm-yyyy format")
                return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE students SET name=?, gender=?, contact=?, address=?, class_name=?, username=?, dob=? WHERE id=?",
                  (name.strip(), gender, contact.strip(), address.strip(), class_name.strip(), bform.strip(), dob.strip(), sid))
        c.execute("UPDATE users SET name=?, class_name=?, gender=?, contact=?, address=?, username=? WHERE username=(SELECT username FROM students WHERE id=?)",
                  (name.strip(), class_name.strip(), gender, contact.strip(), address.strip(), bform.strip(), sid))
        conn.commit()
        conn.close()
        dlg.dismiss()
        self.load_students_list()
        self.show_dialog("Success", "Student updated!")
        fee_ledger = self.manager.get_screen('fee_ledger')
        fee_ledger.load_classes()
        class_panel = self.manager.get_screen('class_panel')
        class_panel.load_classes()
        # Notification
        notify_student(bform.strip(), "Profile Updated", "Your student profile has been updated.", "profile_update")
        notify_teachers("Student Profile Updated", f"Student {name} (B-Form: {bform}) profile updated.", "profile_update")
    def open_add_student_dialog(self):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can add students.")
            return
        scroll = ScrollView(size_hint=(1, None), height=Window.height*0.8)
        box = MDBoxLayout(orientation='vertical', spacing=10, padding=[30,20,20,20], size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        box.add_widget(MDLabel(text="ADD NEW STUDENT", font_style="H5", bold=True, halign="center", 
                               theme_text_color="Custom", text_color=(0.05,0.28,0.63,1), size_hint_y=None, height=35))
        box.add_widget(Widget(size_hint_y=None, height=10))
        avatar_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=20, padding=[20,0,20,0])
        avatar_image = Image(source="assets/default_avatar.png", size_hint_x=None, width=60, height=60, allow_stretch=True)
        avatar_layout.add_widget(Widget(size_hint_x=0.2))
        avatar_layout.add_widget(avatar_image)
        avatar_layout.add_widget(Widget(size_hint_x=0.2))
        box.add_widget(avatar_layout)
        change_avatar_btn = MDRaisedButton(text="Upload Profile Picture", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.6, pos_hint={'center_x':0.5})
        box.add_widget(change_avatar_btn)
        box.add_widget(Widget(size_hint_y=None, height=10))
        name_f = MDTextField(hint_text="Student Name *", mode="rectangle", size_hint_y=None, height=28)
        box.add_widget(name_f)
        contact_f = MDTextField(hint_text="Contact Number *", mode="rectangle", size_hint_y=None, height=28)
        box.add_widget(contact_f)
        class_f = MDTextField(hint_text="Class *", mode="rectangle", size_hint_y=None, height=28)
        box.add_widget(class_f)
        address_f = MDTextField(hint_text="Address *", mode="rectangle", size_hint_y=None, height=28)
        box.add_widget(address_f)
        bform_f = MDTextField(hint_text="B-Form (12345-1234567-8) *", mode="rectangle", size_hint_y=None, height=28)
        box.add_widget(bform_f)
        pwd_f = MDTextField(hint_text="Password *", password=True, mode="rectangle", size_hint_y=None, height=28)
        box.add_widget(pwd_f)
        dob_f = MDTextField(hint_text="Date of Birth (dd-mm-yyyy)", mode="rectangle", size_hint_y=None, height=28)
        box.add_widget(dob_f)
        box.add_widget(Widget(size_hint_y=None, height=45))
        gbox = MDBoxLayout(orientation='horizontal', spacing=12, size_hint_y=None, height=30)
        mb = MDRaisedButton(text="MALE", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5)
        fb = MDRaisedButton(text="FEMALE", md_bg_color=(0.7,0.7,0.7,1), size_hint_x=0.5)
        def set_g(gender):
            self.selected_gender = gender
            mb.md_bg_color = (0.05,0.28,0.63,1) if gender=='Male' else (0.7,0.7,0.7,1)
            fb.md_bg_color = (0.7,0.7,0.7,1) if gender=='Male' else (0.05,0.28,0.63,1)
        mb.bind(on_release=lambda x: set_g("Male"))
        fb.bind(on_release=lambda x: set_g("Female"))
        gbox.add_widget(mb)
        gbox.add_widget(fb)
        box.add_widget(gbox)
        box.add_widget(Widget(size_hint_y=None, height=10))
        scroll.add_widget(box)
        self.selected_gender = "Male"
        self.new_student_pic_path = None
        def on_pic_select(instance):
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            file_manager = MDFileManager(
                exit_manager=lambda *args: None,
                select_path=lambda path: select_pic(path),
                preview=True,
            )
            file_manager.show(os.path.expanduser("~"))
            def select_pic(path):
                if path and os.path.exists(path):
                    ext = os.path.splitext(path)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png']:
                        self.new_student_pic_path = path
                        avatar_image.source = path
                        avatar_image.reload()
                        file_manager.close()
                    else:
                        self.show_dialog("Error", "Please select a JPG or PNG image.")
                else:
                    file_manager.close()
        change_avatar_btn.bind(on_release=on_pic_select)
        dlg = MDDialog(title="", type="custom", content_cls=scroll,
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="ADD", md_bg_color=(0.05,0.28,0.63,1),
                                               on_release=lambda x: self.add_student(name_f.text, contact_f.text, class_f.text, address_f.text, self.selected_gender, bform_f.text, pwd_f.text, dob_f.text, dlg))])
        dlg.open()
    def add_student(self, name, contact, class_name, address, gender, bform, pwd, dob, dlg):
        if not all([name.strip(), contact.strip(), class_name.strip(), address.strip(), bform.strip(), pwd.strip()]):
            self.show_dialog("Error", "All fields required!")
            return
        if not validate_bform(bform):
            self.show_dialog("Error", "B-Form must be in format: 12345-1234567-8")
            return
        if dob.strip():
            try:
                datetime.strptime(dob.strip(), "%d-%m-%Y")
            except ValueError:
                self.show_dialog("Error", "Date of Birth must be in dd-mm-yyyy format")
                return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role, status, name, class_name, gender, contact, address) VALUES (?,?,?, 'Pending', ?, ?, ?, ?, ?)",
                      (bform, pwd, 'Student', name.strip(), class_name.strip(), gender, contact.strip(), address.strip()))
            if self.new_student_pic_path:
                save_profile_picture(bform, self.new_student_pic_path)
            c.execute("INSERT INTO students (name, contact, class_name, address, gender, username, password, father_name, cnic, dob, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                      (name.strip(), contact.strip(), class_name.strip(), address.strip(), gender, bform, pwd, '', '', dob.strip()))
            total_fee = get_fee_by_class(class_name.strip())
            current_month = datetime.now().strftime('%Y-%m')
            c.execute("INSERT INTO fee_records (student_name, student_username, class_name, total_fee, paid_amount, remaining, status, month_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (name.strip(), bform, class_name.strip(), total_fee, 0, total_fee, 'Less Paid', current_month))
            conn.commit()
            add_student_change_log(name.strip(), bform, "Added")
            self.show_dialog("Success", f"Student '{name}' added!")
            self.load_students_list()
            dlg.dismiss()
            class_panel = self.manager.get_screen('class_panel')
            class_panel.refresh_classes()
            fee_ledger = self.manager.get_screen('fee_ledger')
            fee_ledger.load_classes()
            # Notification to all teachers
            notify_teachers("New Student Added", f"Student {name} (B-Form: {bform}) has been added to class {class_name}.", "student_add")
        except sqlite3.IntegrityError:
            self.show_dialog("Error", "B-Form already exists!")
        conn.close()
    def delete_student(self, username):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can delete students.")
            return
        def confirm_delete(instance):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT name FROM students WHERE username=?", (username,))
            row = c.fetchone()
            student_name = row[0] if row else username
            conn.close()
            block_user(username)
            add_student_change_log(student_name, username, "Deleted")
            self.load_students_list()
            self.show_dialog("Success", "Student blocked and removed from active lists. Fee history remains.")
            fee_ledger = self.manager.get_screen('fee_ledger')
            fee_ledger.load_classes()
            class_panel = self.manager.get_screen('class_panel')
            class_panel.load_classes()
            dlg.dismiss()
            # Notification
            notify_teachers("Student Deleted", f"Student {student_name} (B-Form: {username}) has been blocked/deleted.", "student_delete")
        dlg = MDDialog(title="Confirm Delete", text=f"Are you sure you want to delete student {username}? This will block the account.",
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="DELETE", md_bg_color=(0.8,0.2,0.2,1), on_release=confirm_delete)])
        dlg.open()
    def exit_file_manager(self, *args):
        if self.file_manager:
            self.file_manager.close()
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class ClassPanelScreen(Screen):
    def on_enter(self):
        self.refresh_classes()
    def refresh_classes(self):
        container = self.ids.classes_container
        container.clear_widgets()
        spinner = MDSpinner(size_hint=(None, None), size=(dp(46), dp(46)), pos_hint={'center_x':0.5, 'center_y':0.5})
        container.add_widget(spinner)
        Clock.schedule_once(lambda dt: self.load_classes(), 0.5)
    def load_classes(self):
        container = self.ids.classes_container
        container.clear_widgets()
        classes = get_all_classes()
        for class_name in classes:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM students WHERE class_name=? AND is_deleted=0", (class_name,))
            count = c.fetchone()[0]
            c.execute("SELECT name FROM teachers WHERE assigned_class=?", (class_name,))
            teacher_row = c.fetchone()
            teacher_name = teacher_row[0] if teacher_row else "Not assigned"
            conn.close()
            color = get_class_color(class_name)
            card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(100),
                          radius=14, elevation=3, md_bg_color=color, padding=12, spacing=10)
            label = MDLabel(text=f"{class_name}\nStudents: {count}   Teacher: {teacher_name}", 
                            bold=True, halign='center', valign='middle',
                            theme_text_color="Custom", text_color=(1,1,1,1))
            label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
            btn_layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_x=1, size_hint_y=None, height=dp(40))
            students_btn = MDRaisedButton(text="Students", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.3,
                                          on_release=lambda x, cn=class_name: self.edit_class_students(cn))
            results_btn = MDRaisedButton(text="Results", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.3,
                                         on_release=lambda x, cn=class_name: self.manage_results(cn))
            atten_btn = MDRaisedButton(text="Atten", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.3,
                                       on_release=lambda x, cn=class_name: self.open_class_attendance(cn))
            btn_layout.add_widget(students_btn)
            btn_layout.add_widget(results_btn)
            btn_layout.add_widget(atten_btn)
            card.add_widget(label)
            card.add_widget(btn_layout)
            container.add_widget(card)
    def open_class_attendance(self, class_name):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM students WHERE class_name=? AND is_deleted=0", (class_name,))
        total_students = c.fetchone()[0]
        conn.close()
        if total_students == 0:
            self.show_dialog("Info", "No students in this class.")
            return
        content = MDBoxLayout(orientation='vertical', spacing=25, padding=30, size_hint_y=None, height=700)
        content.add_widget(MDLabel(text=f"Mark Attendance - {class_name}", font_style="H6", bold=True, halign="center", size_hint_y=None, height=50))
        present_field = MDTextField(hint_text="Present", mode="rectangle", input_filter="int", size_hint_y=None, height=60)
        absent_field = MDTextField(hint_text="Absent", mode="rectangle", input_filter="int", size_hint_y=None, height=60)
        total_field = MDTextField(text=str(total_students), hint_text="Total", mode="rectangle", readonly=True, size_hint_y=None, height=60)
        content.add_widget(present_field)
        content.add_widget(absent_field)
        content.add_widget(total_field)
        content.add_widget(Widget(size_hint_y=None, height=40))
        btn_layout = MDBoxLayout(orientation='horizontal', spacing=15, size_hint_y=None, height=60)
        send_btn = MDRaisedButton(text="Send", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.6, pos_hint={'center_x':0.5})
        btn_layout.add_widget(Widget(size_hint_x=0.2))
        btn_layout.add_widget(send_btn)
        btn_layout.add_widget(Widget(size_hint_x=0.2))
        content.add_widget(btn_layout)
        dialog = MDDialog(title="", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="Cancel", on_release=lambda x: x.dismiss())])
        def send(instance):
            try:
                present = int(present_field.text) if present_field.text.strip() else 0
                absent = int(absent_field.text) if absent_field.text.strip() else 0
                if present + absent != total_students:
                    self.show_dialog("Error", f"Present + Absent must equal Total ({total_students})")
                    return
                today = datetime.now().strftime("%Y-%m-%d")
                slot = "Manual"
                teacher = MDApp.get_running_app().username
                data = {"present": present, "absent": absent}
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT INTO attendance (class_name, date, slot, teacher_username, attendance_data, total_present, total_absent, total_students) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          (class_name, today, slot, teacher, json.dumps(data), present, absent, total_students))
                conn.commit()
                conn.close()
                dialog.dismiss()
                self.show_dialog("Success", "Attendance sent to Principal Panel.")
                self.manager.current = 'principal_panel'
            except ValueError:
                self.show_dialog("Error", "Please enter valid numbers.")
        send_btn.bind(on_release=send)
        dialog.open()
    def edit_class_students(self, class_name):
        app = MDApp.get_running_app()
        if is_teacher(app.role):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT assigned_class FROM teachers WHERE username=?", (app.username,))
            row = c.fetchone()
            conn.close()
            if not row or row[0] != class_name:
                self.show_dialog("Access Denied", "You can only edit your own class students.")
                return
        elif not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "You don't have permission.")
            return
        edit_screen = self.manager.get_screen('student_edit')
        edit_screen.set_class(class_name)
        self.manager.current = 'student_edit'
    def manage_results(self, class_name):
        app = MDApp.get_running_app()
        if is_teacher(app.role):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT assigned_class FROM teachers WHERE username=?", (app.username,))
            row = c.fetchone()
            conn.close()
            if not row or row[0] != class_name:
                self.show_dialog("Access Denied", "You can only manage results for your own class.")
                return
        elif not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "You don't have permission.")
            return
        results_screen = self.manager.get_screen('results_announcement')
        results_screen.selected_class = class_name
        results_screen.load_classes()
        self.manager.current = 'results_announcement'
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class StudentEditScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.class_name = ""
    def set_class(self, class_name):
        self.class_name = class_name
        self.ids.edit_toolbar.title = f"EDIT STUDENTS - {class_name}"
        self.load_students()
    def load_students(self):
        app = MDApp.get_running_app()
        if is_student(app.role):
            self.show_dialog("Access Denied", "You do not have permission to edit student data.")
            Clock.schedule_once(lambda dt: self.back_to_class_panel(), 0.5)
            return
        container = self.ids.edit_container
        container.clear_widgets()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, username, father_name, cnic, dob FROM students WHERE class_name=? AND is_deleted=0", (self.class_name,))
        students = c.fetchall()
        conn.close()
        if not students:
            container.add_widget(MDLabel(text="No students in this class", halign="center", theme_text_color="Secondary"))
        else:
            for student in students:
                sid, name, bform, father_name, cnic, dob = student
                card = MDCard(orientation='vertical', padding=20, spacing=15, size_hint_y=None, height=900, radius=12, elevation=3, md_bg_color=(1,1,1,1))
                name_field = MDTextField(text=name, hint_text="Name", mode="rectangle", size_hint_y=None, height=60)
                bform_field = MDTextField(text=bform, hint_text="B-Form (12345-1234567-8)", mode="rectangle", size_hint_y=None, height=60)
                father_field = MDTextField(text=father_name if father_name else "", hint_text="Father Name", mode="rectangle", size_hint_y=None, height=60)
                cnic_field = MDTextField(text=cnic if cnic else "", hint_text="CNIC (12345-1234567-8)", mode="rectangle", size_hint_y=None, height=60)
                dob_field = MDTextField(text=dob if dob else "", hint_text="Date of Birth (dd-mm-yyyy)", mode="rectangle", size_hint_y=None, height=60)
                card.add_widget(name_field)
                card.add_widget(bform_field)
                card.add_widget(father_field)
                card.add_widget(cnic_field)
                card.add_widget(dob_field)
                card.add_widget(Widget(size_hint_y=None, height=45))
                btn_layout = MDBoxLayout(orientation='horizontal', spacing=15, size_hint_y=None, height=50, padding=[10,0,10,0])
                save_btn = MDRaisedButton(text="SAVE", md_bg_color=(0.2,0.7,0.3,1), size_hint_x=0.5,
                                          on_release=lambda x, sid=sid, nf=name_field, bf=bform_field, ff=father_field, cf=cnic_field, df=dob_field: self.save_student(sid, nf.text, bf.text, ff.text, cf.text, df.text))
                delete_btn = MDRaisedButton(text="DELETE", md_bg_color=(0.8,0.2,0.2,1), size_hint_x=0.5,
                                           on_release=lambda x, username=bform: self.delete_student_from_class(username))
                btn_layout.add_widget(save_btn)
                btn_layout.add_widget(delete_btn)
                card.add_widget(btn_layout)
                container.add_widget(card)
    def save_student(self, student_id, name, bform, father_name, cnic, dob):
        if bform and not validate_bform(bform):
            self.show_dialog("Error", "B-Form must be in format: 12345-1234567-8")
            return
        if cnic and not validate_bform(cnic):
            self.show_dialog("Error", "CNIC must be in format: 12345-1234567-8")
            return
        if dob.strip():
            try:
                datetime.strptime(dob.strip(), "%d-%m-%Y")
            except ValueError:
                self.show_dialog("Error", "Date of Birth must be in dd-mm-yyyy format")
                return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE students SET name=?, username=?, father_name=?, cnic=?, dob=? WHERE id=?", 
                  (name, bform, father_name, cnic, dob, student_id))
        c.execute("UPDATE users SET name=?, username=? WHERE username=(SELECT username FROM students WHERE id=?)", (name, bform, student_id))
        conn.commit()
        conn.close()
        self.show_dialog("Success", "Student information updated!")
        self.load_students()
        class_panel = self.manager.get_screen('class_panel')
        class_panel.load_classes()
        fee_ledger = self.manager.get_screen('fee_ledger')
        fee_ledger.load_classes()
        # Notification
        notify_student(bform, "Profile Updated", "Your student profile has been updated.", "profile_update")
        notify_teachers("Student Profile Updated", f"Student {name} (B-Form: {bform}) profile updated.", "profile_update")
    def delete_student_from_class(self, username):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can delete students.")
            return
        def confirm_delete(instance):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT name FROM students WHERE username=?", (username,))
            row = c.fetchone()
            student_name = row[0] if row else username
            conn.close()
            block_user(username)
            add_student_change_log(student_name, username, "Deleted")
            self.load_students()
            class_panel = self.manager.get_screen('class_panel')
            class_panel.load_classes()
            fee_ledger = self.manager.get_screen('fee_ledger')
            fee_ledger.load_classes()
            self.show_dialog("Success", "Student blocked successfully!")
            dlg.dismiss()
            # Notification
            notify_teachers("Student Deleted", f"Student {student_name} (B-Form: {username}) has been blocked/deleted.", "student_delete")
        dlg = MDDialog(title="Confirm Delete", text=f"Are you sure you want to delete student {username}? This will block the account.",
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="DELETE", md_bg_color=(0.8,0.2,0.2,1), on_release=confirm_delete)])
        dlg.open()
    def generate_pdf_report(self):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can generate reports.")
            return
        if not REPORTLAB_AVAILABLE:
            self.show_dialog("Error", "ReportLab not installed. Please install it using: pip install reportlab")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT name, username, father_name, cnic, dob FROM students WHERE class_name=? AND is_deleted=0", (self.class_name,))
        students = c.fetchall()
        conn.close()
        if not students:
            self.show_dialog("Info", "No students to generate report.")
            return
        save_path = get_documents_path()
        if not os.path.exists(save_path):
            save_path = os.getcwd()
        filename = os.path.join(save_path, f"{self.class_name}_Students_Report.pdf")
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm, leftMargin=15*mm, rightMargin=15*mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=12)
        story = []
        story.append(Paragraph(f"Class: {self.class_name} - Student Records", title_style))
        story.append(Spacer(1, 10))
        table_data = [['S.No', 'Name', 'B-Form', 'Father Name', 'CNIC', 'DOB']]
        for idx, stu in enumerate(students, 1):
            table_data.append([str(idx), stu[0], stu[1], stu[2], stu[3], stu[4]])
        col_widths = [20*mm, 45*mm, 40*mm, 45*mm, 40*mm, 35*mm]
        table = Table(table_data, repeatRows=1, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        story.append(table)
        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(A4[0]/2, 15*mm, f"Page {page_num}")
            canvas.restoreState()
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        self.show_dialog("Success", f"PDF report saved at:\n{filename}")
    def back_to_class_panel(self):
        self.manager.current = 'class_panel'
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class ResultsAnnouncementScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_term = "Term 1"
        self.terms_list = []
        self.selected_class = None
        self.classes = get_all_classes()
    def on_enter(self):
        self.load_terms()
    def load_terms(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT DISTINCT term_name FROM student_results ORDER BY term_name")
        terms = c.fetchall()
        conn.close()
        self.terms_list = [t[0] for t in terms] if terms else ["Term 1"]
        self.load_classes()
    def add_term(self):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can add terms.")
            return
        def add(term_name_field, dlg):
            term_name = term_name_field.text.strip()
            if not term_name:
                self.show_dialog("Error", "Please enter term name.")
                return
            self.terms_list.append(term_name)
            self.terms_list = list(set(self.terms_list))
            self.terms_list.sort()
            dlg.dismiss()
            self.show_dialog("Success", f"Term '{term_name}' added. You can now enter results for students.")
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=200)
        content.add_widget(MDLabel(text="Enter new term name", font_style="H6", halign="center", size_hint_y=None, height=40))
        term_field = MDTextField(hint_text="e.g., Term 2, Mid Term, Final", mode="rectangle", size_hint_y=None, height=50)
        content.add_widget(term_field)
        dlg = MDDialog(title="", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="ADD", md_bg_color=(0.05,0.28,0.63,1),
                                               on_release=lambda x: add(term_field, dlg))])
        dlg.open()
    def load_classes(self):
        container = self.ids.results_container
        container.clear_widgets()
        term_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=10, padding=[10,5])
        term_label = MDLabel(text="Select Term:", size_hint_x=0.3, font_style="H6")
        term_spinner = MDTextField(hint_text="Term", text=self.current_term, mode="rectangle", size_hint_x=0.5, on_focus=self.on_term_focus)
        term_layout.add_widget(term_label)
        term_layout.add_widget(term_spinner)
        container.add_widget(term_layout)
        class_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=10, padding=[10,5])
        class_label = MDLabel(text="Select Class:", size_hint_x=0.3, font_style="H6")
        class_spinner = MDTextField(hint_text="Class", text=self.selected_class if self.selected_class else "Select Class", mode="rectangle", size_hint_x=0.5, on_focus=self.on_class_focus)
        class_layout.add_widget(class_label)
        class_layout.add_widget(class_spinner)
        container.add_widget(class_layout)
        if not self.selected_class:
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT name, username FROM students WHERE class_name=? AND is_deleted=0 ORDER BY name", (self.selected_class,))
        students = c.fetchall()
        conn.close()
        if not students:
            container.add_widget(MDLabel(text="No students in this class", halign="center", theme_text_color="Secondary"))
            return
        for student_name, student_username in students:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT subject, total_marks, obtained_marks FROM student_results WHERE student_username=? AND term_name=?", (student_username, self.current_term))
            results = c.fetchall()
            conn.close()
            total_obtained = sum(r[2] for r in results)
            total_marks = sum(r[1] for r in results)
            overall_percentage = (total_obtained / total_marks * 100) if total_marks > 0 else 0
            if overall_percentage >= 80: grade = "A+"
            elif overall_percentage >= 70: grade = "A"
            elif overall_percentage >= 60: grade = "B"
            elif overall_percentage >= 50: grade = "C"
            elif overall_percentage >= 40: grade = "D"
            else: grade = "F" if total_marks > 0 else "No data"
            preview = f"Total: {total_obtained}/{total_marks} | {overall_percentage:.1f}% | Grade: {grade}" if total_marks > 0 else "No results entered"
            color = (0.2,0.5,0.8,1)
            card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(120),
                          radius=14, elevation=4, md_bg_color=(1,1,1,1), padding=10, spacing=6)
            card.add_widget(MDLabel(text=student_name, bold=True, font_style="H6", halign="center", 
                                    size_hint_y=None, height=dp(35), theme_text_color="Custom", text_color=(0.05,0.28,0.63,1)))
            card.add_widget(MDLabel(text=preview, font_style="Caption", theme_text_color="Secondary",
                                    halign="center", size_hint_y=None, height=dp(40)))
            btn_layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=dp(40))
            view_btn = MDRaisedButton(text="VIEW", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5,
                                      on_release=lambda x, uname=student_username: self.view_student_result(uname))
            edit_btn = MDRaisedButton(text="EDIT", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5,
                                      on_release=lambda x, uname=student_username, name=student_name: self.edit_student_result(uname, name))
            btn_layout.add_widget(view_btn)
            btn_layout.add_widget(edit_btn)
            card.add_widget(btn_layout)
            container.add_widget(card)
    def on_term_focus(self, instance, focus):
        if focus:
            def on_select(selected_term):
                self.current_term = selected_term
                self.load_classes()
            MDDialog(title="Select Term", text="", 
                     buttons=[MDFlatButton(text=t, on_release=lambda x, term=t: on_select(term)) for t in self.terms_list] + 
                     [MDFlatButton(text="Cancel", on_release=lambda x: x.dismiss())]).open()
    def on_class_focus(self, instance, focus):
        if focus:
            def on_select(cls):
                self.selected_class = cls
                self.load_classes()
            MDDialog(title="Select Class", text="", 
                     buttons=[MDFlatButton(text=c, on_release=lambda x, cls=c: on_select(cls)) for c in self.classes] + 
                     [MDFlatButton(text="Cancel", on_release=lambda x: x.dismiss())]).open()
    def view_student_result(self, student_username):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT name, father_name, cnic, username, class_name FROM students WHERE username=?", (student_username,))
        student = c.fetchone()
        if not student:
            conn.close()
            return
        student_name, father_name, cnic, bform, class_name = student
        c.execute("SELECT value FROM school_settings WHERE key='school_name'")
        school_row = c.fetchone()
        school_name = school_row[0] if school_row else "Al-Hamd Cadet School"
        c.execute("SELECT subject, total_marks, obtained_marks, percentage, grade FROM student_results WHERE student_username=? AND term_name=?", (student_username, self.current_term))
        results = c.fetchall()
        conn.close()
        if not results:
            self.show_dialog("Info", "No results found for this student.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT student_username, SUM(obtained_marks) as total_obtained, SUM(total_marks) as total_marks
            FROM student_results WHERE class_name=? AND term_name=?
            GROUP BY student_username
        """, (class_name, self.current_term))
        all_students = c.fetchall()
        conn.close()
        rank = 1
        for idx, (uname, obtained, total) in enumerate(sorted(all_students, key=lambda x: (x[1]/x[2]) if x[2]>0 else 0, reverse=True)):
            if uname == student_username:
                rank = idx + 1
                break
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
        main_box = MDBoxLayout(orientation='vertical', spacing=15, size_hint_y=None, padding=20, width=Window.width-dp(40))
        main_box.bind(minimum_height=main_box.setter('height'))
        main_box.add_widget(MDLabel(text=school_name, font_style="H4", bold=True, halign='center', size_hint_y=None, height=dp(50)))
        main_box.add_widget(MDLabel(text="ACADEMIC RESULT CARD", font_style="H5", bold=True, halign='center', size_hint_y=None, height=dp(40)))
        main_box.add_widget(Widget(size_hint_y=None, height=dp(10)))
        info_card = MDCard(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=dp(180), radius=12, elevation=2, md_bg_color=(1,1,1,1))
        info_card.add_widget(MDLabel(text=f"Name: {student_name}", bold=True, size_hint_y=None, height=dp(30)))
        info_card.add_widget(MDLabel(text=f"B-Form: {bform}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"Father Name: {father_name}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"CNIC: {cnic if cnic else 'N/A'}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"Class: {class_name}", size_hint_y=None, height=dp(25)))
        info_card.add_widget(MDLabel(text=f"Term: {self.current_term}", size_hint_y=None, height=dp(25)))
        main_box.add_widget(info_card)
        main_box.add_widget(MDLabel(text="Subject-wise Marks", bold=True, font_style="H6", size_hint_y=None, height=dp(40)))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=10)
        header.add_widget(MDLabel(text="Subject", bold=True, size_hint_x=0.4))
        header.add_widget(MDLabel(text="Total", bold=True, size_hint_x=0.3))
        header.add_widget(MDLabel(text="Obtained", bold=True, size_hint_x=0.3))
        main_box.add_widget(header)
        total_marks = 0
        total_obtained = 0
        for subj, tot, obt, perc, grade in results:
            row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=10)
            row_box.add_widget(MDLabel(text=subj, size_hint_x=0.4))
            row_box.add_widget(MDLabel(text=str(tot), size_hint_x=0.3))
            row_box.add_widget(MDLabel(text=str(obt), size_hint_x=0.3))
            main_box.add_widget(row_box)
            total_marks += tot
            total_obtained += obt
        main_box.add_widget(Widget(size_hint_y=None, height=dp(10)))
        percentage = (total_obtained / total_marks * 100) if total_marks > 0 else 0
        if percentage >= 80: grade = "A+"
        elif percentage >= 70: grade = "A"
        elif percentage >= 60: grade = "B"
        elif percentage >= 50: grade = "C"
        elif percentage >= 40: grade = "D"
        else: grade = "F" if total_marks > 0 else "N/A"
        summary_card = MDCard(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=dp(140), radius=12, elevation=2, md_bg_color=(1,1,1,1))
        summary_card.add_widget(MDLabel(text=f"Total Marks: {total_obtained} / {total_marks}", bold=True, size_hint_y=None, height=dp(30)))
        summary_card.add_widget(MDLabel(text=f"Percentage: {percentage:.2f}%", bold=True, size_hint_y=None, height=dp(30)))
        summary_card.add_widget(MDLabel(text=f"Grade: {grade}", bold=True, size_hint_y=None, height=dp(30)))
        summary_card.add_widget(MDLabel(text=f"Position: {rank} / {len(all_students)}", bold=True, size_hint_y=None, height=dp(30)))
        main_box.add_widget(summary_card)
        scroll.add_widget(main_box)
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=10, size_hint_y=None, height=dp(650))
        content.add_widget(scroll)
        dialog = MDDialog(title="", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: x.dismiss())])
        dialog.open()
    def edit_student_result(self, student_username, student_name):
        app = MDApp.get_running_app()
        if is_teacher(app.role):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT assigned_class FROM teachers WHERE username=?", (app.username,))
            row = c.fetchone()
            conn.close()
            if not row or row[0] != self.selected_class:
                self.show_dialog("Access Denied", "You can only edit results for your own class.")
                return
        elif not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "You don't have permission.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT subject, total_marks, obtained_marks FROM student_results WHERE student_username=? AND term_name=?", (student_username, self.current_term))
        existing = c.fetchall()
        conn.close()
        default_subjects = ['Math', 'English', 'Urdu', 'Science', 'Islamiat', 'Pak Studies', 'Computer', 'Physics']
        subjects = []
        if existing:
            subjects = [(s[0], s[1], s[2]) for s in existing]
        else:
            subjects = [(sub, 100, 0) for sub in default_subjects[:8]]
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
        main_box = MDBoxLayout(orientation='vertical', spacing=12, size_hint_y=None, width=Window.width-dp(80))
        main_box.bind(minimum_height=main_box.setter('height'))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
        header.add_widget(MDLabel(text="Subject", bold=True, size_hint_x=0.4))
        header.add_widget(MDLabel(text="Total Marks", bold=True, size_hint_x=0.3))
        header.add_widget(MDLabel(text="Obtained Marks", bold=True, size_hint_x=0.3))
        main_box.add_widget(header)
        row_fields = []
        for subj, tot, obt in subjects:
            row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
            subject_field = MDTextField(text=subj, hint_text="Subject", mode="rectangle", size_hint_x=0.4)
            total_field = MDTextField(text=str(tot), hint_text="Total", mode="rectangle", size_hint_x=0.3, input_filter="int")
            obtained_field = MDTextField(text=str(obt), hint_text="Obtained", mode="rectangle", size_hint_x=0.3, input_filter="int")
            delete_btn = MDIconButton(icon="trash-can", theme_icon_color="Custom", icon_color=(0.8,0.2,0.2,1), size_hint_x=0.1)
            row_box.add_widget(subject_field)
            row_box.add_widget(total_field)
            row_box.add_widget(obtained_field)
            row_box.add_widget(delete_btn)
            main_box.add_widget(row_box)
            row_fields.append((subject_field, total_field, obtained_field, delete_btn, row_box))
        row_fields_list = row_fields
        def delete_row(btn, row_fields_entry):
            idx = row_fields_list.index(row_fields_entry)
            row_fields_list.pop(idx)
            main_box.remove_widget(row_fields_entry[4])
        for entry in row_fields_list:
            entry[3].bind(on_release=lambda btn, e=entry: delete_row(btn, e))
        add_btn = MDRaisedButton(text="+ Add Subject", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5, pos_hint={'center_x':0.5}, height=dp(40))
        main_box.add_widget(Widget(size_hint_y=None, height=10))
        main_box.add_widget(add_btn)
        scroll.add_widget(main_box)
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=dp(500))
        content.add_widget(MDLabel(text=f"Edit Results - {student_name} ({self.current_term})", font_style="H6", bold=True, halign="center", size_hint_y=None, height=40))
        content.add_widget(scroll)
        dlg = MDDialog(title="", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="SAVE", md_bg_color=(0.2,0.7,0.3,1),
                                               on_release=lambda x: self.save_student_results(student_username, student_name, row_fields_list, dlg))])
        def add_subject(instance):
            new_row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
            subject_field = MDTextField(text="", hint_text="Subject", mode="rectangle", size_hint_x=0.4)
            total_field = MDTextField(text="100", hint_text="Total", mode="rectangle", size_hint_x=0.3, input_filter="int")
            obtained_field = MDTextField(text="0", hint_text="Obtained", mode="rectangle", size_hint_x=0.3, input_filter="int")
            delete_btn = MDIconButton(icon="trash-can", theme_icon_color="Custom", icon_color=(0.8,0.2,0.2,1), size_hint_x=0.1)
            new_row_box.add_widget(subject_field)
            new_row_box.add_widget(total_field)
            new_row_box.add_widget(obtained_field)
            new_row_box.add_widget(delete_btn)
            main_box.children.insert(main_box.children.index(add_btn), new_row_box)
            new_entry = (subject_field, total_field, obtained_field, delete_btn, new_row_box)
            row_fields_list.append(new_entry)
            delete_btn.bind(on_release=lambda btn, e=new_entry: delete_row(btn, e))
            main_box.height += 45
        add_btn.bind(on_release=add_subject)
        dlg.open()
    def save_student_results(self, student_username, student_name, row_fields, dialog):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM student_results WHERE student_username=? AND term_name=?", (student_username, self.current_term))
        total_obtained = 0
        total_marks = 0
        for subject_field, total_field, obtained_field, delete_btn, row_box in row_fields:
            subject = subject_field.text.strip()
            if not subject:
                continue
            try:
                total = int(total_field.text) if total_field.text.strip() else 0
                obtained = int(obtained_field.text) if obtained_field.text.strip() else 0
                if total > 0 and obtained > total:
                    self.show_dialog("Error", f"Obtained marks cannot exceed total marks for {subject}")
                    conn.close()
                    return
                percentage = (obtained / total * 100) if total > 0 else 0
                if percentage >= 80: grade = "A+"
                elif percentage >= 70: grade = "A"
                elif percentage >= 60: grade = "B"
                elif percentage >= 50: grade = "C"
                elif percentage >= 40: grade = "D"
                else: grade = "F"
                c.execute("INSERT INTO student_results (student_username, class_name, term_name, subject, total_marks, obtained_marks, percentage, grade) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          (student_username, self.selected_class, self.current_term, subject, total, obtained, percentage, grade))
                total_obtained += obtained
                total_marks += total
            except ValueError:
                self.show_dialog("Error", "Please enter valid numbers for marks.")
                conn.close()
                return
        if total_marks == 0:
            self.show_dialog("Info", "No subjects added. No results saved.")
        else:
            conn.commit()
            self.show_dialog("Success", f"Results for {student_name} saved successfully!")
            # Notification to student and teachers
            notify_student(student_username, "Result Published", f"Your results for term '{self.current_term}' have been published.", "result")
            notify_teachers("Result Updated", f"Results for student {student_name} (Term: {self.current_term}) have been updated.", "result")
        conn.close()
        dialog.dismiss()
        self.load_classes()
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'

class StudentResultViewScreen(Screen):
    def load_result(self):
        container = self.ids.result_container
        container.clear_widgets()
        app = MDApp.get_running_app()
        if not is_student(app.role):
            container.add_widget(MDLabel(text="Access denied. Only students can view results.", halign="center", theme_text_color="Error"))
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT name, father_name, cnic, username, class_name FROM students WHERE username=?", (app.username,))
        student = c.fetchone()
        if not student:
            conn.close()
            container.add_widget(MDLabel(text="Student not found.", halign="center", theme_text_color="Secondary"))
            return
        student_name, father_name, cnic, bform, class_name = student
        c.execute("SELECT value FROM school_settings WHERE key='school_name'")
        school_row = c.fetchone()
        school_name = school_row[0] if school_row else "Al-Hamd Cadet School"
        c.execute("SELECT DISTINCT term_name FROM student_results WHERE student_username=? ORDER BY term_name", (app.username,))
        terms = c.fetchall()
        conn.close()
        if not terms:
            container.add_widget(MDLabel(text="No results found for you.", halign="center", theme_text_color="Secondary"))
            return
        for term_tuple in terms:
            term = term_tuple[0]
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT subject, total_marks, obtained_marks, percentage, grade FROM student_results WHERE student_username=? AND term_name=?", (app.username, term))
            results = c.fetchall()
            conn.close()
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("""
                SELECT student_username, SUM(obtained_marks) as total_obtained, SUM(total_marks) as total_marks
                FROM student_results WHERE class_name=? AND term_name=?
                GROUP BY student_username
            """, (class_name, term))
            all_students = c.fetchall()
            conn.close()
            rank = 1
            for idx, (uname, obtained, total) in enumerate(sorted(all_students, key=lambda x: (x[1]/x[2]) if x[2]>0 else 0, reverse=True)):
                if uname == app.username:
                    rank = idx + 1
                    break
            scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
            main_box = MDBoxLayout(orientation='vertical', spacing=15, size_hint_y=None, padding=20, width=Window.width-dp(40))
            main_box.bind(minimum_height=main_box.setter('height'))
            main_box.add_widget(MDLabel(text=school_name, font_style="H4", bold=True, halign='center', size_hint_y=None, height=dp(50)))
            main_box.add_widget(MDLabel(text="ACADEMIC RESULT CARD", font_style="H5", bold=True, halign='center', size_hint_y=None, height=dp(40)))
            main_box.add_widget(Widget(size_hint_y=None, height=dp(10)))
            info_card = MDCard(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=dp(180), radius=12, elevation=2, md_bg_color=(1,1,1,1))
            info_card.add_widget(MDLabel(text=f"Name: {student_name}", bold=True, size_hint_y=None, height=dp(30)))
            info_card.add_widget(MDLabel(text=f"B-Form: {bform}", size_hint_y=None, height=dp(25)))
            info_card.add_widget(MDLabel(text=f"Father Name: {father_name}", size_hint_y=None, height=dp(25)))
            info_card.add_widget(MDLabel(text=f"CNIC: {cnic if cnic else 'N/A'}", size_hint_y=None, height=dp(25)))
            info_card.add_widget(MDLabel(text=f"Class: {class_name}", size_hint_y=None, height=dp(25)))
            info_card.add_widget(MDLabel(text=f"Term: {term}", size_hint_y=None, height=dp(25)))
            main_box.add_widget(info_card)
            main_box.add_widget(MDLabel(text="Subject-wise Marks", bold=True, font_style="H6", size_hint_y=None, height=dp(40)))
            header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=10)
            header.add_widget(MDLabel(text="Subject", bold=True, size_hint_x=0.4))
            header.add_widget(MDLabel(text="Total", bold=True, size_hint_x=0.3))
            header.add_widget(MDLabel(text="Obtained", bold=True, size_hint_x=0.3))
            main_box.add_widget(header)
            total_marks = 0
            total_obtained = 0
            for subj, tot, obt, perc, grade in results:
                row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=10)
                row_box.add_widget(MDLabel(text=subj, size_hint_x=0.4))
                row_box.add_widget(MDLabel(text=str(tot), size_hint_x=0.3))
                row_box.add_widget(MDLabel(text=str(obt), size_hint_x=0.3))
                main_box.add_widget(row_box)
                total_marks += tot
                total_obtained += obt
            main_box.add_widget(Widget(size_hint_y=None, height=dp(10)))
            percentage = (total_obtained / total_marks * 100) if total_marks > 0 else 0
            if percentage >= 80: grade = "A+"
            elif percentage >= 70: grade = "A"
            elif percentage >= 60: grade = "B"
            elif percentage >= 50: grade = "C"
            elif percentage >= 40: grade = "D"
            else: grade = "F" if total_marks > 0 else "N/A"
            summary_card = MDCard(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=dp(140), radius=12, elevation=2, md_bg_color=(1,1,1,1))
            summary_card.add_widget(MDLabel(text=f"Total Marks: {total_obtained} / {total_marks}", bold=True, size_hint_y=None, height=dp(30)))
            summary_card.add_widget(MDLabel(text=f"Percentage: {percentage:.2f}%", bold=True, size_hint_y=None, height=dp(30)))
            summary_card.add_widget(MDLabel(text=f"Grade: {grade}", bold=True, size_hint_y=None, height=dp(30)))
            summary_card.add_widget(MDLabel(text=f"Position: {rank} / {len(all_students)}", bold=True, size_hint_y=None, height=dp(30)))
            main_box.add_widget(summary_card)
            scroll.add_widget(main_box)
            paper_card = MDCard(orientation='horizontal', size_hint_y=None, height=dp(50), radius=12, elevation=3, md_bg_color=(0.05,0.28,0.63,1), padding=10)
            paper_card.add_widget(MDLabel(text="Paper Generate", bold=True, font_style="Button", halign="center", valign="middle", theme_text_color="Custom", text_color=(1,1,1,1)))
            paper_card.bind(on_release=lambda x: self.generate_result_pdf(school_name, student_name, bform, father_name, cnic, class_name, term, results, all_students, rank))
            content = MDBoxLayout(orientation='vertical', spacing=10, padding=10, size_hint_y=None, height=dp(350))
            content.add_widget(scroll)
            content.add_widget(paper_card)
            dialog = MDDialog(title=f"Result - {term}", type="custom", content_cls=content,
                              buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: x.dismiss())])
            dialog.open()
    
    def generate_result_pdf(self, school_name, student_name, bform, father_name, cnic, class_name, term, results, all_students, rank):
        if not REPORTLAB_AVAILABLE:
            self.show_dialog("Error", "ReportLab not installed. Please install it using: pip install reportlab")
            return
        save_path = get_documents_path()
        if not os.path.exists(save_path):
            save_path = os.getcwd()
        filename = os.path.join(save_path, f"Result_{student_name}_{term}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm, leftMargin=15*mm, rightMargin=15*mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=12)
        story = []
        story.append(Paragraph(f"{school_name}", title_style))
        story.append(Paragraph(f"ACADEMIC RESULT CARD - {term}", title_style))
        story.append(Spacer(1, 10))
        info_data = [['Name:', student_name], ['B-Form:', bform], ['Father Name:', father_name], ['CNIC:', cnic if cnic else 'N/A'], ['Class:', class_name]]
        info_table = Table(info_data, colWidths=[50*mm, 100*mm])
        info_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('FONTNAME', (0,0), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,0), (-1,-1), 10)]))
        story.append(info_table)
        story.append(Spacer(1, 10))
        table_data = [['Subject', 'Total', 'Obtained', 'Percentage', 'Grade']]
        total_marks = 0
        total_obtained = 0
        for subj, tot, obt, perc, grade in results:
            table_data.append([subj, str(tot), str(obt), f"{perc:.1f}%", grade])
            total_marks += tot
            total_obtained += obt
        table_data.append(['TOTAL', str(total_marks), str(total_obtained), '', ''])
        col_widths = [40*mm, 20*mm, 20*mm, 25*mm, 15*mm]
        table = Table(table_data, repeatRows=1, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 10))
        percentage = (total_obtained / total_marks * 100) if total_marks > 0 else 0
        if percentage >= 80: grade = "A+"
        elif percentage >= 70: grade = "A"
        elif percentage >= 60: grade = "B"
        elif percentage >= 50: grade = "C"
        elif percentage >= 40: grade = "D"
        else: grade = "F"
        summary_data = [['Total Percentage:', f"{percentage:.2f}%"], ['Grade:', grade], ['Position:', f"{rank} / {len(all_students)}"]]
        summary_table = Table(summary_data, colWidths=[50*mm, 100*mm])
        summary_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('FONTNAME', (0,0), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,0), (-1,-1), 10), ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold')]))
        story.append(summary_table)
        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(A4[0]/2, 15*mm, f"Page {page_num}")
            canvas.restoreState()
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        self.show_dialog("Success", f"PDF saved at:\n{filename}")
    
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()

class FeeLedgerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_month = datetime.now().strftime('%Y-%m')
    def on_enter(self):
        self.load_classes()
    def show_month_picker(self):
        def on_month_selected(month_year):
            self.current_month = month_year
            self.load_classes()
        show_month_year_dialog(on_month_selected)
    def load_classes(self):
        container = self.ids.fee_classes_container
        container.clear_widgets()
        app = MDApp.get_running_app()
        month_card = MDCard(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=dp(50), 
                            radius=12, elevation=2, md_bg_color=(1,1,1,1), padding=8)
        month_card.add_widget(MDLabel(text=f"Selected Month: {self.current_month}", bold=True, font_style="H6", 
                                      halign="center", theme_text_color="Custom", text_color=(0.05,0.28,0.63,1)))
        container.add_widget(month_card)
        if is_student(app.role):
            student_class = app.student_class
            if not student_class:
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM fee_records fr JOIN students s ON fr.student_username = s.username WHERE fr.class_name=? AND fr.month_year=? AND s.is_deleted=0", (student_class, self.current_month))
            count = c.fetchone()[0]
            conn.close()
            color = get_class_color(student_class)
            card = MDCard(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=dp(100),
                          radius=14, elevation=3, md_bg_color=color, padding=12)
            label = MDLabel(text=f"{student_class}\nStudents: {count}\nMonth: {self.current_month}", 
                            halign='center', valign='middle', bold=True,
                            theme_text_color="Custom", text_color=(1,1,1,1))
            label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
            card.add_widget(label)
            card.bind(on_release=lambda x, cn=student_class: self.show_fee_detail(cn))
            container.add_widget(card)
        else:
            classes = get_all_classes()
            other_classes = [c for c in classes if c != 'Class 10']
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            for class_name in other_classes:
                c.execute("SELECT SUM(fr.paid_amount), COUNT(*) FROM fee_records fr JOIN students s ON fr.student_username = s.username WHERE fr.class_name=? AND fr.month_year=? AND s.is_deleted=0", (class_name, self.current_month))
                row = c.fetchone()
                total = row[0] if row[0] else 0
                count = row[1] if row[1] else 0
                color = get_class_color(class_name)
                card = MDCard(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=dp(100),
                              radius=14, elevation=3, md_bg_color=color, padding=12)
                label = MDLabel(text=f"{class_name}\nStudents: {count}  |  Collection: Rs. {total:,}\nMonth: {self.current_month}", 
                                halign='center', valign='middle', bold=True,
                                theme_text_color="Custom", text_color=(1,1,1,1))
                label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
                card.add_widget(label)
                card.bind(on_release=lambda x, cn=class_name: self.show_fee_detail(cn))
                container.add_widget(card)
            conn.close()
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT SUM(fr.paid_amount), COUNT(*) FROM fee_records fr JOIN students s ON fr.student_username = s.username WHERE fr.class_name=? AND fr.month_year=? AND s.is_deleted=0", ('Class 10', self.current_month))
            row = c.fetchone()
            total = row[0] if row[0] else 0
            count = row[1] if row[1] else 0
            conn.close()
            color = get_class_color('Class 10')
            card = MDCard(orientation='horizontal', size_hint_x=1, size_hint_y=None, height=dp(100),
                          radius=14, elevation=3, md_bg_color=color, padding=12)
            label = MDLabel(text=f"Class 10\nStudents: {count}  |  Collection: Rs. {total:,}\nMonth: {self.current_month}", 
                            halign='center', valign='middle', bold=True,
                            theme_text_color="Custom", text_color=(1,1,1,1))
            label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
            card.add_widget(label)
            card.bind(on_release=lambda x, cn='Class 10': self.show_fee_detail(cn))
            container.add_widget(card)
    def show_fee_detail(self, class_name):
        fee_detail_screen = self.manager.get_screen('fee_detail')
        fee_detail_screen.class_name = class_name
        fee_detail_screen.month_year = self.current_month
        self.manager.current = 'fee_detail'
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'

class FeeDetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.class_name = ""
        self.month_year = ""
    def on_enter(self):
        if self.class_name:
            self.ids.toolbar.title = f"FEE DETAILS - {self.class_name} ({self.month_year})"
            self.load_fee_data()
    def load_fee_data(self):
        self.ids.fee_detail_container.clear_widgets()
        app = MDApp.get_running_app()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if is_student(app.role):
            c.execute("SELECT fr.id, fr.student_name, fr.student_username, fr.total_fee, fr.paid_amount, fr.remaining, fr.status FROM fee_records fr JOIN students s ON fr.student_username = s.username WHERE fr.student_username=? AND fr.month_year=? AND s.is_deleted=0", (app.username, self.month_year))
        else:
            c.execute("SELECT fr.id, fr.student_name, fr.student_username, fr.total_fee, fr.paid_amount, fr.remaining, fr.status FROM fee_records fr JOIN students s ON fr.student_username = s.username WHERE fr.class_name=? AND fr.month_year=? AND s.is_deleted=0 ORDER BY fr.student_name", (self.class_name, self.month_year))
        records = c.fetchall()
        conn.close()
        if not records:
            empty = MDCard(orientation='vertical', padding=30, spacing=10, size_hint_y=None, height=150, radius=15, elevation=2, md_bg_color=(1,1,1,1))
            empty.add_widget(MDLabel(text="No Students Found", halign="center", theme_text_color="Secondary", font_style="H6"))
            self.ids.fee_detail_container.add_widget(empty)
        else:
            can_update = is_admin_or_principal_or_head(app.role)
            for idx, rec in enumerate(records, 1):
                rid, name, uname, total, paid, remaining, status = rec
                card = MDCard(orientation='vertical', padding=15, spacing=10, size_hint_y=None, height=650, radius=12, elevation=3, md_bg_color=(1,1,1,1))
                card.add_widget(MDLabel(text=f"{idx}. {name}", bold=True, theme_text_color="Custom", text_color=(0.05,0.28,0.63,1), size_hint_y=None, height=40))
                card.add_widget(MDLabel(text=f"B-Form: {uname}", size_hint_y=None, height=35))
                total_fee_field = MDTextField(text=str(total), hint_text="Total Fee", mode="rectangle", size_hint_y=None, height=50, disabled=not can_update)
                paid_field = MDTextField(text=str(paid), hint_text="Paid Amount", mode="rectangle", size_hint_y=None, height=50, disabled=not can_update)
                remaining_label = MDLabel(text=f"Remaining: Rs. {remaining}", size_hint_y=None, height=40, bold=True)
                status_color = self.get_status_color(status)
                status_label = MDLabel(text=f"Status: {status}", bold=True, theme_text_color="Custom", text_color=status_color, size_hint_y=None, height=40)
                card.add_widget(total_fee_field)
                card.add_widget(paid_field)
                card.add_widget(remaining_label)
                card.add_widget(status_label)
                card.add_widget(Widget(size_hint_y=None, height=15))
                if can_update:
                    update_btn = MDRaisedButton(text="UPDATE", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.4, on_release=lambda x, rid=rid, tf=total_fee_field, pd=paid_field: self.update_fee_record(rid, tf.text, pd.text))
                    delete_btn = MDRaisedButton(text="DELETE", md_bg_color=(0.8,0.2,0.2,1), size_hint_x=0.4, on_release=lambda x, username=uname: self.delete_student_from_fee(username))
                    btn_box = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
                    btn_box.add_widget(update_btn)
                    btn_box.add_widget(delete_btn)
                    card.add_widget(btn_box)
                self.ids.fee_detail_container.add_widget(card)
    def get_status_color(self, status):
        if status == "Paid":
            return (0.2,0.7,0.3,1)
        elif status == "Over Paid":
            return (0.2,0.5,0.9,1)
        else:
            return (0.8,0.2,0.2,1)
    def update_fee_record(self, record_id, new_total, new_paid):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can update fee records.")
            return
        try:
            total = int(new_total) if new_total.strip() else 0
            paid = int(new_paid) if new_paid.strip() else 0
        except ValueError:
            self.show_dialog("Error", "Please enter valid numbers for Total Fee and Paid Amount!")
            return
        remaining = total - paid
        if remaining == 0: status = "Paid"
        elif remaining < 0: status = "Over Paid"
        else: status = "Less Paid"
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE fee_records SET total_fee=?, paid_amount=?, remaining=?, status=? WHERE id=?",
                  (total, paid, remaining, status, record_id))
        conn.commit()
        conn.close()
        self.show_dialog("Success", "Fee record updated successfully!")
        self.load_fee_data()
        # Notification to student and teachers
        # Get student username from record_id
        conn2 = sqlite3.connect(DB_NAME)
        c2 = conn2.cursor()
        c2.execute("SELECT student_username FROM fee_records WHERE id=?", (record_id,))
        row = c2.fetchone()
        conn2.close()
        if row:
            notify_student(row[0], "Fee Record Updated", f"Your fee record for {self.month_year} has been updated.", "fee")
            notify_teachers("Fee Record Updated", f"Fee record for student {row[0]} for {self.month_year} updated.", "fee")
    def delete_student_from_fee(self, username):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can delete fee records.")
            return
        def confirm_delete(instance):
            block_user(username)
            self.load_fee_data()
            class_panel = self.manager.get_screen('class_panel')
            class_panel.load_classes()
            fee_ledger = self.manager.get_screen('fee_ledger')
            fee_ledger.load_classes()
            self.show_dialog("Success", "Student blocked successfully!")
            dlg.dismiss()
            # Notification
            notify_teachers("Student Deleted from Fee", f"Student {username} has been blocked from fee records.", "fee")
        dlg = MDDialog(title="Confirm Delete", text=f"Are you sure you want to delete student {username}? This will block the account.",
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="DELETE", md_bg_color=(0.8,0.2,0.2,1), on_release=confirm_delete)])
        dlg.open()
    def generate_fee_pdf(self):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can generate fee reports.")
            return
        if not REPORTLAB_AVAILABLE:
            self.show_dialog("Error", "ReportLab not installed. Please install it using: pip install reportlab")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT fr.student_name, fr.student_username, fr.total_fee, fr.paid_amount, fr.remaining, fr.status FROM fee_records fr JOIN students s ON fr.student_username = s.username WHERE fr.class_name=? AND fr.month_year=? AND s.is_deleted=0", (self.class_name, self.month_year))
        records = c.fetchall()
        conn.close()
        if not records:
            self.show_dialog("Info", "No fee records to generate report.")
            return
        save_path = get_documents_path()
        if not os.path.exists(save_path):
            save_path = os.getcwd()
        filename = os.path.join(save_path, f"{self.class_name}_Fee_Report_{self.month_year}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm, leftMargin=15*mm, rightMargin=15*mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=12)
        story = []
        story.append(Paragraph(f"Class: {self.class_name} - Fee Records ({self.month_year})", title_style))
        story.append(Spacer(1, 10))
        table_data = [['S.No', 'Student Name', 'B-Form', 'Total Fee', 'Paid', 'Remaining', 'Status']]
        for idx, rec in enumerate(records, 1):
            table_data.append([str(idx), rec[0], rec[1], f"Rs. {rec[2]}", f"Rs. {rec[3]}", f"Rs. {rec[4]}", rec[5]])
        col_widths = [15*mm, 45*mm, 40*mm, 25*mm, 25*mm, 25*mm, 25*mm]
        table = Table(table_data, repeatRows=1, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        story.append(table)
        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(A4[0]/2, 15*mm, f"Page {page_num}")
            canvas.restoreState()
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        self.show_dialog("Success", f"PDF report saved at:\n{filename}")
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()
    def back_to_ledger(self):
        self.manager.current = 'fee_ledger'

def auto_sync_student(name, class_name, gender, contact, address, uname, pwd):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE username=?", (uname,))
    if not c.fetchone():
        total_fee = get_fee_by_class(class_name)
        current_month = datetime.now().strftime('%Y-%m')
        c.execute("INSERT INTO students (name, contact, class_name, address, gender, username, password, father_name, cnic, dob, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                  (name, contact, class_name, address, gender, uname, pwd, '', '', ''))
        c.execute("INSERT INTO fee_records (student_name, student_username, class_name, total_fee, paid_amount, remaining, status, month_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (name, uname, class_name, total_fee, 0, total_fee, 'Less Paid', current_month))
    conn.commit()
    conn.close()

class TimetableScreen(Screen):
    def on_enter(self):
        self.load_cards()
    def load_cards(self):
        container = self.ids.timetable_container
        container.clear_widgets()
        classes = get_all_classes()
        other_classes = [c for c in classes if c != 'Class 10']
        for class_name in other_classes:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT data FROM timetables WHERE class_name=?", (class_name,))
            row = c.fetchone()
            data = json.loads(row[0]) if row else [{"time":"","subject":"","teacher":""} for _ in range(8)]
            preview = "No entries"
            for entry in data:
                if entry.get("time") and entry.get("subject"):
                    preview = f"{entry['time']} - {entry['subject']}"
                    break
            conn.close()
            card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(100),
                          radius=14, elevation=4, md_bg_color=get_class_color(class_name), padding=12, spacing=10)
            label = MDLabel(text=class_name, bold=True, font_style="H6", halign='center', valign='middle',
                            theme_text_color="Custom", text_color=(1,1,1,1))
            label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
            btn_layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_x=1, size_hint_y=None, height=dp(40))
            view_btn = MDRaisedButton(text="VIEW", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5, on_release=lambda x, cn=class_name: self.view_timetable(cn))
            edit_btn = MDRaisedButton(text="EDIT", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5, on_release=lambda x, cn=class_name: self.edit_timetable(cn))
            btn_layout.add_widget(view_btn)
            btn_layout.add_widget(edit_btn)
            card.add_widget(label)
            card.add_widget(btn_layout)
            container.add_widget(card)
        class_name = 'Class 10'
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT data FROM timetables WHERE class_name=?", (class_name,))
        row = c.fetchone()
        data = json.loads(row[0]) if row else [{"time":"","subject":"","teacher":""} for _ in range(8)]
        preview = "No entries"
        for entry in data:
            if entry.get("time") and entry.get("subject"):
                preview = f"{entry['time']} - {entry['subject']}"
                break
        conn.close()
        card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(100),
                      radius=14, elevation=4, md_bg_color=get_class_color(class_name), padding=12, spacing=10)
        label = MDLabel(text=class_name, bold=True, font_style="H6", halign='center', valign='middle',
                        theme_text_color="Custom", text_color=(1,1,1,1))
        label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
        btn_layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_x=1, size_hint_y=None, height=dp(40))
        view_btn = MDRaisedButton(text="VIEW", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5, on_release=lambda x, cn=class_name: self.view_timetable(cn))
        edit_btn = MDRaisedButton(text="EDIT", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5, on_release=lambda x, cn=class_name: self.edit_timetable(cn))
        btn_layout.add_widget(view_btn)
        btn_layout.add_widget(edit_btn)
        card.add_widget(label)
        card.add_widget(btn_layout)
        container.add_widget(card)
    def view_timetable(self, class_name):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT data FROM timetables WHERE class_name=?", (class_name,))
        row = c.fetchone()
        data = json.loads(row[0]) if row else [{"time":"","subject":"","teacher":""} for _ in range(8)]
        conn.close()
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
        main_box = MDBoxLayout(orientation='vertical', spacing=12, size_hint_y=None, width=Window.width-dp(80))
        main_box.bind(minimum_height=main_box.setter('height'))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
        header.add_widget(MDLabel(text="Time", bold=True, size_hint_x=0.35))
        header.add_widget(MDLabel(text="Subject", bold=True, size_hint_x=0.35))
        header.add_widget(MDLabel(text="Teacher", bold=True, size_hint_x=0.30))
        main_box.add_widget(header)
        for entry in data:
            row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
            row_box.add_widget(MDLabel(text=entry.get("time",""), size_hint_x=0.35, shorten=True))
            row_box.add_widget(MDLabel(text=entry.get("subject",""), size_hint_x=0.35, shorten=True))
            row_box.add_widget(MDLabel(text=entry.get("teacher",""), size_hint_x=0.30, shorten=True))
            main_box.add_widget(row_box)
        scroll.add_widget(main_box)
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=dp(450))
        content.add_widget(MDLabel(text=f"Timetable - {class_name}", font_style="H6", bold=True, halign="center", size_hint_y=None, height=40))
        content.add_widget(scroll)
        MDDialog(title="", type="custom", content_cls=content,
                 buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: x.dismiss())]).open()
    def edit_timetable(self, class_name):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can edit timetables.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT data FROM timetables WHERE class_name=?", (class_name,))
        row = c.fetchone()
        data = json.loads(row[0]) if row else [{"time":"","subject":"","teacher":""} for _ in range(8)]
        conn.close()
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
        main_box = MDBoxLayout(orientation='vertical', spacing=12, size_hint_y=None, width=Window.width-dp(80))
        main_box.bind(minimum_height=main_box.setter('height'))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
        header.add_widget(MDLabel(text="Time", bold=True, size_hint_x=0.35))
        header.add_widget(MDLabel(text="Subject", bold=True, size_hint_x=0.35))
        header.add_widget(MDLabel(text="Teacher", bold=True, size_hint_x=0.30))
        main_box.add_widget(header)
        row_fields = []
        for i in range(8):
            row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
            time_field = MDTextField(text=data[i]["time"], hint_text="e.g., 8:00-9:00", mode="rectangle", size_hint_x=0.35)
            subject_field = MDTextField(text=data[i]["subject"], hint_text="Subject", mode="rectangle", size_hint_x=0.35)
            teacher_field = MDTextField(text=data[i]["teacher"], hint_text="Teacher", mode="rectangle", size_hint_x=0.30)
            row_box.add_widget(time_field)
            row_box.add_widget(subject_field)
            row_box.add_widget(teacher_field)
            main_box.add_widget(row_box)
            row_fields.append((time_field, subject_field, teacher_field))
        scroll.add_widget(main_box)
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=dp(500))
        content.add_widget(MDLabel(text=f"Edit Timetable - {class_name}", font_style="H6", bold=True, halign="center", size_hint_y=None, height=40))
        content.add_widget(scroll)
        dlg = MDDialog(title="", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="SAVE", md_bg_color=(0.2,0.7,0.3,1),
                                               on_release=lambda x: self.save_timetable(class_name, row_fields, dlg))])
        dlg.open()
    def save_timetable(self, class_name, row_fields, dialog):
        new_rows = []
        for time_field, subject_field, teacher_field in row_fields:
            new_rows.append({"time": time_field.text, "subject": subject_field.text, "teacher": teacher_field.text})
        value = json.dumps(new_rows)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO timetables (class_name, data) VALUES (?,?)", (class_name, value))
        conn.commit()
        conn.close()
        dialog.dismiss()
        self.load_cards()
        self.show_dialog("Success", f"Timetable for {class_name} updated!")
        # Notification to all students and teachers
        notify_all_students_and_teachers("Timetable Updated", f"Timetable for {class_name} has been updated.", "timetable")
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'

class DateSheetScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_term = "Term 1"
        self.terms_list = []
    def on_enter(self):
        self.load_terms()
    def load_terms(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT DISTINCT term_name FROM date_sheets ORDER BY term_name")
        terms = c.fetchall()
        conn.close()
        self.terms_list = [t[0] for t in terms] if terms else ["Term 1"]
        if not terms:
            classes = get_all_classes()
            default_datesheet = json.dumps([{"date": "", "day": "", "subject": ""} for _ in range(8)])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            for cls in classes:
                c.execute("INSERT OR IGNORE INTO date_sheets (class_name, term_name, data) VALUES (?, ?, ?)", (cls, "Term 1", default_datesheet))
            conn.commit()
            conn.close()
            self.terms_list = ["Term 1"]
        self.load_cards()
    def add_term(self):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can add terms.")
            return
        def add(term_name_field, dlg):
            term_name = term_name_field.text.strip()
            if not term_name:
                self.show_dialog("Error", "Please enter term name.")
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT term_name FROM date_sheets WHERE term_name=?", (term_name,))
            if c.fetchone():
                self.show_dialog("Error", "Term already exists.")
                conn.close()
                return
            classes = get_all_classes()
            default_datesheet = json.dumps([{"date": "", "day": "", "subject": ""} for _ in range(8)])
            for cls in classes:
                c.execute("INSERT INTO date_sheets (class_name, term_name, data) VALUES (?, ?, ?)", (cls, term_name, default_datesheet))
            conn.commit()
            conn.close()
            dlg.dismiss()
            self.load_terms()
            self.show_dialog("Success", f"Term '{term_name}' added.")
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=200)
        content.add_widget(MDLabel(text="Enter new term name", font_style="H6", halign="center", size_hint_y=None, height=40))
        term_field = MDTextField(hint_text="e.g., Term 2, Mid Term, Final", mode="rectangle", size_hint_y=None, height=50)
        content.add_widget(term_field)
        dlg = MDDialog(title="", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="ADD", md_bg_color=(0.05,0.28,0.63,1),
                                               on_release=lambda x: add(term_field, dlg))])
        dlg.open()
    def load_cards(self):
        container = self.ids.datesheet_container
        container.clear_widgets()
        term_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=10, padding=[10,5])
        term_spinner = MDTextField(hint_text="Select Term", text=self.current_term, mode="rectangle", size_hint_x=0.8, on_focus=self.on_term_focus)
        term_layout.add_widget(term_spinner)
        container.add_widget(term_layout)
        classes = get_all_classes()
        other_classes = [c for c in classes if c != 'Class 10']
        for class_name in other_classes:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT data FROM date_sheets WHERE class_name=? AND term_name=?", (class_name, self.current_term))
            row = c.fetchone()
            data = json.loads(row[0]) if row else [{"date": "", "day": "", "subject": ""} for _ in range(8)]
            preview = "No entries"
            for entry in data:
                if entry.get("date") and entry.get("subject"):
                    preview = f"{entry['date']} - {entry['subject']}"
                    break
            conn.close()
            card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(100),
                          radius=14, elevation=4, md_bg_color=get_class_color(class_name), padding=12, spacing=10)
            label = MDLabel(text=class_name, bold=True, font_style="H6", halign='center', valign='middle',
                            theme_text_color="Custom", text_color=(1,1,1,1))
            label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
            btn_layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_x=1, size_hint_y=None, height=dp(40))
            view_btn = MDRaisedButton(text="VIEW", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5, on_release=lambda x, cn=class_name: self.view_datesheet(cn))
            edit_btn = MDRaisedButton(text="EDIT", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5, on_release=lambda x, cn=class_name: self.edit_datesheet(cn))
            btn_layout.add_widget(view_btn)
            btn_layout.add_widget(edit_btn)
            card.add_widget(label)
            card.add_widget(btn_layout)
            container.add_widget(card)
        class_name = 'Class 10'
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT data FROM date_sheets WHERE class_name=? AND term_name=?", (class_name, self.current_term))
        row = c.fetchone()
        data = json.loads(row[0]) if row else [{"date": "", "day": "", "subject": ""} for _ in range(8)]
        preview = "No entries"
        for entry in data:
            if entry.get("date") and entry.get("subject"):
                preview = f"{entry['date']} - {entry['subject']}"
                break
        conn.close()
        card = MDCard(orientation='vertical', size_hint_x=1, size_hint_y=None, height=dp(100),
                      radius=14, elevation=4, md_bg_color=get_class_color(class_name), padding=12, spacing=10)
        label = MDLabel(text=class_name, bold=True, font_style="H6", halign='center', valign='middle',
                        theme_text_color="Custom", text_color=(1,1,1,1))
        label.bind(size=lambda l, s: setattr(l, 'text_size', (s[0], None)))
        btn_layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_x=1, size_hint_y=None, height=dp(40))
        view_btn = MDRaisedButton(text="VIEW", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5, on_release=lambda x, cn=class_name: self.view_datesheet(cn))
        edit_btn = MDRaisedButton(text="EDIT", md_bg_color=(0.05,0.28,0.63,1), size_hint_x=0.5, on_release=lambda x, cn=class_name: self.edit_datesheet(cn))
        btn_layout.add_widget(view_btn)
        btn_layout.add_widget(edit_btn)
        card.add_widget(label)
        card.add_widget(btn_layout)
        container.add_widget(card)
    def on_term_focus(self, instance, focus):
        if focus:
            def on_select(selected_term):
                self.current_term = selected_term
                self.load_cards()
            MDDialog(title="Select Term", text="", buttons=[MDFlatButton(text=t, on_release=lambda x, term=t: on_select(term)) for t in self.terms_list] + [MDFlatButton(text="Cancel", on_release=lambda x: x.dismiss())]).open()
    def view_datesheet(self, class_name):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT data FROM date_sheets WHERE class_name=? AND term_name=?", (class_name, self.current_term))
        row = c.fetchone()
        data = json.loads(row[0]) if row else [{"date": "", "day": "", "subject": ""} for _ in range(8)]
        conn.close()
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
        main_box = MDBoxLayout(orientation='vertical', spacing=12, size_hint_y=None, width=Window.width-dp(80))
        main_box.bind(minimum_height=main_box.setter('height'))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
        header.add_widget(MDLabel(text="Date (dd-mm)", bold=True, size_hint_x=0.30))
        header.add_widget(MDLabel(text="Day", bold=True, size_hint_x=0.30))
        header.add_widget(MDLabel(text="Subject", bold=True, size_hint_x=0.40))
        main_box.add_widget(header)
        for entry in data:
            row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
            row_box.add_widget(MDLabel(text=entry.get("date",""), size_hint_x=0.30, shorten=True))
            row_box.add_widget(MDLabel(text=entry.get("day",""), size_hint_x=0.30, shorten=True))
            row_box.add_widget(MDLabel(text=entry.get("subject",""), size_hint_x=0.40, shorten=True))
            main_box.add_widget(row_box)
        scroll.add_widget(main_box)
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=dp(450))
        content.add_widget(MDLabel(text=f"Date Sheet - {class_name} ({self.current_term})", font_style="H6", bold=True, halign="center", size_hint_y=None, height=40))
        content.add_widget(scroll)
        MDDialog(title="", type="custom", content_cls=content,
                 buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: x.dismiss())]).open()
    def edit_datesheet(self, class_name):
        app = MDApp.get_running_app()
        if not is_admin_or_principal_or_head(app.role):
            self.show_dialog("Access Denied", "Only Admin, Principal or Head can edit date sheets.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT data FROM date_sheets WHERE class_name=? AND term_name=?", (class_name, self.current_term))
        row = c.fetchone()
        data = json.loads(row[0]) if row else [{"date": "", "day": "", "subject": ""} for _ in range(8)]
        conn.close()
        scroll = ScrollView(size_hint=(1,1), do_scroll_x=False, do_scroll_y=True)
        main_box = MDBoxLayout(orientation='vertical', spacing=12, size_hint_y=None, width=Window.width-dp(80))
        main_box.bind(minimum_height=main_box.setter('height'))
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
        header.add_widget(MDLabel(text="Date (dd-mm)", bold=True, size_hint_x=0.30))
        header.add_widget(MDLabel(text="Day", bold=True, size_hint_x=0.30))
        header.add_widget(MDLabel(text="Subject", bold=True, size_hint_x=0.40))
        main_box.add_widget(header)
        row_fields = []
        for i in range(8):
            row_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=12)
            date_field = MDTextField(text=data[i]["date"], hint_text="DD-MM", mode="rectangle", size_hint_x=0.30)
            day_field = MDTextField(text=data[i]["day"], hint_text="Day", mode="rectangle", size_hint_x=0.30)
            subject_field = MDTextField(text=data[i]["subject"], hint_text="Subject", mode="rectangle", size_hint_x=0.40)
            row_box.add_widget(date_field)
            row_box.add_widget(day_field)
            row_box.add_widget(subject_field)
            main_box.add_widget(row_box)
            row_fields.append((date_field, day_field, subject_field))
        scroll.add_widget(main_box)
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, size_hint_y=None, height=dp(500))
        content.add_widget(MDLabel(text=f"Edit Date Sheet - {class_name} ({self.current_term})", font_style="H6", bold=True, halign="center", size_hint_y=None, height=40))
        content.add_widget(scroll)
        dlg = MDDialog(title="", type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="SAVE", md_bg_color=(0.2,0.7,0.3,1),
                                               on_release=lambda x: self.save_datesheet(class_name, row_fields, dlg))])
        dlg.open()
    def save_datesheet(self, class_name, row_fields, dialog):
        new_rows = []
        for date_field, day_field, subject_field in row_fields:
            new_rows.append({"date": date_field.text, "day": day_field.text, "subject": subject_field.text})
        value = json.dumps(new_rows)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO date_sheets (class_name, term_name, data) VALUES (?, ?, ?)", (class_name, self.current_term, value))
        conn.commit()
        conn.close()
        dialog.dismiss()
        self.load_cards()
        self.show_dialog("Success", f"Date sheet for {class_name} ({self.current_term}) updated!")
        # Notification to all students and teachers
        notify_all_students_and_teachers("Date Sheet Updated", f"Date sheet for {class_name} ({self.current_term}) has been updated.", "datesheet")
    def show_dialog(self, title, text):
        MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.dismiss())]).open()
    def back_to_dashboard(self):
        self.manager.current = 'dashboard'

class AttendanceViewScreen(Screen):
    def load_attendance(self):
        container = self.ids.attendance_container
        container.clear_widgets()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT date, class_name, slot, teacher_username, total_present, total_absent, total_students FROM attendance ORDER BY date DESC, slot DESC")
        records = c.fetchall()
        conn.close()
        if not records:
            container.add_widget(MDLabel(text="No attendance records found.", halign="center", theme_text_color="Secondary", size_hint_y=None, height=50))
        for rec in records:
            date, cls, slot, teacher, present, absent, total = rec
            card = MDCard(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=160, radius=12, elevation=3, md_bg_color=(1,1,1,1))
            card.add_widget(MDLabel(text=f"Date: {date}  |  Class: {cls}", bold=True, size_hint_y=None, height=30))
            card.add_widget(MDLabel(text=f"Slot: {slot}  |  Teacher: {teacher}", size_hint_y=None, height=25))
            card.add_widget(MDLabel(text=f"Present: {present}  |  Absent: {absent}  |  Total: {total}", size_hint_y=None, height=25))
            container.add_widget(card)
    def back_to_principal(self):
        self.manager.current = 'principal_panel'

# ---------------------------- MAIN APP ----------------------------
class AlHamdApp(MDApp):
    def build(self):
        if not is_connected():
            from kivy.core.window import Window
            Window.show()
            dialog = MDDialog(title="No Internet Connection", text="This app requires an active internet connection to work.\nPlease check your connection and restart the app.",
                              buttons=[MDFlatButton(text="Exit", on_release=lambda x: exit())])
            dialog.open()
            Clock.schedule_once(lambda dt: exit(), 1)
            return Widget()
        self.ensure_last_active_column()
        init_db()
        self.username = None
        self.role = None
        self.user_gender = None
        self.student_class = None
        self.lock_dialog_shown = False
        if not os.path.exists(PROFILE_PICS_DIR):
            os.makedirs(PROFILE_PICS_DIR)
        if not os.path.exists("assets/default_avatar.png"):
            os.makedirs("assets", exist_ok=True)
            try:
                from PIL import Image as PILImage
                img = PILImage.new('RGB', (100, 100), color=(200,200,200))
                img.save("assets/default_avatar.png")
            except:
                pass
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT value FROM school_settings WHERE key='theme'")
        theme_row = c.fetchone()
        conn.close()
        saved_theme = theme_row[0] if theme_row else 'light'
        if saved_theme == 'dark':
            self.theme_cls.theme_style = 'Dark'
        else:
            self.theme_cls.theme_style = 'Light'
        self.theme_cls.primary_palette = 'Blue'
        from kivy.core.window import Window
        Window.bind(on_keyboard=self.on_keyboard)
        return Builder.load_string(KV)
    
    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            current_screen = self.root.current_screen
            if hasattr(current_screen, 'on_back_button'):
                return current_screen.on_back_button()
            else:
                if len(self.root.history) > 1:
                    self.root.current = self.root.history[-2].name
                    return True
                else:
                    if self.root.current != 'dashboard':
                        self.root.current = 'dashboard'
                        return True
                    return False
        return False
    
    def ensure_last_active_column(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("ALTER TABLE users ADD COLUMN last_active TEXT DEFAULT ''")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        conn.close()

if __name__ == '__main__':
    AlHamdApp().run()           
