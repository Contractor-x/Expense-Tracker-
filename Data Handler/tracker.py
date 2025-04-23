import pandas as pd
import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pymysql
from dotenv import load_dotenv
print("MySQL imported successfully")

load_dotenv()
connection = pymysql.connect(
    host  = os.environ.get('DB_HOST'),
    user  = os.environ.get('DB_USER'),
    password =   os.environ.get('DB_PASSWORD'),
    database = os.environ.get('DB_NAME')
)
print("Connection successful")

cursor = connection.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
user_id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(255) NOT NULL UNIQUE,
user_email VARCHAR(255) NOT NULL UNIQUE,
password VARCHAR(255) NOT NULL,
created_at DATETIME NOT NULL,
last_login DATETIME NULL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS expense (
expense_id INT AUTO_INCREMENT PRIMARY KEY,
user_id INT NOT NULL,
amount DECIMAL(10, 2) NOT NULL,
category VARCHAR(255) NOT NULL,
date DATE NOT NULL,
note TEXT,
payment_method VARCHAR(255),
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS income (
income_id INT AUTO_INCREMENT PRIMARY KEY,
user_id INT NOT NULL,
amount DECIMAL(10, 2) NOT NULL,
source VARCHAR(255) NOT NULL,
date DATE NOT NULL,
note TEXT,
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
)
""")

def register_user(cursor, connection):
    print("\nInsert User Data")
    username = input("Enter username: ").strip()
    user_email = input("Enter email: ").strip()
    password = input("Enter password: ").strip()
    confirm_password = input("Confirm password: ").strip()
    if password != confirm_password:
        print("Passwords do not match. Insertion failed.")
        return False
    cursor.execute("SELECT * FROM users WHERE username=%s OR user_email=%s", (username, user_email))
    if cursor.fetchone():
        print("Username or email already exists. Insertion failed.")
        return False
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO users (username, user_email, password, created_at, last_login) VALUES (%s, %s, %s, %s, %s)",
        (username, user_email, password, created_at, None)
    )
    connection.commit()
    user_id = cursor.lastrowid
    print("Your registration was successful.")
    print(f"Welcome, {username}! Your user ID is {user_id}.")
    return user_id


def login_user(cursor, connection):
    print("\nUser Login")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    cursor.execute("SELECT user_id FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()
    if user:
        user_id = user[0]
        last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE users SET last_login=%s WHERE user_id=%s", (last_login, user_id))
        connection.commit()
        print(f"Login successful. Welcome, {username}!")
        # Display expense pie chart for the logged-in user
        (cursor, user_id)
        return user_id
    else:
        print("Invalid username or password.")
        return None


def expense_data(cursor, connection, user_id):
    print("\nInsert Expense Data")
    try:
        amount = float(input("Enter expense amount: ").strip())
        category = input("Enter expense category: ").strip()
        date = input("Enter date (YYYY-MM-DD): ").strip()
        note = input("Enter note (optional): ").strip()
        payment_method = input("Enter payment method (optional): ").strip()

        # Validate date format
        from datetime import datetime
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            return False

        cursor.execute(
            """
            INSERT INTO expense (user_id, amount, category, date, note, payment_method)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, amount, category, date, note, payment_method)
        )
        connection.commit()
        print("Expense data inserted successfully.")
        # Check budget status after expense insertion
        check_budget_status(cursor, user_id)
        return True
    except Exception as e:
        print(f"Failed to insert expense data: {e}")
        return False

