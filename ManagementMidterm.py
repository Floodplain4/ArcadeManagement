import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import random

# Data Structures
class GameMachine:
    def __init__(self, machine_id, machine_type, revenue=0):
        self.machine_id = machine_id
        self.machine_type = machine_type
        self.revenue = revenue

    def update_revenue(self, amount):
        self.revenue += amount

# Player class to hold player data
class Player:
    def __init__(self, username, score, arcade, revenue, most_played_game, event_placement):
        self.username = username
        self.score = score
        self.arcade = arcade
        self.revenue = revenue
        self.most_played_game = most_played_game
        self.event_placement = event_placement

class Event:
    def __init__(self, event_id, name, date):
        self.event_id = event_id
        self.name = name
        self.date = date

class LocalArcade:
    def __init__(self, arcade_id, location):
        self.arcade_id = arcade_id
        self.location = location
        self.machines = []
        self.players = []
        self.events = []

    def add_machine(self, machine):
        self.machines.append(machine)

    def add_player(self, player):
        self.players.append(player)

    def schedule_event(self, event):
        self.events.append(event)

    def calculate_revenue(self):
        return sum(machine.revenue for machine in self.machines)

class RegionalManager:
    def __init__(self, region_name):
        self.region_name = region_name
        self.local_arcades = []

    def add_arcade(self, arcade):
        self.local_arcades.append(arcade)

    def calculate_region_revenue(self):
        return sum(arcade.calculate_revenue() for arcade in self.local_arcades)

class GlobalManager:
    def __init__(self):
        self.regions = []

    def add_region(self, region):
        self.regions.append(region)

    def calculate_global_revenue(self):
        return sum(region.calculate_region_revenue() for region in self.regions)

# Database setup
def initialize_db():
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    
    # Create tables if they do not exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS arcades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arcade_id TEXT NOT NULL,
            location TEXT NOT NULL,
            region_id INTEGER,
            FOREIGN KEY (region_id) REFERENCES regions (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT NOT NULL,
            machine_type TEXT NOT NULL,
            token_cost REAL NOT NULL,
            arcade_id TEXT NOT NULL,
            FOREIGN KEY (arcade_id) REFERENCES arcades (arcade_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            username TEXT PRIMARY KEY,
            score INTEGER NOT NULL
        )
    ''')
    
    # Check if the token_cost column exists, and if not, add it
    cursor.execute("PRAGMA table_info(machines)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'token_cost' not in columns:
        cursor.execute("ALTER TABLE machines ADD COLUMN token_cost REAL NOT NULL DEFAULT 0")

    conn.commit()
    conn.close()

# Leaderboard setup and definition
leaderboard = {}  # Making this empty so the variable has definition

# Function to add a region to the database
def add_region_to_db(region_name):
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO regions (name) VALUES (?)', (region_name,))
    conn.commit()
    conn.close()

# Function to add an arcade to the database
def add_arcade_to_db(arcade_id, location, region_name):
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    
    # Get the region ID
    cursor.execute('SELECT id FROM regions WHERE name = ?', (region_name,))
    region_id = cursor.fetchone()
    
    if region_id:
        cursor.execute('INSERT INTO arcades (arcade_id, location, region_id) VALUES (?, ?, ?)', 
                       (arcade_id, location, region_id[0]))
        conn.commit()
        print(f"Arcade '{arcade_id}' added to region '{region_name}' in the database.")  # Debugging
    else:
        print(f"Region '{region_name}' not found in the database.")  # Debugging
    conn.close()

# Function to refresh the arcade list based on the selected region
def refresh_arcade_list(event=None):
    for item in arcade_list.get_children():
        arcade_list.delete(item)
    
    selected_region = region_dropdown.get()  # Get the selected region from the dropdown
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT arcade_id, location FROM arcades 
        WHERE region_id = (SELECT id FROM regions WHERE name = ?)
    ''', (selected_region,))
    
    rows = cursor.fetchall()
    for row in rows:
        arcade_list.insert('', 'end', values=row)
    
    conn.close()

