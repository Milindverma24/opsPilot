import pytest
from fastapi.testclient import TestClient
from apps.api.app.main import app
from apps.api.app.core.database import SessionLocal
from apps.api.app.core.security import create_access_token, get_password_hash
from apps.api.app.models import (
    Organization, User, Role, Permission,
    Vendor, Customer, PurchaseOrder, Invoice,
    Complaint, Task, Workflow, Approval, Policy,
    KnowledgeDocument, AuditLog, Website, WebsitePage
)
from apps.api.app.services import (
    OrganizationService, UserService, CustomerService, VendorService,
    DocumentService, WebsiteService, KnowledgeService,
    InvoiceService, PurchaseOrderService, ComplaintService,
    TaskService, WorkflowService, PolicyService, AuditService
)
from scripts.seed import seed_database

client = TestClient(app)


def test_organization_creation(db_session):
    org = OrganizationService.create_organization(
        db=db_session,
        name="Delta Corp Industrial",
        slug="delta-corp-test",
        industry="Aerospace",
        description="Aviation components manufacturer",
        country="India",
        timezone="Asia/Kolkata",
        currency="INR"
    )
    assert org.id is not None
    assert org.slug == "delta-corp-test"
    assert org.currency == "INR"

    retrieved = OrganizationService.get_by_slug(db_session, "delta-corp-test")
    assert retrieved is not None
    assert retrieved.name == "Delta Corp Industrial"


def test_user_creation_and_rbac(db_session):
    org = OrganizationService.get_by_slug(db_session, "acme-test")
    user = UserService.create_user(
        db=db_session,
        organization_id=org.id,
        email="test.officer@acme.test",
        password="SecurePassword123!",
        full_name="Test Compliance Officer",
        role="FINANCE_MANAGER"
    )
    assert user.id is not None
    assert user.password_hash != "SecurePassword123!"
    assert "SecurePassword123!" not in user.password_hash

    # Fetch role and check permissions
    role = db_session.query(Role).filter_by(name="FINANCE_MANAGER").first()
    assert role is not None
    perm_names = [p.name for p in role.permissions]
    assert "invoices.approve" in perm_names
    assert "approvals.approve" in perm_names


def test_tenant_isolation_api(db_session):
    """
    Section 54: Tenant Isolation Test
    Create Company A and Company B.
    Create Invoice A belonging to Company A.
    Authenticate as user from Company B.
    Attempt GET /api/v1/invoices/{invoice_A}.
    Expected: 404 or 403. Never return Invoice A.
    """
    company_a = OrganizationService.get_by_slug(db_session, "acme-test")
    company_b = OrganizationService.get_by_slug(db_session, "beta-corp")

    # 1. Create Invoice in Company A
    inv_a = InvoiceService.create_invoice(
        db=db_session,
        organization_id=company_a.id,
        invoice_number="INV-TENANT-A-001",
        total=54000.0,
        subtotal=45000.0,
        tax=9000.0,
        status="RECEIVED"
    )
    assert inv_a.id is not None

    # 2. Authenticate as Company B user
    user_b = db_session.query(User).filter_by(email="admin@beta.test").first()
    assert user_b is not None
    assert user_b.organization_id == company_b.id

    token_b = create_access_token({
        "sub": user_b.id,
        "org_id": user_b.organization_id,
        "role": user_b.role,
        "email": user_b.email,
        "name": user_b.full_name
    })

    # 3. Company B attempts to access Invoice A
    headers = {"Authorization": f"Bearer {token_b}"}
    response = client.get(f"/api/v1/invoices/{inv_a.id}", headers=headers)

    # 4. Strict isolation assertion: must be 404 or 403, NEVER return invoice A
    assert response.status_code in [404, 403]
    assert response.status_code == 404
    assert "Invoice not found or access denied" in response.json()["detail"]


def test_customer_and_vendor_isolation(db_session):
    company_a = OrganizationService.get_by_slug(db_session, "acme-test")
    company_b = OrganizationService.get_by_slug(db_session, "beta-corp")

    # Create customer in Company A
    cust_a = CustomerService.create_customer(
        db=db_session,
        organization_id=company_a.id,
        name="Alpha Aerospace Client",
        customer_number="CUST-ALPHA-01",
        email="contact@alpha.test"
    )

    # Verify Company B cannot access it via service layer
    res_b = CustomerService.get_by_id(db_session, cust_a.id, organization_id=company_b.id)
    assert res_b is None


