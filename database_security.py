import re


# =========================================================
# INTERNAL COLUMNS
# =========================================================

HIDDEN_COLUMNS = {
    # PostgreSQL / SQL Server common internal IDs
    "id",
    "customerid",
    "productid",
    "employeeid",
    "requestid",
    "addressid",
    "salesorderid",
    "salesorderdetailid",
    "productmodelid",
    "orderid",
    "productcategoryid",
    "rowguid",
}


# =========================================================
# REMOVE INTERNAL IDS FROM RESULTS
# =========================================================

def remove_internal_ids(rows):

    cleaned_rows = []

    for row in rows:

        cleaned_row = {
            key: value
            for key, value in row.items()
            if key.lower() not in HIDDEN_COLUMNS
        }

        cleaned_rows.append(cleaned_row)

    return cleaned_rows


# =========================================================
# CHECK FOR FORBIDDEN SQL OPERATIONS
# =========================================================

def contains_forbidden_operation(query: str, forbidden):

    query_lower = query.lower()

    for keyword in forbidden:

        # IMPORTANT:
        # \b ensures that "create" does NOT match
        # "CreatedDate" or "CreatedBy"

        pattern = rf"\b{re.escape(keyword)}\b"

        if re.search(pattern, query_lower):
            return keyword

    return None


# =========================================================
# CHECK SELECT
# =========================================================

def validate_select(query: str):

    query = query.strip()

    if not query:
        return False, "SQL query cannot be empty."

    query_lower = query.lower()

    if not query_lower.startswith("select"):
        return False, "Only SELECT queries are allowed."

    # Prevent SELECT *
    if re.search(r"\bselect\s+\*", query_lower):
        return (
            False,
            "SELECT * is not allowed. "
            "Please explicitly specify the required columns."
        )

    forbidden = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke",
    ]

    forbidden_operation = contains_forbidden_operation(
        query,
        forbidden
    )

    if forbidden_operation:

        return (
            False,
            f"SQL operation '{forbidden_operation}' "
            "is not allowed."
        )

    return True, ""


# =========================================================
# CHECK WRITE
# =========================================================

def validate_write(query: str):

    query = query.strip()

    if not query:
        return False, "SQL query cannot be empty."

    query_lower = query.lower()

    allowed = (
        query_lower.startswith("insert")
        or query_lower.startswith("update")
        or query_lower.startswith("delete")
    )

    if not allowed:

        return (
            False,
            "Only INSERT, UPDATE, and DELETE "
            "queries are allowed."
        )

    # -----------------------------------------------------
    # UPDATE MUST HAVE WHERE
    # -----------------------------------------------------

    if query_lower.startswith("update"):

        if not re.search(r"\bwhere\b", query_lower):

            return (
                False,
                "UPDATE queries must contain a WHERE clause."
            )

    # -----------------------------------------------------
    # DELETE MUST HAVE WHERE
    # -----------------------------------------------------

    if query_lower.startswith("delete"):

        if not re.search(r"\bwhere\b", query_lower):

            return (
                False,
                "DELETE queries must contain a WHERE clause."
            )

    # -----------------------------------------------------
    # FORBIDDEN OPERATIONS
    # -----------------------------------------------------

    forbidden = [
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke",
    ]

    forbidden_operation = contains_forbidden_operation(
        query,
        forbidden
    )

    if forbidden_operation:

        return (
            False,
            f"SQL operation '{forbidden_operation}' "
            "is not allowed."
        )

    return True, ""