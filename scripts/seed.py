"""
Idempotent Database Seed Script for OpsPilot Phase 2.
Populates complete company data foundation:
- Organization: Acme Industries & Beta Corp
- 8 Departments (Finance, Operations, Support, Sales, HR, IT, Procurement, Legal)
- Teams & Role-Based Permissions
- 5 Demo Users (admin, finance, operations, support, auditor)
- 25 Vendors
- 50 Customers
- 30 Purchase Orders
- 50 Invoices (Normal, High-Value, Duplicate, Missing PO, Suspicious, etc.)
- 30 Complaints (Normal, Urgent, Critical, Refund Request, etc.)
- 20 Tasks
- 20 Workflows
- 10 Policies with compliance rules
- 15 Knowledge Documents & SOPs
"""

import sys
import uuid
import datetime
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apps.api.app.core.database import SessionLocal, engine, Base
from apps.api.app.core.database_init import init_db
from apps.api.app.core.security import get_password_hash
from apps.api.app.models import (
    Organization, Department, Team, User, Role, Permission,
    Vendor, Customer, PurchaseOrder, PurchaseOrderItem,
    Invoice, InvoiceLineItem, Complaint, Task,
    Workflow, WorkflowStep, Approval,
    Agent, Tool, Policy, PolicyRule,
    KnowledgeDocument, KnowledgeChunk,
    AuditLog, Notification, Integration
)
from apps.api.app.services.knowledge_service import KnowledgeService


