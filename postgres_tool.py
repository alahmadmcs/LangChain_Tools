import os
import psycopg

from dotenv import load_dotenv

load_dotenv()


# =========================================================
# CONNECTION
# =========================================================

def get_connection():

    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    print("PostgreSQL configuration:")
    print("Host:", host)
    print("Port:", port)
    print("Database:", database)
    print("User:", user)
    print("Password:", "SET" if password else "MISSING")

    return psycopg.connect(
        host=host,
        port=port,
        dbname=database,
        user=user,
        password=password
    )


# =========================================================
# DATABASE SCHEMA
# =========================================================

def get_database_schema():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    table_name,
                    column_name,
                    data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY
                    table_name,
                    ordinal_position;
            """)

            rows = cursor.fetchall()

            schema = {}

            for table, column, data_type in rows:

                if table not in schema:

                    schema[table] = []

                schema[table].append({
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

        with connection.cursor() as cursor:

            # Get columns
            cursor.execute("""
                SELECT
                    table_name,
                    column_name,
                    data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """)

            columns = cursor.fetchall()

            # Get foreign keys
            cursor.execute("""
                SELECT
                    tc.table_name AS table_name,
                    kcu.column_name AS column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public';
            """)

            foreign_keys = cursor.fetchall()

            output = []

            output.append("DATABASE TABLES")
            output.append("================")

            current_table = None

            for table, column, data_type in columns:

                if table != current_table:

                    output.append("")
                    output.append(
                        f"TABLE: {table}"
                    )

                    current_table = table

                output.append(
                    f"  {column} ({data_type})"
                )

            output.append("")
            output.append("RELATIONSHIPS")
            output.append("================")

            for (
                table,
                column,
                foreign_table,
                foreign_column
            ) in foreign_keys:

                output.append(
                    f"{table}.{column} "
                    f"→ "
                    f"{foreign_table}.{foreign_column}"
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

        with connection.cursor() as cursor:

            cursor.execute(query)

            rows = cursor.fetchall()

            if not cursor.description:

                return []

            columns = [
                column.name
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


def execute_write(query: str):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(query)

            affected_rows = cursor.rowcount

            connection.commit()

            return affected_rows

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()