def income_data(cursor, connection, user_id):
    print("\nInsert Income Data")
    try:
        amount = float(input("Enter income amount: ").strip())
        source = input("Enter income source: ").strip()
        date = input("Enter date (YYYY-MM-DD): ").strip()
        note = input("Enter note (optional): ").strip()

        # Validate date format
        from datetime import datetime
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            return False

        cursor.execute(
            """
            INSERT INTO income (user_id, amount, source, date, note)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, amount, source, date, note)
        )
        connection.commit()
        print("Income data inserted successfully.")
        # Check budget status after income insertion
        check_budget_status(cursor, user_id)
        return True
    except Exception as e:
        print(f"Failed to insert income data: {e}")
        return False


def expense_bar_chart(cursor, user_id, username):
    cursor.execute(
        """
        SELECT category, SUM(amount) as total_amount
        FROM expense
        WHERE user_id = %s
        GROUP BY category
        """,
        (user_id,)
    )
    results = cursor.fetchall()
    if not results:
        print("No expense data found for this user.")
        return

    categories = [row[0] for row in results]
    amounts = [float(row[1]) for row in results]
    
    # Calculate percentages for annotations
    total = sum(amounts)
    percentages = [(amount/total)*100 for amount in amounts]
    
    # Sort data by amount in descending order
    sorted_data = sorted(zip(categories, amounts, percentages), key=lambda x: x[1], reverse=True)
    categories, amounts, percentages = zip(*sorted_data)
    
    fig , ax = plt.subplots()
    
    # Create bar colors
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA62B', '#A0D995']
    
    # Create the bar chart
    bars = ax.bar(categories, amounts, color=colors[:len(categories)])
    
    # Add percentage labels on top of each bar
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2.,
            height + 0.1,
            f'{percentages[i]:.1f}%',
            ha='center', 
            va='bottom',
            fontweight='bold'
        )
    
    # Add value labels inside bars for larger ones
    for i, bar in enumerate(bars):
        height = bar.get_height()
        if height > max(amounts) * 0.05:  # Only add text for bars that are large enough
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height/2,
                f'{amounts[i]:.2f}',
                ha='center', 
                va='center',
                color='white',
                fontweight='bold'
            )
    
    ax.set_title(f"{username} This is your expense Distribution", fontsize=16)
    ax.set_xlabel("Category", fontsize=12)
    ax.set_ylabel("Amount ($)", fontsize=12)
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    fig.set_size_inches(12, 8)
    fig.tight_layout()
    
    plt.show()



if __name__ == "__main__":
    user_id = None

    def check_budget_status(cursor, user_id):
        cursor.execute(
            """
            SELECT
                (SELECT IFNULL(SUM(amount), 0) FROM income WHERE user_id = %s) AS total_income,
                (SELECT IFNULL(SUM(amount), 0) FROM expense WHERE user_id = %s) AS total_expense
            """,
            (user_id, user_id)
        )
        result = cursor.fetchone()
        total_income = float(result[0])
        total_expense = float(result[1])
        print(f"\nBudget Status: Total Income = ${total_income:.2f}, Total Expense = ${total_expense:.2f}")
        if total_expense > total_income:
            print("Alert: Your expenses exceed your income!")

    while True:
        print("\nOptions:")
        print("1. Register")
        print("2. Login")
        print("3. Add Expenses")
        print("4. Add Income")
        print("5. View Expense Bar Chart")
        print("6. View Budget Status")
        print("7. Quit")
        choice = input("Enter choice: ").strip()
        if choice == '1':
            user_id = register_user(cursor, connection)
            if user_id:
                print(f"User ID {user_id} registered successfully.")
        elif choice == '2':
            user_id = login_user(cursor, connection)
            if user_id:
                print(f"User ID {user_id} logged in successfully.")
        elif choice == '3':
            if user_id:
                expense_data(cursor, connection, user_id)
            else:
                print("Please login first to add expenses.")
        elif choice == '4':
            if user_id:
                income_data(cursor, connection, user_id)
            else:
                print("Please login first to add income.")
        elif choice == '5':
            if user_id:
                # Retrieve username for the logged-in user
                cursor.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()
                if result:
                    username = result[0]
                    expense_bar_chart(cursor, user_id, username)
                else:
                    print("Username not found for the given user ID.")
            else:
                print("Please login first to view expense Bar chart.")
        elif choice == '6':
            if user_id:
                check_budget_status(cursor, user_id)
            else:
                print("Please login first to view budget status.")
        elif choice == '7':
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")
