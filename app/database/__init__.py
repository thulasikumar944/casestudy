from app.database.connection import get_db_connection

def execute_dynamic_query(sql: str, params: tuple = ()):
    """
    Execute dynamically generated, validated, read-only SQL.
    """
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        columns = [description[0] for description in cursor.description]
        records = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        return records
    finally:
        connection.close()