def test_invoice_creation_and_duplicate_check(db_session):
    org = OrganizationService.get_by_slug(db_session, "acme-test")
    inv_num = "INV-DUPCHECK-999"

    # Not duplicate initially
    assert InvoiceService.is_duplicate(db_session, inv_num, org.id) is False

    # Create invoice
    inv = InvoiceService.create_invoice(
        db=db_session,
        organization_id=org.id,
        invoice_number=inv_num,
        total=25000.0,
        subtotal=21000.0,
        tax=4000.0
    )
    assert inv.id is not None

    # Now duplicate detection returns True
    assert InvoiceService.is_duplicate(db_session, inv_num, org.id) is True


def test_purchase_order_matching(db_session):
    org = OrganizationService.get_by_slug(db_session, "acme-test")
    po = PurchaseOrderService.create_po(
        db=db_session,
        organization_id=org.id,
        po_number="PO-MATCH-TEST-01",
        total=100000.0,
        subtotal=84000.0,
        tax=16000.0,
        status="APPROVED"
    )

    # 1. Exact match
    match_exact = PurchaseOrderService.match_invoice_to_po(db_session, org.id, "PO-MATCH-TEST-01", 100000.0)
    assert match_exact["matched"] is True

    # 2. Variance within 5%
    match_within_tol = PurchaseOrderService.match_invoice_to_po(db_session, org.id, "PO-MATCH-TEST-01", 104000.0, tolerance=0.05)
    assert match_within_tol["matched"] is True

    # 3. Variance beyond 5%
    match_mismatch = PurchaseOrderService.match_invoice_to_po(db_session, org.id, "PO-MATCH-TEST-01", 125000.0, tolerance=0.05)
    assert match_mismatch["matched"] is False


def test_website_and_page_untrusted_data(db_session):
    org = OrganizationService.get_by_slug(db_session, "acme-test")
    web = WebsiteService.register_website(
        db=db_session,
        organization_id=org.id,
        url="https://acme-supplies.test",
        name="Acme Supplies Portal"
    )
    assert web.id is not None

    # Add page
    page1 = WebsiteService.add_or_update_page(
        db=db_session,
        website_id=web.id,
        organization_id=org.id,
        url="https://acme-supplies.test/terms",
        content="All sales Net 30 payment terms.",
        title="Terms & Conditions"
    )
    assert page1.id is not None
    assert page1.content_hash is not None

    # Deduplication test: re-adding same URL updates instead of duplicating
    page2 = WebsiteService.add_or_update_page(
        db=db_session,
        website_id=web.id,
        organization_id=org.id,
        url="https://acme-supplies.test/terms",
        content="Updated: All sales Net 45 payment terms.",
        title="Terms & Conditions V2"
    )
    assert page2.id == page1.id
    assert page2.content == "Updated: All sales Net 45 payment terms."


def test_immutable_audit_logging(db_session):
    org = OrganizationService.get_by_slug(db_session, "acme-test")
    log = AuditService.log_action(
        db=db_session,
        organization_id=org.id,
        actor_id="finance@acme.test",
        actor_type="USER",
        action="INVOICE_DISBURSED",
        resource_type="invoice",
        resource_id="INV-AUDIT-001",
        metadata={"amount": 99710.0, "vendor": "ABC Supplies"}
    )
    assert log.id is not None

    # Query audit logs
    logs = AuditService.list_logs(db_session, org.id, action="INVOICE_DISBURSED")
    assert len(logs) > 0
    assert logs[0].action == "INVOICE_DISBURSED"


def test_seed_idempotency(db_session):
    """
    Section 52: Seed Idempotency Test
    Running seed command multiple times must not create duplicate records.
    """
    # Count before
    vendors_count_1 = db_session.query(Vendor).count()
    policies_count_1 = db_session.query(Policy).count()

    # Re-run seed
    seed_database()

    # Count after
    vendors_count_2 = db_session.query(Vendor).count()
    policies_count_2 = db_session.query(Policy).count()

    assert vendors_count_1 == vendors_count_2
    assert policies_count_1 == policies_count_2


def test_ai_direct_database_access_prevention():
    """
    Section 55: AI Database Access Test
    The AI agent CANNOT directly execute raw SQL or bypass service layers.
    Architecture requires: Agent -> Tool -> Service -> Authorization -> Database.
    """
    from apps.api.app.agents.base_agent import BaseAgent
    from apps.api.app.tools.registry import ToolRegistry, ToolExecutionError

    # 1. BaseAgent does not possess a DB session or raw SQL execution tool
    assert not hasattr(BaseAgent, "execute_sql")
    assert not hasattr(BaseAgent, "raw_query")

    # 2. Attempting to invoke an unauthorized or unregistered SQL tool is blocked by ToolRegistry
    with pytest.raises(ToolExecutionError) as exc_info:
        ToolRegistry.execute(
            tool_name="raw_sql_query",
            arguments={"query": "SELECT * FROM invoices;"},
            organization_id="acme-test",
            actor_id="ai_agent"
        )
    assert "does not exist" in str(exc_info.value).lower()
