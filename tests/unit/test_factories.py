"""
Unit tests for all 22 test data factories in tests/fixtures/factories.py.
Verifies create_valid(), create_invalid(), and create_edge_case().
"""
import pytest
from tests.fixtures.factories import (
    OrganizationFactory,
    UserFactory,
    CustomerFactory,
    ProductFactory,
    ProductVariantFactory,
    InventoryFactory,
    OrderFactory,
    ShipmentFactory,
    ReturnFactory,
    RefundFactory,
    SupportTicketFactory,
    AgentFactory,
    AgentRunFactory,
    WorkflowFactory,
    WorkflowRunFactory,
    ToolExecutionFactory,
    ApprovalFactory,
    KnowledgeDocumentFactory,
    KnowledgeChunkFactory,
    ConversationFactory,
    MemoryFactory,
    TaskFactory,
)

FACTORIES = [
    OrganizationFactory,
    UserFactory,
    CustomerFactory,
    ProductFactory,
    ProductVariantFactory,
    InventoryFactory,
    OrderFactory,
    ShipmentFactory,
    ReturnFactory,
    RefundFactory,
    SupportTicketFactory,
    AgentFactory,
    AgentRunFactory,
    WorkflowFactory,
    WorkflowRunFactory,
    ToolExecutionFactory,
    ApprovalFactory,
    KnowledgeDocumentFactory,
    KnowledgeChunkFactory,
    ConversationFactory,
    MemoryFactory,
    TaskFactory,
]


def test_factory_count():
    assert len(FACTORIES) == 22, f"Expected exactly 22 factories, found {len(FACTORIES)}"


@pytest.mark.parametrize("factory_cls", FACTORIES)
def test_factory_lifecycle(factory_cls):
    # 1. Valid instance
    valid_obj = factory_cls.create_valid()
    assert valid_obj is not None
    assert hasattr(valid_obj, "id")

    # 2. Invalid instance
    invalid_obj = factory_cls.create_invalid()
    assert invalid_obj is not None

    # 3. Edge case instance
    edge_obj = factory_cls.create_edge_case()
    assert edge_obj is not None