# Function to open the edit arcade dialog
def open_edit_arcade_dialog(arcade_id, current_location):
    edit_window = tk.Toplevel(root)
    edit_window.title("Edit Arcade")
    
    ttk.Label(edit_window, text="Arcade ID:").grid(row=0, column=0, padx=10, pady=10)
    arcade_id_label = ttk.Label(edit_window, text=arcade_id)
    arcade_id_label.grid(row=0, column=1, padx=10, pady=10)
    
    ttk.Label(edit_window, text="New Location:").grid(row=1, column=0, padx=10, pady=10)
    new_location_entry = ttk.Entry(edit_window)
    new_location_entry.grid(row=1, column=1, padx=10, pady=10)
    new_location_entry.insert(0, current_location)  # Pre-fill with current location

    def save_changes():
        new_location = new_location_entry.get()
        if new_location:
            conn = sqlite3.connect('arcade_management.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE arcades 
                SET location = ? 
                WHERE arcade_id = ?
            ''', (new_location, arcade_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"Arcade '{arcade_id}' updated.")
            refresh_arcade_list()  # Refresh the arcade list
            edit_window.destroy()
        else:
            messagebox.showwarning("Input Error", "Please enter a new location.")

    save_button = ttk.Button(edit_window, text="Save", command=save_changes)
    save_button.grid(row=2, column=0, columnspan=2, pady=10)

# Function to edit the selected arcade
def edit_arcade():
    selected_item = arcade_list.selection()
    if selected_item:
        arcade_id = arcade_list.item(selected_item)['values'][0]  # Get the arcade ID from the selected item
        current_location = arcade_list.item(selected_item)['values'][1]  # Get the current location
        open_edit_arcade_dialog(arcade_id, current_location)
    else:
        messagebox.showwarning("Selection Error", "Please select an arcade to edit.")

# Function to delete the selected arcade
def delete_arcade():
    selected_item = arcade_list.selection()
    if selected_item:
        arcade_id = arcade_list.item(selected_item)['values'][0]  # Get the arcade ID from the selected item
        conn = sqlite3.connect('arcade_management.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM arcades WHERE arcade_id = ?', (arcade_id,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"Arcade '{arcade_id}' deleted.")
        refresh_arcade_list()  # Refresh the arcade list
    else:
        messagebox.showwarning("Selection Error", "Please select an arcade to delete.")

# Function to populate the region dropdown
def populate_region_dropdown():
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM regions')
    regions = [row[0] for row in cursor.fetchall()]
    region_dropdown['values'] = regions
    conn.close()

# Function to add an arcade
def add_arcade():
    arcade_id = arcade_id_entry.get()
    location = location_entry.get()
    selected_region = region_dropdown.get()
    
    if arcade_id and location and selected_region:
        add_arcade_to_db(arcade_id, location, selected_region)
        refresh_arcade_list()  # Refresh the arcade list after adding
        arcade_id_entry.delete(0, tk.END)  # Clear the entry
        location_entry.delete(0, tk.END)  # Clear the entry
    else:
        messagebox.showwarning("Input Error", "Please fill in all fields.")

# Function to add a machine to the database
def add_machine_to_db(machine_name, game_title, token_cost, arcade_id):
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO machines (machine_id, machine_type, token_cost, arcade_id) 
        VALUES (?, ?, ?, ?)
    ''', (machine_name, game_title, token_cost, arcade_id))
    conn.commit()
    conn.close()
    print(f"Machine '{machine_name}' added to arcade '{arcade_id}' in the database.")  # Debugging

