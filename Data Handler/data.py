import pandas as pd
import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

DATA_FILE = "expenses.csv"
REQUIRED_COLUMNS = ["Amount", "Category", "Note", "Date"]

INCOME_FILE = "income.csv"
INCOME_COLUMNS = ["Month", "Income"]

def validate_expense(amount, category, date):
    """Validate expense data before saving"""
    try:
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Amount must be a positive number")
        if not category or not isinstance(category, str):
            raise ValueError("Category must be a non-empty string")
        datetime.strptime(date, "%Y-%m-%d")  # Validate date format
        return True
    except ValueError as e:
        print(f"Validation error: {e}")
        return False

def load_data():
    """Load expense data with error handling"""
    try:
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            # Validate loaded data structure
            if not all(col in df.columns for col in REQUIRED_COLUMNS):
                raise ValueError("CSV file has incorrect structure")
            return df
        return pd.DataFrame(columns = REQUIRED_COLUMNS)
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(columns = REQUIRED_COLUMNS)

def save_data(df):
    """Save data with error handling"""
    try:
        df.to_csv(DATA_FILE, index=False)
    except Exception as e:
        print(f"Error saving data: {e}")
        raise

def add_expense(amount, category, note="", date=None):
    """Add expense with validation"""
    date = date or datetime.now().strftime("%Y-%m-%d")
    if not validate_expense(amount, category, date):
        return False
    
    try:
        df = load_data()
        new_row = pd.DataFrame([{
            "Amount": float(amount),
            "Category": category,
            "Note": note,
            "Date": date
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        return True
    except Exception as e:
        print(f"Error adding expense: {e}")
        return False

def add_expenses_batch(expenses):
    """Add multiple expenses efficiently"""
    valid_expenses = [
        exp for exp in expenses 
        if validate_expense(exp["amount"], exp["category"], exp.get("date", ""))
    ]
    if not valid_expenses:
        return False
        
    try:
        df = load_data()
        new_rows = pd.DataFrame([{
            "Amount": float(exp["amount"]),
            "Category": exp["category"],
            "Note": exp.get("note", ""),
            "Date": exp.get("date", datetime.now().strftime("%Y-%m-%d"))
        } for exp in valid_expenses])
        df = pd.concat([df, new_rows], ignore_index=True)
        save_data(df)
        return True
    except Exception as e:
        print(f"Error adding batch expenses: {e}")
        return False

def filter_data(category=None, start_date=None, end_date=None):
    """Filter data with date parsing optimization"""
    df = load_data()
    if df.empty:
        return df
        
    try:
        if start_date:
            df = df[pd.to_datetime(df["Date"]) >= pd.to_datetime(start_date)]
        if end_date:
            df = df[pd.to_datetime(df["Date"]) <= pd.to_datetime(end_date)]
        if category:
            df = df[df["Category"] == category]
        return df
    except Exception as e:
        print(f"Error filtering data: {e}")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

def get_summary_stats():
    """Get spending statistics"""
    df = load_data()
    if df.empty:
        return {}
        
    return {
        "total_spent": df["Amount"].sum(),
        "average_spending": df["Amount"].mean(),
        "category_counts": df["Category"].value_counts().to_dict(),
        "daily_average": df.groupby("Date")["Amount"].sum().mean()
    }

def get_monthly_breakdown():
    """Get monthly spending breakdown"""
    df = load_data()
    if df.empty:
        return {}
        
    df["Month"] = pd.to_datetime(df["Date"]).dt.to_period("M")
    monthly = df.groupby("Month")["Amount"].sum()
    return monthly.to_dict()


def load_income_data():
    """Load monthly income data with error handling"""
    try:
        if os.path.exists(INCOME_FILE):
            df = pd.read_csv(INCOME_FILE)
            if not all(col in df.columns for col in INCOME_COLUMNS):
                raise ValueError("Income CSV file has incorrect structure")
            return df
        return pd.DataFrame(columns=INCOME_COLUMNS)
    except Exception as e:
        print(f"Error loading income data: {e}")
        return pd.DataFrame(columns=INCOME_COLUMNS)

def save_income_data(df):
    """Save monthly income data with error handling"""
    try:
        df.to_csv(INCOME_FILE, index=False)
    except Exception as e:
        print(f"Error saving income data: {e}")
        raise

def add_income(month, income):
    """Add or update income for a given month"""
    try:
        df = load_income_data()
        month = str(month)
        income = float(income)
        if month in df["Month"].values:
            df.loc[df["Month"] == month, "Income"] = income
        else:
            new_row = pd.DataFrame([{"Month": month, "Income": income}])
            df = pd.concat([df, new_row], ignore_index=True)
        save_income_data(df)
        return True
    except Exception as e:
        print(f"Error adding income: {e}")
        return False

def get_monthly_income_breakdown():
    """Get monthly income breakdown"""
    df = load_income_data()
    if df.empty:
        return {}
    df["Month"] = df["Month"].astype(str)
    income_dict = df.set_index("Month")["Income"].to_dict()
    return income_dict

def plot_monthly_trend():
    """Generate line plot of monthly spending and income"""
    expense_monthly = get_monthly_breakdown()
    income_monthly = get_monthly_income_breakdown()
    
    if not expense_monthly and not income_monthly:
        print("No data to plot")
        return
    
    # Convert expense_monthly keys (Period) to string "YYYY-MM"
    expense_months_str = [str(m) if not isinstance(m, str) else m for m in expense_monthly.keys()]
    income_months_str = [str(m) if not isinstance(m, str) else m for m in income_monthly.keys()]
    
    # Combine months from both datasets
    all_months = sorted(set(expense_months_str + income_months_str))
    
    expense_values = [expense_monthly.get(pd.Period(month), 0) for month in all_months]
    income_values = [income_monthly.get(month, 0) for month in all_months]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(all_months, expense_values, marker='o', linestyle='--', color='green', linewidth=2, label='Expenses')
    ax.plot(all_months, income_values, marker='v', linestyle='--', color='blue', linewidth=2, label='Income')
    ax.set_title("Monthly Spending and Income Trend", pad=20, fontsize=14)
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Amount", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='x', rotation=45)
    ax.legend()
    fig.tight_layout()
    print("Displaying plot now...")
    plt.show()
    print("Plot display finished.")


def plot_pie_chart():
    """Generate a simple pie chart showing spending by category"""
    category_data = get_category_breakdown()
    if not category_data:
        print("No data to plot")
        return
    
    categories = list(category_data.keys())
    amounts = list(category_data.values())
    
    # Create figure
    fig, ax = plt.subplots()
    
    # Create simple pie chart
    ax.pie(
        amounts,
        labels=categories,
        autopct='%1.1f%%',
        startangle=90
    )
    
    # Set title
    ax.set_title("Spending by Category", pad = 20)
    
    # Ensure the pie chart is circular
    plt.axis('equal')
    
    plt.show()
def get_category_breakdown():
    """Get spending breakdown by category"""
    df = load_data()
    if df.empty:
        return {}
    
    category_spending = df.groupby("Category")["Amount"].sum()
    return category_spending.to_dict()

if __name__ == "__main__":
    print("Expense Tracker - Enter your expenses and monthly income")
    print("--------------------------------------------------------")
    
    while True:
        try:
            choice = input("Enter 'e' to add expense, 'i' to add income, or 'q' to quit: ").strip().lower()
            if choice == 'e':
                amount = float(input("Enter expense amount: "))
                category = input("Enter expense category: ")
                note = input("Enter a note (optional): ")
                date = input("Enter date (YYYY-MM-DD, leave blank for today): ") or None
                if add_expense(amount, category, note, date):
                    print("Expense added successfully!")
                else:
                    print("Failed to add expense.")
            elif choice == 'i':
                month = input("Enter month (YYYY-MM): ")
                income = float(input("Enter income amount for the month: "))
                if add_income(month, income):
                    print("Income added successfully!")
                else:
                    print("Failed to add income.")
            elif choice == 'q':
                break
            else:
                print("Invalid choice. Please enter 'e', 'i', or 'q'.")
        except ValueError as e:
            print(f"Invalid input: {e}. Please try again.")
    
    print("\nAll expenses:")
    print(load_data())
    
    print("\nAll income:")
    print(load_income_data())
    
    print("\nSummary statistics:")
    print(get_summary_stats())
    
    print("\nMonthly breakdown:")
    print(get_monthly_breakdown())
    
    plot_monthly_trend()
    plot_pie_chart()
