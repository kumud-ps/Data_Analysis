# SQL & Python Data Integration Project
## Overview
This project demonstrates the integration of SQL databases with Python for data manipulation, transformation, and analysis. It highlights how Python can interact with SQL databases, specifically MySQL, to fetch, analyze, and process data for various applications.

## Objectives
Demonstrate how Python can interact with SQL databases.
Load data from CSV files into MySQL using Python.
Perform CRUD (Create, Read, Update, Delete) operations in MySQL through Python.
Showcase how to analyze data stored in an SQL database using pandas and other Python libraries.

## Project Structure
### CSV to SQL Data Loading:
The project loads multiple CSV files (such as customers.csv, orders.csv, sellers.csv) into MySQL tables.
### CRUD Operations: 
Insert, update, and delete operations are demonstrated using Python's mysql.connector library.
### Data Analysis: 
Basic exploratory data analysis (EDA) is performed using pandas and seaborn to extract meaningful insights from the data.

## Prerequisites
Ensure you have the following installed:

- Python 3.x
- MySQL (or any SQL database)
- Jupyter Notebook (optional, but useful for running the code interactively)
- Required Python libraries:

``` bash
pip install pandas mysql-connector-python matplotlib seaborn numpy
```
## File Structure
### SQL + Python.ipynb: 
This is the main notebook containing the integration code.
### CSV Files: 
The dataset files used in this project (e.g., customers.csv, orders.csv, etc.).

## Data Sources
- The following CSV files are loaded into the MySQL database:

-- customers.csv: Customer details (e.g., customer_id, name).
-- orders.csv: Order information (e.g., order_id, order_date).
-- sellers.csv: Seller information (e.g., seller_id, location).
-- products.csv: Product catalog (e.g., product_id, category).
-- order_items.csv: Itemized details for each order.
-- geolocation.csv: Geographical data of orders and sellers.

## Key Steps
### 1. SQL Table Creation
The project dynamically creates MySQL tables based on the structure of the CSV files. It automatically infers SQL data types from the pandas DataFrame.

``` python
def get_sql_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return 'INT'
    elif pd.api.types.is_float_dtype(dtype):
        return 'FLOAT'
    elif pd.api.types.is_bool_dtype(dtype):
        return 'BOOLEAN'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return 'DATETIME'
    else:
        return 'TEXT'
```
### 2. Data Loading and Insertion
Once tables are created, data from the CSV files is inserted into the corresponding tables using MySQL's INSERT queries.

``` python
sql = f"INSERT INTO `{table_name}` ({', '.join(['`' + col + '`' for col in df.columns])}) VALUES ({', '.join(['%s'] * len(row))})"
cursor.execute(sql, values)
```

### 3. Data Exploration and Analysis
Once the data is loaded into the SQL tables, you can query it and perform analysis using pandas and matplotlib for visualization.

``` python
import seaborn as sns
sns.barplot(x='order_id', y='product_id', data=df_orders)
plt.show()
```

## Modify the database connection settings in the code to reflect your MySQL setup:
``` python
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='your-password',
    database='portfolio_projects'
)
```

## Run the Jupyter Notebook: 
Launch the notebook (SQL + Python.ipynb) to load the CSV data, create tables, and perform operations.

## Future Enhancements
### Data Visualization: 
Add more detailed data visualization techniques using matplotlib and seaborn.
### Advanced Analytics: 
Apply advanced analytics like clustering or regression on the dataset.
### API Integration: 
Integrate API endpoints to dynamically fetch and load data into MySQL.
