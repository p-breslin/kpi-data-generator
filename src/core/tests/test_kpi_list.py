import logging
from typing import List

from core.clients.mysql_client import mysql_cursor
from core.utils.logger import setup_logging

log = logging.getLogger(__name__)

setup_logging(stream=False)


def get_kpi_list() -> List[str]:
    """Queries the database to get a unique list of all available KPI names.

    Returns:
        list[str]: list of strings, where each string is a KPI name.
    """
    log.info("Fetching list of KPIs from the database...")

    # Find all distinct kpiName values from the metricDefs table
    query = "SELECT distinct(kpiName) as kpiName FROM metricDefs WHERE kpiName != ''"

    kpi_names = []
    with mysql_cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()  # fetchall() returns a list of tuples
        kpi_names = [row[0] for row in results]

    log.info(f"Found {len(kpi_names)} KPIs.")
    return kpi_names


if __name__ == "__main__":
    try:
        available_kpis = get_kpi_list()

        if not available_kpis:
            print("\nNo KPIs found in the database.")
        else:
            print("\n--- Available KPIs ---")
            for kpi in available_kpis:
                print(f"- {kpi}")

    except Exception as e:
        log.error(f"Failed to fetch KPIs due to an error: {e}", exc_info=True)
        print("\nAn error occurred. Check logs.")
