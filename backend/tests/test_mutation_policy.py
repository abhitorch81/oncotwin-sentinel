import asyncio

import pytest

from backend.app.config import Settings
from backend.app.data_scope import governed_dataset_urn
from backend.app.datahub_graphql import DataHubGraphQL
from backend.app.governed_repair import GovernedFeatureRepair
from backend.app.mcp_client import DataHubMCP
from backend.app.mutation_policy import (
    MutationPolicyError,
    is_mutation_operation,
    mutation_policy_snapshot,
    require_external_mutation,
)


VALID_SECRET = "test-only-approval-secret-32-chars"


def live_settings(**overrides):
    values = {
        "demo_mode": False,
        "tools_is_mutation_enabled": True,
        "human_approval_required": True,
        "writeback_approval_secret": VALID_SECRET,
        "bigquery_dataset": "oncotwin_agentic",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_demo_mode_blocks_external_writes_even_when_flag_is_enabled():
    settings = live_settings(demo_mode=True)
    with pytest.raises(MutationPolicyError, match="demo mode"):
        require_external_mutation(
            settings,
            operation="datahub_raise_incident",
            approval_secret=VALID_SECRET,
        )


def test_live_mode_fails_closed_when_mutations_are_disabled():
    settings = live_settings(tools_is_mutation_enabled=False)
    with pytest.raises(MutationPolicyError, match="disabled"):
        require_external_mutation(
            settings,
            operation="bigquery_execute_governed_repair",
            approval_secret=VALID_SECRET,
        )


def test_live_mode_rejects_default_or_incorrect_approval_secrets():
    insecure = live_settings(writeback_approval_secret="change-me")
    with pytest.raises(MutationPolicyError, match="securely configured"):
        require_external_mutation(
            insecure,
            operation="datahub_knowledge_writeback",
            approval_secret="change-me",
        )

    secure = live_settings()
    with pytest.raises(MutationPolicyError, match="invalid"):
        require_external_mutation(
            secure,
            operation="datahub_knowledge_writeback",
            approval_secret="wrong-secret",
        )


def test_live_mode_allows_only_the_fully_authorized_path():
    settings = live_settings()
    require_external_mutation(
        settings,
        operation="datahub_knowledge_writeback",
        approval_secret=VALID_SECRET,
    )
    snapshot = mutation_policy_snapshot(settings)
    assert snapshot["fail_closed"] is True
    assert snapshot["external_mutations_allowed"] is True


def test_mutation_tool_classifier_covers_destructive_verbs():
    for name in (
        "create_document",
        "delete_tag",
        "raise_incident",
        "resolve_incident",
        "save_document",
        "update_description",
        "upsert_contract",
        "write_metadata",
    ):
        assert is_mutation_operation(name) is True
    assert is_mutation_operation("get_lineage") is False
    assert is_mutation_operation("search") is False


def test_agentic_dataset_scope_is_used_in_datahub_urns():
    settings = live_settings()
    urn = governed_dataset_urn(settings, "project-test", "feature_quality")
    assert ".oncotwin_agentic.progression_features" in urn
    assert ".oncotwin.progression_features" not in urn


def test_graphql_transport_blocks_mutation_before_network_access():
    settings = live_settings(tools_is_mutation_enabled=False)
    with pytest.raises(MutationPolicyError, match="disabled"):
        asyncio.run(
            DataHubGraphQL(settings).execute(
                "mutation { raiseIncident(input: {}) }",
                {},
                approval_secret=VALID_SECRET,
            )
        )


def test_bigquery_transport_blocks_mutation_before_client_creation():
    settings = live_settings(tools_is_mutation_enabled=False)
    repair = GovernedFeatureRepair(settings)
    with pytest.raises(MutationPolicyError, match="disabled"):
        repair._query(
            "INSERT INTO `project.dataset.table` (value) VALUES (1)",
            "unit-test",
            "mission-test",
            VALID_SECRET,
        )


def test_mcp_adapter_blocks_mutation_before_server_start():
    settings = live_settings(tools_is_mutation_enabled=False)
    with pytest.raises(MutationPolicyError, match="disabled"):
        asyncio.run(
            DataHubMCP(settings).call(
                "update_description",
                {"urn": "urn:test"},
                approval_secret=VALID_SECRET,
            )
        )
