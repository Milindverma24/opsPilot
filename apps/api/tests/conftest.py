import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.core.database import Base, get_db
from apps.api.app.core.security import get_password_hash
from apps.api.app.models import (
    Organization, User, Role, Permission, Agent, Tool, Policy, PolicyRule,
    UserSession, PasswordResetToken
)
from apps.api.app.main import app

TEST_DATABASE_URL = "sqlite:///./test_opspilot.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed test orgs
    acme = Organization(name="Acme Test", slug="acme-test", country="India", currency="INR", status="ACTIVE")
    beta = Organization(name="Beta Corp", slug="beta-corp", country="India", currency="INR", status="ACTIVE")
    beta_test = Organization(name="Beta Test", slug="beta-test", country="India", currency="INR", status="ACTIVE")
    globex = Organization(name="Globex Manufacturing", slug="globex-manufacturing", country="India", currency="INR", status="ACTIVE")
    db.add_all([acme, beta, beta_test, globex])
    db.flush()

    # Seed roles & permissions
    perms_data = [
        ("organization.read", "View org", "organization"),
        ("organization.update", "Update org", "organization"),
        ("users.read", "View users", "users"),
        ("users.create", "Create users", "users"),
        ("users.update", "Update users", "users"),
        ("users.delete", "Delete users", "users"),
        ("invoices.read", "View invoices", "invoices"),
        ("invoices.create", "Create invoices", "invoices"),
        ("invoices.approve", "Approve invoices", "invoices"),
        ("invoices.reject", "Reject invoices", "invoices"),
        ("approvals.read", "Read approvals", "approvals"),
        ("approvals.approve", "Sign off approvals", "approvals"),
        ("audit.read", "View audit logs", "audit"),
        ("documents.read", "View documents", "documents"),
        ("documents.upload", "Upload documents", "documents"),
        ("tools.execute", "Execute tools", "tools"),
        ("workflows.read", "Read workflows", "workflows"),
        ("workflows.create", "Create workflows", "workflows")
    ]
    perm_objs = {}
    for pname, pdesc, pmod in perms_data:
        p = Permission(name=pname, description=pdesc, module=pmod)
        db.add(p)
        perm_objs[pname] = p
    db.flush()

    r_admin = Role(name="SUPER_ADMIN", description="Super Admin role", is_system=True)
    r_admin.permissions = list(perm_objs.values())

    r_fm = Role(name="FINANCE_MANAGER", description="Finance Manager role", is_system=True)
    r_fm.permissions = [perm_objs[k] for k in ["invoices.read", "invoices.create", "invoices.approve", "invoices.reject", "approvals.read", "approvals.approve", "audit.read", "users.read"]]

    r_fu = Role(name="FINANCE_USER", description="Finance User role", is_system=True)
    r_fu.permissions = [perm_objs[k] for k in ["invoices.read", "invoices.create", "approvals.read"]]

    r_emp = Role(name="EMPLOYEE", description="Employee role", is_system=True)
    r_emp.permissions = [perm_objs[k] for k in ["documents.read", "documents.upload"]]

    db.add_all([r_admin, r_fm, r_fu, r_emp])
    db.flush()

    pw = get_password_hash("DemoPassword123!")
    pw_test = get_password_hash("TestPassword123!")

    # Users
    u1 = User(organization_id=acme.id, email="finance@acme.test", password_hash=pw, full_name="Finance Manager", role="FINANCE_MANAGER", role_id=r_fm.id, status="ACTIVE", is_active=True, email_verified=True)
    u2 = User(organization_id=acme.id, email="finance@acme-test.com", password_hash=pw_test, full_name="Finance Tester", role="FINANCE_MANAGER", role_id=r_fm.id, status="ACTIVE", is_active=True, email_verified=True)
    u3 = User(organization_id=acme.id, email="admin@acme.test", password_hash=pw, full_name="Acme Admin", role="SUPER_ADMIN", role_id=r_admin.id, status="ACTIVE", is_active=True, is_superuser=True, email_verified=True)
    u4 = User(organization_id=beta.id, email="admin@beta.test", password_hash=pw, full_name="Beta Admin", role="SUPER_ADMIN", role_id=r_admin.id, status="ACTIVE", is_active=True, is_superuser=True, email_verified=True)
    u5 = User(organization_id=beta_test.id, email="admin@beta-test.com", password_hash=pw, full_name="Beta Test Admin", role="SUPER_ADMIN", role_id=r_admin.id, status="ACTIVE", is_active=True, is_superuser=True, email_verified=True)
    u6 = User(organization_id=globex.id, email="admin@globex.test", password_hash=pw, full_name="Globex Admin", role="SUPER_ADMIN", role_id=r_admin.id, status="ACTIVE", is_active=True, is_superuser=True, email_verified=True)
    u7 = User(organization_id=globex.id, email="finance@globex.test", password_hash=pw, full_name="Globex Finance", role="FINANCE_MANAGER", role_id=r_fm.id, status="ACTIVE", is_active=True, email_verified=True)
    u8 = User(organization_id=acme.id, email="clerk@acme.test", password_hash=pw, full_name="Finance Clerk", role="FINANCE_USER", role_id=r_fu.id, status="ACTIVE", is_active=True, email_verified=True)
    u9 = User(organization_id=acme.id, email="suspended@acme.test", password_hash=pw, full_name="Suspended User", role="EMPLOYEE", role_id=r_emp.id, status="SUSPENDED", is_active=False, email_verified=True)

    db.add_all([u1, u2, u3, u4, u5, u6, u7, u8, u9])

    # 11 Specialized Agents
    agents_data = [
        ("Intake Agent", "INTAKE", "Sanitizes and prepares raw documents"),
        ("Classification Agent", "CLASSIFICATION", "Categorizes documents into domain streams"),
        ("Extraction Agent", "EXTRACTION", "Extracts structured entity schemas"),
        ("Validation Agent", "VALIDATION", "Performs mathematical and integrity checks"),
        ("Reasoning Agent", "REASONING", "Performs multi-step operational synthesis"),
        ("Policy Agent", "POLICY", "Evaluates business compliance rules"),
        ("Risk Agent", "RISK", "Evaluates transaction risk score"),
        ("Planning Agent", "PLANNING", "Formulates sequential action plans"),
        ("Execution Agent", "EXECUTION", "Safely invokes approved tools"),
        ("Communication Agent", "COMMUNICATION", "Generates notifications and customer responses"),
        ("Supervisor Agent", "SUPERVISOR", "Controls workflow state transitions and HITL pauses")
    ]
    for aname, acode, adesc in agents_data:
        ag = Agent(name=aname, agent_type=acode, description=adesc, system_prompt="Operational directive", model="gpt-4o", enabled=True)
        db.add(ag)

    # Controlled Tools
    # Phase 8 full tool registry seed
    from scripts.seed_tool_registry import TOOL_DEFINITIONS
    existing_tool_names = {t.name for t in db.query(Tool).all()}
    for defn in TOOL_DEFINITIONS:
        if defn["name"] not in existing_tool_names:
            tool = Tool(**defn, enabled=True)
            db.add(tool)

    # Policies
    pol1 = Policy(organization_id=acme.id, name="High-Value Invoice Threshold", code="FIN-001", department="FINANCE", description="Invoices > 100k require approval", enabled=True)
    db.add(pol1)
    db.flush()
    r1 = PolicyRule(organization_id=acme.id, policy_id=pol1.id, name="FIN-001 Rule", condition="invoice.total > 100000", action="REQUIRE_APPROVAL", priority="HIGH", enabled=True)
    db.add(r1)

    db.commit()
    db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_opspilot.db"):
        os.remove("./test_opspilot.db")


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def org_and_seed_data(db_session):
    """Shared fixture: active UrbanThread org with customer, product, order."""
    from apps.api.app.models.tenant import Organization
    from apps.api.app.models.operations import Customer
    from apps.api.app.models.ecommerce import (
        Order, Product, ProductVariant, Shipment, Payment,
    )
    from apps.api.app.models.agent import AIEmployee

    org = db_session.query(Organization).filter_by(slug="urbanthread-test").first()
    if not org:
        org = Organization(
            name="UrbanThread Test",
            slug="urbanthread-test",
            industry="Fashion / Apparel",
            currency="INR",
            status="ACTIVE",
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

    customer = db_session.query(Customer).filter_by(
        organization_id=org.id, email="customer@urbanthread.local"
    ).first()
    if not customer:
        customer = Customer(
            organization_id=org.id,
            name="Priya Sharma",
            email="customer@urbanthread.local",
            phone="+919876543210",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)

    prod = db_session.query(Product).filter_by(
        organization_id=org.id, sku="SKU-TSHIRT-BLK"
    ).first()
    if not prod:
        prod = Product(
            organization_id=org.id,
            sku="SKU-TSHIRT-BLK",
            name="Classic Organic Cotton T-Shirt",
            brand="UrbanThread",
            base_price=999.0,
            status="ACTIVE",
        )
        db_session.add(prod)
        db_session.commit()
        db_session.refresh(prod)

    order = db_session.query(Order).filter_by(
        organization_id=org.id, order_number="ORD-P8-001"
    ).first()
    if not order:
        order = Order(
            organization_id=org.id,
            customer_id=customer.id,
            order_number="ORD-P8-001",
            status="CONFIRMED",
            payment_status="PAID",
            fulfillment_status="PENDING",
            total_amount=1998.0,
            currency="INR",
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        payment = Payment(
            organization_id=org.id,
            order_id=order.id,
            amount=1998.0,
            currency="INR",
            status="COMPLETED",
            payment_method_type="CARD",
            provider="MOCK",
            payment_reference="MOCK-TXN-001",
        )
        db_session.add(payment)
        db_session.commit()

    emp = db_session.query(AIEmployee).filter_by(organization_id=org.id).first()
    if not emp:
        emp = AIEmployee(
            organization_id=org.id,
            name="Aria - UrbanThread AI",
            role="AI_OPERATIONS_EMPLOYEE",
            status="ACTIVE",
            permissions=["orders.read", "orders.cancel", "products.read", "refunds.request"],
            configuration={"provider": "deterministic"},
        )
        db_session.add(emp)
        db_session.commit()

    return {"org": org, "customer": customer, "order": order, "product": prod}
