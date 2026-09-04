"""
Comprehensive database seeder for OpsPilot.
Creates:
- Demo Organization: Acme Industries (and Beta Corp for tenant testing)
- Departments and Teams
- Standard Roles and Granular Permissions
- Demo Users (admin@acme.test, finance@acme.test, operations@acme.test, etc.)
- Approved Vendors
- Customers
- Purchase Orders matching test data
- Active Operational Policies (FIN-001, FIN-002, FIN-003, SUP-001, SEC-001)
- Mock Integrations
"""

import sys
import os
from datetime import date, datetime, timezone
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apps.api.app.core.database import SessionLocal, engine, Base
from apps.api.app.core.security import get_password_hash
from apps.api.app.models import (
    Organization, Department, Team, Permission, Role, User,
    Vendor, Customer, PurchaseOrder, PurchaseOrderItem,
    Policy, PolicyRule, Integration, Agent, Tool
)

DEMO_PASSWORD = "DemoPassword123!"


def seed():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("Seeding OpsPilot demo data...")

        # 1. Check if already seeded
        existing_org = db.query(Organization).filter_by(slug="acme-industries").first()
        if existing_org:
            print("Acme Industries organization already exists. Re-verifying...")
            # We will return or continue
        else:
            print("Creating Acme Industries and Beta Corp organizations...")

        # Create Acme Industries
        if not existing_org:
            acme = Organization(
                name="Acme Industries",
                slug="acme-industries",
                settings={
                    "currency": "INR",
                    "fiscal_year_start": "04-01",
                    "auto_approval_threshold": 50000,
                    "confidence_threshold": 0.80,
                    "autonomy_level": 2
                }
            )
            db.add(acme)
            db.flush()
        else:
            acme = existing_org

        # Create Secondary Tenant: Beta Corp
        beta = db.query(Organization).filter_by(slug="beta-corp").first()
        if not beta:
            beta = Organization(
                name="Beta Corp",
                slug="beta-corp",
                settings={"currency": "USD", "autonomy_level": 1}
            )
            db.add(beta)
            db.flush()

        # 2. Departments for Acme
        dept_names = ["Finance", "Operations", "Support", "Engineering", "Administration", "Legal"]
        depts = {}
        for dname in dept_names:
            dept = db.query(Department).filter_by(organization_id=acme.id, name=dname).first()
            if not dept:
                dept = Department(organization_id=acme.id, name=dname, description=f"{dname} Department")
                db.add(dept)
                db.flush()
            depts[dname] = dept

        # 3. Permissions
        permissions_list = [
            ("documents.read", "Read documents and parsed content", "documents"),
            ("documents.upload", "Upload new documents", "documents"),
            ("documents.delete", "Delete documents", "documents"),
            ("invoices.read", "View invoices and line items", "invoices"),
            ("invoices.create", "Create or edit invoices", "invoices"),
            ("invoices.approve", "Approve invoice payments", "invoices"),
            ("invoices.reject", "Reject invoice payments", "invoices"),
            ("workflows.read", "View workflows and step executions", "workflows"),
            ("workflows.create", "Trigger workflows", "workflows"),
            ("workflows.cancel", "Cancel running workflows", "workflows"),
            ("approvals.read", "View pending approvals", "approvals"),
            ("approvals.approve", "Grant human approval", "approvals"),
            ("approvals.reject", "Reject approval requests", "approvals"),
            ("agents.read", "View agent metrics and runs", "agents"),
            ("agents.configure", "Configure agent prompts and parameters", "agents"),
            ("tools.read", "View registered tools", "tools"),
            ("tools.execute", "Execute controlled tools", "tools"),
            ("policies.read", "View business policies", "policies"),
            ("policies.create", "Create new policy rules", "policies"),
            ("policies.update", "Update policy rules", "policies"),
            ("policies.delete", "Delete policy rules", "policies"),
            ("audit.read", "Access immutable audit trail", "audit"),
            ("users.manage", "Manage team and users", "users"),
            ("settings.manage", "Manage organization settings", "settings"),
            ("complaints.manage", "Manage customer complaints and refunds", "complaints"),
        ]

        perms_map = {}
        for pname, pdesc, pmod in permissions_list:
            perm = db.query(Permission).filter_by(name=pname).first()
            if not perm:
                perm = Permission(name=pname, description=pdesc, module=pmod)
                db.add(perm)
                db.flush()
            perms_map[pname] = perm

        # 4. Roles
        roles_data = [
            ("SUPER_ADMIN", "Super Administrator with all permissions", list(perms_map.keys())),
            ("ADMIN", "Organization Administrator", list(perms_map.keys())),
            ("FINANCE_MANAGER", "Finance Manager with approval rights", [
                "documents.read", "documents.upload", "invoices.read", "invoices.approve",
                "invoices.reject", "workflows.read", "approvals.read", "approvals.approve",
                "approvals.reject", "tools.read", "policies.read", "audit.read"
            ]),
            ("FINANCE_USER", "Finance Specialist", [
                "documents.read", "documents.upload", "invoices.read", "invoices.create",
                "workflows.read", "approvals.read", "audit.read"
            ]),
            ("OPERATIONS_MANAGER", "Operations Manager", [
                "documents.read", "documents.upload", "workflows.read", "workflows.create",
                "workflows.cancel", "approvals.read", "approvals.approve", "tools.read", "tools.execute", "audit.read"
            ]),
            ("SUPPORT_MANAGER", "Customer Support Manager", [
                "documents.read", "complaints.manage", "workflows.read", "approvals.read",
                "approvals.approve", "approvals.reject", "audit.read"
            ]),
            ("SUPPORT_AGENT", "Support Specialist", [
                "documents.read", "complaints.manage", "workflows.read", "approvals.read"
            ]),
            ("EMPLOYEE", "Standard employee view", ["documents.read", "documents.upload", "workflows.read"]),
            ("AUDITOR", "Compliance Auditor (Read-only)", [
                "documents.read", "invoices.read", "workflows.read", "approvals.read",
                "policies.read", "audit.read"
            ]),
            ("AI_AGENT", "Autonomous Agent identity", [
                "documents.read", "invoices.read", "invoices.create", "workflows.read",
                "workflows.create", "tools.read", "tools.execute", "policies.read"
            ])
        ]

        for rname, rdesc, rperms in roles_data:
            role = db.query(Role).filter_by(organization_id=acme.id, name=rname).first()
            if not role:
                role = Role(organization_id=acme.id, name=rname, description=rdesc, is_system=True)
                for p in rperms:
                    if p in perms_map:
                        role.permissions.append(perms_map[p])
                db.add(role)
                db.flush()

        # 5. Demo Users
        users_seed = [
            ("admin@acme.test", "Acme Super Administrator", "SUPER_ADMIN", "Administration", True),
            ("finance@acme.test", "Anita Sharma (Finance Manager)", "FINANCE_MANAGER", "Finance", False),
            ("operations@acme.test", "Vikram Patel (Operations Lead)", "OPERATIONS_MANAGER", "Operations", False),
            ("support@acme.test", "Sneha Roy (Support Manager)", "SUPPORT_MANAGER", "Support", False),
            ("auditor@acme.test", "David Chen (Lead Auditor)", "AUDITOR", "Finance", False),
            ("employee@acme.test", "Karan Mehta (Staff Associate)", "EMPLOYEE", "Operations", False),
        ]

        hashed_demo_pw = get_password_hash(DEMO_PASSWORD)
        for email, full_name, role_name, dept_name, is_super in users_seed:
            u = db.query(User).filter_by(email=email).first()
            if not u:
                u = User(
                    organization_id=acme.id,
                    email=email,
                    hashed_password=hashed_demo_pw,
                    full_name=full_name,
                    role=role_name,
                    department_name=dept_name,
                    is_active=True,
                    is_superuser=is_super
                )
                db.add(u)
                db.flush()

        # Beta Corp User for Tenant Isolation verification
        beta_user = db.query(User).filter_by(email="admin@beta.test").first()
        if not beta_user:
            beta_user = User(
                organization_id=beta.id,
                email="admin@beta.test",
                hashed_password=hashed_demo_pw,
                full_name="Beta Corp Admin",
                role="ADMIN",
                department_name="Management",
                is_active=True,
                is_superuser=False
            )
            db.add(beta_user)
            db.flush()

        # 6. Approved Vendors
        vendors_data = [
            ("ABC Industrial Supplies", "GSTIN-07AAAAA0000A1Z5", "billing@abcsupplies.com", "+91 11 2345 6789", "APPROVED", "LOW",
             {"bank_name": "HDFC Bank", "account_number": "50200012345678", "ifsc": "HDFC0000123"}),
            ("Apex Cloud Infrastructure", "GSTIN-27BBBBB1111B2Z6", "cloud-billing@apexcloud.com", "+91 22 9876 5432", "APPROVED", "LOW",
             {"bank_name": "ICICI Bank", "account_number": "001105009988", "ifsc": "ICIC0000011"}),
            ("Zenith Office Ergonomics", "GSTIN-29CCCCC2222C3Z7", "sales@zenithergo.in", "+91 80 4455 6677", "APPROVED", "LOW",
             {"bank_name": "Axis Bank", "account_number": "918020011223344", "ifsc": "UTIB0000123"}),
            ("Global Logistics Express", "GSTIN-06DDDDD3333D4Z8", "dispatch@globallogistics.com", "+91 124 5566 778", "APPROVED", "LOW",
             {"bank_name": "State Bank of India", "account_number": "300123456789", "ifsc": "SBIN0001234"}),
            ("Prime Facility Services", "GSTIN-33EEEEE4444E5Z9", "facilities@primefacility.com", "+91 44 8877 6655", "APPROVED", "LOW",
             {"bank_name": "Kotak Mahindra Bank", "account_number": "1234567890", "ifsc": "KKBK0000123"}),
            ("Quantum Precision Tools", "GSTIN-19FFFFF5555F6Z0", "orders@quantumtools.in", "+91 33 2211 4433", "APPROVED", "MEDIUM",
             {"bank_name": "Bank of Baroda", "account_number": "01234567890123", "ifsc": "BARB0000123"}),
            ("CyberShield Defense Labs", "GSTIN-08GGGGG6666G7Z1", "security@cybershield.in", "+91 141 9988 776", "APPROVED", "LOW",
             {"bank_name": "HDFC Bank", "account_number": "50200099887766", "ifsc": "HDFC0000456"}),
            ("GreenLeaf Packaging Corp", "GSTIN-24HHHHH7777H8Z2", "invoicing@greenleafpackaging.com", "+91 79 3322 1100", "APPROVED", "LOW",
             {"bank_name": "ICICI Bank", "account_number": "001105001234", "ifsc": "ICIC0000022"}),
            ("BlueLine Telecommunications", "GSTIN-36IIIII8888I9Z3", "enterprise@bluelinetelecom.com", "+91 40 6677 8899", "APPROVED", "LOW",
             {"bank_name": "Standard Chartered", "account_number": "445566778899", "ifsc": "SCBL0036001"}),
            ("Starlight Print & Media", "GSTIN-09JJJJJ9999J0Z4", "accounts@starlightprint.com", "+91 120 4433 221", "APPROVED", "LOW",
             {"bank_name": "Canara Bank", "account_number": "112233445566", "ifsc": "CNRB0001234"})
        ]

        vendors_map = {}
        for vname, vtax, vemail, vphone, vstatus, vrisk, vbank in vendors_data:
            v = db.query(Vendor).filter_by(organization_id=acme.id, name=vname).first()
            if not v:
                v = Vendor(
                    organization_id=acme.id,
                    name=vname,
                    tax_id=vtax,
                    email=vemail,
                    phone=vphone,
                    status=vstatus,
                    risk_tier=vrisk,
                    bank_details=vbank
                )
                db.add(v)
                db.flush()
            vendors_map[vname] = v

        # 7. Customers
        customers_data = [
            ("Rajesh Sharma", "CUST-1049", "rajesh.sharma@example.com", "+91 9876543210"),
            ("Anita Desai", "CUST-2031", "anita.desai@example.com", "+91 9811223344"),
            ("Sunil Kumar", "CUST-3319", "sunil.k@example.com", "+91 9988776655"),
            ("Priya Menon", "CUST-4110", "priya.m@techcorp.in", "+91 9765432109"),
            ("Vikram Malhotra", "CUST-5221", "v.malhotra@zenith.org", "+91 9822334455"),
            ("Modern Retail Enterprises", "CUST-7080", "procurement@modernretail.com", "+91 22 4000 8000"),
            ("ByteFlow Systems", "CUST-1190", "devops@byteflow.io", "+91 80 5500 6600")
        ]
        for cname, ccode, cemail, cphone in customers_data:
            c = db.query(Customer).filter_by(organization_id=acme.id, customer_code=ccode).first()
            if not c:
                c = Customer(organization_id=acme.id, name=cname, customer_code=ccode, email=cemail, phone=cphone)
                db.add(c)
                db.flush()

        # 8. Purchase Orders
        po_seeds = [
            ("PO-2026-001", "ABC Industrial Supplies", 84500.0, 15210.0, 99710.0, "Operations", [
                ("Industrial Safety Helmets (Class E)", 50, 450.0, 22500.0),
                ("Heavy Duty Neoprene Work Gloves", 100, 250.0, 25000.0),
                ("Spill Containment Pallets 4-Drum", 2, 18500.0, 37000.0)
            ]),
            ("PO-2026-002", "Apex Cloud Infrastructure", 125000.0, 22500.0, 147500.0, "Engineering", [
                ("Dedicated Compute Cluster Instance (Q1)", 1, 125000.0, 125000.0)
            ]),
            ("PO-2026-003", "Zenith Office Ergonomics", 48000.0, 8640.0, 56640.0, "Human Resources", [
                ("Ergonomic Lumbar Mesh Chairs", 4, 12000.0, 48000.0)
            ]),
            ("PO-2026-004", "Global Logistics Express", 32000.0, 5760.0, 37760.0, "Supply Chain", [
                ("Express Freight Dispatch - North Hub", 1, 32000.0, 32000.0)
            ]),
            ("PO-2026-005", "Prime Facility Services", 65000.0, 11700.0, 76700.0, "Administration", [
                ("HVAC Bi-Monthly Maintenance & Filter Replacement", 1, 65000.0, 65000.0)
            ]),
            ("PO-2026-006", "Quantum Precision Tools", 95000.0, 17100.0, 112100.0, "Manufacturing", [
                ("Digital Calibration Calipers & Micrometer Set", 5, 19000.0, 95000.0)
            ]),
            ("PO-2026-007", "CyberShield Defense Labs", 280000.0, 50400.0, 330400.0, "Security", [
                ("Annual SOC Log Ingestion & Threat Intelligence Tier-2", 1, 280000.0, 280000.0)
            ]),
            ("PO-2026-008", "GreenLeaf Packaging Corp", 42500.0, 7650.0, 50150.0, "Packaging", [
                ("Biodegradable Corrugated Cartons (500x400x300)", 2500, 17.0, 42500.0)
            ]),
            ("PO-2026-009", "BlueLine Telecommunications", 18500.0, 3330.0, 21830.0, "IT Operations", [
                ("Dedicated Leased Line 1 Gbps Monthly Billing", 1, 18500.0, 18500.0)
            ]),
            ("PO-2026-010", "Starlight Print & Media", 27000.0, 4860.0, 31860.0, "Marketing", [
                ("Product Catalogs Edition 2026 High Gloss", 1000, 27.0, 27000.0)
            ])
        ]

        for ponum, vname, sub, tax, amt, dept, items in po_seeds:
            existing_po = db.query(PurchaseOrder).filter_by(organization_id=acme.id, po_number=ponum).first()
            if not existing_po:
                v = vendors_map.get(vname)
                po = PurchaseOrder(
                    organization_id=acme.id,
                    vendor_id=v.id if v else None,
                    po_number=ponum,
                    order_date=date(2026, 2, 10),
                    subtotal=sub,
                    tax=tax,
                    amount=amt,
                    currency="INR",
                    status="APPROVED",
                    department=dept
                )
                db.add(po)
                db.flush()
                for item_desc, qty, u_price, tot in items:
                    po_item = PurchaseOrderItem(
                        purchase_order_id=po.id,
                        description=item_desc,
                        quantity=qty,
                        unit_price=u_price,
                        total=tot
                    )
                    db.add(po_item)
                db.flush()

        # 9. Configurable Policies & Rules
        policies_data = [
            ("FIN-001", "High Value Invoice Approval Policy", "Finance", [
                ("Invoice total > INR 100,000 requires Finance Manager approval", "total", "GREATER_THAN", "100000", "REQUIRE_APPROVAL", "HIGH"),
                ("Invoice total > INR 500,000 requires Executive approval", "total", "GREATER_THAN", "500000", "REQUIRE_APPROVAL", "CRITICAL")
            ]),
            ("FIN-002", "Vendor Compliance & Due Diligence Policy", "Finance", [
                ("Unapproved / unknown vendor requires compliance clearance", "vendor_status", "NOT_EQUALS", "APPROVED", "REQUIRE_APPROVAL", "HIGH"),
                ("Blocked vendor invoices must be immediately blocked", "vendor_status", "EQUALS", "BLOCKED", "BLOCK_EXECUTION", "CRITICAL")
            ]),
            ("FIN-003", "Purchase Order Variance Control Policy", "Operations", [
                ("Invoice differing from PO by more than 10% requires manual review", "po_variance_percent", "GREATER_THAN", "10", "REQUIRE_APPROVAL", "MEDIUM")
            ]),
            ("SUP-001", "Customer Refund Policy", "Support", [
                ("Refund request exceeding INR 10,000 requires Support Manager approval", "refund_amount", "GREATER_THAN", "10000", "REQUIRE_APPROVAL", "HIGH"),
                ("Critical urgency complaint requires priority assignment", "urgency", "EQUALS", "CRITICAL", "FLAG_HIGH_RISK", "HIGH")
            ]),
            ("SEC-001", "Autonomous AI Security & Guardrail Policy", "Security", [
                ("Prompt injection signature triggers CRITICAL risk and freezes tools", "prompt_injection_detected", "EQUALS", "TRUE", "BLOCK_EXECUTION", "CRITICAL")
            ])
        ]

        for pcode, pname, pdept, rules in policies_data:
            p = db.query(Policy).filter_by(organization_id=acme.id, code=pcode).first()
            if not p:
                p = Policy(organization_id=acme.id, name=pname, code=pcode, department=pdept, is_active=True)
                db.add(p)
                db.flush()
                for rname, cfield, op, tval, act, prio in rules:
                    pr = PolicyRule(
                        organization_id=acme.id,
                        policy_id=p.id,
                        name=rname,
                        condition_field=cfield,
                        operator=op,
                        threshold_value=tval,
                        action=act,
                        priority=prio,
                        is_active=True
                    )
                    db.add(pr)
                db.flush()

        # 10. Tools in Registry
        tools_data = [
            ("process_mock_payment", "Executes safe simulated invoice payments through bank mock API", "HIGH", "tools.execute"),
            ("create_accounting_entry", "Posts general ledger journal entries in mock accounting system", "MEDIUM", "tools.execute"),
            ("send_notification", "Sends in-app notifications and alerts to relevant teams", "LOW", "tools.execute"),
            ("send_email", "Sends mock outbound email communications to vendors or customers", "MEDIUM", "tools.execute"),
            ("create_task", "Creates an operational task assigned to an employee or team", "LOW", "tools.execute"),
            ("lookup_vendor", "Retrieves approved vendor master data and payment history", "LOW", "tools.read"),
            ("lookup_purchase_order", "Fetches purchase order items and status for 3-way match", "LOW", "tools.read"),
            ("search_knowledge_base", "Queries company SOPs and policies using vector semantic search", "LOW", "tools.read"),
            ("create_approval", "Generates human-in-the-loop approval request in the approval inbox", "LOW", "tools.execute"),
            ("generate_report", "Compiles operational performance summary report", "LOW", "tools.read")
        ]

        for tname, tdesc, trisk, tperm in tools_data:
            t = db.query(Tool).filter_by(name=tname).first()
            if not t:
                t = Tool(name=tname, description=tdesc, risk_level=trisk, required_permission=tperm, is_enabled=True)
                db.add(t)
                db.flush()

        # 11. Mock Integrations
        integrations_data = [
            ("Mock Banking Gateway", "PAYMENT", "CONNECTED", {"mode": "simulated", "latency_ms": 120}),
            ("Mock Enterprise Ledger (ERP)", "ACCOUNTING", "CONNECTED", {"ledger": "General_Ops_2026"}),
            ("Mock Corporate Mailer (SMTP)", "EMAIL", "CONNECTED", {"domain": "ops.acme.test"}),
            ("Mock Customer CRM", "CRM", "CONNECTED", {"sync": "realtime"}),
            ("Mock Operations Ticketing", "TICKETING", "CONNECTED", {"sla_hours": 24})
        ]

        for iname, itype, istatus, iconfig in integrations_data:
            integ = db.query(Integration).filter_by(organization_id=acme.id, name=iname).first()
            if not integ:
                integ = Integration(
                    organization_id=acme.id,
                    name=iname,
                    integration_type=itype,
                    status=istatus,
                    config=iconfig,
                    is_mock=True
                )
                db.add(integ)
                db.flush()

        # 12. Specialized Agents registered in database
        agents_data = [
            ("Intake Agent", "INTAKE", "Normalizes incoming events, documents, and emails into structured payloads"),
            ("Classification Agent", "CLASSIFICATION", "Classifies documents as Invoice, Complaint, PO, or Other with confidence"),
            ("Extraction Agent", "EXTRACTION", "Extracts typed entities (amounts, vendors, dates, line items) via Pydantic"),
            ("Validation Agent", "VALIDATION", "Performs mathematical consistency checks, field verification, and PO matching"),
            ("Reasoning Agent", "REASONING", "Evaluates contextual business logic, historical trends, and anomalies"),
            ("Policy Agent", "POLICY", "Evaluates configurable organizational rules and identifies approval triggers"),
            ("Risk Agent", "RISK", "Computes comprehensive multi-factor risk score (0-100) and risk level"),
            ("Planning Agent", "PLANNING", "Formulates an ordered, safe action plan without direct tool execution"),
            ("Execution Agent", "EXECUTION", "Executes permitted tools following approval verification"),
            ("Communication Agent", "COMMUNICATION", "Drafts concise, professional stakeholder responses and alerts"),
            ("Supervisor Agent", "SUPERVISOR", "Monitors workflow execution, detects errors/low confidence, and manages HITL gates")
        ]

        for aname, acode, adesc in agents_data:
            ag = db.query(Agent).filter_by(code=acode).first()
            if not ag:
                ag = Agent(
                    name=aname,
                    code=acode,
                    description=adesc,
                    system_prompt=f"You are the OpsPilot {aname}. Reason step-by-step and produce strictly valid structured outputs.",
                    model="gpt-4o-mini",
                    temperature=0.1,
                    is_active=True
                )
                db.add(ag)
                db.flush()

        db.commit()
        print("Demo data seeded successfully!")
        print("\nDemo Accounts:")
        print(f"  Super Admin:        admin@acme.test      / {DEMO_PASSWORD}")
        print(f"  Finance Manager:    finance@acme.test    / {DEMO_PASSWORD}")
        print(f"  Operations Manager: operations@acme.test / {DEMO_PASSWORD}")
        print(f"  Support Manager:    support@acme.test    / {DEMO_PASSWORD}")
        print(f"  Auditor:            auditor@acme.test    / {DEMO_PASSWORD}")
        print(f"  Beta Corp (Tenant): admin@beta.test      / {DEMO_PASSWORD}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding demo data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
