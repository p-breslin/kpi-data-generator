import json
import logging
import sys

from core.clients.domain_mgmt import DomainMgmtApiClient
from core.configs import cfg
from core.utils.logger import setup_logging

setup_logging(level=2, stream=False)
log = logging.getLogger(__name__)


def save_json(file, filename):
    with open(f"{filename}.json", "w") as f:
        json.dump(file, f, indent=2)


def main(save_definitions=False, save_verbose=False):
    """Queries model information (KPIs, functions, roles, contexts, dicts)."""
    client = DomainMgmtApiClient(
        base_url=cfg.ONBOARDING_API_URL,
        email=cfg.ADMIN_EMAIL,
        password=cfg.ADMIN_PASSWORD,
    )
    industry_id = cfg.INDUSTRY_ID
    customer_email = cfg.CUSTOMER_EMAIL

    try:
        # Authenticate
        log.info("Authenticating partner and customer tokens...")
        client.authenticate()
        client.generate_customer_token(customer_email)

        # KPIs
        log.info("Querying KPIs...")
        kpi_dict = client.list_kpis(industry_id)
        kpis = kpi_dict.get("data", {})
        if not kpis:
            log.warning("Query Warning: No KPIs found in payload.")
        else:
            log.info(f"Found {len(kpis)} KPIs.")

            log.debug(json.dumps(kpis, indent=2))
            if save_verbose:
                save_json(kpis, "kpis")

            print("\n--- Useful KPI info ---\n")
            kpi_map = {}
            for kpi in kpis:
                # Transform the attributes list into a direct lookup dict
                attrs = {
                    attr.get("attributeName"): attr.get("defaultValue")
                    for attr in kpi.get("attributes", [])
                }
                try:
                    data_details = json.loads(kpi.get("data", "{}"))
                except json.JSONDecodeError:
                    data_details = {}

                # Assemble the profile using direct lookups
                kpi_map[kpi["id"]] = {
                    "kpi_id": kpi.get("id"),
                    "kpi_name": kpi.get("name"),
                    "display_name": kpi.get("displayName"),
                    "category": kpi.get("category"),
                    "definition": {
                        "description": data_details.get("formula", {}).get(
                            "description", "N/A"
                        ),
                        "source_table": data_details.get("formula", {})
                        .get("data_source", {})
                        .get("table"),
                    },
                    "business_rules": {
                        "goal": float(attrs.get("Goal"))
                        if attrs.get("Goal") is not None
                        else None,
                        "is_higher_better": attrs.get("GI", "").lower() == "more",
                        "unit_of_measure": attrs.get("UOM Display Name"),
                    },
                }
            print(json.dumps(kpi_map, indent=2))
            if save_definitions:
                save_json(kpi_map, "kpi_definitions")

        # Contexts
        log.info("Querying Contexts...")
        records = client.industry_metric_functions(industry_id)
        contexts = [r for r in records if r.get("typeName") == "Context"]
        log.info(f"Found {len(contexts)} Contexts.")

        log.debug(json.dumps(contexts, indent=2))
        if save_verbose:
            save_json(contexts, "contexts")

        context_map = {}
        function_codes = []
        for ctx in contexts:
            function_codes.append(ctx.get("functionCode"))
            context_map[ctx["id"]] = {
                "context_id": ctx.get("id"),
                "context_name": ctx.get("name"),
                "source_column_name": ctx.get("attribute"),
            }
        print("\n--- Useful contexts info ---\n" + json.dumps(context_map, indent=2))
        if save_definitions:
            save_json(context_map, "ctx_definitions")

        # Dictionaries
        log.info("Querying Dictionaries...")
        for f_code in set(function_codes):
            dictionary = client.get_dictionary(f_code)

            log.debug(json.dumps(dictionary, indent=2))
            if save_verbose:
                save_json(dictionary, f"dictionary_{f_code}")

            print(f"\n--- Useful dictionary info for functionCode: {f_code} ---")

            dict_map = []
            for d in dictionary:
                # Only need the table name and its column definitions
                dict_map.append(
                    {
                        "table_name": d.get("name"),
                        "columns": [
                            {
                                "column_name": attr.get("name"),
                                "data_type": attr.get("dataType"),
                            }
                            for attr in d.get("entity_attributes", [])
                        ],
                    }
                )
            print(json.dumps(dict_map, indent=2))
            if save_definitions:
                save_json(dict_map, f"dict_definitions_{f_code}")

    except Exception as e:
        log.error(f"An error occurred during model query: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main(save_definitions=True)
