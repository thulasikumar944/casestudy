import pandas as pd

from app.database.connection import DB_PATH, get_db_connection

PROJECT_ROOT = DB_PATH.parent.parent

CLEANED_FILE = (
    PROJECT_ROOT / "data" / "processed" / "cosmetics_cleaned.csv"
)


def ingest_data():

    if not CLEANED_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned CSV not found: {CLEANED_FILE}"
        )

    df = pd.read_csv(CLEANED_FILE)

    # Convert date columns into ISO format
    date_columns = [
        "InitialDateReported",
        "MostRecentDateReported",
        "DiscontinuedDate",
        "ChemicalCreatedAt",
        "ChemicalUpdatedAt",
        "ChemicalDateRemoved"
    ]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col], errors="coerce"
            ).dt.strftime("%Y-%m-%d")

    connection = get_db_connection() if DB_PATH.exists() else __import__(
        "sqlite3"
    ).connect(DB_PATH)

    try:
        df.to_sql(
            "cosmetics",
            connection,
            if_exists="replace",
            index=False
        )

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_product_id ON cosmetics(CDPHId)",
            "CREATE INDEX IF NOT EXISTS idx_chemical_name ON cosmetics(ChemicalName)",
            "CREATE INDEX IF NOT EXISTS idx_cas_number ON cosmetics(CasNumber)",
            "CREATE INDEX IF NOT EXISTS idx_company_name ON cosmetics(CompanyName)",
            "CREATE INDEX IF NOT EXISTS idx_brand_name ON cosmetics(BrandName)",
            "CREATE INDEX IF NOT EXISTS idx_category ON cosmetics(PrimaryCategory)",
            "CREATE INDEX IF NOT EXISTS idx_subcategory ON cosmetics(SubCategory)"
        ]

        for query in indexes:
            connection.execute(query)

        connection.commit()

        print(f"Successfully ingested {len(df)} records.")

    finally:
        connection.close()


if __name__ == "__main__":
    ingest_data()