# **Overview**
This project performs an analysis of Zomato data using Python. The dataset contains various details about restaurants, such as location, cuisine, ratings, and other features.
The objective of the analysis is to explore patterns in the data, handle missing values, and gain insights into customer preferences and restaurant characteristics.

## **Libraries Used**
The following Python libraries are required for this project:

- **pandas:** For data manipulation and analysis.
- **numpy:** For numerical computations.
- **matplotlib & seaborn:** For data visualization.
- sqlite3: To handle database operations for reading raw data from an SQLite database.
- **folium:** (optional) For generating geographic visualizations, if included later.


## Data Overview
The dataset is retrieved from an SQLite database. The data includes several columns like:

- name: Name of the restaurant
- location: Restaurant's location
- rate: Rating of the restaurant
- cuisines: Types of cuisines offered
- votes: Number of votes received
- approx_cost(for two people): Approximate cost for two people.


Missing Values
The dataset contains missing values in several columns, such as rate, phone, location, and cuisines.
Missing values are handled through various techniques, including replacing certain values with NaN and calculating the percentage of missing data in each column.

## **Key Steps in the Analysis**
### **Data Loading:**
The data is loaded from an SQLite database using the pandas.read_sql_query() function.
Connection is established using sqlite3.
```python

con = sqlite3.connect('zomato_rawdata.sqlite')
df = pd.read_sql_query("SELECT * FROM users", con)
```
### **Data Cleaning:**

Missing values are identified and handled.
Invalid or placeholder values in the rate column (like 'NEW' or '-') are replaced with NaN.
```python

df['rate'] = df['rate'].replace(('NEW', '-'), np.nan)
```

### **Exploratory Data Analysis (EDA):**
Data visualization techniques using matplotlib and seaborn are applied to gain insights into the distribution of ratings, popular cuisines, and more.

### **Geographic Analysis:**
(If applicable) You can generate geographic heatmaps to visualize restaurant density by location using folium for interactive maps.

### **Results and Insights**
Various insights regarding restaurant locations, cuisines, and customer preferences were extracted.
The percentage of missing data for key columns was calculated.
Distribution of restaurant ratings and their corresponding categories were analyzed.

