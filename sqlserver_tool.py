import os
import pyodbc
import re
from dotenv import load_dotenv

load_dotenv()


# =========================================================
# CONNECTION
# =========================================================

def get_connection():

    server = os.getenv("SQLSERVER_SERVER")
    database = os.getenv("SQLSERVER_DATABASE")
    user = os.getenv("SQLSERVER_USERNAME")
    password = os.getenv("SQLSERVER_PASSWORD")
    driver = os.getenv(
        "SQLSERVER_DRIVER",
        "ODBC Driver 18 for SQL Server"
    )

    # print("SQL Server configuration:")
    # print("Server:", server)
    # print("Database:", database)
    # print("User:", user)
    # print(
    #     "Password:",
    #     "SET" if password else "MISSING"
    # )
    # print("Driver:", driver)

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
    )

    return pyodbc.connect(
        connection_string
    )


# =========================================================
# DATABASE SCHEMA
# =========================================================

def get_database_schema():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                TABLE_SCHEMA,
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            ORDER BY
                TABLE_SCHEMA,
                TABLE_NAME,
                ORDINAL_POSITION;
        """)

        rows = cursor.fetchall()

        schema = {}

        for (
            table_schema,
            table,
            column,
            data_type
        ) in rows:

            table_key = (
                f"{table_schema}.{table}"
            )

            if table_key not in schema:

                schema[table_key] = []

            schema[table_key].append({
                "column": column,
                "type": data_type
            })

        return schema

    finally:

        connection.close()


# =========================================================
# FORMAT SCHEMA FOR LLM
# =========================================================

def get_schema_text():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # =================================================
        # GET COLUMNS
        # =================================================

        cursor.execute("""
            SELECT
                TABLE_SCHEMA,
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            ORDER BY
                TABLE_SCHEMA,
                TABLE_NAME,
                ORDINAL_POSITION;
        """)

        columns = cursor.fetchall()

        # =================================================
        # GET FOREIGN KEYS
        # =================================================

        cursor.execute("""
            SELECT
                SCHEMA_NAME(tp.schema_id)
                    AS table_schema,

                tp.name
                    AS table_name,

                cp.name
                    AS column_name,

                SCHEMA_NAME(tr.schema_id)
                    AS foreign_schema,

                tr.name
                    AS foreign_table,

                cr.name
                    AS foreign_column

            FROM sys.foreign_keys fk

            INNER JOIN sys.foreign_key_columns fkc
                ON fk.object_id = fkc.constraint_object_id

            INNER JOIN sys.tables tp
                ON fkc.parent_object_id = tp.object_id

            INNER JOIN sys.columns cp
                ON fkc.parent_object_id = cp.object_id
                AND fkc.parent_column_id = cp.column_id

            INNER JOIN sys.tables tr
                ON fkc.referenced_object_id = tr.object_id

            INNER JOIN sys.columns cr
                ON fkc.referenced_object_id = cr.object_id
                AND fkc.referenced_column_id = cr.column_id

            ORDER BY
                table_schema,
                table_name,
                column_name;
        """)

        foreign_keys = cursor.fetchall()

        # =================================================
        # BUILD TEXT
        # =================================================

        output = []

        output.append(
            "SQL SERVER DATABASE TABLES"
        )

        output.append(
            "=========================="
        )

        current_table = None

        for (
            table_schema,
            table,
            column,
            data_type
        ) in columns:

            table_name = (
                f"{table_schema}.{table}"
            )

            if table_name != current_table:

                output.append("")

                output.append(
                    f"TABLE: {table_name}"
                )

                current_table = table_name

            output.append(
                f"  {column} ({data_type})"
            )

        # =================================================
        # RELATIONSHIPS
        # =================================================

        output.append("")

        output.append(
            "RELATIONSHIPS"
        )

        output.append(
            "=========================="
        )

        for (
            table_schema,
            table,
            column,
            foreign_schema,
            foreign_table,
            foreign_column
        ) in foreign_keys:

            output.append(
                f"{table_schema}.{table}.{column} "
                f"→ "
                f"{foreign_schema}.{foreign_table}."
                f"{foreign_column}"
            )

        return "\n".join(output)

    finally:

        connection.close()


# =========================================================
# EXECUTE SELECT
# =========================================================

def execute_select(query: str):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(query)

        rows = cursor.fetchall()

        if not cursor.description:

            return []

        columns = [
            column[0]
            for column in cursor.description
        ]

        results = []

        for row in rows:

            results.append(
                dict(
                    zip(
                        columns,
                        row
                    )
                )
            )

        return results

    finally:

        connection.close()


# =========================================================
# EXECUTE WRITE
# =========================================================

def execute_write(query: str):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(query)

        affected_rows = cursor.rowcount

        connection.commit()

        return affected_rows

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()