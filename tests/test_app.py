from io import StringIO
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import load_data


def test_load_data_success():
    csv_data = StringIO(
        "date,product,quantity,price\n"
        "2026-01-01,Ноутбук,2,55000\n"
        "2026-01-02,Мышь,3,1200\n"
    )

    df = load_data(csv_data)

    assert not df.empty
    assert "revenue" in df.columns
    assert df.iloc[0]["revenue"] == 110000
    assert df.iloc[1]["revenue"] == 3600


def test_load_data_missing_column():
    csv_data = StringIO(
        "date,product,quantity\n"
        "2026-01-01,Ноутбук,2\n"
    )

    with pytest.raises(ValueError):
        load_data(csv_data)


def test_load_data_invalid_rows_removed():
    csv_data = StringIO(
        "date,product,quantity,price\n"
        "2026-01-01,Ноутбук,2,55000\n"
        "invalid_date,Мышь,abc,1200\n"
    )

    df = load_data(csv_data)

    assert len(df) == 1
    assert df.iloc[0]["product"] == "Ноутбук"


def test_required_columns_exist_after_processing():
    csv_data = StringIO(
        "date,product,quantity,price\n"
        "2026-01-01,Ноутбук,2,55000\n"
    )

    df = load_data(csv_data)

    assert "date" in df.columns
    assert "product" in df.columns
    assert "quantity" in df.columns
    assert "price" in df.columns
    assert "revenue" in df.columns