import streamlit as st
import pandas as pd
import plotly.express as px



# App title
st.set_page_config(
    page_title="Data Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Data Analysis Dashboard")
st.write("Upload your CSV or Excel file to start analyzing your data.")

# File uploader
uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:

    # Read CSV file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    # Read Excel file
    else:
        df = pd.read_excel(uploaded_file)

    # Drop stray index columns pandas sometimes leaves behind
    # (e.g. "Unnamed: 0" from a CSV that was saved with index=True)
    df = df.loc[:, ~df.columns.str.match(r"^Unnamed: \d+$")]

    # Guard against duplicate column names, which break groupby()
    # with "Column(s) ... already selected" errors
    if df.columns.duplicated().any():
        st.warning(
            "⚠️ Duplicate column names found in the file — "
            "keeping only the first occurrence of each."
        )
        df = df.loc[:, ~df.columns.duplicated()]

    # Show success message
    st.success("File uploaded successfully!")

    # Display dataset
    st.subheader("Dataset Preview")
    st.dataframe(df)

    # Display basic information
    st.subheader("Dataset Information")

    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", df.shape[0])
    col2.metric("Columns", df.shape[1])
    col3.metric("Missing Values", df.isnull().sum().sum())

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Show missing values
    missing_values = df.isnull().sum().sum()

    st.subheader("🧹 Data Cleaning")
    st.write(f"Duplicate rows removed. Total missing values: {missing_values}")

    # Get numeric columns
    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()

    st.subheader("📊 Key Performance Indicators")

    if numeric_columns:
        # Let user select a numeric column
        selected_column = st.selectbox(
            "Select a column for analysis",
            numeric_columns
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", f"{df[selected_column].sum():,.2f}")
        col2.metric("Average", f"{df[selected_column].mean():,.2f}")
        col3.metric("Maximum", f"{df[selected_column].max():,.2f}")
        col4.metric("Minimum", f"{df[selected_column].min():,.2f}")
    else:
        st.warning("No numeric columns found in the dataset.")

    st.subheader("📈 Data Visualization")

    if numeric_columns:
        chart_column = st.selectbox(
            "Select numeric column for chart",
            numeric_columns,
            key="chart_column"
        )

        fig = px.histogram(
            df,
            x=chart_column,
            title=f"Distribution of {chart_column}"
        )
        st.plotly_chart(fig, width='stretch')

    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # Select categorical columns
    categorical_columns = df.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()

    # Create a copy for filtering
    filtered_df = df.copy()

    # Dynamic filters — apply EACH column's selection, one at a time
    for column in categorical_columns:
        options = ["All"] + list(df[column].dropna().unique())
        selected_values = st.sidebar.selectbox(
            f"Select {column}",
            options=options,
            key=f"filter_{column}"
        )
        if selected_values != "All":
            filtered_df = filtered_df[filtered_df[column] == selected_values]
            col1.metric("Rows", filtered_df.shape[0])

    # ---------------- AUTOMATIC LINE CHART ----------------

    st.subheader("📈 Trend Analysis")

    # Find date columns
    # (skip numeric columns — pandas will happily "convert" numbers like
    # 1500 into a timestamp, which falsely flags Sales/Profit/etc. as dates)
    date_columns = []

    candidate_columns = df.select_dtypes(exclude=["number"]).columns.tolist()

    for column in candidate_columns:
        converted = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        # If most values can be converted to dates
        if converted.notna().mean() >= 0.7:
            date_columns.append(column)

    # Find numeric columns
    numeric_columns = df.select_dtypes(
        include=["number"]
    ).columns.tolist()

    if date_columns and numeric_columns:

        # Select date column
        date_column = st.selectbox(
            "Select Date Column",
            date_columns,
            key="line_date"
        )

        # Select numeric column
        value_column = st.selectbox(
            "Select Value",
            numeric_columns,
            key="line_value"
        )

        # Convert date
        temp_df = filtered_df.copy()

        temp_df[date_column] = pd.to_datetime(
            temp_df[date_column],
            errors="coerce"
        )

        temp_df = temp_df.dropna(
            subset=[date_column, value_column]
        )

        # Monthly aggregation
        temp_df["Month"] = (
            temp_df[date_column]
            .dt.to_period("M")
            .astype(str)
        )

        trend_data = (
            temp_df
            .groupby("Month")[value_column]
            .sum()
            .reset_index()
        )

        # Create line chart
        fig_line = px.line(
            trend_data,
            x="Month",
            y=value_column,
            markers=True,
            title=f"{value_column} Trend Over Time"
        )

        st.plotly_chart(
            fig_line,
            width="stretch"
        )

    else:

        st.info(
            "📌 A line chart requires at least "
            "one date column and one numeric column."
        )

    # Bar chart
    st.subheader("📊 Bar Chart")

    if categorical_columns and numeric_columns:
        category_column = st.selectbox(
            "Select category column",
            categorical_columns
        )

        value_column = st.selectbox(
            "Select value column",
            numeric_columns,
            key="bar_value"
        )

        bar_data = (
            filtered_df.groupby(category_column)[value_column]
            .sum()
            .reset_index()
        )

        fig_bar = px.bar(
            bar_data,
            x=category_column,
            y=value_column,
            title=f"{value_column} by {category_column}"
        )
        st.plotly_chart(fig_bar, width='stretch')
    else:
        st.info("Need at least one categorical and one numeric column for a bar chart.")

    # Pie chart
    st.subheader("🥧 Pie Chart")

    if categorical_columns and numeric_columns:
        pie_category = st.selectbox(
            "Select category for pie chart",
            categorical_columns,
            key="pie_category"
        )

        pie_value = st.selectbox(
            "Select value for pie chart",
            numeric_columns,
            key="pie_value"
        )

        pie_data = (
            filtered_df.groupby(pie_category)[pie_value]
            .sum()
            .reset_index()
        )

        fig_pie = px.pie(
            pie_data,
            names=pie_category,
            values=pie_value,
            title=f"{pie_value} Distribution by {pie_category}"
        )

        st.plotly_chart(fig_pie, width='stretch')
    else:
        st.info("Need at least one categorical and one numeric column for a pie chart.")

    st.subheader("📥 Download Data")

    csv = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name="filtered_data.csv",
        mime="text/csv"
    )

    # ---------------- AUTOMATIC BUSINESS INSIGHTS ----------------

    st.subheader("💡 Automatic Business Insights")

    # Check required columns
    if "Profit" in filtered_df.columns:

        profit = filtered_df["Profit"]

        # 1. Overall Profit
        total_profit = profit.sum()

        if total_profit > 0:
            st.success(
                f"💰 Total Profit is {total_profit:,.2f}. "
                "Overall, the business is profitable."
            )
        else:
            st.error(
                f"🚨 Total Profit is {total_profit:,.2f}. "
                "The business is currently making a loss."
            )

        # 2. Category Analysis
        if "Category" in filtered_df.columns:

            category_profit = (
                filtered_df.groupby("Category")["Profit"]
                .sum()
                .sort_values(ascending=False)
            )

            best_category = category_profit.index[0]
            best_profit = category_profit.iloc[0]

            worst_category = category_profit.index[-1]
            worst_profit = category_profit.iloc[-1]

            st.write(
                f"🏆 **Best Category:** {best_category} "
                f"({best_profit:,.2f} profit)"
            )

            st.write(
                f"⚠️ **Weakest Category:** {worst_category} "
                f"({worst_profit:,.2f} profit)"
            )

        # 3. Region Analysis
        if "Region" in filtered_df.columns:

            region_profit = (
                filtered_df.groupby("Region")["Profit"]
                .sum()
                .sort_values(ascending=False)
            )

            best_region = region_profit.index[0]
            worst_region = region_profit.index[-1]

            st.write(
                f"🌍 **Best Region:** {best_region}"
            )

            st.write(
                f"⚠️ **Region needing attention:** {worst_region}"
            )

        # 4. Loss-making products
        if "Product Name" in filtered_df.columns:

            product_profit = (
                filtered_df.groupby("Product Name")["Profit"]
                .sum()
                .sort_values()
            )

            loss_products = product_profit[product_profit < 0]

            if len(loss_products) > 0:

                st.warning(
                    f"🚨 {len(loss_products)} products are generating losses."
                )

                st.write(
                    "Consider reviewing pricing, discounts, "
                    "or costs for these products."
                )

        # 5. Discount Analysis
        if "Discount" in filtered_df.columns:

            high_discount = filtered_df[
                filtered_df["Discount"] >= 0.30
            ]

            if len(high_discount) > 0:

                high_discount_profit = high_discount["Profit"].sum()

                if high_discount_profit < 0:

                    st.warning(
                        "💸 High discounts are associated with an overall loss. "
                        "Consider reducing discounts on these products."
                    )

    else:

        st.info(
            "💡 Add a 'Profit' column to your dataset "
            "to generate automatic profit insights."
        )