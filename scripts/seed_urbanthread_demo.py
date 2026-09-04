"""
Phase 15–18: Master UrbanThread Local Demo Seeder.
One-command script executed by `make seed` or `make demo`.
Populates:
- UrbanThread Organization & Configuration
- Operations & Warehouse Demo Users
- 6 Autonomous AI Employees
- Complete Fashion Catalog & Inventory
- Initial Real-Time Warehouse Tasks (Pick & Pack, Return, Audit)
- Standard Operating Policies & Workflows
"""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apps.api.app.core.database import SessionLocal, engine, Base
from apps.api.app.core.database_init import init_db
from apps.api.app.core.security import get_password_hash
from apps.api.app.models.tenant import Organization, Department, Team, User, Role
from apps.api.app.models.agent import Agent, AgentRun, Tool
from apps.api.app.models.ecommerce import Product, ProductVariant, Inventory, Order, OrderItem, Shipment, Return, Refund
from apps.api.app.models.operations import Customer, Task
from apps.api.app.models.workflow import Workflow, WorkflowStep, Approval
from apps.api.app.models.policy import Policy, PolicyRule


DEMO_PASSWORD = "DemoPassword123!"


def seed_urbanthread():
    print("=" * 60)
    print("OpsPilot — Seeding UrbanThread Autonomous AI Workforce")
    print("=" * 60)

    init_db()
    db = SessionLocal()

    try:
        # 1. Organization
        org = db.query(Organization).filter(Organization.slug == "urbanthread").first()
        if not org:
            org = db.query(Organization).filter(Organization.slug == "acme-test").first()
        if not org:
            org = Organization(
                id=str(uuid.uuid4()),
                name="UrbanThread Fashion",
                slug="urbanthread",
                currency="INR",
                timezone="Asia/Kolkata",
                settings={
                    "auto_approval_threshold": 2000.0,
                    "confidence_threshold": 0.85,
                    "return_window_days": 30,
                    "autonomy_level": "HYBRID_CONTROLLED",
                },
            )
            db.add(org)
            db.commit()
            db.refresh(org)
        print(f"✓ Organization: {org.name} ({org.slug}) [ID: {org.id}]")

        # 2. Departments
        depts = {}
        for dname in ["Operations", "Customer Support", "Finance", "Warehouse", "Engineering"]:
            dept = db.query(Department).filter(Department.organization_id == str(org.id), Department.name == dname).first()
            if not dept:
                dept = Department(
                    id=str(uuid.uuid4()),
                    organization_id=str(org.id),
                    name=dname,
                    description=f"UrbanThread {dname} Department",
                )
                db.add(dept)
                db.commit()
                db.refresh(dept)
            depts[dname] = dept
        print(f"✓ Departments: {len(depts)} verified")

        # 3. Demo Users
        users_data = [
            ("admin@acme.test", "Admin", "User", "ADMIN", "Engineering"),
            ("operations@acme.test", "Operations", "Lead", "OPERATIONS", "Operations"),
            ("warehouse@acme.test", "Rahul", "Warehouse", "OPERATIONS", "Warehouse"),
            ("support@acme.test", "Sarah", "Support", "SUPPORT", "Customer Support"),
            ("finance@acme.test", "Anand", "Finance", "FINANCE", "Finance"),
        ]
        users = {}
        for email, fn, ln, role, dname in users_data:
            user = db.query(User).filter(User.organization_id == str(org.id), User.email == email).first()
            if not user:
                user = User(
                    id=str(uuid.uuid4()),
                    organization_id=str(org.id),
                    department_id=str(depts[dname].id),
                    email=email,
                    password_hash=get_password_hash(DEMO_PASSWORD),
                    first_name=fn,
                    last_name=ln,
                    full_name=f"{fn} {ln}",
                    role=role,
                    is_active=True,
                    is_superuser=(role == "ADMIN"),
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            users[email] = user
        print(f"✓ Users: {len(users)} demo accounts active (Password: {DEMO_PASSWORD})")

        # 4. AI Employees
        agents_data = [
            ("Aria", "Customer Experience AI", "CUSTOMER_FACING", "Handles customer inquiries, tracking, and sizing"),
            ("Alex", "Order Fulfillment AI", "OPERATIONS", "Orchestrates order routing, packing, and dispatch"),
            ("Maya", "Support & Escalation AI", "SUPPORT", "Resolves customer complaints and complex tickets"),
            ("Devon", "Inventory & Stock AI", "OPERATIONS", "Monitors SKU thresholds, reorders, and stockouts"),
            ("Sam", "Returns & Logistics AI", "OPERATIONS", "Evaluates returns eligibility and reverse logistics"),
            ("Priya", "Purchasing & Vendor AI", "FINANCE", "Manages supplier purchase orders and fabric invoices"),
        ]
        for name, title, role_type, desc in agents_data:
            agent = db.query(Agent).filter(Agent.organization_id == str(org.id), Agent.name == name).first()
            if not agent:
                agent = Agent(
                    id=str(uuid.uuid4()),
                    organization_id=str(org.id),
                    name=name,
                    agent_type=role_type,
                    description=desc,
                    model="gpt-4o-mini",
                    enabled=True,
                    system_prompt=f"You are {name}, the {title} for UrbanThread. {desc}.",
                )
                db.add(agent)
                db.commit()
        print("✓ AI Employees: 6 autonomous workforce personas registered")

        # 5. Warehouse, Catalog Products & Inventory
        from apps.api.app.models.ecommerce import Warehouse
        warehouse = db.query(Warehouse).filter(Warehouse.organization_id == str(org.id)).first()
        if not warehouse:
            warehouse = Warehouse(
                id=str(uuid.uuid4()),
                organization_id=str(org.id),
                name="Main Fulfillment Hub Bengaluru",
                code="BLR-01",
                city="Bengaluru",
                state="Karnataka",
                country="India",
                is_active=True,
            )
            db.add(warehouse)
            db.commit()
            db.refresh(warehouse)

        products_data = [
            ("Classic Denim Jacket", "SKU-DENIM-01", 3499.0, 45, "Indigo Blue"),
            ("Slim-Fit Stretch Chino", "SKU-CHINO-02", 1999.0, 80, "Navy"),
            ("Heavy Streetwear Hoodie", "SKU-HOODIE-03", 2499.0, 30, "Sage Green"),
            ("Relaxed Fit Graphic Tee", "SKU-TEE-04", 899.0, 150, "Off-White"),
            ("Merino Wool Crew Sweater", "SKU-SWEATER-05", 3999.0, 25, "Charcoal Grey"),
        ]
        seeded_products = []
        for pname, sku, price, stock_qty, color in products_data:
            prod = db.query(Product).filter(Product.organization_id == str(org.id), Product.sku == sku).first()
            if not prod:
                prod = Product(
                    id=str(uuid.uuid4()),
                    organization_id=str(org.id),
                    name=pname,
                    sku=sku,
                    base_price=price,
                    currency="INR",
                    color=color,
                    is_active=True,
                )
                db.add(prod)
                db.commit()
                db.refresh(prod)

                # Variant
                variant = ProductVariant(
                    id=str(uuid.uuid4()),
                    organization_id=str(org.id),
                    product_id=str(prod.id),
                    sku=f"{sku}-M",
                    size="M",
                    color=color,
                    is_active=True,
                )
                db.add(variant)
                db.commit()
                db.refresh(variant)

                # Inventory
                inv = Inventory(
                    id=str(uuid.uuid4()),
                    organization_id=str(org.id),
                    product_variant_id=str(variant.id),
                    warehouse_id=str(warehouse.id),
                    quantity_on_hand=stock_qty,
                    quantity_reserved=5,
                    reorder_level=20,
                )
                db.add(inv)
                db.commit()
            seeded_products.append(prod)
        print(f"✓ Catalog: {len(seeded_products)} clothing SKUs with active warehouse stock")

        # 6. Sample Customers
        cust = db.query(Customer).filter(Customer.organization_id == str(org.id)).first()
        if not cust:
            cust = Customer(
                id=str(uuid.uuid4()),
                organization_id=str(org.id),
                name="Rahul Sharma",
                email="rahul.sharma@example.test",
                phone="+919876543210",
            )
            db.add(cust)
            db.commit()
            db.refresh(cust)
        print(f"✓ Customer: {cust.name} ({cust.email})")

        # 7. Initial Real-time Warehouse Tasks
        warehouse_user = users["warehouse@acme.test"]
        existing_tasks = db.query(Task).filter(Task.organization_id == str(org.id)).count()
        if existing_tasks < 3:
            sample_tasks = [
                ("Pick & Pack Order UT-10482", "PICK_AND_PACK", "NORMAL", "UT-10482", "Rahul Sharma", ["1x Classic Denim Jacket (M)"]),
                ("Quality Inspection: Batch B-88", "QC_INSPECTION", "HIGH", "PO-9912", "Devon Stock AI", ["50x Slim-Fit Chino Navy"]),
                ("Process Return: RET-4491", "PROCESS_RETURN", "NORMAL", "UT-09921", "Pooja Verma", ["1x Heavy Hoodie Sage Green"]),
            ]
            for title, ttype, prio, ord_id, cust_nm, items in sample_tasks:
                task = Task(
                    id=str(uuid.uuid4()),
                    organization_id=str(org.id),
                    title=title,
                    task_type=ttype,
                    priority=prio,
                    status="CREATED",
                    order_id=ord_id,
                    customer_name=cust_nm,
                    items_summary=items,
                    due_at=datetime.utcnow() + timedelta(hours=4),
                )
                db.add(task)
            db.commit()
            print("✓ Tasks: 3 initial warehouse employee tasks dispatched")
        else:
            print(f"✓ Tasks: {existing_tasks} active operations tasks in queue")

        # 8. Workflows
        wf = db.query(Workflow).filter(Workflow.organization_id == str(org.id), Workflow.name == "Order Fulfillment Pipeline").first()
        if not wf:
            wf = Workflow(
                id=str(uuid.uuid4()),
                organization_id=str(org.id),
                name="Order Fulfillment Pipeline",
                trigger_type="EVENT",
                idempotency_key=f"wf-seed-{uuid.uuid4().hex[:8]}",
                enabled=True,
            )
            db.add(wf)
            db.commit()
        print("✓ Workflows: Core fulfillment pipeline active")

        print("=" * 60)
        print("UrbanThread Local Seed Complete!")
        print("=" * 60)

    except Exception as exc:
        db.rollback()
        print(f"Error seeding UrbanThread: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_urbanthread()
