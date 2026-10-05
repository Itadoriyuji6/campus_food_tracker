import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Setup page configuration
st.set_page_config(page_title="Campus Food Rescue Tracker", page_icon="🍲", layout="wide")

# Database connection
conn = sqlite3.connect('campus_food.db', check_same_thread=False)
c = conn.cursor()

# Create table
c.execute('''
    CREATE TABLE IF NOT EXISTS donations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        donor_name TEXT,
        food_type TEXT,
        quantity INTEGER,
        expiry_window TEXT,
        status TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = ["Dashboard", "Log Surplus Food", "Data Explorer", "Manage Records"]
choice = st.sidebar.selectbox("Select a Module", menu)

# Functions for CRUD operations
def add_donation(donor, food, qty, expiry):
    c.execute('INSERT INTO donations(donor_name, food_type, quantity, expiry_window, status) VALUES (?,?,?,?,?)',
              (donor, food, qty, expiry, "Available"))
    conn.commit()

def view_all_donations():
    c.execute('SELECT * FROM donations')
    data = c.fetchall()
    return data

def update_status(d_id, new_status):
    c.execute('UPDATE donations SET status=? WHERE id=?', (new_status, d_id))
    conn.commit()

def delete_donation(d_id):
    c.execute('DELETE FROM donations WHERE id=?', (d_id,))
    conn.commit()

# --- Module 1: Dashboard ---
if choice == "Dashboard":
    st.title("📊 Impact Dashboard")
    st.markdown("Monitor surplus food recovery and distribution across the campus.")
    
    data = view_all_donations()
    if data:
        df = pd.DataFrame(data, columns=['ID', 'Donor', 'Food Type', 'Quantity (Meals)', 'Expiry Window', 'Status', 'Date'])
        
        # Key Metrics
        total_rescued = df[df['Status'] == 'Picked Up']['Quantity (Meals)'].sum()
        total_available = df[df['Status'] == 'Available']['Quantity (Meals)'].sum()
        co2_saved = round(total_rescued * 2.5, 1) # Estimated 2.5kg CO2 prevented per meal
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Meals Rescued", total_rescued)
        col2.metric("CO2 Emissions Saved (kg)", co2_saved)
        col3.metric("Currently Available (Meals)", total_available)
        
        st.markdown("---")
        
        # Advanced Visualizations
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Food Status Breakdown")
            fig1 = px.pie(df, names='Status', values='Quantity (Meals)', hole=0.3, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_chart2:
            st.subheader("Top Donors (Hostels/Canteens)")
            donor_counts = df.groupby('Donor')['Quantity (Meals)'].sum().reset_index()
            fig2 = px.bar(donor_counts, x='Donor', y='Quantity (Meals)', text='Quantity (Meals)', color='Donor')
            st.plotly_chart(fig2, use_container_width=True)
            
    else:
        st.info("No data available yet. Please log some surplus food to view dashboard metrics.")

# --- Module 2: Add Records ---
elif choice == "Log Surplus Food":
    st.title("🍲 Log Surplus Food")
    st.markdown("Use this form to broadcast available food to volunteers.")
    
    with st.form(key="add_form"):
        donor = st.text_input("Hostel / Canteen Name (Donor)")
        food = st.text_input("Food Type (e.g., Rice, Dal, Mixed Veg)")
        qty = st.number_input("Quantity (in Meals)", min_value=1)
        expiry = st.selectbox("Expiry Window", ["1 Hour", "2 Hours", "4 Hours", "End of Day"])
        submit = st.form_submit_button("Report Surplus Food")
        
        if submit:
            if donor and food:
                add_donation(donor, food, qty, expiry)
                st.success(f"Successfully logged {qty} meals from {donor}!")
            else:
                st.error("Please fill in all required fields.")

# --- Module 3: Data Explorer ---
elif choice == "Data Explorer":
    st.title("🔍 Active Food Listings")
    data = view_all_donations()
    if data:
        df = pd.DataFrame(data, columns=['ID', 'Donor', 'Food Type', 'Quantity (Meals)', 'Expiry Window', 'Status', 'Date'])
        
        # Filtering
        status_filter = st.selectbox("Filter by Status", ["All", "Available", "Accepted", "Picked Up"])
        if status_filter != "All":
            df = df[df['Status'] == status_filter]
            
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("No records found in the database.")

# --- Module 4: Manage Records (CRUD) ---
elif choice == "Manage Records":
    st.title("⚙️ Manage Records")
    data = view_all_donations()
    if data:
        df = pd.DataFrame(data, columns=['ID', 'Donor', 'Food', 'Quantity', 'Expiry', 'Status', 'Date'])
        st.dataframe(df, hide_index=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Update Status")
            update_id = st.number_input("Enter Record ID to Update", min_value=1, step=1)
            new_status = st.selectbox("New Status", ["Available", "Accepted", "Picked Up"])
            if st.button("Update Record"):
                update_status(update_id, new_status)
                st.success(f"Record {update_id} updated to {new_status}!")
                st.rerun()
                
        with col2:
            st.subheader("Delete Record")
            del_id = st.number_input("Enter Record ID to Delete", min_value=1, step=1)
            if st.button("Delete Record"):
                delete_donation(del_id)
                st.error(f"Record {del_id} deleted!")
                st.rerun()
    else:
        st.info("No records to manage.")
