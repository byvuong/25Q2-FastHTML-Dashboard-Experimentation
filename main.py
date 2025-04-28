from fasthtml.common import *
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta
import random

# Create the FastHTML app with Plotly script
app, rt = fast_app(hdrs=[Script(src="https://cdn.plot.ly/plotly-2.32.0.min.js")])

# Generate fake credit card consumption data
def generate_fake_data(num_entries=100):
    # Define categories with their possible items and average price ranges
    categories = {
        "Groceries": {
            "items": ["Supermarket", "Farmer's Market", "Butcher Shop", "Bakery", "Health Food Store"],
            "price_range": (15, 150)
        },
        "Dining": {
            "items": ["Restaurant", "Fast Food", "Coffee Shop", "Bar", "Food Delivery"],
            "price_range": (10, 100)
        },
        "Entertainment": {
            "items": ["Movie Theater", "Concert", "Streaming Service", "Gaming", "Theme Park"],
            "price_range": (15, 120)
        },
        "Shopping": {
            "items": ["Clothing Store", "Electronics", "Home Goods", "Online Shopping", "Department Store"],
            "price_range": (20, 300)
        },
        "Transportation": {
            "items": ["Gas Station", "Public Transit", "Ride Share", "Parking", "Airline"],
            "price_range": (5, 200)
        },
        "Utilities": {
            "items": ["Electric Bill", "Water Bill", "Internet", "Phone Bill", "Streaming Subscription"],
            "price_range": (30, 150)
        },
        "Healthcare": {
            "items": ["Pharmacy", "Doctor Visit", "Dental Care", "Vision Care", "Health Insurance"],
            "price_range": (15, 250)
        }
    }
    
    # Generate random dates within the last 3 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    dates = [start_date + timedelta(days=random.randint(0, 90)) for _ in range(num_entries)]
    dates.sort()  # Sort dates chronologically
    
    data = []
    for date in dates:
        # Select a random category
        category = random.choice(list(categories.keys()))
        category_info = categories[category]
        
        # Select a random item from the category
        item = random.choice(category_info["items"])
        
        # Generate a random amount within the category's price range
        min_price, max_price = category_info["price_range"]
        amount = round(random.uniform(min_price, max_price), 2)
        
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "item": item,
            "category": category,
            "amount": amount
        })
    
    return pd.DataFrame(data)

# Create a DataFrame with fake data
df = generate_fake_data(150)

# Helper functions for data processing and visualization
def get_total_spending():
    return f"${df['amount'].sum():.2f}"

def get_category_spending():
    return df.groupby('category')['amount'].sum().reset_index()

def get_daily_spending():
    df['date'] = pd.to_datetime(df['date'])
    daily = df.groupby(df['date'].dt.strftime('%Y-%m-%d'))['amount'].sum().reset_index()
    daily['date'] = pd.to_datetime(daily['date'])
    daily = daily.sort_values('date')
    return daily

def get_recent_transactions(limit=10):
    return df.sort_values('date', ascending=False).head(limit)

