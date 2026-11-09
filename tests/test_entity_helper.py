from app.core.entity_helper import EntityHelper
from app.agents.entity_extractor import EntityExtractorAgent


def test_entity_helper():

    helper = EntityHelper()

    try:
        # Populate catalog
        helper.populate_catalog()

        # Test exact entity validation
        result = helper.validate_entity(
            entity_type="chemical_name",
            value="Titanium dioxide"
        )

        print("\nSingle Entity Validation:")
        print(result)

        assert result["valid"] is True

        # Test complete entity validation
        extractor = EntityExtractorAgent()

        extraction_result = extractor.extract_entities(
            "Find products containing Titanium dioxide "
            "manufactured by New Avon LLC"
        )

        validation_result = helper.validate_entities(
            extraction_result.entities
        )

        print("\nComplete Entity Validation:")
        print(validation_result)

        assert validation_result["status"] == "VALID"

    finally:
        helper.close()