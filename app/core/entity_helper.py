import logging

from app.database.connection import get_db_connection

logger = logging.getLogger(__name__)

SOURCE_TABLE = "cosmetics"

ENTITY_COLUMNS = {
    "chemical_name": "ChemicalName",
    "cas_number": "CasNumber",
    "company_name": "CompanyName",
    "brand_name": "BrandName",
    "product_name": "ProductName"
}


class EntityHelper:

    def __init__(self):
        self.connection = get_db_connection()

    # -----------------------------------------
    # 1. Create Entity Catalog Table
    # -----------------------------------------

    def create_catalog_table(self):

        query = """
        CREATE TABLE IF NOT EXISTS entity_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_value TEXT NOT NULL,
            normalized_value TEXT NOT NULL,
            UNIQUE(entity_type, normalized_value)
        )
        """

        try:
            self.connection.execute(query)

            self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_catalog_lookup
                ON entity_catalog(entity_type, normalized_value)
            """)

            self.connection.commit()

            logger.info("Entity catalog table created successfully")

        except Exception:
            self.connection.rollback()
            logger.exception("Failed to create entity catalog")
            raise

    # -----------------------------------------
    # 2. Populate Entity Catalog
    # -----------------------------------------

    def populate_catalog(self):

        self.create_catalog_table()

        try:
            for entity_type, column_name in ENTITY_COLUMNS.items():

                query = f"""
                    INSERT OR IGNORE INTO entity_catalog (
                        entity_type,
                        entity_value,
                        normalized_value
                    )
                    SELECT DISTINCT
                        ?,
                        TRIM({column_name}),
                        LOWER(TRIM({column_name}))
                    FROM {SOURCE_TABLE}
                    WHERE {column_name} IS NOT NULL
                      AND TRIM({column_name}) != ''
                """

                self.connection.execute(
                    query,
                    (entity_type,)
                )

                logger.info(
                    "Entity catalog populated: %s",
                    entity_type
                )

            self.connection.commit()

            logger.info("Entity catalog population completed")

        except Exception:
            self.connection.rollback()
            logger.exception("Entity catalog population failed")
            raise

    # -----------------------------------------
    # 3. Validate Single Entity
    # -----------------------------------------

    def validate_entity(
        self,
        entity_type: str,
        value: str
    ) -> dict:

        if entity_type not in ENTITY_COLUMNS:
            raise ValueError(
                f"Unsupported entity type: {entity_type}"
            )

        if not value or not value.strip():
            return {
                "valid": False,
                "original_value": value,
                "matched_value": None
            }

        query = """
            SELECT entity_value
            FROM entity_catalog
            WHERE entity_type = ?
              AND normalized_value = ?
            LIMIT 1
        """

        result = self.connection.execute(
            query,
            (
                entity_type,
                value.strip().lower()
            )
        ).fetchone()

        return {
            "valid": result is not None,
            "original_value": value,
            "matched_value": result[0] if result else None
        }

    # -----------------------------------------
    # 4. Validate Extracted Entities
    # -----------------------------------------

    def validate_entities(self, extracted_entities):

        validation_results = {}
        valid_entities = {}
        invalid_entities = {}

        entities = (
            extracted_entities.model_dump()
            if hasattr(extracted_entities, "model_dump")
            else extracted_entities
        )

        for entity_type, values in entities.items():

            validation_results[entity_type] = []

            for value in values:

                result = self.validate_entity(
                    entity_type=entity_type,
                    value=value
                )

                validation_results[entity_type].append(result)

                if result["valid"]:

                    valid_entities.setdefault(
                        entity_type, []
                    ).append(result["matched_value"])

                else:

                    invalid_entities.setdefault(
                        entity_type, []
                    ).append(value)

        status = (
            "VALID"
            if not invalid_entities
            else "ENTITY_NOT_FOUND"
        )

        logger.info(
            "Entity validation completed | Status: %s",
            status
        )

        return {
            "status": status,
            "valid_entities": valid_entities,
            "invalid_entities": invalid_entities,
            "validation_results": validation_results
        }

    # -----------------------------------------
    # 5. Close Database Connection
    # -----------------------------------------

    def close(self):

        if self.connection:
            self.connection.close()