def seed_database():
    print("Starting Idempotent Phase 2 Seed Script for OpsPilot...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Organizations
        org = db.query(Organization).filter_by(slug="acme-test").first()
        if not org:
            org = Organization(
                name="Acme Industries",
                slug="acme-test",
                industry="Manufacturing & Industrial Tech",
                description="Global industrial manufacturing and operations leader.",
                website_url="https://acme-industries.test",
                email_domain="acme.test",
                country="India",
                timezone="Asia/Kolkata",
                currency="INR",
                status="ACTIVE",
                settings={"autonomy_level": "LEVEL_2", "max_auto_disburse": 50000}
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            print("✓ Created Acme Industries organization")
        else:
            print("✓ Acme Industries organization already exists")

        # Secondary organization for tenant isolation tests
        beta_org = db.query(Organization).filter_by(slug="beta-corp").first()
        if not beta_org:
            beta_org = Organization(
                name="Beta Corp",
                slug="beta-corp",
                industry="Logistics & Retail",
                description="Secondary enterprise tenant for data isolation testing.",
                website_url="https://beta-corp.test",
                email_domain="beta.test",
                country="India",
                timezone="Asia/Kolkata",
                currency="INR",
                status="ACTIVE",
                settings={"autonomy_level": "LEVEL_1"}
            )
            db.add(beta_org)
            db.commit()
            db.refresh(beta_org)
            print("✓ Created Beta Corp secondary tenant")

        # Globex Manufacturing organization per Section 71
        globex_org = db.query(Organization).filter_by(slug="globex-manufacturing").first()
        if not globex_org:
            globex_org = Organization(
                name="Globex Manufacturing",
                slug="globex-manufacturing",
                industry="Heavy Industrial Manufacturing",
                description="Secondary industrial tenant for cross-tenant isolation testing.",
                website_url="https://globex.test",
                email_domain="globex.test",
                country="India",
                timezone="Asia/Kolkata",
                currency="INR",
                status="ACTIVE",
                settings={"autonomy_level": "LEVEL_1"}
            )
            db.add(globex_org)
            db.commit()
            db.refresh(globex_org)
            print("✓ Created Globex Manufacturing organization")

        # 2. Departments (8 core departments)
        dept_names = ["Finance", "Operations", "Support", "Sales", "HR", "IT", "Procurement", "Legal"]
        dept_map = {}
        for dname in dept_names:
            dept = db.query(Department).filter_by(organization_id=org.id, name=dname).first()
            if not dept:
                dept = Department(
                    organization_id=org.id,
                    name=dname,
                    description=f"Acme {dname} Corporate Division"
                )
                db.add(dept)
                db.commit()
                db.refresh(dept)
            dept_map[dname] = dept
        print(f"✓ Verified {len(dept_map)} Departments")

        # 3. Teams
        teams_data = [
            ("Accounts Payable", "Finance"),
            ("Financial Controller", "Finance"),
            ("Operations Dispatch", "Operations"),
            ("Tier 2 Customer Care", "Support"),
            ("Procurement Sourcing", "Procurement"),
            ("IT Infrastructure", "IT")
        ]
        for tname, dname in teams_data:
            t = db.query(Team).filter_by(organization_id=org.id, name=tname).first()
            if not t:
                t = Team(
                    organization_id=org.id,
                    department_id=dept_map[dname].id,
                    name=tname,
                    description=f"{tname} operating under {dname}"
                )
                db.add(t)
        db.commit()
        print("✓ Verified Teams")

        # 4. Roles & Permissions
        permissions_list = [
            ("organization.read", "View company organization info", "organization"),
            ("organization.update", "Update company settings", "organization"),
            ("users.read", "Read user directory", "users"),
            ("users.create", "Create company users", "users"),
            ("users.update", "Update company users", "users"),
            ("users.delete", "Delete company users", "users"),
            ("departments.read", "View departments", "departments"),
            ("departments.manage", "Manage departments", "departments"),
            ("teams.read", "View teams", "teams"),
            ("teams.manage", "Manage teams", "teams"),
            ("documents.read", "View documents", "documents"),
            ("documents.upload", "Upload new documents", "documents"),
            ("documents.delete", "Delete documents", "documents"),
            ("invoices.read", "View invoices", "invoices"),
            ("invoices.create", "Create invoices", "invoices"),
            ("invoices.update", "Update invoices", "invoices"),
            ("invoices.approve", "Approve invoice payments", "invoices"),
            ("invoices.reject", "Reject invoices", "invoices"),
            ("purchase_orders.read", "View purchase orders", "purchase_orders"),
            ("purchase_orders.create", "Create purchase orders", "purchase_orders"),
            ("purchase_orders.update", "Update purchase orders", "purchase_orders"),
            ("customers.read", "View customer records", "customers"),
            ("customers.update", "Update customer records", "customers"),
            ("vendors.read", "View vendor directory", "vendors"),
            ("vendors.update", "Update vendor directory", "vendors"),
            ("complaints.read", "View customer complaints", "complaints"),
            ("complaints.update", "Resolve complaints", "complaints"),
            ("tasks.read", "View operational tasks", "tasks"),
            ("tasks.create", "Create tasks", "tasks"),
            ("tasks.update", "Update tasks", "tasks"),
            ("tasks.assign", "Assign tasks", "tasks"),
            ("workflows.read", "Monitor workflows", "workflows"),
            ("workflows.create", "Trigger workflows", "workflows"),
            ("workflows.cancel", "Cancel workflows", "workflows"),
            ("approvals.read", "View pending approvals", "approvals"),
            ("approvals.approve", "Sign off approvals", "approvals"),
            ("approvals.reject", "Reject approval requests", "approvals"),
            ("agents.read", "Inspect agent fleet telemetry", "agents"),
            ("agents.configure", "Configure agents", "agents"),
            ("tools.read", "Inspect tools registry", "tools"),
            ("tools.execute", "Execute controlled tools", "tools"),
            ("knowledge.read", "Search knowledge base", "knowledge"),
            ("knowledge.upload", "Index new SOPs", "knowledge"),
            ("knowledge.delete", "Delete SOPs", "knowledge"),
            ("policies.read", "Read compliance policies", "policies"),
            ("policies.create", "Create policies", "policies"),
            ("policies.update", "Update policies", "policies"),
            ("policies.delete", "Delete policies", "policies"),
            ("audit.read", "Inspect immutable audit trail", "audit"),
            ("analytics.read", "View business analytics", "analytics")
        ]
        perm_objs = {}
        for pname, pdesc, pmod in permissions_list:
            p = db.query(Permission).filter_by(name=pname).first()
            if not p:
                p = Permission(name=pname, description=pdesc, module=pmod)
                db.add(p)
                db.commit()
                db.refresh(p)
            perm_objs[pname] = p

        roles_specs = [
            ("SUPER_ADMIN", "Full organizational administrator privileges", list(perm_objs.values())),
            ("ADMIN", "Administrative oversight of business operations", [p for k, p in perm_objs.items() if "audit" not in k]),
            ("FINANCE_MANAGER", "Sign-off authority for high-value invoices and disbursements", [perm_objs[k] for k in ["invoices.read", "invoices.create", "invoices.update", "invoices.approve", "invoices.reject", "approvals.read", "approvals.approve", "approvals.reject", "vendors.read", "purchase_orders.read", "audit.read", "workflows.read", "analytics.read", "users.read"]]),
            ("FINANCE_USER", "Finance operations without high-value approval authority", [perm_objs[k] for k in ["invoices.read", "invoices.create", "invoices.update", "vendors.read", "purchase_orders.read", "approvals.read", "users.read"]]),
            ("OPERATIONS_MANAGER", "Manages automated workflows, documents, and tasks", [perm_objs[k] for k in ["workflows.read", "workflows.create", "workflows.cancel", "documents.read", "documents.upload", "tasks.read", "tasks.create", "tasks.update", "tools.read", "tools.execute", "audit.read", "users.read"]]),
            ("SUPPORT_MANAGER", "Customer complaints resolution and refund authority", [perm_objs[k] for k in ["customers.read", "customers.update", "complaints.read", "complaints.update", "tasks.read", "tasks.create", "tasks.update", "approvals.read", "approvals.approve", "approvals.reject", "knowledge.read", "users.read"]]),
            ("SUPPORT_AGENT", "Customer care triage and complaint handling", [perm_objs[k] for k in ["customers.read", "complaints.read", "complaints.update", "tasks.read", "tasks.create", "tasks.update", "knowledge.read"]]),
            ("AUDITOR", "Strict read-only compliance auditor", [perm_objs[k] for k in ["audit.read", "workflows.read", "documents.read", "invoices.read", "complaints.read", "policies.read", "analytics.read"]]),
            ("EMPLOYEE", "Standard employee profile", [perm_objs[k] for k in ["documents.read", "documents.upload", "tasks.read", "tasks.create", "knowledge.read"]])
        ]
        role_map = {}
        for rname, rdesc, rperms in roles_specs:
            role = db.query(Role).filter_by(name=rname).first()
            if not role:
                role = Role(name=rname, description=rdesc, is_system=True)
                role.permissions = rperms
                db.add(role)
                db.commit()
                db.refresh(role)
            role_map[rname] = role
        db.commit()
        print("✓ Verified Roles & Granular Permissions")

        # 5. Demo Users
        pw_hash = get_password_hash("DemoPassword123!")
        users_specs = [
            ("admin@acme.test", "System Administrator", "SUPER_ADMIN", "IT", True, org.id),
            ("finance@acme.test", "Priya Sharma", "FINANCE_MANAGER", "Finance", False, org.id),
            ("operations@acme.test", "Vikram Patel", "OPERATIONS_MANAGER", "Operations", False, org.id),
            ("support@acme.test", "Ananya Iyer", "SUPPORT_MANAGER", "Support", False, org.id),
            ("auditor@acme.test", "Rajesh Nair", "AUDITOR", "Legal", False, org.id),
            ("admin@beta.test", "Beta Admin", "SUPER_ADMIN", "IT", True, beta_org.id),
            ("admin@globex.test", "Globex Admin", "SUPER_ADMIN", "IT", True, globex_org.id),
            ("finance@globex.test", "Globex Finance", "FINANCE_MANAGER", "Finance", False, globex_org.id)
        ]
        for email, name, rname, dname, is_su, user_org_id in users_specs:
            u = db.query(User).filter_by(email=email).first()
            target_role = role_map.get(rname)
            if not u:
                u = User(
                    organization_id=user_org_id,
                    email=email,
                    password_hash=pw_hash,
                    full_name=name,
                    first_name=name.split()[0],
                    last_name=name.split()[-1] if len(name.split()) > 1 else "",
                    role=rname,
                    role_id=target_role.id if target_role else None,
                    department_name=dname,
                    status="ACTIVE",
                    is_active=True,
                    is_superuser=is_su,
                    email_verified=True,
                    email_verified_at=datetime.datetime.now(datetime.timezone.utc)
                )
                db.add(u)
            else:
                u.status = "ACTIVE"
                u.is_active = True
                u.email_verified = True
                if target_role:
                    u.role_id = target_role.id
        db.commit()
        print("✓ Verified Demo Users with Active Status and Email Verification")

        # 6. 25 Vendors
        vendors_seed = [
            ("VEND-001", "ABC Industrial Supplies", "27AABCA1234F1Z1", "sales@abc-supplies.test", "Bangalore, India", "APPROVED", "LOW"),
            ("VEND-002", "Apex Cloud Infrastructure", "29XYZAP9876G2Z4", "billing@apexcloud.test", "Hyderabad, India", "APPROVED", "LOW"),
            ("VEND-003", "Precision Logistics Express", "33PRELO5432H3Z7", "ops@precisionlogistics.test", "Chennai, India", "APPROVED", "LOW"),
            ("VEND-004", "Global Packaging Corp", "27GLOBP1122J4Z9", "orders@globalpackaging.test", "Mumbai, India", "APPROVED", "LOW"),
            ("VEND-005", "Dynamic Micro Electronics", "07DYNEL3344K5Z2", "accounts@dynamicelec.test", "Delhi, India", "APPROVED", "LOW"),
            ("VEND-006", "Reliable Hardware Tools", "06RELHT5566L6Z5", "info@reliabletools.test", "Gurugram, India", "APPROVED", "LOW"),
            ("VEND-007", "CyberShield Defense Labs", "29CYBER7788M7Z8", "billing@cybershield.test", "Bangalore, India", "APPROVED", "LOW"),
            ("VEND-008", "Supreme Facility Services", "36SUPFA9900N8Z1", "facility@supremeservices.test", "Hyderabad, India", "APPROVED", "LOW"),
            ("VEND-009", "Starlight Electric Works", "24STARE2233P9Z4", "dispatch@starlightelectric.test", "Ahmedabad, India", "APPROVED", "LOW"),
            ("VEND-010", "Rapid Courier Network", "19RAPCN4455Q1Z7", "support@rapidcourier.test", "Kolkata, India", "APPROVED", "LOW"),
            ("VEND-011", "Delta Office Automation", "27DELOF6677R2Z0", "sales@deltaoffice.test", "Pune, India", "APPROVED", "LOW"),
            ("VEND-012", "Zenith Safety Helmets", "33ZENSH8899S3Z3", "orders@zenithsafety.test", "Coimbatore, India", "APPROVED", "LOW"),
            ("VEND-013", "Titan Heavy Machinery", "29TITAN1234T4Z6", "machinery@titanheavy.test", "Mysore, India", "APPROVED", "MEDIUM"),
            ("VEND-014", "NexGen Software Licenses", "07NEXGN5678U5Z9", "renewals@nexgensoft.test", "Noida, India", "APPROVED", "LOW"),
            ("VEND-015", "EcoEnergy Solar Systems", "24ECOEN9012V6Z2", "projects@ecoenergy.test", "Surat, India", "APPROVED", "LOW"),
            ("VEND-016", "Prime Catering Services", "36PRIMC3456W7Z5", "events@primecatering.test", "Secunderabad, India", "APPROVED", "LOW"),
            ("VEND-017", "Allied Chemical Reagents", "27ALLCH7890X8Z8", "lab@alliedchem.test", "Thane, India", "APPROVED", "MEDIUM"),
            ("VEND-018", "BlueStar Freight Carriers", "33BLUES2345Y9Z1", "freight@bluestar.test", "Madurai, India", "APPROVED", "LOW"),
            ("VEND-019", "Quantum Telecom Solutions", "29QUANT6789Z1Z4", "enterprise@quantumtele.test", "Bangalore, India", "APPROVED", "LOW"),
            ("VEND-020", "Falcon Security Personnel", "07FALCO0123A2Z7", "admin@falconsecurity.test", "Faridabad, India", "APPROVED", "LOW"),
            ("VEND-021", "Horizon Travel Desk", "27HORIZ4567B3Z0", "corporate@horizontravel.test", "Mumbai, India", "APPROVED", "LOW"),
            ("VEND-022", "Matrix Medical Supplies", "24MATRX8901C4Z3", "pharma@matrixmedical.test", "Vadodara, India", "APPROVED", "LOW"),
            ("VEND-023", "Pinnacle Consulting Group", "29PINNC2345D5Z6", "advisory@pinnacle.test", "Bangalore, India", "APPROVED", "LOW"),
            ("VEND-024", "Universal Spare Parts", "06UNIVS6789E6Z9", "spares@universalparts.test", "Manesar, India", "APPROVED", "LOW"),
            ("VEND-025", "Unknown Ghost Holdings LLC", "99GHOST0000X9Z9", "wire@ghostholdings.fake", "Offshore, Seychelles", "BLOCKED", "CRITICAL")
        ]
        vendor_objs = {}
        for code, name, tax, email, addr, st, risk in vendors_seed:
            v = db.query(Vendor).filter_by(organization_id=org.id, name=name).first()
            if not v:
                v = Vendor(
                    organization_id=org.id,
                    vendor_code=code,
                    name=name,
                    tax_id=tax,
                    email=email,
                    address=addr,
                    status=st,
                    approved=(st == "APPROVED"),
                    risk_level=risk,
                    bank_details={"bank_name": "HDFC Bank", "account_number": f"XX{code[-4:]}9921", "ifsc": "HDFC0001234"}
                )
                db.add(v)
                db.commit()
                db.refresh(v)
            vendor_objs[code] = v
        print(f"✓ Verified {len(vendor_objs)} Vendors")

        # 7. 50 Customers
        first_names = ["Amit", "Sneha", "Rahul", "Pooja", "Rohan", "Meera", "Karan", "Kavita", "Sanjay", "Divya"]
        last_names = ["Verma", "Rao", "Gupta", "Nambiar", "Kulkarni", "Reddy", "Bose", "Choudhury", "Deshmukh", "Singhal"]
        cust_objs = []
        for i in range(1, 51):
            c_num = f"CUST-{i:03d}"
            c = db.query(Customer).filter_by(organization_id=org.id, customer_number=c_num).first()
            if not c:
                fn = first_names[(i - 1) % len(first_names)]
                ln = last_names[((i - 1) * 3) % len(last_names)]
                full_n = f"{fn} {ln}"
                c = Customer(
                    organization_id=org.id,
                    customer_number=c_num,
                    first_name=fn,
                    last_name=ln,
                    name=full_n,
                    email=f"{fn.lower()}.{ln.lower()}{i}@example-client.test",
                    phone=f"+91 98765 {i:04d}0",
                    company_name=f"{ln} Enterprises Pvt Ltd" if i % 2 == 0 else f"{fn} Solutions",
                    status="ACTIVE"
                )
                db.add(c)
                db.commit()
                db.refresh(c)
            cust_objs.append(c)
        print(f"✓ Verified {len(cust_objs)} Customers")

        # 8. 30 Purchase Orders
        po_objs = {}
        for i in range(1, 31):
            po_num = f"PO-2026-{i:03d}"
            po = db.query(PurchaseOrder).filter_by(organization_id=org.id, po_number=po_num).first()
            if not po:
                v_code = f"VEND-{(i % 24) + 1:03d}"
                vendor = vendor_objs.get(v_code, list(vendor_objs.values())[0])
                subtotal = 10000.0 * (i + 1)
                tax = round(subtotal * 0.18, 2)
                total = subtotal + tax
                po = PurchaseOrder(
                    organization_id=org.id,
                    po_number=po_num,
                    vendor_id=vendor.id,
                    issue_date=datetime.date(2026, 1, (i % 28) + 1),
                    currency="INR",
                    subtotal=subtotal,
                    tax=tax,
                    total=total,
                    status="APPROVED",
                    department="Operations" if i % 2 == 0 else "Finance"
                )
                db.add(po)
                db.flush()

                poi = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    description=f"Procurement Item Lot #{i}",
                    quantity=float(i * 5),
                    unit_price=float(subtotal / (i * 5)),
                    tax=tax,
                    total=total
                )
                db.add(poi)
                db.commit()
                db.refresh(po)
            po_objs[po_num] = po
        print(f"✓ Verified {len(po_objs)} Purchase Orders")

        # 9. 50 Invoices
        for i in range(1, 51):
            inv_num = f"INV-2026-{i:03d}"
            inv = db.query(Invoice).filter_by(organization_id=org.id, invoice_number=inv_num).first()
            if not inv:
                v_code = f"VEND-{(i % 24) + 1:03d}"
                vendor = vendor_objs.get(v_code, list(vendor_objs.values())[0])
                po_match_num = f"PO-2026-{((i - 1) % 30) + 1:03d}"
                matched_po = po_objs.get(po_match_num)

                # Synthetic conditions
                if i in [2, 7, 14, 25, 33, 42]:  # High-Value (> ₹100,000)
                    subtotal = 125000.0 + (i * 1000.0)
                    tax = round(subtotal * 0.18, 2)
                    total = subtotal + tax
                    status = "PENDING_APPROVAL"
                    risk = "HIGH"
                    risk_score = 65.0
                elif i == 5:  # Suspicious vendor
                    subtotal = 750000.0
                    tax = 135000.0
                    total = 885000.0
                    status = "REJECTED"
                    risk = "CRITICAL"
                    risk_score = 95.0
                    vendor = vendor_objs.get("VEND-025", vendor)
                    matched_po = None
                else:  # Normal invoice
                    subtotal = 15000.0 + (i * 500.0)
                    tax = round(subtotal * 0.18, 2)
                    total = subtotal + tax
                    status = "PAID" if i < 20 else "APPROVED"
                    risk = "LOW"
                    risk_score = 12.0

                inv = Invoice(
                    organization_id=org.id,
                    vendor_id=vendor.id,
                    purchase_order_id=matched_po.id if matched_po else None,
                    invoice_number=inv_num,
                    invoice_date=datetime.date(2026, 2, (i % 28) + 1),
                    due_date=datetime.date(2026, 3, (i % 28) + 1),
                    currency="INR",
                    subtotal=subtotal,
                    tax=tax,
                    total=total,
                    purchase_order_number=matched_po.po_number if matched_po else None,
                    payment_terms="Net 30",
                    status=status,
                    risk_level=risk,
                    risk_score=risk_score,
                    ai_confidence=0.98,
                    bank_details=vendor.bank_details or {}
                )
                db.add(inv)
                db.flush()

                li = InvoiceLineItem(
                    invoice_id=inv.id,
                    description=f"Goods/Services Delivery for {inv_num}",
                    quantity=2.0,
                    unit_price=subtotal / 2.0,
                    tax=tax,
                    total=total
                )
                db.add(li)
        db.commit()
        print("✓ Verified 50 Invoices & Line Items")

        # 10. 30 Complaints
        complaint_topics = [
            ("Delayed shipment on industrial valves", "DELIVERY", "NEGATIVE", "HIGH", "P2", 0.0),
            ("Third time contacting you: order still not arrived. Refund demanded immediately.", "DELIVERY", "NEGATIVE", "CRITICAL", "P1", 14500.0),
            ("Damaged packaging on precision sensor lot", "PRODUCT", "NEGATIVE", "MEDIUM", "P3", 4200.0),
            ("Incorrect invoice tax rate applied on billing statement", "PAYMENT", "NEUTRAL", "LOW", "P3", 0.0),
            ("Administrator portal access locked out for engineering team", "TECHNICAL", "NEGATIVE", "CRITICAL", "P1", 0.0),
            ("Requesting quotation update for annual service maintenance", "OTHER", "POSITIVE", "LOW", "P4", 0.0),
        ]
        for i in range(1, 31):
            comp_title = f"COMP-2026-{i:03d}"
            c_desc, cat, sent, urg, pri, ref = complaint_topics[(i - 1) % len(complaint_topics)]
            comp = db.query(Complaint).filter_by(organization_id=org.id, order_id=f"ORD-99{i:03d}").first()
            if not comp:
                cust = cust_objs[(i - 1) % len(cust_objs)]
                comp = Complaint(
                    organization_id=org.id,
                    customer_id=cust.id,
                    order_id=f"ORD-99{i:03d}",
                    customer_name=cust.name,
                    customer_email=cust.email,
                    category=cat,
                    description=f"{c_desc} (Reference #{i})",
                    sentiment=sent,
                    urgency=urg,
                    priority=pri,
                    refund_amount=ref,
                    status="OPEN" if i > 15 else "RESOLVED",
                    ai_confidence=0.96
                )
                db.add(comp)
        db.commit()
        print("✓ Verified 30 Customer Complaints")

        # 11. 20 Tasks
        task_specs = [
            ("Review high-value disbursement INV-2026-002", "HIGH", "OPEN"),
            ("Verify GSTIN compliance for newly onboarded vendor", "MEDIUM", "COMPLETED"),
            ("Escalate damaged shipment claim with Precision Logistics", "HIGH", "OPEN"),
            ("Update quarterly vendor rate card in ERP", "LOW", "COMPLETED"),
            ("Quarterly SOC2 compliance and immutable audit check", "HIGH", "OPEN")
        ]
        for i in range(1, 21):
            ttitle, tpri, tst = task_specs[(i - 1) % len(task_specs)]
            t = db.query(Task).filter_by(organization_id=org.id, title=f"Task #{i}: {ttitle}").first()
            if not t:
                t = Task(
                    organization_id=org.id,
                    title=f"Task #{i}: {ttitle}",
                    description="Autonomous ops generated workflow item requiring attention.",
                    priority=tpri,
                    status=tst,
                    due_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=i)
                )
                db.add(t)
        db.commit()
        print("✓ Verified 20 Tasks")

        # 12. 20 Workflows
        for i in range(1, 21):
            idemp_key = f"wf-seed-2026-{i:03d}"
            wf = db.query(Workflow).filter_by(organization_id=org.id, idempotency_key=idemp_key).first()
            if not wf:
                wf_type = "INVOICE_PROCESSING" if i % 2 == 0 else "COMPLAINT_RESOLUTION"
                wf = Workflow(
                    organization_id=org.id,
                    workflow_type=wf_type,
                    idempotency_key=idemp_key,
                    status="COMPLETED" if i > 5 else "WAITING_APPROVAL",
                    input_data={"reference": f"Doc-{i:03d}", "source": "EMAIL"},
                    output_data={"result": "SUCCESS"},
                    context={"title": f"Process Ops Event #{i}", "risk_score": 25.0}
                )
                db.add(wf)
                db.flush()

                for s_order, s_type in enumerate(["INTAKE", "CLASSIFY", "EXTRACT", "VALIDATE", "POLICY", "EXECUTE"], start=1):
                    step = WorkflowStep(
                        workflow_id=wf.id,
                        step_order=s_order,
                        step_type=s_type,
                        status="COMPLETED",
                        input_data={},
                        output_data={"status": "OK"},
                        duration_ms=120
                    )
                    db.add(step)
        db.commit()
        print("✓ Verified 20 Workflows & Steps")

        # 13. 10 Policies
        policies_seed = [
            ("FIN-001", "High-Value Invoice Threshold", "FINANCE", "All invoices exceeding INR 100,000 require Finance Manager approval.", "invoice.total > 100000", "REQUIRE_APPROVAL"),
            ("FIN-002", "Strict Duplicate Invoice Rejection", "FINANCE", "Invoices with matching vendor, invoice number, and amount must be halted.", "invoice.is_duplicate == True", "BLOCK_EXECUTION"),
            ("FIN-003", "Auto-Disbursement PO Match Under INR 50k", "FINANCE", "Invoices under INR 50,000 matching an approved PO are auto-disbursed.", "invoice.total <= 50000", "AUTO_APPROVE"),
            ("SUP-001", "Customer Refund Escalation Ceiling", "SUPPORT", "Refund requests exceeding INR 10,000 require Support Manager sign-off.", "complaint.refund_amount > 10000", "REQUIRE_APPROVAL"),
            ("SUP-002", "Repeated Contact Urgency Escalation", "SUPPORT", "Customers contacting 3 or more times are escalated to Priority P1.", "complaint.contact_count >= 3", "FLAG_HIGH_RISK"),
            ("SEC-001", "Prompt Injection Zero Tolerance", "SECURITY", "Any instruction overrides or exfiltration halts the workflow immediately.", "security.injection_detected == True", "BLOCK_EXECUTION"),
            ("VEND-001", "Unapproved Vendor Hold", "PROCUREMENT", "Disbursements to non-approved vendors must be held for review.", "vendor.status != APPROVED", "REQUIRE_APPROVAL"),
            ("PO-001", "PO Amount Tolerance Constraint", "PROCUREMENT", "Invoice totals differing from PO by > 5% require procurement manager approval.", "po.variance_percent > 5.0", "REQUIRE_APPROVAL"),
            ("AUD-001", "Mandatory Cryptographic Audit Trail", "LEGAL", "All financial and customer tool operations must be committed to append-only logs.", "audit.enabled == True", "LOG_AUDIT"),
            ("AI-001", "Autonomous Confidence Threshold", "OPERATIONS", "AI decisions with confidence below 80% must be routed to human review.", "ai.confidence < 0.80", "REQUIRE_APPROVAL")
        ]
        for pcode, pname, pdept, pdesc, pcond, pact in policies_seed:
            pol = db.query(Policy).filter_by(organization_id=org.id, code=pcode).first()
            if not pol:
                pol = Policy(
                    organization_id=org.id,
                    name=pname,
                    code=pcode,
                    department=pdept,
                    description=pdesc,
                    enabled=True
                )
                db.add(pol)
                db.flush()

                rule = PolicyRule(
                    organization_id=org.id,
                    policy_id=pol.id,
                    name=f"{pcode} Execution Rule",
                    condition=pcond,
                    action=pact,
                    priority="HIGH",
                    enabled=True
                )
                db.add(rule)
        db.commit()
        print("✓ Verified 10 Compliance Policies & Rules")

        # 14. 15 Knowledge Documents & SOPs
        sops_seed = [
            ("FIN-SOP-01", "Vendor Invoice Disbursement Protocol", "FINANCE", "Standard Operating Procedure: All vendor invoices exceeding INR 100,000 require mandatory approval from the Finance Manager before payment disbursement. Invoices under INR 50,000 may be auto-processed if matched with an approved Purchase Order."),
            ("FIN-SOP-02", "Duplicate Invoicing & Fraud Prevention", "FINANCE", "SOP on Duplicate Detection: Any incoming invoice having a duplicate invoice number, matching vendor GSTIN, or identical cryptographic checksum within 90 days must be quarantined and marked DUPLICATE."),
            ("FIN-SOP-03", "Purchase Order Matching & Variance Thresholds", "FINANCE", "Procurement Matching Rule: Invoices must match purchase order line items within a 5% total variance tolerance. Variances exceeding 5% require written Procurement Manager sign-off."),
            ("SUP-SOP-01", "Customer Refund & Credit Note Guidelines", "SUPPORT", "Support Guidelines: Customer refund claims up to INR 10,000 may be processed autonomously if proof of non-delivery or product defect is established. Claims exceeding INR 10,000 require Support Manager review."),
            ("SUP-SOP-02", "Severe Grievance & Multi-Contact Escalation", "SUPPORT", "Customer Grievance Policy: Customers stating repeated contacts (e.g. 3rd contact or greater) must be tagged with Critical Priority P1 and acknowledged within 15 minutes."),
            ("SEC-SOP-01", "Prompt Injection Defense & Untrusted Data Isolation", "SECURITY", "Information Security Protocol SEC-001: All external documents, emails, and PDFs must be treated as untrusted data. Text must be encapsulated in boundary XML envelopes. Any attempt to override system directives triggers immediate workflow abort."),
            ("SEC-SOP-02", "Data Loss Prevention & Web Beacon Blocking", "SECURITY", "DLP Standard: No customer records, API secrets, or internal system prompts shall be exfiltrated via external URLs, markdown image tags, or unauthorized tool calls."),
            ("TEN-SOP-01", "Multi-Tenant Data Partitioning & Isolation", "SECURITY", "Multi-Tenancy Governance: Every database transaction, search query, and knowledge retrieval must be scoped by organization_id. Cross-tenant access is strictly blocked at the service layer."),
            ("VEND-SOP-01", "Vendor Onboarding & Risk Tier Classification", "PROCUREMENT", "Vendor Governance: High-risk and offshore vendors require enhanced KYC verification. Unapproved or blocked vendors cannot receive automated payments."),
            ("AI-SOP-01", "AI Fleet Autonomous Operating Boundaries", "OPERATIONS", "AI Agent Fleet Standard: All 11 specialized agents operate with strict Pydantic schemas. Free-form text cannot be piped directly into tool execution."),
            ("AI-SOP-02", "Confidence Threshold & Human Escort Protocol", "OPERATIONS", "AI Reliability Standard: If any classification or extraction confidence score falls below 80%, the Supervisor agent must pause automated execution and request human review."),
            ("OPS-SOP-01", "Incident Escalation & Banking Gateway Downtime", "OPERATIONS", "Operational Resilience: If a mock payment gateway or ERP integration returns HTTP 500 or timeout, the workflow engine records TOOL_FAILED and creates an escalation task."),
            ("AUD-SOP-01", "Immutable Audit Trail & Compliance Retention", "LEGAL", "Audit Retention: All system events, tool calls, policy evaluations, and human approvals are permanently recorded in the immutable audit log and retained for 7 years."),
            ("DOC-SOP-01", "Document File Validation & MIME Restrictions", "OPERATIONS", "Ingestion Guidelines: Files are limited to 25MB. Supported formats are PDF, DOCX, XLSX, CSV, JSON, and TXT. Executables and scripts are quarantined."),
            ("SOP-GEN-01", "General Operations Inquiry & Support Triage", "OPERATIONS", "Standard Inquiry Routing: General company correspondence is routed to the Operations inbox with P3 priority for review.")
        ]
        for scode, stitle, scat, scontent in sops_seed:
            kdoc = db.query(KnowledgeDocument).filter_by(organization_id=org.id, title=f"{scode}: {stitle}").first()
            if not kdoc:
                KnowledgeService.index_document(
                    organization_id=org.id,
                    title=f"{scode}: {stitle}",
                    category=scat,
                    content=scontent,
                    db=db
                )
        print("✓ Verified 15 Grounded Knowledge Documents & Chunks")

        # 15. Tools & Mock Integrations
        tools_list = [
            ("process_mock_payment", "Disburse simulated vendor payment", "invoices.approve", "HIGH"),
            ("create_erp_accounting_entry", "Post journal voucher to ERP ledger", "invoices.approve", "LOW"),
            ("send_customer_email", "Dispatch transactional update email", "complaints.update", "LOW"),
            ("create_support_ticket", "Create CRM customer ticket", "complaints.update", "LOW"),
            ("send_notification_alert", "Send internal operational broadcast", "workflows.create", "LOW")
        ]
        for tname, tdesc, tperm, trisk in tools_list:
            tool = db.query(Tool).filter_by(name=tname).first()
            if not tool:
                tool = Tool(
                    name=tname,
                    description=tdesc,
                    required_permission=tperm,
                    risk_level=trisk,
                    enabled=True
                )
                db.add(tool)
        db.commit()
        print("✓ Verified Controlled Tool Registry")

        # Phase 4: UrbanThread Clothing E-Commerce Foundation
        from scripts.seed_ecommerce import seed_urbanthread_ecommerce
        seed_urbanthread_ecommerce(db)

        # Phase 5: Business Website, Email & Data Ingestion Foundation
        from scripts.seed_synthetic_website import seed_synthetic_urbanthread_website
        from scripts.seed_synthetic_documents import seed_synthetic_urbanthread_documents
        from scripts.seed_synthetic_emails import seed_synthetic_urbanthread_emails
        
        urban_org = db.query(Organization).filter_by(slug="urbanthread").first()
        if urban_org:
            seed_synthetic_urbanthread_website(db, urban_org.id)
            seed_synthetic_urbanthread_documents(db, urban_org.id)
            seed_synthetic_urbanthread_emails(db, urban_org.id)
            print("✓ Phase 5: Ingestion data sources successfully seeded for UrbanThread.")

    except Exception as e:
        db.rollback()
        print(f"Error during seed: {str(e)}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
