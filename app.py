import pandas as pd
import plotly.express as px
import streamlit as st

REQUIRED_COLUMNS = ["date", "product", "quantity", "price"]


def load_data(file) -> pd.DataFrame:
    """Загружает и подготавливает данные о продажах из CSV-файла."""
    df = pd.read_csv(file)

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"В файле отсутствуют обязательные столбцы: {missing}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    df = df.dropna(subset=["date", "product", "quantity", "price"]).copy()
    if df.empty:
        raise ValueError("После обработки в файле не осталось корректных данных.")

    df["product"] = df["product"].astype(str).str.strip()
    df = df[df["product"] != ""].copy()
    if df.empty:
        raise ValueError("В файле отсутствуют корректные наименования товаров.")

    df["quantity"] = df["quantity"].astype(float)
    df["price"] = df["price"].astype(float)
    df["revenue"] = df["quantity"] * df["price"]

    return df.sort_values("date").reset_index(drop=True)


def filter_data(df: pd.DataFrame, products: list[str], date_range) -> pd.DataFrame:
    """Фильтрует данные по товарам и периоду."""
    filtered_df = df[df["product"].isin(products)].copy()

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["date"].dt.date >= start_date)
            & (filtered_df["date"].dt.date <= end_date)
        ]

    return filtered_df


def build_monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.assign(month=df["date"].dt.to_period("M"))
        .groupby("month", as_index=False)["revenue"]
        .sum()
        .sort_values("month")
    )
    monthly["month"] = monthly["month"].astype(str)
    return monthly


def build_product_revenue(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("product", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )


def build_product_quantity(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("product", as_index=False)["quantity"]
        .sum()
        .sort_values("quantity", ascending=False)
    )


def build_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("product", as_index=False)
        .agg(
            total_quantity=("quantity", "sum"),
            total_revenue=("revenue", "sum"),
            average_price=("price", "mean"),
        )
        .sort_values("total_revenue", ascending=False)
    )


def format_number(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ")


def main() -> None:
    st.set_page_config(page_title="Анализ продаж интернет-магазина", layout="wide")

    st.title("Модуль визуализации и анализа данных продаж интернет-магазина")
    st.write(
        "Загрузите CSV-файл с данными о продажах. "
        "Обязательные столбцы: date, product, quantity, price."
    )

    uploaded_file = st.file_uploader("Выберите CSV-файл", type=["csv"])

    if uploaded_file is None:
        st.info("Для начала работы загрузите CSV-файл с данными о продажах.")
        return

    try:
        df = load_data(uploaded_file)
    except Exception as error:
        st.error(f"Ошибка обработки данных: {error}")
        return

    st.subheader("Исходные данные")
    st.dataframe(df, use_container_width=True)

    st.subheader("Фильтрация данных")
    all_products = sorted(df["product"].unique().tolist())
    selected_products = st.multiselect(
        "Выберите товары",
        options=all_products,
        default=all_products,
    )

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    selected_dates = st.date_input(
        "Выберите период",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    filtered_df = filter_data(df, selected_products, selected_dates)

    if filtered_df.empty:
        st.warning("По выбранным параметрам данные отсутствуют.")
        return

    total_revenue = filtered_df["revenue"].sum()
    total_quantity = filtered_df["quantity"].sum()
    total_orders = len(filtered_df)
    average_check = total_revenue / total_orders if total_orders else 0

    st.subheader("Основные показатели")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Выручка", format_number(total_revenue))
    col2.metric("Количество проданных единиц", str(int(total_quantity)))
    col3.metric("Количество записей о продажах", str(int(total_orders)))
    col4.metric("Средний чек", format_number(average_check))

    monthly_revenue = build_monthly_revenue(filtered_df)
    product_revenue = build_product_revenue(filtered_df)
    product_quantity = build_product_quantity(filtered_df)
    summary_table = build_summary_table(filtered_df)

    st.subheader("Динамика выручки по месяцам")
    revenue_chart = px.line(
        monthly_revenue,
        x="month",
        y="revenue",
        markers=True,
        title="Выручка по месяцам",
    )
    st.plotly_chart(revenue_chart, use_container_width=True)

    st.subheader("Выручка по товарам")
    product_chart = px.bar(
        product_revenue,
        x="product",
        y="revenue",
        title="Выручка по товарам",
    )
    st.plotly_chart(product_chart, use_container_width=True)

    st.subheader("Структура продаж по количеству")
    quantity_chart = px.pie(
        product_quantity,
        names="product",
        values="quantity",
        title="Количество проданных единиц по товарам",
    )
    st.plotly_chart(quantity_chart, use_container_width=True)

    st.subheader("Сводная таблица")
    st.dataframe(summary_table, use_container_width=True)


if __name__ == "__main__":
    main()
