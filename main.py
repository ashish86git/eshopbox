import os
import pandas as pd
import streamlit as st
import plotly.express as px





# 📂 Folder Path for CSV Files
folder_path = r"C:\Users\ashis\Downloads\EShop_Dash_RawFiles\powerbi"

# 🔹 Get all CSV files from the folder
csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

# 🔹 Load all CSV files into a dictionary
dataframes = {}

for file in csv_files:
    file_path = os.path.join(folder_path, file)
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.upper().str.replace(" ", "_")  # Clean column names
    dataframes[file] = df



# 🏢 **Set up Streamlit Dashboard**
st.set_page_config(page_title="📊 Power BI Warehouse Dashboard", layout="wide")

# 🎨 Custom Background Color
st.markdown(
    """
    <style>
        .stApp {
            background-color: #f5bcbc; /* Light Gray Background */
        }
        .custom-header {
            background-color: #4CAF50; /* Green */
            color: white;
            text-align: center;
            padding: 10px;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)



# 🖼️ **Add Logo**
logo_path = "C:/Users/ashis/Downloads/EShop_Dash_RawFiles/logo.jpg"  # Change this to your actual logo path
st.image(logo_path, width=150)
st.title("📦 E-Shop Box Warehouse Operational Dashboard")
st.markdown("Real-time visualization of Inventory, Returns, and Orders details etc.")

# 📅 **Date Range Filter**
start_date, end_date = st.sidebar.date_input("📅 Select Date Range", []), st.sidebar.date_input("📅 Select End Date", [])
if start_date and end_date:
    for file in dataframes:
        df = dataframes[file]
        date_col = next((col for col in df.columns if "DATE" in col or "AT" in col), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            dataframes[file] = df[(df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))]


# 📍 **Location Selection**
all_locations = set()
for df in dataframes.values():
    if "LOCATION" in df.columns:
        all_locations.update(df["LOCATION"].unique())

locations = ["ALL"] + list(all_locations)
selected_location = st.sidebar.radio("📍 Select Location", locations)

# 🔍 **Filter data by location**
for file in dataframes:
    df = dataframes[file]
    if "LOCATION" in df.columns and selected_location != "ALL":
        dataframes[file] = df[df["LOCATION"] == selected_location]

# 📈 **Summarized Data using Pivot Tables**
if "ALL_LOC_Inventory_Report.csv" in dataframes:
    df_inventory = dataframes["ALL_LOC_Inventory_Report.csv"]
    df_inventory["CREATED_AT_DATE"] = pd.to_datetime(df_inventory["CREATED_AT_DATE"], errors="coerce")
    df_pivot_inventory = df_inventory.groupby("CREATED_AT_DATE").sum().reset_index()
else:
    st.error("Inventory report not found!")

if "Return_Report_ALL_Location.csv" in dataframes:
    df_return = dataframes["Return_Report_ALL_Location.csv"]
    df_pivot_return = df_return.groupby("RETURN_TYPE").sum().reset_index()
    # Group by RETURN_TYPE and count occurrences of RETURN_SHIPMENTS_RECEIVED_AT
    df_return_count = df_return.groupby("RETURN_TYPE")["REVERSE_TRACKING_ID"].count().reset_index()
else:
    st.error("Return report not found!")

if "GRN_Report_ALL_Location.csv" in dataframes:
    df_grn = dataframes["GRN_Report_ALL_Location.csv"]
    df_grn["GRN_COMPLETED_AT"] = pd.to_datetime(df_grn["GRN_COMPLETED_AT"], errors="coerce")
    df_pivot_grn = df_grn.groupby("GRN_COMPLETED_AT").sum().reset_index()
else:
    st.error("GRN report not found!")

if "OPD_report.csv" in dataframes:
    df_opd = dataframes["OPD_report.csv"]
    df_opd["DATE"] = pd.to_datetime(df_opd["DATE"], errors="coerce")
    df_pivot_opd = df_opd.groupby("DATE").sum().reset_index()
else:
    st.error("OPD report not found!")






# 📌 **KPIs (Key Performance Indicators)**
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📦 Total Inward", dataframes.get("ALL_LOC_Inventory_Report.csv", pd.DataFrame()).get("TOTAL_INVENTORY", pd.Series()).sum())
col2.metric("🚚 Total Dispatch", dataframes.get("OPD_report.csv", pd.DataFrame()).get("DISPATCH_ORDERS", pd.Series()).sum())
col3.metric("🔄 Return Received", dataframes.get("Return_Report_ALL_Location.csv", pd.DataFrame()).get("RETURN_SHIPMENTS_RECEIVED_AT", pd.Series()).count())
col4.metric("✅ Return Processed", dataframes.get("Return_Report_ALL_Location.csv", pd.DataFrame()).get("RETURN_TYPE", pd.Series()).count())
col5.metric("📋 Total Orders", dataframes.get("OPD_report.csv", pd.DataFrame()).get("TOTAL_ORDERS", pd.Series()).sum())

# 📊 **Inventory Trends**
st.subheader("📊 Total Inventory Trend")
fig_inventory = px.line(df_pivot_inventory, x="CREATED_AT_DATE", y="TOTAL_INVENTORY",
                        title="Total Inventory Over Time", markers=True,
                        )
fig_inventory.update_traces(line=dict(color="red"))
st.plotly_chart(fig_inventory, use_container_width=True)

# 📦 **Order Trends**
st.subheader("📦 Total Orders vs Packed Orders vs Dispatched Orders")
fig_orders = px.line(df_pivot_opd, x="DATE",
                     y=["TOTAL_ORDERS", "PACKED_ORDERS", "DISPATCH_ORDERS"],
                     title="Order Processing Trends",
                     markers=True)
st.plotly_chart(fig_orders, use_container_width=True)


if "SLA_REPORT_ALL.csv" in dataframes:
    df_sla = dataframes["SLA_REPORT_ALL.csv"]

    # ✅ Convert Date Columns
    df_sla["SHIPMENT_CREATED_IN_FLEX"] = pd.to_datetime(df_sla["SHIPMENT_CREATED_IN_FLEX"], errors="coerce")
    df_sla["EXPECTED_RTS_AT"] = pd.to_datetime(df_sla["EXPECTED_RTS_AT"], errors="coerce")
    df_sla["PACKED_AT"] = pd.to_datetime(df_sla["PACKED_AT"], errors="coerce")

    # ✅ Group by "SHIPMENT_CREATED_IN_FLEX"
    df_pivot_sla = df_sla.groupby(df_sla["SHIPMENT_CREATED_IN_FLEX"].dt.date).size().reset_index(name="TOTAL_SHIPMENTS")

    # 📊 **Shipment Status Distribution**
    st.subheader("📦 Report: Shipment Status ")
    df_status_count = df_sla["SHIPMENT_STATUS"].value_counts().reset_index()
    df_status_count.columns = ["SHIPMENT_STATUS", "COUNT"]

    fig_status = px.bar(df_status_count, x="SHIPMENT_STATUS", y="COUNT",
                        title="Shipment Status", color="SHIPMENT_STATUS")
    st.plotly_chart(fig_status, use_container_width=True)

    # 📊 **Total Breach Based on SLA**
    if "SLA" in df_sla.columns:
        st.subheader("⏳ SLA Report: Total Breach Count")

        df_sla_count = df_sla["SLA"].value_counts().reset_index()
        df_sla_count.columns = ["SLA", "COUNT"]

        fig_sla = px.bar(df_sla_count, x="SLA", y="COUNT",
                         title="SLA Breach Count", color="SLA")
        st.plotly_chart(fig_sla, use_container_width=True)
    else:
        st.warning("⚠️ 'SLA' column not found in SLA_REPORT_ALL.csv!")

else:
    st.error("⚠️ SLA_REPORT_ALL.csv not found!")




if "SLA_Yest_REPORT_ALL.csv" in dataframes:
    df_sla_yest = dataframes["SLA_Yest_REPORT_ALL.csv"]

    # ✅ Convert Date Columns
    df_sla_yest["SHIPMENT_CREATED_IN_FLEX"] = pd.to_datetime(df_sla_yest["SHIPMENT_CREATED_IN_FLEX"], errors="coerce")
    df_sla_yest["EXPECTED_RTS_AT"] = pd.to_datetime(df_sla_yest["EXPECTED_RTS_AT"], errors="coerce")
    df_sla_yest["PACKED_AT"] = pd.to_datetime(df_sla_yest["PACKED_AT"], errors="coerce")

    # ✅ Group by "SHIPMENT_CREATED_IN_FLEX"
    df_pivot_sla_yest = df_sla_yest.groupby(df_sla_yest["SHIPMENT_CREATED_IN_FLEX"].dt.date).size().reset_index(name="TOTAL_SHIPMENTS")

    # 📊 **Shipment Status Distribution**
    st.subheader("📦 SLA Yesterday Report: Yesterday breached")
    df_status_count_yest = df_sla_yest["SHIPMENT_STATUS"].value_counts().reset_index()
    df_status_count_yest.columns = ["SHIPMENT_STATUS", "COUNT"]

    fig_status_yest = px.bar(df_status_count_yest, x="SHIPMENT_STATUS", y="COUNT",
                             title="Yesterday Breached", color="SHIPMENT_STATUS")
    st.plotly_chart(fig_status_yest, use_container_width=True)

else:
    st.error("⚠️ SLA_Yest_REPORT_ALL.csv not found!")





# 🔄 **Return Analysis (Pie Chart)**
st.subheader("🔄 Return Types Distribution")
fig_return = px.pie(df_return_count, names="RETURN_TYPE", values="REVERSE_TRACKING_ID",
                    title="Return Types", hole=0.4)
st.plotly_chart(fig_return, use_container_width=True)


# # ⏳ **Turn Around Time (TAT)**
# st.subheader("⏳ Turn Around Time (TAT)")
# if {"ORDER_TO_INVOICE", "ORDER_TO_DISPATCH", "INVOICE_TO_DISPATCH"}.issubset(df_pivot_inventory.columns):
#     fig_tat = px.line(df_pivot_inventory, x="CREATED_AT_DATE",
#                       y=["ORDER_TO_INVOICE", "ORDER_TO_DISPATCH", "INVOICE_TO_DISPATCH"],
#                       title="Turnaround Time Analysis", markers=True)
#     st.plotly_chart(fig_tat, use_container_width=True)
#

if "All_TAT_Report.csv" in dataframes:
    df_tat = dataframes["All_TAT_Report.csv"]

    # ✅ Convert Date Columns
    df_tat["DATE"] = pd.to_datetime(df_tat["DATE"], errors="coerce")
    df_tat["SHIPMENT_CREATED_IN_FLEX"] = pd.to_datetime(df_tat["SHIPMENT_CREATED_IN_FLEX"], errors="coerce")
    df_tat["PACKED_AT"] = pd.to_datetime(df_tat["PACKED_AT"], errors="coerce")
    df_tat["MANIFEST_COMPLETED_AT"] = pd.to_datetime(df_tat["MANIFEST_COMPLETED_AT"], errors="coerce")

    # ✅ Select only numerical columns for aggregation
    num_cols = ["ORDER_TO_INVOICE", "ORDER_TO_DISPATCH", "INVOICE_TO_DISPATCH"]

    # ✅ Group by Date and Sum Only Numeric Columns
    df_pivot_tat = df_tat.groupby(df_tat["DATE"].dt.date)[num_cols].sum().reset_index()

    # 📊 **Turn Around Time (TAT) Analysis**
    st.subheader("⏳ Turn Around Time (TAT) Report")
    fig_tat = px.line(df_pivot_tat, x="DATE",
                      y=["ORDER_TO_INVOICE", "ORDER_TO_DISPATCH", "INVOICE_TO_DISPATCH"],
                      title="Turnaround Time Analysis", markers=True,color_discrete_map={"ORDER_TO_INVOICE": "#33ffee",
                                                                                         "ORDER_TO_DISPATCH": "#ffe733",
                                                                                         "INVOICE_TO_DISPATCH":"#ff4733"})  # Custom colors)
    st.plotly_chart(fig_tat, use_container_width=True)

else:
    st.error("⚠️ All_TAT_Report.csv not found!")


if "Inward_MIS_Report.csv" in dataframes:
    df_inward = dataframes["Inward_MIS_Report.csv"]

    # ✅ Convert Date Column
    df_inward["RECEIVED_DATE"] = pd.to_datetime(df_inward["RECEIVED_DATE"], errors="coerce")

    # ✅ Group by Date
    df_pivot_inward = df_inward.groupby(df_inward["RECEIVED_DATE"].dt.date)[["INVOICE_QTY", "GRN_QTY"]].sum().reset_index()

    # 📊 **GRN vs Invoice Quantity Analysis**
    st.subheader("📦 GRN vs Invoice Quantity Report")
    fig_inward = px.line(df_pivot_inward, x="RECEIVED_DATE",
                         y=["INVOICE_QTY", "GRN_QTY"],
                         title="Goods Received vs Invoiced",
                         markers=True,
                         color_discrete_map={"INVOICE_QTY": "#33ffee", "GRN_QTY": "#ff4733"})  # Custom colors

    st.plotly_chart(fig_inward, use_container_width=True)

else:
    st.error("⚠️ Inward_MIS_Report.csv not found!")





# 📊 **Aging Analysis Table**
st.subheader("📊 Aging Analysis")
aging_data = {
    "Aging": ["3 to 5 days", "5 to 10 days", "More than 10 days", "Within 2 days"],
    "Inward Sellable": [4, 3, 11, 349],
    "Return Sellable": [3, 3, 6, 12]
}
df_aging = pd.DataFrame(aging_data)
st.dataframe(df_aging)

st.success("✅ Dashboard successfully loaded!")
