from app.agents.sql_agent import SQLAgent


def test_sql_agent():

    agent = SQLAgent()

    result = agent.run(
        user_question=(
            "Find products containing Titanium dioxide "
            "discontinued in 2011"
        ),
        validated_entities={
            "chemical_name": ["Titanium dioxide"]
        },
        filters={
            "lifecycle_status": "discontinued",
            "discontinued_date_from": "2011-01-01",
            "discontinued_date_to": "2011-12-31"
        }
    )

    print("\nSQL Agent Result:")
    print(result)

    assert result["error"] is None
    assert result["sql_query"] is not None