# Function to refresh the machine list based on the selected arcade
def refresh_machine_list(event=None):
    for item in machine_list.get_children():
        machine_list.delete(item)

    selected_arcade = arcade_selection_dropdown.get()  # Get the selected arcade from the dropdown
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT machine_id, machine_type, token_cost FROM machines 
        WHERE arcade_id = ?
    ''', (selected_arcade,))
    
    rows = cursor.fetchall()
    for row in rows:
        machine_list.insert('', 'end', values=row)
    
    conn.close()

# Function to add a machine
def add_machine():
    machine_name = machine_name_entry.get()
    game_title = game_title_entry.get()
    token_cost = token_cost_entry.get()
    
    selected_arcade = arcade_selection_dropdown.get()  # Get the selected arcade from the dropdown
    if selected_arcade:
        if machine_name and game_title and token_cost:
            add_machine_to_db(machine_name, game_title, token_cost, selected_arcade)
            refresh_machine_list()  # Refresh the machine list after adding
            machine_name_entry.delete(0, tk.END)  # Clear the entry
            game_title_entry.delete(0, tk.END)  # Clear the entry
            token_cost_entry.delete(0, tk.END)  # Clear the entry
        else:
            messagebox.showwarning("Input Error", " Please fill in all fields.")
    else:
        messagebox.showwarning("Selection Error", "Please select an arcade to add a machine.")

# Function to open the edit machine dialog
def open_edit_machine_dialog(machine_id, current_type, current_cost):
    edit_window = tk.Toplevel(root)
    edit_window.title("Edit Machine")
    
    ttk.Label(edit_window, text="Machine ID:").grid(row=0, column=0, padx=10, pady=10)
    machine_id_label = ttk.Label(edit_window, text=machine_id)
    machine_id_label.grid(row=0, column=1, padx=10, pady=10)
    
    ttk.Label(edit_window, text="New Type:").grid(row=1, column=0, padx=10, pady=10)
    new_type_entry = ttk.Entry(edit_window)
    new_type_entry.grid(row=1, column=1, padx=10, pady=10)
    new_type_entry.insert(0, current_type)  # Pre-fill with current type

    ttk.Label(edit_window, text="New Token Cost:").grid(row=2, column=0, padx=10, pady=10)
    new_cost_entry = ttk.Entry(edit_window)
    new_cost_entry.grid(row=2, column=1, padx=10, pady=10)
    new_cost_entry.insert(0, current_cost)  # Pre-fill with current cost

    def save_changes():
        new_type = new_type_entry.get()
        new_cost = new_cost_entry.get()
        if new_type and new_cost:
            conn = sqlite3.connect('arcade_management.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE machines 
                SET machine_type = ?, token_cost = ? 
                WHERE machine_id = ?
            ''', (new_type, new_cost, machine_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"Machine '{machine_id}' updated.")
            refresh_machine_list()  # Refresh the machine list
            edit_window.destroy()
        else:
            messagebox.showwarning("Input Error", "Please enter both type and cost.")

    save_button = ttk.Button(edit_window, text="Save", command=save_changes)
    save_button.grid(row=3, column=0, columnspan=2, pady=10)

# Function to edit the selected machine
def edit_machine():
    selected_item = machine_list.selection()
    if selected_item:
        machine_id = machine_list.item(selected_item)['values'][0]  # Get the machine ID from the selected item
        current_type = machine_list.item(selected_item)['values'][1]  # Get the current type
        current_cost = machine_list.item(selected_item)['values'][2]  # Get the current cost
        open_edit_machine_dialog(machine_id, current_type, current_cost)
    else:
        messagebox.showwarning("Selection Error", "Please select a machine to edit.")

