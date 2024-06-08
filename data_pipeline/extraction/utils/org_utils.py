import sqlite3

"""
Function Library containing functions related to the target organizations
"""


def get_company_names(insight_db_conn: sqlite3.Connection) -> list[(int, str)]:
    """
        Retrieves the list of company names from the insights database

        Parameters:
        @insight_db_conn - SQLite Connection object connected to the insights database

        Returns:
         list of tuples for the form (company_id, company_name)
        """
    sql = "SELECT id, name FROM organisations ORDER BY id"
    cur = insight_db_conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    if len(rows) == 0:
        return []
    else:
        return rows