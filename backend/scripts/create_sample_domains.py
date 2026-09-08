"""
Generates 4 diverse domain datasets in backend/data/sample_domains/:
1. retail_sales.csv (E-commerce / Retail)
2. hr_workforce.csv (Human Resources / Payroll)
3. finance_expenses.csv (Corporate Finance / OpEx)
4. inventory_supply.csv (Supply Chain / Warehouse)
"""

import os
import random
import pandas as pd
from datetime import datetime, timedelta

def generate_domains():
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_domains")
    os.makedirs(output_dir, exist_ok=True)
    random.seed(42)

    # ----------------------------------------------------
    # 1. Retail Sales
    # ----------------------------------------------------
    products = [
        ("Electronics", "Smartphone Pro X", 899.99),
        ("Electronics", "Wireless Noise-Cancel Headphones", 199.99),
        ("Electronics", "4K Ultra Gaming Monitor", 349.50),
        ("Electronics", "Smart Fitness Tracker", 79.99),
        ("Apparel", "Waterproof Hiking Jacket", 120.00),
        ("Apparel", "Running Performance Shoes", 95.00),
        ("Apparel", "Cotton Casual Hoodie", 45.00),
        ("Home & Kitchen", "Espresso Coffee Machine", 249.00),
        ("Home & Kitchen", "Air Purifier HEPA Filter", 129.99),
        ("Home & Kitchen", "Non-Stick Cookware Set", 89.95),
        ("Sports", "Yoga Mat Premium", 35.00),
        ("Sports", "Adjustable Dumbbell Set", 150.00),
    ]
    regions = ["Western", "Central", "Southern", "Northern", "Eastern"]
    reps = ["Kasun Perera", "Amara Silva", "Nimal Fernando", "Dinithi Jayasinghe", "Rohan De Silva"]
    payment_methods = ["Credit Card", "Bank Transfer", "Cash on Delivery", "PayPal"]

    retail_rows = []
    base_date = datetime(2024, 1, 1)
    for i in range(1, 61):
        cat, prod, unit_p = random.choice(products)
        qty = random.randint(1, 8)
        disc = random.choice([0.0, 0.05, 0.10, 0.15, 0.20])
        gross = round(qty * unit_p, 2)
        sales_amt = round(gross * (1 - disc), 2)
        cost_p = unit_p * random.uniform(0.55, 0.75)
        profit = round(sales_amt - (qty * cost_p), 2)
        t_date = base_date + timedelta(days=random.randint(0, 180))

        retail_rows.append({
            "Transaction_ID": f"TXN-{1000 + i}",
            "Date": t_date.strftime("%Y-%m-%d"),
            "Product_Category": cat,
            "Product_Name": prod,
            "Sales_Amount": sales_amt,
            "Quantity": qty,
            "Unit_Price": unit_p,
            "Discount_Pct": disc,
            "Region": random.choice(regions),
            "Sales_Rep": random.choice(reps),
            "Payment_Method": random.choice(payment_methods),
            "Profit": profit
        })
    df_retail = pd.DataFrame(retail_rows)
    retail_path = os.path.join(output_dir, "retail_sales.csv")
    df_retail.to_csv(retail_path, index=False)
    print(f"Created {retail_path} ({len(df_retail)} rows)")

    # ----------------------------------------------------
    # 2. HR & Workforce
    # ----------------------------------------------------
    depts = {
        "Engineering": [("Software Engineer", 120000), ("Senior Architect", 175000), ("QA Engineer", 85000), ("DevOps Specialist", 130000)],
        "Marketing": [("Content Strategist", 70000), ("SEO Specialist", 65000), ("Marketing Lead", 110000)],
        "Sales": [("Account Executive", 80000), ("Sales Director", 150000), ("BDR Specialist", 55000)],
        "Human Resources": [("HR Generalist", 65000), ("Talent Recruiter", 72000), ("HR Director", 135000)],
        "Finance": [("Financial Analyst", 85000), ("Accountant", 75000), ("Finance Manager", 140000)]
    }
    locations = ["Colombo", "Kandy", "Galle", "Remote - Sri Lanka", "Singapore"]
    first_names = ["Kavinda", "Thisara", "Shanika", "Bhanuka", "Dilani", "Suranga", "Nadeesha", "Pathum", "Sachini", "Mahesh"]
    last_names = ["Bandara", "Wickramasinghe", "Rathnayake", "Dissanayake", "Jayawardena", "Gunaratne", "Karunaratne", "Senanayake"]

    hr_rows = []
    emp_id = 101
    for dept, roles in depts.items():
        for _ in range(8):  # ~40 employees total
            role, base = random.choice(roles)
            exp = random.randint(1, 15)
            salary = base + (exp * 2500) + random.randint(-4000, 5000)
            rating = random.choice([3.0, 3.5, 4.0, 4.2, 4.5, 4.8, 5.0])
            bonus = round(salary * (0.05 if rating < 4.0 else (0.12 if rating < 4.5 else 0.20)), 2)
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            hire_d = datetime(2023 - random.randint(0, 8), random.randint(1, 12), random.randint(1, 28))

            hr_rows.append({
                "Employee_ID": f"EMP-{emp_id}",
                "Full_Name": f"{fname} {lname}",
                "Department": dept,
                "Job_Title": role,
                "Base_Salary": salary,
                "Bonus": bonus,
                "Performance_Rating": rating,
                "Years_Experience": exp,
                "Location": random.choice(locations),
                "Hire_Date": hire_d.strftime("%Y-%m-%d"),
                "Employment_Status": random.choice(["Active", "Active", "Active", "On Leave"])
            })
            emp_id += 1
    df_hr = pd.DataFrame(hr_rows)
    hr_path = os.path.join(output_dir, "hr_workforce.csv")
    df_hr.to_csv(hr_path, index=False)
    print(f"Created {hr_path} ({len(df_hr)} rows)")

    # ----------------------------------------------------
    # 3. Finance & Corporate Expenses
    # ----------------------------------------------------
    expense_categories = [
        ("Cloud Infrastructure", "AWS Cloud Services", ["Engineering", "DevOps"]),
        ("Software Licenses", "JetBrains & GitHub", ["Engineering"]),
        ("Marketing & Ads", "Google Ads Network", ["Marketing"]),
        ("Marketing & Ads", "LinkedIn Talent & Ads", ["Marketing", "HR"]),
        ("Travel & Lodging", "SriLankan Airlines Corporate", ["Executive", "Sales"]),
        ("Office Supplies", "Stationery & Consumables Co", ["Admin", "HR"]),
        ("Consulting & Legal", "Deloitte Advisory", ["Finance", "Executive"]),
        ("Hardware Equipment", "Dell Technologies Enterprise", ["IT Support", "Engineering"])
    ]
    finance_rows = []
    quarters = ["Q1-2024", "Q2-2024", "Q3-2024", "Q4-2024"]
    for i in range(1, 51):
        cat, vendor, dept_opts = random.choice(expense_categories)
        amt = round(random.uniform(250.0, 15000.0), 2)
        q = random.choice(quarters)
        t_date = datetime(2024, random.randint(1, 12), random.randint(1, 28))
        status = random.choice(["Approved", "Approved", "Approved", "Pending", "Rejected"])
        pay_type = random.choice(["Corporate Card", "Wire Transfer", "ACH Invoice"])

        finance_rows.append({
            "Expense_ID": f"EXP-{2000 + i}",
            "Transaction_Date": t_date.strftime("%Y-%m-%d"),
            "Category": cat,
            "Vendor": vendor,
            "Department": random.choice(dept_opts),
            "Amount": amt,
            "Payment_Type": pay_type,
            "Quarter": q,
            "Approval_Status": status,
            "Project_Code": f"PRJ-{random.randint(101, 108)}"
        })
    df_finance = pd.DataFrame(finance_rows)
    finance_path = os.path.join(output_dir, "finance_expenses.csv")
    df_finance.to_csv(finance_path, index=False)
    print(f"Created {finance_path} ({len(df_finance)} rows)")

    # ----------------------------------------------------
    # 4. Inventory & Supply Chain
    # ----------------------------------------------------
    product_lines = [
        ("Microcontrollers & ICs", "ESP32-WROOM-32D Module", 2.45, 14),
        ("Microcontrollers & ICs", "STM32F401 Microcontroller", 4.80, 21),
        ("Power Management", "Step-Down Buck Converter 5V", 1.20, 7),
        ("Power Management", "Lithium Ion Battery 18650 3000mAh", 3.75, 10),
        ("Display & Modules", "OLED 0.96 inch I2C Display", 2.10, 12),
        ("Display & Modules", "TFT LCD Touchscreen 3.5 inch", 11.50, 18),
        ("Sensors & Transducers", "BME280 Environmental Sensor", 3.20, 10),
        ("Sensors & Transducers", "Ultrasonic Distance Sensor HC-SR04", 0.95, 5),
        ("Passive Components", "Precision Resistor Kit 1/4W", 8.50, 4),
        ("Passive Components", "Ceramic Capacitor Assortment", 7.20, 4)
    ]
    warehouses = ["Colombo North Hub", "Biyagama Free Zone", "Katuwana Logistic Park", "Changi Regional Hub"]
    suppliers = ["Sunway Electronics", "Global IC Distro", "Apex Semis Ltd", "Pacific Component Supply"]

    inventory_rows = []
    for i, (pline, item_desc, unit_c, ltime) in enumerate(product_lines * 4, 1):
        stock = random.randint(20, 1200)
        reorder = random.randint(100, 300)
        status = "Critical Low" if stock < reorder else ("Normal" if stock < (reorder * 3) else "Overstocked")

        inventory_rows.append({
            "SKU_Code": f"SKU-{8000 + i}",
            "Item_Description": item_desc,
            "Product_Line": pline,
            "Warehouse_Location": random.choice(warehouses),
            "Stock_Quantity": stock,
            "Reorder_Point": reorder,
            "Unit_Cost": unit_c,
            "Lead_Time_Days": ltime + random.randint(-2, 5),
            "Supplier_Name": random.choice(suppliers),
            "Stock_Status": status
        })
    df_inventory = pd.DataFrame(inventory_rows)
    inventory_path = os.path.join(output_dir, "inventory_supply.csv")
    df_inventory.to_csv(inventory_path, index=False)
    print(f"Created {inventory_path} ({len(df_inventory)} rows)")

if __name__ == "__main__":
    generate_domains()
