import json
import logging
from typing import Any, Dict

from core.clients.mysql_client import mysql_cursor
from core.utils.logger import setup_logging

log = logging.getLogger(__name__)

setup_logging(stream=False)


def get_kpi_profile(kpi_name: str) -> Dict[str, Any]:
    """Fetches a complete, structured profile for a given KPI.

    Queries the database, joining multiple tables to gather all relevant context, and formats it into a JSON object designed to be easily parsable by an LLM agent.

    Args:
        kpi_name (str): The official name of the KPI to profile.

    Returns:
        dict: contains the structured KPI profile, or None if not found.
    """
    log.info(f"Generating profile for KPI: '{kpi_name}'...")

    query = """
        SELECT
            -- Identity
            m.displayName,
            m.kpiName,
            m.id,
            -- Definition & Formula (from JSON)
            m.data->>'$.formula.description' AS definition,
            m.data->'$.formula' AS formula_details,
            -- Business Context
            m.isHigherBetter,
            m.metCriteriaPct,
            mc.name AS category,
            du.displayName AS data_unit,
            -- Hierarchy
            m.parentId,
            m.ctxName
        FROM
            metricDefs m
        LEFT JOIN
            dataUnitDefs du ON m.dataUnitDefId = du.id
        LEFT JOIN
            metricCategories mc ON m.metricCategoryId = mc.id
        LEFT JOIN
            metricTypeDefs mt ON m.typeId = mt.id
        WHERE
            m.kpiName = %s
        LIMIT 1;
    """

    with mysql_cursor() as cursor:
        cursor.execute(query, (kpi_name,))
        result = cursor.fetchone()

        if not result:
            log.warning(f"No data found for KPI '{kpi_name}'.")
            return None

        # Map the flat SQL result to a structured dictionary
        profile = {
            "identity": {
                "displayName": result[0],
                "kpiName": result[1],
                "id": result[2],
            },
            "description": result[3],
            "calculation_logic": {
                "formula_details": json.loads(result[4]) if result[4] else None
            },
            "business_context": {
                "is_higher_better": bool(result[5]),
                "goal_threshold_pct": result[6],
                "category": result[7],
                "data_unit": result[8],
            },
            "hierarchy": {"parent_id": result[9], "context_path": result[10]},
        }
        return profile


if __name__ == "__main__":
    kpi_to_profile = "Stories Closed"

    try:
        kpi_profile = get_kpi_profile(kpi_to_profile)

        if kpi_profile:
            print(f"\n--- KPI Profile for: {kpi_to_profile} ---\n")
            print(json.dumps(kpi_profile, indent=2))
        else:
            print(f"Could not generate a profile for '{kpi_to_profile}'.")

    except Exception as e:
        log.error(f"An error occurred during profile generation: {e}", exc_info=True)
