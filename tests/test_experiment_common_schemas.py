import pytest

from viu_mrob_tfm.experiment_common.schemas import SCHEMAS_V1, validate_columns


@pytest.mark.parametrize("schema_name,columns", SCHEMAS_V1.items())
def test_common_v1_schemas_accept_their_contract(schema_name: str, columns: tuple[str, ...]) -> None:
    assert validate_columns(schema_name, columns) == []


def test_common_v1_schema_reports_missing_columns() -> None:
    assert "world_sha256" in validate_columns("world_registry", ["world_id"])
