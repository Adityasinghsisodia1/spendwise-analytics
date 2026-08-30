"""Excel export for the currently filtered expense list."""

import io

import pandas as pd


def build_excel(rows: list[dict]) -> bytes:
    """Build an in-memory .xlsx from expense rows and return its bytes."""
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.rename(
            columns={
                "expense_date": "Date",
                "category": "Category",
                "description": "Description",
                "amount": "Amount",
            }
        )[["Date", "Category", "Description", "Amount"]]

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Expenses")

        worksheet = writer.sheets["Expenses"]
        for column_cells in worksheet.columns:
            max_length = max(len(str(cell.value)) for cell in column_cells if cell.value is not None)
            worksheet.column_dimensions[column_cells[0].column_letter].width = max_length + 4

    return buffer.getvalue()