# Create Plotly charts
def create_category_pie_chart():
    category_data = get_category_spending()
    fig = px.pie(
        category_data, 
        values='amount', 
        names='category',
        title='Spending by Category',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig.to_json()

def create_spending_time_chart():
    daily_data = get_daily_spending()
    fig = px.line(
        daily_data, 
        x='date', 
        y='amount',
        title='Daily Spending Over Time',
        markers=True
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        dragmode='select',
        clickmode='event+select',
        hovermode='closest'
    )
    fig.update_traces(
        customdata=daily_data.index.tolist(),
        hovertemplate='Date: %{x}<br>Amount: $%{y:.2f}<extra></extra>'
    )
    return fig.to_json()

# FastHTML routes
@rt
def index():
    total_spending = get_total_spending()
    category_pie = create_category_pie_chart()
    time_chart = create_spending_time_chart()
    recent_transactions = get_recent_transactions()
    
    all_transactions = df.copy()
    all_transactions['date'] = pd.to_datetime(all_transactions['date']).dt.strftime('%Y-%m-%d')
    all_transactions_json = all_transactions.to_json(orient='records', date_format='iso')
    
    return (
        Title("Credit Card Dashboard"),
        H1("Credit Card Consumption Dashboard", cls="dashboard-title"),
        
        Div(
            Div(
                H3("Total Spending"),
                P(total_spending, cls="total-amount"),
                cls="card"
            ),
            
            Div(
                H3("Spending by Category"),
                Div(id="category-chart"),
                Script(f"""
                    var categoryData = {category_pie};
                    Plotly.newPlot('category-chart', categoryData.data, categoryData.layout);
                """),
                cls="card"
            ),
            
            Div(
                H3("Spending Over Time"),
                Div(id="time-chart"),
                Script(f"""
                    var timeData = {time_chart};
                    var allTransactions = {all_transactions_json};
                    
                    Plotly.newPlot('time-chart', timeData.data, timeData.layout);
                    
                    document.allTransactions = allTransactions;
                    
                    document.getElementById('time-chart').on('plotly_selected', function(eventData) {{
                        if (!eventData || !eventData.points || eventData.points.length === 0) {{
                            updateTransactionsTable(allTransactions.slice(0, 10));
                            return;
                        }}
                        
                        var selectedDates = eventData.points.map(pt => pt.x);
                        
                        var filteredTransactions = allTransactions.filter(
                            transaction => selectedDates.includes(transaction.date)
                        );
                        
                        updateTransactionsTable(filteredTransactions);
                    }});
                    
                    function updateTransactionsTable(transactions) {{
                        var tbody = document.querySelector('.transactions-table tbody');
                        tbody.innerHTML = '';
                        
                        transactions.sort((a, b) => new Date(b.date) - new Date(a.date));
                        
                        var displayTransactions = transactions.slice(0, 20);
                        
                        displayTransactions.forEach(function(row) {{
                            var tr = document.createElement('tr');
                            
                            var dateCell = document.createElement('td');
                            dateCell.textContent = row.date;
                            tr.appendChild(dateCell);
                            
                            var itemCell = document.createElement('td');
                            itemCell.textContent = row.item;
                            tr.appendChild(itemCell);
                            
                            var categoryCell = document.createElement('td');
                            categoryCell.textContent = row.category;
                            tr.appendChild(categoryCell);
                            
                            var amountCell = document.createElement('td');
                            amountCell.textContent = '$' + parseFloat(row.amount).toFixed(2);
                            tr.appendChild(amountCell);
                            
                            tbody.appendChild(tr);
                        }});
                        
                        var header = document.querySelector('.transactions-header');
                        if (header) {{
                            header.textContent = "Transactions (" + displayTransactions.length + " of " + transactions.length + " shown)";
                        }}
                    }}
                """),
                cls="card full-width"
            ),
            
            Div(
                H3("Recent Transactions", cls="transactions-header"),
                Table(
                    Thead(
                        Tr(
                            Th("Date"),
                            Th("Item"),
                            Th("Category"),
                            Th("Amount")
                        )
                    ),
                    Tbody(
                        *[Tr(
                            Td(row['date']),
                            Td(row['item']),
                            Td(row['category']),
                            Td(f"${row['amount']:.2f}")
                          ) for _, row in recent_transactions.iterrows()]
                    ),
                    cls="transactions-table"
                ),
                cls="card full-width"
            ),
            
            cls="dashboard-grid"
        ),
        
        Style("""
            body { font-family: 'Arial', sans-serif; background-color: #f5f5f5; }
            .dashboard-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                padding: 20px;
            }
            .card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .full-width {
                grid-column: 1 / -1;
            }
            .total-amount {
                font-size: 2.5rem;
                font-weight: bold;
                color: #2c3e50;
            }
            .transactions-table {
                width: 100%;
                border-collapse: collapse;
            }
            .transactions-table th, .transactions-table td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            .transactions-table th {
                background-color: #f2f2f2;
            }
        """)
    )

# Filter by category route
@rt
def filter_by_category(category: str):
    filtered_df = df[df['category'] == category]
    total = f"${filtered_df['amount'].sum():.2f}"
    
    filtered_df['date'] = pd.to_datetime(filtered_df['date'])
    daily = filtered_df.groupby(filtered_df['date'].dt.strftime('%Y-%m-%d'))['amount'].sum().reset_index()
    daily['date'] = pd.to_datetime(daily['date'])
    daily = daily.sort_values('date')
    
    fig = px.line(
        daily, 
        x='date', 
        y='amount',
        title=f'{category} Spending Over Time',
        markers=True
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Amount ($)"
    )
    time_chart = fig.to_json()
    
    return (
        Div(
            H3(f"{category} Total Spending"),
            P(total, cls="total-amount"),
            cls="card"
        ),
        Div(
            H3(f"{category} Spending Over Time"),
            Div(id="filtered-time-chart"),
            Script(f"""
                var timeData = {time_chart};
                Plotly.newPlot('filtered-time-chart', timeData.data, timeData.layout);
            """),
            cls="card full-width"
        )
    )

serve()