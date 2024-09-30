import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import io  # For in-memory buffer to hold Excel data

# --- File Upload for Location 1 ---
uploaded_file_loc1 = st.file_uploader("Upload your CSV file for Location 1 (e.g., Hyd)", type=["csv"], key="loc1")

# --- File Upload for Location 2 ---
uploaded_file_loc2 = st.file_uploader("Upload your CSV file for Location 2 (e.g., Mumbai)", type=["csv"], key="loc2")

# --- File Upload for Location 3 ---
uploaded_file_loc3 = st.file_uploader("Upload your CSV file for Location 3 (e.g., Gurgoan)", type=["csv"], key="loc3")

# Function to process files and create pivot tables
def process_file(uploaded_file, location_name, excel_writer):
    if uploaded_file is not None:
        try:
            # Read the uploaded CSV file and skip rows with errors
            df = pd.read_csv(uploaded_file, on_bad_lines='skip')  # skips bad lines
            df.columns = df.columns.str.upper()
            df.columns = df.columns.str.replace(" ", "_")

            st.write(f"Data loaded successfully for {location_name} with the following columns:")
            st.write(df.columns)

            # Ensure the necessary columns are present
            required_columns = ['SALES_CHANNEL', 'SHIPMENT_STATUS', 'SHIPMENT_ID', 'EXPECTED_RTS_AT', 'ORDER_CREATED_IN_ESHOPBOX', 'ORDER_ITEM_IDS']
            for col in required_columns:
                if col not in df.columns:
                    st.write(f"Column '{col}' not found in the DataFrame.")
                    return False  # No data to write

            # Convert EXPECTED_RTS and ORDER_CREATED_IN_ESHOPBOX columns to datetime
            df['EXPECTED_RTS_AT'] = pd.to_datetime(df['EXPECTED_RTS_AT'], errors='coerce')
            df['ORDER_CREATED_IN_ESHOPBOX'] = pd.to_datetime(df['ORDER_CREATED_IN_ESHOPBOX'], errors='coerce')

            # Convert ORDER_ITEM_IDS to numeric, coercing errors
            df['ORDER_ITEM_IDS'] = pd.to_numeric(df['ORDER_ITEM_IDS'], errors='coerce')

            # Current date and times
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            eleven_fifty_nine_am = today.replace(hour=11, minute=59)
            four_pm = today.replace(hour=16, minute=0)

            # Filter for 'MEESHO_UNDERATED' and 'CRED_FARMLEY_CMUM' based on timestamp condition
            special_channels = ['MEESHO_UNDERATED', 'CRED_FARMLEY_CMUM']
            mask_special = (df['SALES_CHANNEL'].isin(special_channels)) & (df['ORDER_CREATED_IN_ESHOPBOX'] < eleven_fifty_nine_am)

            # Process only those orders that need to be done before 4:00 PM today
            df_special_filtered = df[mask_special & (df['EXPECTED_RTS_AT'] < four_pm)]

            # Other channels will follow the regular pivot logic
            mask_other_channels = ~df['SALES_CHANNEL'].isin(special_channels)
            df_other_filtered = df[mask_other_channels]

            # Combine the filtered dataframes
            filtered_df = pd.concat([df_special_filtered, df_other_filtered])

            # Sidebar for filters
            st.sidebar.title(f"Filter Options for {location_name}")
            channels = df['SALES_CHANNEL'].unique()
            selected_channels = st.sidebar.multiselect(f"Select Channels for {location_name}:", channels, default=channels, key=f"multiselect_{location_name}")

            # Filter the final dataframe based on the selected channel
            filtered_df = filtered_df[filtered_df['SALES_CHANNEL'].isin(selected_channels)]

            # --- Channel-wise Status Pivot Table ---
            st.markdown(f"## Channel-wise Status Pivot Table for {location_name}")

            if 'SHIPMENT_STATUS' in filtered_df.columns:
                # Creating the pivot table with sum of ORDER_ITEM_IDS
                pivot_table_status_filtered = filtered_df.pivot_table(
                    index='SALES_CHANNEL',
                    columns='SHIPMENT_STATUS',
                    values='ORDER_ITEM_IDS',
                    aggfunc='sum',
                    fill_value=0
                )

                # Add a total column and row sum
                pivot_table_status_filtered['Row Total'] = pivot_table_status_filtered.sum(axis=1)  # Sum of each row
                pivot_table_status_filtered.loc['Column Total'] = pivot_table_status_filtered.sum(axis=0)  # Sum of each column

                # Display the pivot table
                st.write("Pivot Table - Sum of 'ORDER_ITEM_IDS' by Sales Channel and Shipment Status:")
                st.dataframe(pivot_table_status_filtered)

                # --- Channel vs Shipment Status Count Bar Graph ---
                st.markdown(f"## Channel vs Shipment Status Count Bar Graph for {location_name}")
                st.write("Bar Graph - Count of Shipment Status by Sales Channel:")
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.countplot(data=filtered_df, x='SALES_CHANNEL', hue='SHIPMENT_STATUS', palette='Set2', ax=ax)
                ax.set_xlabel("Sales Channel")
                ax.set_ylabel("Count of Shipment Status")
                ax.set_title(f"Count of Shipment Status by Sales Channel for {location_name}")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig)

                # Write the pivot table to the Excel file
                pivot_table_status_filtered.to_excel(excel_writer, sheet_name=location_name, index=True)
                return True  # Indicates that data has been written
            else:
                st.write("The 'SHIPMENT_STATUS' column is missing.")
                return False
        except pd.errors.ParserError as e:
            st.write(f"Error while reading the CSV file: {e}")
            return False

# Initialize an in-memory Excel writer
output = io.BytesIO()
sheets_written = 0  # Track the number of sheets written

with pd.ExcelWriter(output, engine='openpyxl') as excel_writer:
    # Process all uploaded files
    if uploaded_file_loc1 is not None:
        if process_file(uploaded_file_loc1, "Location 1 (Hyd)", excel_writer):
            sheets_written += 1

    if uploaded_file_loc2 is not None:
        if process_file(uploaded_file_loc2, "Location 2 (Mumbai)", excel_writer):
            sheets_written += 1

    if uploaded_file_loc3 is not None:
        if process_file(uploaded_file_loc3, "Location 3 (Gurgoan)", excel_writer):
            sheets_written += 1

# Ensure at least one sheet exists before downloading
if sheets_written > 0:
    output.seek(0)  # Go back to the start of the BytesIO object

    # Download button to allow users to download the pivot table Excel file
    st.markdown("### Download Pivot Tables by Location")
    st.download_button(
        label="Download All Pivot Tables",
        data=output.getvalue(),
        file_name="pivot_tables_by_location.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.write("No pivot tables were generated. Please check your uploaded files.")
