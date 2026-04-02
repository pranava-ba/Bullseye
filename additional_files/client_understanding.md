---

# Bullseye NSE Project
---
## 1. Download Data

* Get NSE data from the official NSE Website
* Unzip and clean the data to create CSV files

---

## 2. Column Extraction

Extract the following columns:

| Original Column | Standardized Name |
| --------------- | ----------------- |
| SECURITY        | SECURITY          |
| SYMBOL          | SYMBOL            |
| CATEGORY        | CATEGORY          |
| DATE            | DATE              |
| OPEN            | OPEN_PRICE        |
| HIGH            | HIGH_PRICE        |
| LOW             | LOW_PRICE         |
| CLOSE           | CLOSE_PRICE       |
| PREV_CLOSE      | PREV_CL_PR        |
| NET_TRDVAL      | NET_TRDVAL        |
| NET_TRDQTY      | NET_TRDQTY        |
| HI_52           | HI_52_WK          |
| LO_52           | LO_52_WK          |


---

## 3. Pivot Point Calculation

Use the cleaned data to calculate **pivot points**, and based on these compute:

* Support Levels
* Resistance Levels

---

## 4. Pivot Methods

Apply the following methods:

* Classic Pivot
* Fibonacci Pivot
* Woodie Pivot
* Camarilla Pivot

---

## 5. Data Presentation

### Comparison Table

* Display calculated data in a **comparison table**
* Compare across:

  * Various stocks
  * Different pivot methods

### Filters

Allow the user to filter based on:

* Date
* Stock
* Market
* Method

---

## 6. Visualization

* Display the data on a **graph for analysis**

---

## 7. Aesthetics

* Apply a silver/grey theme for the app style
* Avoid using black in the app
* Use Red, Green and Amber (Orange) colors to indicate profit and loss 