# Function to delete the selected machine
def delete_machine():
    selected_item = machine_list.selection()
    if selected_item:
        machine_id = machine_list.item(selected_item)['values'][0]  # Get the machine ID from the selected item
        conn = sqlite3.connect('arcade_management.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM machines WHERE machine_id = ?', (machine_id,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"Machine '{machine_id}' deleted.")
        refresh_machine_list()  # Refresh the machine list
    else:
        messagebox.showwarning("Selection Error", "Please select a machine to delete.")

# Function to populate the arcade selection dropdown
def populate_arcade_selection():
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT arcade_id FROM arcades')
    arcades = [row[0] for row in cursor.fetchall()]
    arcade_selection_dropdown['values'] = arcades
    conn.close()

# Function to display arcade data and revenue in Global Management
def display_global_management_data(region):
    for item in global_arcade_list.get_children():
        global_arcade_list.delete(item)

    arcade_data = fetch_arcade_data(region)
    revenue_data = calculate_revenue(arcade_data)

    for arcade in revenue_data:
        arcade_name, num_machines, avg_token_cost, total_revenue = arcade
        
        # Handle None values for avg_token_cost
        if avg_token_cost is None:
            avg_token_cost = 0.00  # Set to 0.00 if no machines are found

        global_arcade_list.insert('', 'end', values=(arcade_name, num_machines, f"{avg_token_cost:.2f}", f"${total_revenue:.2f}"))

def fetch_arcade_data(region):
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT arcades.arcade_id, COUNT(machines.machine_id), AVG(machines.token_cost) 
        FROM arcades 
        LEFT JOIN machines ON arcades.arcade_id = machines.arcade_id 
        WHERE arcades.region_id = (SELECT id FROM regions WHERE name = ?) 
        GROUP BY arcades.arcade_id
    ''', (region,))
    arcade_data = cursor.fetchall()
    conn.close()
    return arcade_data

def calculate_revenue(arcade_data):
    revenue_data = []
    for arcade in arcade_data:
        arcade_name, num_machines, avg_token_cost = arcade
        total_revenue = sum(random.uniform(50.00, 1200.00) for _ in range(num_machines))
        revenue_data.append((arcade_name, num_machines, avg_token_cost, total_revenue))
    return revenue_data

# Leaderboard Setup
usernames = [
    "ByteMe", "CodeCracker", "DebugDiva", "PixelPioneer", "ScriptSage",
    "BitBard", "DataDancer", "LoopGuru", "StackSamurai", "CacheCow",
    "NullPointer", "SyntaxSleuth", "VariableVixen", "QuantumQuokka", "BinaryBard",
    "FunctionFreak", "ArrayAce", "CompileCaptain", "LogicLynx", "ByteBandit",
    "CodeCoyote", "DebugDynamo", "PixelPirate", "ScriptSorcerer", "BitBuster",
    "DataDruid", "LoopLegend", "StackSultan", "CacheChameleon", "NullNinja",
    "SyntaxSphinx", "VariableVortex", "QuantumQuokka", "BinaryBison", "FunctionFox",
    "ArrayArcher", "CompileCrusader", "LogicLlama", "ByteBison", "CodeCobra",
    "DebugDolphin", "PixelPuma", "ScriptShark", "BitBuffalo", "DataDragon",
    "LoopLynx", "StackStallion", "CacheCheetah", "NullNarwhal", "SyntaxSwan",
    "VariableViper", "QuantumQuail", "BinaryBeetle", "FunctionFalcon", "ArrayAntelope",
    "CompileCoyote", "LogicLobster", "ByteBadger", "CodeCaterpillar", "DebugDuck",
    "PixelPenguin", "ScriptSquirrel", "BitBear", "DataDolphin", "LoopLemur",
    "StackSparrow", "CacheCrane", "NullNewt", "SyntaxSeal", "VariableVulture",
    "QuantumQuokka", "BinaryBumblebee", "FunctionFerret", "ArrayAardvark", "CompileCrocodile",
    "LogicLion", "ByteBumblebee", "CodeChameleon", "DebugDingo", "PixelParrot",
    "ScriptSeahorse", "BitBison", "DataDingo", "LoopLynx", "StackStarling",
    "CacheCobra", "NullNighthawk", "SyntaxSparrow", "VariableViper", "QuantumQuokka",
    "BinaryBison", "FunctionFrog", "ArrayArmadillo", "CompileCheetah", "LogicLynx"
]

# Load scores from the database
def load_scores():
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, score FROM leaderboard')
    scores = cursor.fetchall()
    conn.close()
    
    # Initialize the leaderboard with scores from the database
    global leaderboard  # Ensure you are modifying the global leaderboard variable
    leaderboard = {username: score for username, score in scores}

# Initialize scores for the top 50 usernames if the leaderboard is empty
def initialize_leaderboard():
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM leaderboard')
    count = cursor.fetchone()[0]
    
    global leaderboard  # Ensure you are modifying the global leaderboard variable
    if count == 0:  # If the leaderboard is empty, randomize scores
        leaderboard = {username: random.randint(1, 50000) for username in random.sample(usernames, 50)}
        save_scores()  # Save the randomized scores to the database
    else:
        load_scores()  # Load existing scores from the database

    conn.close()  # Ensure the connection is closed

# Save scores for the leaderboard
def save_scores():
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()    

    for username, score in leaderboard.items():
        cursor.execute('INSERT OR REPLACE INTO leaderboard (username, score) VALUES (?, ?)', (username, score))    

    conn.commit()
    conn.close()

# Initialize the leaderboard
initialize_leaderboard()

# Function to update scores randomly
def update_scores():
    username = random.choice(list(leaderboard.keys()))
    change = random.randint(-1000, 1000)  # Randomly add or remove points
    leaderboard[username] = max(0, leaderboard[username] + change)  # Ensure score doesn't go below 0
    display_leaderboard()
    root.after(30000, update_scores)  # Schedule next update in 30 seconds

# Function to display the leaderboard
def display_leaderboard():
    for item in leaderboard_list.get_children():
        leaderboard_list.delete(item)
    
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    for username, score in sorted_leaderboard:
        leaderboard_list.insert('', 'end', values=(username, score))

# Function to refresh scores for a random number of users
def refresh_scores():
    save_scores()  # Save current scores to the database
    
    num_updates = random.randint(3, 8)  # Choose a random number of scores to update
    for _ in range(num_updates):
        username = random.choice(list(leaderboard.keys()))
        change = random.randint(-5000, 5000)  # Randomly add or subtract points
        leaderboard[username] = max(0, leaderboard[username] + change)  # Ensure score doesn't go below 0
    display_leaderboard()

# Create the main window
root = tk.Tk()
root.title("International Gaming Arcade Management System")
root.geometry("800x600")

# Initialize the database
initialize_db()

# Add regions to the database
regions = ["North America", "Europe East", "Europe West", "Asia", "Other"]
for region in regions:
    add_region_to_db(region)

# Create a Notebook widget
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

# Create frames for each tab
operations_frame = ttk.Frame(notebook)
leaderboard_frame = ttk.Frame(notebook)
players_frame = ttk.Frame(notebook)
events_frame = ttk.Frame(notebook)
revenue_frame = ttk.Frame(notebook)

# Add tabs to the notebook
notebook.add(operations_frame, text="Managing Operations")
notebook.add(leaderboard_frame, text="Global Leaderboard")
notebook.add(players_frame, text="Player Tracking")
notebook.add(events_frame, text="Event Scheduling")
notebook.add(revenue_frame, text="Revenue Tracking")

# Create a Notebook widget for sub-tabs in Managing Operations
operations_notebook = ttk.Notebook(operations_frame)
operations_notebook.pack(expand=True, fill='both')

# Create frames for each sub-tab
global_frame = ttk.Frame(operations_notebook)
regional_frame = ttk.Frame(operations_notebook)
local_frame = ttk.Frame(operations_notebook)

# Add sub-tabs to the operations notebook
operations_notebook.add(global_frame, text="Global Management")
operations_notebook.add(regional_frame, text="Regional Management")
operations_notebook.add(local_frame, text="Local Management")

# Global Management
ttk.Label(global_frame, text="Global Management").pack(pady=10)
ttk.Label(global_frame, text="Select Region:").pack(pady=5)
region_dropdown_global = ttk.Combobox(global_frame, values=regions, state='readonly')
region_dropdown_global.pack(pady=5)
region_dropdown_global.bind("<<ComboboxSelected>>", lambda event: display_global_management_data(region_dropdown_global.get()))

# Global Arcade List
global_arcade_list = ttk.Treeview(global_frame, columns=('Arcade Name', 'Number of Machines', 'Avg Token Cost', 'Total Revenue'), show='headings')
global_arcade_list.heading('Arcade Name', text='Arcade Name')
global_arcade_list.heading('Number of Machines', text='Number of Machines')
global_arcade_list.heading('Avg Token Cost', text='Avg Token Cost')
global_arcade_list.heading('Total Revenue', text='Total Revenue')
global_arcade_list.pack(expand=True, fill='both')

# Regional Management
ttk.Label(regional_frame, text="Regional Management").pack(pady=10)
ttk.Label(regional_frame, text="Select Region:").pack(pady=5)
region_dropdown = ttk.Combobox(regional_frame, values=regions, state='readonly')
region_dropdown.pack(pady=5)

ttk.Label(regional_frame, text="Arcade ID:").pack(pady=5)
arcade_id_entry = ttk.Entry(regional_frame)
arcade_id_entry.pack(pady=5)
ttk.Label(regional_frame, text="Location:").pack(pady=5)
location_entry = ttk.Entry(regional_frame)
location_entry.pack(pady=5)

# Buttons for Add, Edit, and Delete Arcade
button_frame = ttk.Frame(regional_frame)
button_frame.pack(pady=5)

add_arcade_button = ttk.Button(button_frame, text="Add Arcade", command=add_arcade)
add_arcade_button.grid(row=0, column=0, padx=5)

edit_arcade_button = ttk.Button(button_frame, text="Edit Arcade", command=edit_arcade)
edit_arcade_button.grid(row=0, column=1, padx=5)

delete_arcade_button = ttk.Button(button_frame, text="Delete Arcade", command=delete_arcade)
delete_arcade_button.grid(row=0, column=2, padx=5)

# Arcade List for Regional Management
arcade_list = ttk.Treeview(regional_frame, columns=('Arcade ID', 'Location'), show='headings')
arcade_list.heading('Arcade ID', text='Arcade ID')
arcade_list.heading('Location', text='Location')
arcade_list.pack(expand=True, fill='both')

# Local Management UI
ttk.Label(local_frame, text="Local Management").grid(row=0, column=0, columnspan=3, pady=10)

ttk.Label(local_frame, text="Select Arcade:").grid(row=1, column=0, padx=5, pady=5)
arcade_selection_dropdown = ttk.Combobox(local_frame, state='readonly')
arcade_selection_dropdown.grid(row=1, column=1, padx=5, pady=5)

# Create entries for machine details
ttk.Label(local_frame, text="Machine Name:").grid(row=2, column=0, padx=5, pady=5)
machine_name_entry = ttk.Entry(local_frame)
machine_name_entry.grid(row=2, column=1, padx=5, pady=5)

ttk.Label(local_frame, text="Game Title:").grid(row=3, column=0, padx=5, pady=5)
game_title_entry = ttk.Entry(local_frame)
game_title_entry.grid(row=3, column=1, padx=5, pady=5)

ttk.Label(local_frame, text="Token Cost:").grid(row=4, column=0, padx=5, pady=5)
token_cost_entry = ttk.Entry(local_frame)
token_cost_entry.grid(row=4, column=1, padx=5, pady=5)

# Button frame for machine operations
button_frame = ttk.Frame(local_frame)
button_frame.grid(row=5, column=0, columnspan=2, pady=10)

# Button to add machine
add_machine_button = ttk.Button(button_frame, text="Add Machine", command=add_machine)
add_machine_button.grid(row=0, column=0, padx=5)

# Button to edit machine
edit_machine_button = ttk.Button(button_frame, text="Edit Machine", command=edit_machine)
edit_machine_button.grid(row=0, column=1, padx=5)

# Button to delete machine
delete_machine_button = ttk.Button(button_frame, text="Delete Machine", command=delete_machine)
delete_machine_button.grid(row=0, column=2, padx=5)

# Machine List for Local Management
machine_list = ttk.Treeview(local_frame, columns=('Machine Name', 'Game Title', 'Token Cost'), show='headings')
machine_list.heading('Machine Name', text='Machine Name')
machine_list.heading('Game Title', text='Game Title')
machine_list.heading('Token Cost', text='Token Cost')
machine_list.grid(row=6, column=0, columnspan=2, sticky='nsew')

# Populate the arcade selection dropdown
def populate_arcade_selection():
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT arcade_id FROM arcades')
    arcades = [row[0] for row in cursor.fetchall()]
    arcade_selection_dropdown['values'] = arcades
    conn.close()

# Call the function to populate the arcade selection dropdown
populate_arcade_selection()

# Refresh the arcade list on startup
refresh_arcade_list()

# Bind the region dropdown selection to refresh the arcade list
region_dropdown.bind("<<ComboboxSelected>>", refresh_arcade_list)

# Bind the arcade selection dropdown to refresh the machine list
arcade_selection_dropdown.bind("<<ComboboxSelected>>", refresh_machine_list)

# Leaderboard List
leaderboard_list = ttk.Treeview(leaderboard_frame, columns=('Username', 'Score'), show='headings')
leaderboard_list.heading('Username', text='Username')
leaderboard_list.heading('Score', text='Score')
leaderboard_list.pack(expand=True, fill='both')

# Refresh Button for Leaderboard
refresh_button = ttk.Button(leaderboard_frame, text="Refresh Scores", command=refresh_scores)
refresh_button.pack(pady=10)

# Function to reset the leaderboard
def reset_leaderboard():
    # Clear existing scores from the database
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM leaderboard')  # Delete all entries in the leaderboard
    conn.commit()
    conn.close()

    # Reinitialize the leaderboard with random scores
    global leaderboard
    leaderboard = {username: random.randint(1, 50000) for username in random.sample(usernames, 50)}
    save_scores()  # Save the new randomized scores to the database
    display_leaderboard()  # Update the display to show the new scores    

# Reset Button for Leaderboard
reset_button = ttk.Button(leaderboard_frame, text="Reset Leaderboard", command=reset_leaderboard)
reset_button.pack(pady=10)

# Function to get arcade machines from the database
def get_arcade_machines():
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT machine_id FROM machines')  # Adjust the query as needed
    arcade_machines = [row[0] for row in cursor.fetchall()]  # Fetch all machine IDs
    conn.close()
    return arcade_machines

#Function to gather arcade names
def get_arcade_names():
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT arcade_id FROM arcades')  # Adjust the query as needed
    arcade_names = [row[0] for row in cursor.fetchall()]  # Fetch all arcade IDs
    conn.close()
    return arcade_names

#Function to gather player scores
def get_player_data():
    conn = sqlite3.connect('arcade_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, score FROM leaderboard')  # Adjust the query as needed
    player_data = cursor.fetchall()  # Fetch all player data
    conn.close()
    return player_data

# Function to generate player data
def generate_player_data():
    players = []
    arcade_machines = get_arcade_machines()  # Get the list of machine IDs
    arcade_names = get_arcade_names()  # Get the list of arcade names
    
    # Fetch player data from the database
    player_scores = get_player_data()  # Get player data from the database
    
    for username, score in player_scores:
        arcade = random.choice(arcade_names)  # Use dynamic arcade names
        revenue = round(score / random.uniform(1.0, 2.0) * .25, 2)  # Calculate revenue
        most_played_game = random.choice(arcade_machines)  # Randomly select a game
        event_placement = min(max(1, 64 - (score // 781.25)), 64)  # Calculate event placement based on score
        players.append(Player(username, score, arcade, revenue, most_played_game, event_placement))
    return players

# Generate player data
player_data = generate_player_data()


# Player Tracking List
player_tracking_list = ttk.Treeview(players_frame, columns=('Player', 'Score', 'Revenue', 'Arcade', 'Most Played Game', 'Event Placement', 'Tournament Winner'), show='headings')
player_tracking_list.heading('Player', text='Player')
player_tracking_list.heading('Score', text='Score')
player_tracking_list.heading('Revenue', text='Revenue')
player_tracking_list.heading('Arcade', text='Arcade')
player_tracking_list.heading('Most Played Game', text='Most Played Game')
player_tracking_list.heading('Event Placement', text='Event Placement')
player_tracking_list.heading('Tournament Winner', text='Tournament Winner')
player_tracking_list.pack(expand=True, fill='both')

# Function to display player data in the Player Tracking tab
def display_player_tracking():
    for item in player_tracking_list.get_children():
        player_tracking_list.delete(item)

    # Sort players by revenue
    sorted_players = sorted(player_data, key=lambda p: p.revenue, reverse=True)

    for player in sorted_players:
        crown_symbol = "👑" if player.event_placement == 1 else ""
        player_tracking_list.insert('', 'end', values=(player.username, player.score, f"${player.revenue:.2f}", player.arcade, player.most_played_game, player.event_placement, crown_symbol))

# Function to display player tracking
display_player_tracking()

# Start the score updates
update_scores()

# Start the application
root.mainloop()
