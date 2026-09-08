"""
LUMYD Multi-Domain Distillation Dataset Generator
================================================
Generates 200+ high-quality, verified training examples across 4 diverse domains:
1. Retail & E-Commerce (retail_sales.csv)
2. HR & Workforce Payroll (hr_workforce.csv)
3. Finance & Corporate Expenses (finance_expenses.csv)
4. Inventory & Supply Chain (inventory_supply.csv)

Across 3 dialects:
- Singlish (~40%)
- English (~35%)
- Sinhala (~25%)

CRITICAL REQUIREMENT:
Every single Python code snippet MUST be executed and verified via `CodeSandbox.execute(code, df)`
before being admitted into `teacher_distillation_dataset.jsonl` and `CodeKnowledgeBank`.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.models.dataset import Dataset
from app.services.code_engine.sandbox import CodeSandbox
from app.services.code_engine.distillation_manager import DistillationManager

def get_domain_samples():
    """
    Returns a structured dictionary of domain sample generators.
    Each item contains:
    - filename: CSV filename in backend/data/sample_domains/
    - samples: List of dicts with:
        - query: str
        - language: "singlish" | "english" | "sinhala"
        - intent_label: str
        - python_code: str (must assign answer to variable `result`)
        - human_explanation: str
    """
    return [
        # =========================================================================
        # 1. RETAIL SALES DOMAIN
        # =========================================================================
        {
            "filename": "retail_sales.csv",
            "samples": [
                # Singlish
                {
                    "query": "machan wadiyenma profit dunna product category eka mokakda",
                    "language": "singlish",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Product_Category')['Profit'].sum()\nbest_cat = grouped.idxmax()\nresult = {'category': str(best_cat), 'profit': round(float(grouped[best_cat]), 2)}",
                    "human_explanation": "Mcn wadiyenma profit dunne {category} category eka, total profit eka Rs. {profit} kiyala record wela thiyenawa!"
                },
                {
                    "query": "Western region eke total sales kochcharada",
                    "language": "singlish",
                    "intent_label": "filtered_aggregation",
                    "python_code": "val = df[df['Region'] == 'Western']['Sales_Amount'].sum()\nresult = round(float(val), 2)",
                    "human_explanation": "Western region eke total sales amount eka Rs. {result} wenawa machan."
                },
                {
                    "query": "Credit Card valin karapu transactions gana kiyada",
                    "language": "singlish",
                    "intent_label": "entity_count",
                    "python_code": "result = int((df['Payment_Method'] == 'Credit Card').sum())",
                    "human_explanation": "Credit Card payment method eken mulu transactions {result} k karala thiyenawa."
                },
                {
                    "query": "aduma discount thiyena sales rep kawda",
                    "language": "singlish",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Sales_Rep')['Discount_Pct'].mean()\nrep = grouped.idxmin()\nresult = {'sales_rep': str(rep), 'avg_discount': round(float(grouped[rep]), 4)}",
                    "human_explanation": "Aduma average discount ekak deela thiyenne {sales_rep} ({avg_discount}) kiyana sales rep mcn."
                },
                {
                    "query": "overall average sales amount eka calculate karala denna",
                    "language": "singlish",
                    "intent_label": "overall_aggregation",
                    "python_code": "result = round(float(df['Sales_Amount'].mean()), 2)",
                    "human_explanation": "Mulu dataset eke overall average sales amount eka Rs. {result} wenawa."
                },
                {
                    "query": "machan paadu una (negative profit) transactions thiyenawada",
                    "language": "singlish",
                    "intent_label": "anomaly_detection",
                    "python_code": "loss_df = df[df['Profit'] < 0]\nresult = {'count': len(loss_df), 'details': loss_df[['Transaction_ID', 'Product_Name', 'Profit']].to_dict(orient='records')}",
                    "human_explanation": "Negative profit (loss) una transactions {count} k identify kala mcn."
                },
                {
                    "query": "Electronics valata wada Apparel vala sales wadi da",
                    "language": "singlish",
                    "intent_label": "comparison",
                    "python_code": "elec_s = float(df[df['Product_Category'] == 'Electronics']['Sales_Amount'].sum())\napp_s = float(df[df['Product_Category'] == 'Apparel']['Sales_Amount'].sum())\nresult = {'electronics_sales': round(elec_s, 2), 'apparel_sales': round(app_s, 2), 'is_apparel_higher': bool(app_s > elec_s)}",
                    "human_explanation": "Electronics sales Rs. {electronics_sales} saha Apparel sales Rs. {apparel_sales}. Apparel sales wadi da kiyana eka: {is_apparel_higher}."
                },
                {
                    "query": "unit price eka 100 ta wadi items monawada",
                    "language": "singlish",
                    "intent_label": "threshold_filter",
                    "python_code": "items = df[df['Unit_Price'] > 100]['Product_Name'].unique().tolist()\nresult = items",
                    "human_explanation": "Unit price eka 100 ta wadi products mehemai: {result}."
                },
                {
                    "query": "Kasun Perera ge total sales kiyada",
                    "language": "singlish",
                    "intent_label": "entity_lookup",
                    "python_code": "val = df[df['Sales_Rep'] == 'Kasun Perera']['Sales_Amount'].sum()\nresult = round(float(val), 2)",
                    "human_explanation": "Kasun Perera ge total sales eka Rs. {result} wenawa machan."
                },
                {
                    "query": "region wise sales breakdown eka denna",
                    "language": "singlish",
                    "intent_label": "group_aggregation",
                    "python_code": "res = df.groupby('Region')['Sales_Amount'].sum().round(2).to_dict()\nresult = res",
                    "human_explanation": "Menna region wise total sales breakdown eka mcn: {result}."
                },
                {
                    "query": "wadiyenma vikunapu top 3 products monawada",
                    "language": "singlish",
                    "intent_label": "top_k_ranking",
                    "python_code": "top = df.groupby('Product_Name')['Quantity'].sum().nlargest(3).to_dict()\nresult = top",
                    "human_explanation": "Wadiyenma Quantity ekakin vikunapu Top 3 products thamai: {result}."
                },
                {
                    "query": "mulu dataset eke transactions kiyak thiyeda",
                    "language": "singlish",
                    "intent_label": "record_count",
                    "python_code": "result = int(len(df))",
                    "human_explanation": "Dataset eke total transactions {result} k record wela thiyenawa."
                },
                {
                    "query": "payment methods monawada thiyenne",
                    "language": "singlish",
                    "intent_label": "unique_values",
                    "python_code": "result = df['Payment_Method'].unique().tolist()",
                    "human_explanation": "Mehi thiyena payment methods: {result}."
                },
                {
                    "query": "profit margin eka percentage ekak widiyata calculate karanna",
                    "language": "singlish",
                    "intent_label": "derived_metric",
                    "python_code": "tot_sales = df['Sales_Amount'].sum()\ntot_profit = df['Profit'].sum()\nmargin = (tot_profit / tot_sales) * 100 if tot_sales > 0 else 0\nresult = round(float(margin), 2)",
                    "human_explanation": "Overall profit margin eka {result}% k lesa calculate kala mcn."
                },
                {
                    "query": "highest single sales transaction amount eka kiyada",
                    "language": "singlish",
                    "intent_label": "extremum_analysis",
                    "python_code": "result = round(float(df['Sales_Amount'].max()), 2)",
                    "human_explanation": "Single highest transaction sales amount eka Rs. {result} wenawa."
                },
                # English
                {
                    "query": "What is the total sales amount across all records?",
                    "language": "english",
                    "intent_label": "overall_aggregation",
                    "python_code": "result = round(float(df['Sales_Amount'].sum()), 2)",
                    "human_explanation": "The overall gross sales amount across the entire dataset is ${result:,.2f}."
                },
                {
                    "query": "Which sales representative generated the highest profit?",
                    "language": "english",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Sales_Rep')['Profit'].sum()\ntop_rep = grouped.idxmax()\nresult = {'sales_rep': str(top_rep), 'total_profit': round(float(grouped[top_rep]), 2)}",
                    "human_explanation": "The top-performing sales representative by total profit is {sales_rep} with ${total_profit:,.2f}."
                },
                {
                    "query": "Show average discount percentage by payment method",
                    "language": "english",
                    "intent_label": "group_aggregation",
                    "python_code": "res = (df.groupby('Payment_Method')['Discount_Pct'].mean() * 100).round(2).to_dict()\nresult = res",
                    "human_explanation": "Here is the average discount percentage broken down by payment method: {result}."
                },
                {
                    "query": "Find the top 3 best-selling products by quantity sold",
                    "language": "english",
                    "intent_label": "top_k_ranking",
                    "python_code": "result = df.groupby('Product_Name')['Quantity'].sum().nlargest(3).to_dict()",
                    "human_explanation": "The top 3 best-selling products by quantity sold are: {result}."
                },
                {
                    "query": "What is the median transaction sales amount?",
                    "language": "english",
                    "intent_label": "overall_aggregation",
                    "python_code": "result = round(float(df['Sales_Amount'].median()), 2)",
                    "human_explanation": "The median transaction sales amount across all orders is ${result:,.2f}."
                },
                {
                    "query": "How many transactions offered a discount greater than 10%?",
                    "language": "english",
                    "intent_label": "threshold_filter",
                    "python_code": "result = int((df['Discount_Pct'] > 0.10).sum())",
                    "human_explanation": "A total of {result} transactions had a discount rate strictly higher than 10%."
                },
                {
                    "query": "List sales breakdown by product category",
                    "language": "english",
                    "intent_label": "group_aggregation",
                    "python_code": "result = df.groupby('Product_Category')['Sales_Amount'].sum().round(2).to_dict()",
                    "human_explanation": "The total sales breakdown per product category is: {result}."
                },
                {
                    "query": "Which region had the lowest total sales?",
                    "language": "english",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Region')['Sales_Amount'].sum()\nlowest_reg = grouped.idxmin()\nresult = {'region': str(lowest_reg), 'sales': round(float(grouped[lowest_reg]), 2)}",
                    "human_explanation": "The region with the lowest total sales is {region} with ${sales:,.2f}."
                },
                {
                    "query": "Calculate the average profit per unit sold for Electronics",
                    "language": "english",
                    "intent_label": "derived_metric",
                    "python_code": "elec = df[df['Product_Category'] == 'Electronics']\ntot_p = elec['Profit'].sum()\ntot_q = elec['Quantity'].sum()\nresult = round(float(tot_p / tot_q), 2) if tot_q > 0 else 0.0",
                    "human_explanation": "The average profit per unit sold in Electronics is ${result:,.2f}."
                },
                {
                    "query": "Are there any missing or null values in this sales table?",
                    "language": "english",
                    "intent_label": "data_quality",
                    "python_code": "result = df.isnull().sum().to_dict()",
                    "human_explanation": "Null value check completed. Here is the count of missing entries per column: {result}."
                },
                # Sinhala
                {
                    "query": "වැඩිම ලාභයක් ලැබූ නිෂ්පාදන කාණ්ඩය කුමක්ද?",
                    "language": "sinhala",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Product_Category')['Profit'].sum()\nbest = grouped.idxmax()\nresult = {'category': str(best), 'profit': round(float(grouped[best]), 2)}",
                    "human_explanation": "වැඩිම ලාභයක් උපයා ඇත්තේ {category} කාණ්ඩය වන අතර එහි මුළු ලාභය රු. {profit} කි."
                },
                {
                    "query": "සමස්ත විකුණුම් ප්‍රමාණය කොපමණද?",
                    "language": "sinhala",
                    "intent_label": "overall_aggregation",
                    "python_code": "result = round(float(df['Sales_Amount'].sum()), 2)",
                    "human_explanation": "සමස්ත විකුණුම් එකතුව රු. {result} ක් වේ."
                },
                {
                    "query": "Western කලාපයේ විකුණුම් එකතුව කීයද?",
                    "language": "sinhala",
                    "intent_label": "filtered_aggregation",
                    "python_code": "val = df[df['Region'] == 'Western']['Sales_Amount'].sum()\nresult = round(float(val), 2)",
                    "human_explanation": "Western කලාපයේ මුළු විකුණුම් අගය රු. {result} කි."
                },
                {
                    "query": "අඩුම විකුණුම් කළ නියෝජිතයා කවුද?",
                    "language": "sinhala",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Sales_Rep')['Sales_Amount'].sum()\nlow = grouped.idxmin()\nresult = {'sales_rep': str(low), 'sales': round(float(grouped[low]), 2)}",
                    "human_explanation": "අඩුම විකුණුම් වාර්තා කළ නියෝජිතයා {sales_rep} වන අතර විකුණුම් අගය රු. {sales} කි."
                },
                {
                    "query": "ණයපත් (Credit Card) මගින් සිදු කළ ගනුදෙනු ගණන කීයද?",
                    "language": "sinhala",
                    "intent_label": "entity_count",
                    "python_code": "result = int((df['Payment_Method'] == 'Credit Card').sum())",
                    "human_explanation": "Credit Card මගින් සිදු කළ ගනුදෙනු ගණන {result} කි."
                },
            ]
        },

        # =========================================================================
        # 2. HR & WORKFORCE DOMAIN
        # =========================================================================
        {
            "filename": "hr_workforce.csv",
            "samples": [
                # Singlish
                {
                    "query": "machan wadiyenma salary ganna employee kawda",
                    "language": "singlish",
                    "intent_label": "extremum_analysis",
                    "python_code": "top = df.loc[df['Base_Salary'].idxmax()]\nresult = {'name': str(top['Full_Name']), 'salary': float(top['Base_Salary']), 'department': str(top['Department'])}",
                    "human_explanation": "Company eke wadiyenma base salary ganna employee thamai {name} ({department}), salary eka Rs. {salary:,.2f} mcn!"
                },
                {
                    "query": "Engineering department eke average base salary eka kiyada",
                    "language": "singlish",
                    "intent_label": "filtered_aggregation",
                    "python_code": "eng_sal = df[df['Department'] == 'Engineering']['Base_Salary'].mean()\nresult = round(float(eng_sal), 2)",
                    "human_explanation": "Engineering department eke average base salary eka Rs. {result:,.2f} wenawa machan."
                },
                {
                    "query": "experience eka awurudu 10ta wadi aya kidenek innawada",
                    "language": "singlish",
                    "intent_label": "threshold_filter",
                    "python_code": "result = int((df['Years_Experience'] > 10).sum())",
                    "human_explanation": "Experience eka awurudu 10 ta wadi employeesla {result} denek innawa."
                },
                {
                    "query": "performance rating eka 4.5 ta wadi employeesla kawda",
                    "language": "singlish",
                    "intent_label": "filter_list",
                    "python_code": "high_p = df[df['Performance_Rating'] >= 4.5]['Full_Name'].tolist()\nresult = high_p",
                    "human_explanation": "Rating eka 4.5 ta wadi top performersla: {result}."
                },
                {
                    "query": "department wise total salary expense eka kochcharada",
                    "language": "singlish",
                    "intent_label": "group_aggregation",
                    "python_code": "result = df.groupby('Department')['Base_Salary'].sum().round(2).to_dict()",
                    "human_explanation": "Department wise total salary cost eka menna mcn: {result}."
                },
                {
                    "query": "Colombo office eke active employees kidenek innawada",
                    "language": "singlish",
                    "intent_label": "compound_filter",
                    "python_code": "res = len(df[(df['Location'] == 'Colombo') & (df['Employment_Status'] == 'Active')])\nresult = int(res)",
                    "human_explanation": "Colombo office eke inna active employees gana {result} k wenawa."
                },
                {
                    "query": "aduma salary ganna job role eka mokakda",
                    "language": "singlish",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Job_Title')['Base_Salary'].mean()\nrole = grouped.idxmin()\nresult = {'role': str(role), 'avg_salary': round(float(grouped[role]), 2)}",
                    "human_explanation": "Aduma average salary thiyena job role eka thamai {role} (Rs. {avg_salary:,.2f})."
                },
                {
                    "query": "machan total bonus amount eka calculate karanna",
                    "language": "singlish",
                    "intent_label": "overall_aggregation",
                    "python_code": "result = round(float(df['Bonus'].sum()), 2)",
                    "human_explanation": "Mulu workforce ekatama gewapu total bonus eka Rs. {result:,.2f} wenawa."
                },
                {
                    "query": "Remote wada karana staff eka kiyak innawada",
                    "language": "singlish",
                    "intent_label": "entity_count",
                    "python_code": "result = int((df['Location'].str.contains('Remote', case=False)).sum())",
                    "human_explanation": "Remote widiyata wada karana staff membersla {result} denek innawa mcn."
                },
                {
                    "query": "total compensation (salary + bonus) company ekatama kiyada",
                    "language": "singlish",
                    "intent_label": "derived_metric",
                    "python_code": "comp = (df['Base_Salary'] + df['Bonus']).sum()\nresult = round(float(comp), 2)",
                    "human_explanation": "Company eke total payroll expenditure (Base + Bonus) eka Rs. {result:,.2f} wenawa."
                },
                {
                    "query": "Sales director kawda kiyala hoyala denna",
                    "language": "singlish",
                    "intent_label": "entity_lookup",
                    "python_code": "directors = df[df['Job_Title'] == 'Sales Director']['Full_Name'].tolist()\nresult = directors",
                    "human_explanation": "Sales Director role eka thiyena staff members: {result}."
                },
                {
                    "query": "department kiyak company eke thiyeda",
                    "language": "singlish",
                    "intent_label": "unique_count",
                    "python_code": "result = int(df['Department'].nunique())",
                    "human_explanation": "Company eke departments {result} k thiyenawa."
                },
                # English
                {
                    "query": "Who is the highest paid employee in the organization?",
                    "language": "english",
                    "intent_label": "extremum_analysis",
                    "python_code": "top = df.loc[df['Base_Salary'].idxmax()]\nresult = {'name': str(top['Full_Name']), 'salary': float(top['Base_Salary']), 'department': str(top['Department']), 'role': str(top['Job_Title'])}",
                    "human_explanation": "The highest paid employee is {name} working as {role} in {department} earning ${salary:,.2f}."
                },
                {
                    "query": "What is the average years of experience across the engineering team?",
                    "language": "english",
                    "intent_label": "filtered_aggregation",
                    "python_code": "val = df[df['Department'] == 'Engineering']['Years_Experience'].mean()\nresult = round(float(val), 2)",
                    "human_explanation": "The average experience in the Engineering department is {result} years."
                },
                {
                    "query": "Calculate total payroll cost including base salaries and bonuses",
                    "language": "english",
                    "intent_label": "derived_metric",
                    "python_code": "total_cost = (df['Base_Salary'] + df['Bonus']).sum()\nresult = round(float(total_cost), 2)",
                    "human_explanation": "The combined organizational payroll expenditure across base salaries and bonuses is ${result:,.2f}."
                },
                {
                    "query": "How many employees are currently located in Singapore?",
                    "language": "english",
                    "intent_label": "entity_count",
                    "python_code": "result = int((df['Location'] == 'Singapore').sum())",
                    "human_explanation": "There are currently {result} team members based in Singapore."
                },
                {
                    "query": "Find the department with the highest average performance rating",
                    "language": "english",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Department')['Performance_Rating'].mean()\nbest_dept = grouped.idxmax()\nresult = {'department': str(best_dept), 'average_rating': round(float(grouped[best_dept]), 2)}",
                    "human_explanation": "The department with the highest average performance rating is {department} at {average_rating}."
                },
                {
                    "query": "List all employees with On Leave status",
                    "language": "english",
                    "intent_label": "threshold_filter",
                    "python_code": "result = df[df['Employment_Status'] == 'On Leave']['Full_Name'].tolist()",
                    "human_explanation": "Employees currently marked as On Leave: {result}."
                },
                {
                    "query": "What is the average bonus paid in Marketing?",
                    "language": "english",
                    "intent_label": "filtered_aggregation",
                    "python_code": "mkt_bonus = df[df['Department'] == 'Marketing']['Bonus'].mean()\nresult = round(float(mkt_bonus), 2)",
                    "human_explanation": "The average bonus awarded in the Marketing department is ${result:,.2f}."
                },
                {
                    "query": "What is the overall average employee rating?",
                    "language": "english",
                    "intent_label": "overall_aggregation",
                    "python_code": "result = round(float(df['Performance_Rating'].mean()), 2)",
                    "human_explanation": "The overall average employee performance rating across the company is {result}."
                },
                {
                    "query": "Show employee headcount by department",
                    "language": "english",
                    "intent_label": "group_aggregation",
                    "python_code": "result = df['Department'].value_counts().to_dict()",
                    "human_explanation": "The employee headcount breakdown by department is: {result}."
                },
                # Sinhala
                {
                    "query": "ආයතනයේ වැඩිම වැටුපක් ලබන සේවකයා කවුද?",
                    "language": "sinhala",
                    "intent_label": "extremum_analysis",
                    "python_code": "top = df.loc[df['Base_Salary'].idxmax()]\nresult = {'name': str(top['Full_Name']), 'salary': float(top['Base_Salary']), 'department': str(top['Department'])}",
                    "human_explanation": "වැඩිම වැටුපක් ලබන සේවකයා වන්නේ {department} අංශයේ {name} වන අතර වැටුප රු. {salary:,.2f} කි."
                },
                {
                    "query": "ඉංජිනේරු අංශයේ (Engineering) සාමාන්‍ය වැටුප කීයද?",
                    "language": "sinhala",
                    "intent_label": "filtered_aggregation",
                    "python_code": "val = df[df['Department'] == 'Engineering']['Base_Salary'].mean()\nresult = round(float(val), 2)",
                    "human_explanation": "ඉංජිනේරු අංශයේ සාමාන්‍ය මූලික වැටුප රු. {result:,.2f} කි."
                },
                {
                    "query": "වසර 5කට වඩා සේවා පළපුරුද්දක් ඇති සේවකයින් කීදෙනෙක් සිටීද?",
                    "language": "sinhala",
                    "intent_label": "threshold_filter",
                    "python_code": "result = int((df['Years_Experience'] > 5).sum())",
                    "human_explanation": "වසර 5කට වඩා පළපුරුද්දක් ඇති සේවකයින් {result} දෙනෙකු සිටී."
                },
                {
                    "query": "කොළඹ කාර්යාලයේ සේවකයින් ගණන කොපමණද?",
                    "language": "sinhala",
                    "intent_label": "entity_count",
                    "python_code": "result = int((df['Location'] == 'Colombo').sum())",
                    "human_explanation": "කොළඹ ශාඛාවේ සේවය කරන මුළු සේවකයින් සංඛ්‍යාව {result} කි."
                },
                {
                    "query": "දෙපාර්තමේන්තු අනුව වැටුප් එකතුව පෙන්වන්න",
                    "language": "sinhala",
                    "intent_label": "group_aggregation",
                    "python_code": "result = df.groupby('Department')['Base_Salary'].sum().round(2).to_dict()",
                    "human_explanation": "දෙපාර්තමේන්තු අනුව වැටුප් වියදම මෙසේය: {result}."
                },
            ]
        },

        # =========================================================================
        # 3. FINANCE & CORPORATE EXPENSES DOMAIN
        # =========================================================================
        {
            "filename": "finance_expenses.csv",
            "samples": [
                # Singlish
                {
                    "query": "machan wadiyenma expense wela thiyenne mona category ekatada",
                    "language": "singlish",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Category')['Amount'].sum()\ncat = grouped.idxmax()\nresult = {'category': str(cat), 'amount': round(float(grouped[cat]), 2)}",
                    "human_explanation": "Wadiyenma expense wela thiyenne {category} category ekata mcn, total amount eka Rs. {amount:,.2f} wenawa."
                },
                {
                    "query": "AWS ekata gewapu total amount eka kiyada",
                    "language": "singlish",
                    "intent_label": "filtered_aggregation",
                    "python_code": "val = df[df['Vendor'].str.contains('AWS', case=False, na=False)]['Amount'].sum()\nresult = round(float(val), 2)",
                    "human_explanation": "AWS ekata gewapu total expense eka Rs. {result:,.2f} wenawa machan."
                },
                {
                    "query": "Q1-2024 eke approve una expenses kochcharada",
                    "language": "singlish",
                    "intent_label": "compound_filter",
                    "python_code": "val = df[(df['Quarter'] == 'Q1-2024') & (df['Approval_Status'] == 'Approved')]['Amount'].sum()\nresult = round(float(val), 2)",
                    "human_explanation": "Q1-2024 කාර්තුවේදී Approve වුණු මුළු වියදම Rs. {result:,.2f} ක් වෙනවා."
                },
                {
                    "query": "Pending status thiyena transactions gana kiyada",
                    "language": "singlish",
                    "intent_label": "entity_count",
                    "python_code": "result = int((df['Approval_Status'] == 'Pending').sum())",
                    "human_explanation": "Thama approve novee Pending thiyena transactions {result} k thiyenawa mcn."
                },
                {
                    "query": "Corporate Card eken gewapu total eka balala denna",
                    "language": "singlish",
                    "intent_label": "filtered_aggregation",
                    "python_code": "val = df[df['Payment_Type'] == 'Corporate Card']['Amount'].sum()\nresult = round(float(val), 2)",
                    "human_explanation": "Corporate Card eken gewapu total expenditure eka Rs. {result:,.2f} wenawa."
                },
                {
                    "query": "Rejected una expenses kochchara thiyenawada",
                    "language": "singlish",
                    "intent_label": "filtered_aggregation",
                    "python_code": "val = df[df['Approval_Status'] == 'Rejected']['Amount'].sum()\nresult = {'rejected_count': int((df['Approval_Status'] == 'Rejected').sum()), 'total_amount': round(float(val), 2)}",
                    "human_explanation": "Reject una claims {rejected_count} k thiyenawa, eke total amount eka Rs. {total_amount:,.2f}."
                },
                {
                    "query": "Engineering department eke loku expenses monawada",
                    "language": "singlish",
                    "intent_label": "top_k_ranking",
                    "python_code": "top_eng = df[df['Department'] == 'Engineering'].nlargest(3, 'Amount')[['Vendor', 'Amount', 'Category']].to_dict(orient='records')\nresult = top_eng",
                    "human_explanation": "Engineering department eke Top 3 largest expenses: {result}."
                },
                {
                    "query": "overall total company expenses kiyada",
                    "language": "singlish",
                    "intent_label": "overall_aggregation",
                    "python_code": "result = round(float(df['Amount'].sum()), 2)",
                    "human_explanation": "Company eke recorded total expenses Rs. {result:,.2f} wenawa machan."
                },
                {
                    "query": "quarter wise expenses breakdown eka denna",
                    "language": "singlish",
                    "intent_label": "group_aggregation",
                    "python_code": "result = df.groupby('Quarter')['Amount'].sum().round(2).to_dict()",
                    "human_explanation": "Quarterly expense breakdown: {result}."
                },
                {
                    "query": "PRJ-101 project ekata giya wiyadama kiyada",
                    "language": "singlish",
                    "intent_label": "entity_lookup",
                    "python_code": "val = df[df['Project_Code'] == 'PRJ-101']['Amount'].sum()\nresult = round(float(val), 2)",
                    "human_explanation": "Project PRJ-101 ekata giya total expense eka Rs. {result:,.2f} wenawa."
                },
                {
                    "query": "average expense amount eka transaction ekakata kiyada",
                    "language": "singlish",
                    "intent_label": "overall_aggregation",
                    "python_code": "result = round(float(df['Amount'].mean()), 2)",
                    "human_explanation": "Average transaction amount eka Rs. {result:,.2f} wenawa."
                },
                # English
                {
                    "query": "What is the total expenditure for Q1-2024?",
                    "language": "english",
                    "intent_label": "filtered_aggregation",
                    "python_code": "val = df[df['Quarter'] == 'Q1-2024']['Amount'].sum()\nresult = round(float(val), 2)",
                    "human_explanation": "The total expenditure recorded for Q1-2024 is ${result:,.2f}."
                },
                {
                    "query": "Which vendor received the highest total payment?",
                    "language": "english",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Vendor')['Amount'].sum()\ntop_v = grouped.idxmax()\nresult = {'vendor': str(top_v), 'total_paid': round(float(grouped[top_v]), 2)}",
                    "human_explanation": "The vendor with the highest aggregate payment is {vendor} with ${total_paid:,.2f}."
                },
                {
                    "query": "Find all pending expense requests that require review",
                    "language": "english",
                    "intent_label": "filter_records",
                    "python_code": "result = df[df['Approval_Status'] == 'Pending'][['Expense_ID', 'Vendor', 'Amount', 'Department']].to_dict(orient='records')",
                    "human_explanation": "Found {len(result)} pending expense claims needing management approval."
                },
                {
                    "query": "Show expense breakdown by department",
                    "language": "english",
                    "intent_label": "group_aggregation",
                    "python_code": "result = df.groupby('Department')['Amount'].sum().round(2).to_dict()",
                    "human_explanation": "Total expenditure breakdown by corporate department: {result}."
                },
                {
                    "query": "What is the total spend on Cloud Infrastructure?",
                    "language": "english",
                    "intent_label": "entity_lookup",
                    "python_code": "val = df[df['Category'] == 'Cloud Infrastructure']['Amount'].sum()\nresult = round(float(val), 2)",
                    "human_explanation": "The cumulative spend on Cloud Infrastructure is ${result:,.2f}."
                },
                {
                    "query": "List the top 5 largest expense transactions",
                    "language": "english",
                    "intent_label": "top_k_ranking",
                    "python_code": "result = df.nlargest(5, 'Amount')[['Expense_ID', 'Vendor', 'Amount', 'Category']].to_dict(orient='records')",
                    "human_explanation": "The top 5 largest expenses recorded are: {result}."
                },
                {
                    "query": "What percentage of claims were approved vs rejected vs pending?",
                    "language": "english",
                    "intent_label": "derived_metric",
                    "python_code": "counts = df['Approval_Status'].value_counts(normalize=True) * 100\nresult = counts.round(2).to_dict()",
                    "human_explanation": "Approval status breakdown: {result}."
                },
                {
                    "query": "Which project incurred the highest cost?",
                    "language": "english",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Project_Code')['Amount'].sum()\ntop_p = grouped.idxmax()\nresult = {'project': str(top_p), 'amount': round(float(grouped[top_p]), 2)}",
                    "human_explanation": "The highest cost project is {project} with total spending of ${amount:,.2f}."
                },
                # Sinhala
                {
                    "query": "වැඩිම වියදමක් දැරූ අංශය කුමක්ද?",
                    "language": "sinhala",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Department')['Amount'].sum()\ntop_d = grouped.idxmax()\nresult = {'department': str(top_d), 'amount': round(float(grouped[top_d]), 2)}",
                    "human_explanation": "වැඩිම වියදමක් දරා ඇත්තේ {department} අංශය වන අතර වියදම රු. {amount:,.2f} කි."
                },
                {
                    "query": "Q1 කාර්තුවේ අනුමත වූ මුළු වියදම කීයද?",
                    "language": "sinhala",
                    "intent_label": "compound_filter",
                    "python_code": "val = df[(df['Quarter'] == 'Q1-2024') & (df['Approval_Status'] == 'Approved')]['Amount'].sum()\nresult = round(float(val), 2)",
                    "human_explanation": "Q1 කාර්තුවේ අනුමත වියදම් එකතුව රු. {result:,.2f} කි."
                },
                {
                    "query": "තවමත් අනුමත නොවූ (Pending) වියදම් ගණන කීයද?",
                    "language": "sinhala",
                    "intent_label": "entity_count",
                    "python_code": "result = int((df['Approval_Status'] == 'Pending').sum())",
                    "human_explanation": "තවමත් අනුමත කිරීම සඳහා පොරොත්තු ලේඛනයේ ඇති වියදම් ගණන {result} කි."
                },
                {
                    "query": "දෙපාර්තමේන්තු අනුව වියදම් සාරාංශයක් ලබා දෙන්න",
                    "language": "sinhala",
                    "intent_label": "group_aggregation",
                    "python_code": "result = df.groupby('Department')['Amount'].sum().round(2).to_dict()",
                    "human_explanation": "දෙපාර්තමේන්තු අනුව වියදම් බෙදීයාම මෙසේය: {result}."
                },
            ]
        },

        # =========================================================================
        # 4. INVENTORY & SUPPLY CHAIN DOMAIN
        # =========================================================================
        {
            "filename": "inventory_supply.csv",
            "samples": [
                # Singlish
                {
                    "query": "machan Critical Low thiyena items monawada",
                    "language": "singlish",
                    "intent_label": "threshold_filter",
                    "python_code": "crit = df[df['Stock_Status'] == 'Critical Low']['Item_Description'].tolist()\nresult = crit",
                    "human_explanation": "Critical Low status thiyena stock items: {result} mcn."
                },
                {
                    "query": "Colombo North Hub eke total stock quantity eka kiyada",
                    "language": "singlish",
                    "intent_label": "filtered_aggregation",
                    "python_code": "val = df[df['Warehouse_Location'] == 'Colombo North Hub']['Stock_Quantity'].sum()\nresult = int(val)",
                    "human_explanation": "Colombo North Hub eke total stock quantity eka units {result} k wenawa."
                },
                {
                    "query": "reorder point ekata wada stock adu items kiyak thiyenawada",
                    "language": "singlish",
                    "intent_label": "comparison_filter",
                    "python_code": "result = int((df['Stock_Quantity'] < df['Reorder_Point']).sum())",
                    "human_explanation": "Reorder point ekata wada adu stock thiyena items {result} k thiyenawa mcn."
                },
                {
                    "query": "total inventory valuation eka calculate karanna",
                    "language": "singlish",
                    "intent_label": "derived_metric",
                    "python_code": "val = (df['Stock_Quantity'] * df['Unit_Cost']).sum()\nresult = round(float(val), 2)",
                    "human_explanation": "Mulu warehouse wala athi inventory eke total monetary value eka Rs. {result:,.2f} wenawa."
                },
                {
                    "query": "lead time eka wadiyenma thiyena supplier kawda",
                    "language": "singlish",
                    "intent_label": "extremum_analysis",
                    "python_code": "top = df.loc[df['Lead_Time_Days'].idxmax()]\nresult = {'supplier': str(top['Supplier_Name']), 'lead_time': int(top['Lead_Time_Days']), 'item': str(top['Item_Description'])}",
                    "human_explanation": "Wadiyenma lead time ekak thiyenne {supplier} ta ({lead_time} days for {item})."
                },
                {
                    "query": "Overstocked wela thiyena product lines monawada",
                    "language": "singlish",
                    "intent_label": "filter_unique",
                    "python_code": "lines = df[df['Stock_Status'] == 'Overstocked']['Product_Line'].unique().tolist()\nresult = lines",
                    "human_explanation": "Overstocked status thiyena product lines: {result}."
                },
                {
                    "query": "Sensors and Transducers vala average unit cost eka kiyada",
                    "language": "singlish",
                    "intent_label": "filtered_aggregation",
                    "python_code": "val = df[df['Product_Line'].str.contains('Sensor', case=False)]['Unit_Cost'].mean()\nresult = round(float(val), 2)",
                    "human_explanation": "Sensors product line eke average unit cost eka Rs. {result} wenawa."
                },
                {
                    "query": "aduma lead time eka thiyena item eka mokakda",
                    "language": "singlish",
                    "intent_label": "extremum_analysis",
                    "python_code": "low = df.loc[df['Lead_Time_Days'].idxmin()]\nresult = {'item': str(low['Item_Description']), 'lead_time': int(low['Lead_Time_Days'])}",
                    "human_explanation": "Aduma lead time eka thiyenne {item} item ekata ({lead_time} days)."
                },
                {
                    "query": "warehouse locations monawada thiyenne",
                    "language": "singlish",
                    "intent_label": "unique_values",
                    "python_code": "result = df['Warehouse_Location'].unique().tolist()",
                    "human_explanation": "Thiyena warehouse locations: {result}."
                },
                {
                    "query": "unit cost eka 5 ta wadi items monawada",
                    "language": "singlish",
                    "intent_label": "threshold_filter",
                    "python_code": "items = df[df['Unit_Cost'] > 5.0]['Item_Description'].unique().tolist()\nresult = items",
                    "human_explanation": "Unit cost eka $5 ta wadi items: {result}."
                },
                # English
                {
                    "query": "List all inventory items currently flagged as Critical Low",
                    "language": "english",
                    "intent_label": "threshold_filter",
                    "python_code": "result = df[df['Stock_Status'] == 'Critical Low'][['SKU_Code', 'Item_Description', 'Stock_Quantity', 'Reorder_Point']].to_dict(orient='records')",
                    "human_explanation": "Found {len(result)} inventory lines currently flagged as Critical Low stock."
                },
                {
                    "query": "What is the total monetary value of inventory on hand?",
                    "language": "english",
                    "intent_label": "derived_metric",
                    "python_code": "total_val = (df['Stock_Quantity'] * df['Unit_Cost']).sum()\nresult = round(float(total_val), 2)",
                    "human_explanation": "The total carrying value of all warehouse inventory is ${result:,.2f}."
                },
                {
                    "query": "Which warehouse holds the largest volume of physical stock?",
                    "language": "english",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Warehouse_Location')['Stock_Quantity'].sum()\ntop_wh = grouped.idxmax()\nresult = {'warehouse': str(top_wh), 'total_units': int(grouped[top_wh])}",
                    "human_explanation": "The warehouse holding the largest physical stock volume is {warehouse} with {total_units:,} units."
                },
                {
                    "query": "What is the average lead time in days across all suppliers?",
                    "language": "english",
                    "intent_label": "overall_aggregation",
                    "python_code": "result = round(float(df['Lead_Time_Days'].mean()), 2)",
                    "human_explanation": "The average procurement lead time across suppliers is {result} days."
                },
                {
                    "query": "Show stock quantity breakdown by product line",
                    "language": "english",
                    "intent_label": "group_aggregation",
                    "python_code": "result = df.groupby('Product_Line')['Stock_Quantity'].sum().to_dict()",
                    "human_explanation": "Stock quantity breakdown by product line: {result}."
                },
                {
                    "query": "Identify suppliers with lead times exceeding 15 days",
                    "language": "english",
                    "intent_label": "threshold_filter",
                    "python_code": "suppliers = df[df['Lead_Time_Days'] > 15]['Supplier_Name'].unique().tolist()\nresult = suppliers",
                    "human_explanation": "Suppliers with lead times exceeding 15 days: {result}."
                },
                {
                    "query": "Which product line has the highest average unit cost?",
                    "language": "english",
                    "intent_label": "extremum_analysis",
                    "python_code": "grouped = df.groupby('Product_Line')['Unit_Cost'].mean()\ntop_pl = grouped.idxmax()\nresult = {'product_line': str(top_pl), 'avg_cost': round(float(grouped[top_pl]), 2)}",
                    "human_explanation": "The product line with the highest average unit cost is {product_line} at ${avg_cost:.2f}."
                },
                # Sinhala
                {
                    "query": "තොග මට්ටම අවම (Critical Low) භාණ්ඩ මොනවාද?",
                    "language": "sinhala",
                    "intent_label": "threshold_filter",
                    "python_code": "items = df[df['Stock_Status'] == 'Critical Low']['Item_Description'].tolist()\nresult = items",
                    "human_explanation": "තොග මට්ටම අවම මට්ටමක පවතින භාණ්ඩ: {result}."
                },
                {
                    "query": "ගබඩාවේ ඇති මුළු තොගයේ වටිනාකම කීයද?",
                    "language": "sinhala",
                    "intent_label": "derived_metric",
                    "python_code": "val = (df['Stock_Quantity'] * df['Unit_Cost']).sum()\nresult = round(float(val), 2)",
                    "human_explanation": "ගබඩාවේ ඇති සමස්ත තොගයේ මූල්‍යමය වටිනාකම රු. {result:,.2f} කි."
                },
                {
                    "query": "වැඩිම දින ගණනක් ගතවන (Lead Time) සැපයුම්කරු කවුද?",
                    "language": "sinhala",
                    "intent_label": "extremum_analysis",
                    "python_code": "top = df.loc[df['Lead_Time_Days'].idxmax()]\nresult = {'supplier': str(top['Supplier_Name']), 'days': int(top['Lead_Time_Days'])}",
                    "human_explanation": "භාණ්ඩ සැපයීමට වැඩිම දින ගණනක් ගතවන සැපයුම්කරු {supplier} වන අතර ඒ සඳහා දින {days} ක් ගතවේ."
                },
                {
                    "query": "කොළඹ ගබඩාවේ ඇති භාණ්ඩ ප්‍රමාණය කොපමණද?",
                    "language": "sinhala",
                    "intent_label": "filtered_aggregation",
                    "python_code": "val = df[df['Warehouse_Location'] == 'Colombo North Hub']['Stock_Quantity'].sum()\nresult = int(val)",
                    "human_explanation": "කොළඹ උතුරු ගබඩාවේ ඇති මුළු භාණ්ඩ ප්‍රමාණය {result} කි."
                },
            ]
        }
    ]

def expand_queries_with_variations(base_samples):
    """
    Synthesizes natural linguistic dialect variations for each base sample
    so that the fine-tuning dataset learns syntactic invariance.
    Expands base samples into a rich, balanced 200+ sample collection.
    """
    expanded = []
    
    # Prefix / suffix mappings for Singlish
    singlish_variations = [
        lambda q: f"machan {q}",
        lambda q: f"ane {q} kiyala kiyanna",
        lambda q: f"{q} balala denna",
        lambda q: f"mcn mata {q} hoyala denna puluwanda",
        lambda q: f"{q} kiyada",
    ]
    
    # English variations
    english_variations = [
        lambda q: f"Can you tell me {q[0].lower() + q[1:] if len(q) > 1 else q}",
        lambda q: f"Please {q[0].lower() + q[1:] if len(q) > 1 else q}",
        lambda q: f"Find {q[0].lower() + q[1:] if len(q) > 1 else q}",
        lambda q: f"Show me: {q}",
    ]
    
    # Sinhala variations
    sinhala_variations = [
        lambda q: f"කරුණාකර {q}",
        lambda q: f"{q} පෙන්වන්න",
        lambda q: f"මට {q} දැනගැනීමට අවශ්‍යයි",
    ]

    for domain_pack in base_samples:
        fname = domain_pack["filename"]
        domain_expanded = []
        for sample in domain_pack["samples"]:
            # Always include the original
            domain_expanded.append(sample)
            
            lang = sample["language"]
            q = sample["query"]
            code = sample["python_code"]
            expl = sample["human_explanation"]
            intent = sample["intent_label"]

            if lang == "singlish":
                # Generate 2 variations
                var1 = f"machan mata {q} hoyala denna" if not q.startswith("machan") else q.replace("machan ", "mcn ")
                var2 = f"{q} puluwanda" if not q.endswith("da") else f"ane {q}"
                domain_expanded.append({
                    "query": var1,
                    "language": "singlish",
                    "intent_label": intent,
                    "python_code": code,
                    "human_explanation": expl
                })
                domain_expanded.append({
                    "query": var2,
                    "language": "singlish",
                    "intent_label": intent,
                    "python_code": code,
                    "human_explanation": expl
                })
            elif lang == "english":
                var1 = f"Please {q[0].lower() + q[1:]}" if not q.startswith("Please") else q
                var2 = f"Can you show me {q[0].lower() + q[1:]}"
                domain_expanded.append({
                    "query": var1,
                    "language": "english",
                    "intent_label": intent,
                    "python_code": code,
                    "human_explanation": expl
                })
                domain_expanded.append({
                    "query": var2,
                    "language": "english",
                    "intent_label": intent,
                    "python_code": code,
                    "human_explanation": expl
                })
            elif lang == "sinhala":
                var1 = f"කරුණාකර {q}" if not q.startswith("කරුණාකර") else q
                var2 = f"{q} පෙන්වන්න"
                domain_expanded.append({
                    "query": var1,
                    "language": "sinhala",
                    "intent_label": intent,
                    "python_code": code,
                    "human_explanation": expl
                })
                domain_expanded.append({
                    "query": var2,
                    "language": "sinhala",
                    "intent_label": intent,
                    "python_code": code,
                    "human_explanation": expl
                })

        expanded.append({
            "filename": fname,
            "samples": domain_expanded
        })
    
    return expanded

def run_multi_domain_distillation():
    db = SessionLocal()
    sample_dir = backend_dir / "data" / "sample_domains"
    total_verified = 0
    total_rejected = 0
    
    domain_packs = expand_queries_with_variations(get_domain_samples())
    
    print("\n" + "="*70)
    print("🚀 LUMYD MULTI-DOMAIN DISTILLATION GENERATOR & SANDBOX VERIFIER")
    print("="*70 + "\n")

    for pack in domain_packs:
        filename = pack["filename"]
        samples = pack["samples"]
        csv_path = sample_dir / filename
        if not csv_path.exists():
            print(f"[!] Warning: File {csv_path} not found. Skipping.")
            continue

        df = pd.read_csv(csv_path)
        columns = [str(c) for c in df.columns]

        # Lookup dataset_id from DB
        db_dataset = db.query(Dataset).filter(Dataset.filename == filename).first()
        dataset_id = db_dataset.id if db_dataset else f"local-{filename}"

        print(f"\n📂 Processing Domain: {filename} (ID: {dataset_id})")
        print(f"   Columns: {columns}")
        print(f"   Candidate Samples: {len(samples)}")

        for i, s in enumerate(samples, 1):
            q = s["query"]
            code = s["python_code"]
            lang = s["language"]
            intent = s["intent_label"]
            expl_tmpl = s["human_explanation"]

            # 1. RIGID SANDBOX VERIFICATION
            exec_out = CodeSandbox.execute(code, df)
            if not exec_out["success"]:
                print(f"   ❌ [REJECTED] '{q}' -> Error: {exec_out.get('error')}")
                total_rejected += 1
                continue

            raw_res = exec_out["result"]
            # Extract clean result summary
            if isinstance(raw_res, dict) and "value" in raw_res:
                summary_val = raw_res["value"]
            elif isinstance(raw_res, dict) and "rows" in raw_res:
                summary_val = f"Table with {raw_res.get('total_rows', 0)} rows"
            else:
                summary_val = str(raw_res)

            # Format explanation safely
            try:
                if isinstance(raw_res, dict) and raw_res.get("type") == "scalar":
                    human_expl = expl_tmpl.replace("{result}", str(raw_res.get("value", "")))
                elif isinstance(raw_res, dict):
                    human_expl = expl_tmpl.format(**raw_res)
                else:
                    human_expl = expl_tmpl.replace("{result}", str(raw_res))
            except Exception:
                human_expl = expl_tmpl.replace("{result}", str(summary_val))

            # 2. RECORD IN KNOWLEDGE BANK & DISTILLATION JSONL
            DistillationManager.record_solution(
                db=db,
                dataset_id=dataset_id,
                query=q,
                intent_label=intent,
                python_code=code,
                explanation=human_expl,
                language=lang,
                execution_success=True,
                source="verified_synthetic",
                columns=columns,
                result_summary=summary_val,
            )
            total_verified += 1

        print(f"   ✅ Verified and stored {len(samples)} samples for {filename}")

    # Summary
    print("\n" + "="*70)
    print("📊 DISTILLATION GENERATION SUMMARY")
    print(f"   Total Verified Executable Samples Generated: {total_verified}")
    print(f"   Total Rejected Samples: {total_rejected}")
    
    stats = DistillationManager.get_statistics(db)
    print(f"   Total Lines in teacher_distillation_dataset.jsonl: {stats['distillation_dataset_lines']}")
    print(f"   Total Verified in PostgreSQL Knowledge Bank: {stats['verified_executable_solutions']}")
    print(f"   Ready for SLM Fine-Tuning: {stats['ready_for_slm_fine_tuning']}")
    print("="*70 + "\n")
    db.close()

if __name__ == "__main__":
    run_multi_domain_distillation()
