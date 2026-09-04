"""
Tool Registry Seed — Phase 8.

Seeds all 29 tools into the Tool table with explicit:
- category, risk_level, required_permissions, approval_mode,
  handler_key, enabled, version, description

This is the ONLY way tools are created.
AI agents cannot create or modify tool definitions.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.api.app.core.database import SessionLocal
from apps.api.app.models.agent import Tool

TOOL_DEFINITIONS = [
    # -----------------------------------------------------------------------
    # READ — Low risk, no approval required
    # -----------------------------------------------------------------------
    {
        "name": "get_order",
        "display_name": "Get Order",
        "description": "Retrieve order details by order number. Read-only.",
        "category": "ORDER",
        "risk_level": "LOW",
        "required_permission": "orders.read",
        "required_permissions": ["orders.read"],
        "approval_mode": "NEVER",
        "handler_key": "get_order",
        "timeout_seconds": 10,
        "max_retries": 3,
        "version": "v1",
    },
    {
        "name": "get_customer",
        "display_name": "Get Customer",
        "description": "Retrieve customer profile by ID or email. Read-only.",
        "category": "CUSTOMER",
        "risk_level": "LOW",
        "required_permission": "customers.read",
        "required_permissions": ["customers.read"],
        "approval_mode": "NEVER",
        "handler_key": "get_customer",
        "timeout_seconds": 10,
        "max_retries": 3,
        "version": "v1",
    },
    {
        "name": "get_product",
        "display_name": "Get Product",
        "description": "Search or retrieve product catalog entries. Read-only.",
        "category": "READ",
        "risk_level": "LOW",
        "required_permission": "products.read",
        "required_permissions": ["products.read"],
        "approval_mode": "NEVER",
        "handler_key": "get_product",
        "timeout_seconds": 10,
        "max_retries": 3,
        "version": "v1",
    },
    {
        "name": "get_inventory",
        "display_name": "Get Inventory",
        "description": "Check inventory levels across warehouses. Read-only.",
        "category": "INVENTORY",
        "risk_level": "LOW",
        "required_permission": "inventory.read",
        "required_permissions": ["inventory.read"],
        "approval_mode": "NEVER",
        "handler_key": "get_inventory",
        "timeout_seconds": 10,
        "max_retries": 3,
        "version": "v1",
    },
    {
        "name": "get_shipment",
        "display_name": "Get Shipment",
        "description": "Retrieve shipment and tracking details. Read-only.",
        "category": "READ",
        "risk_level": "LOW",
        "required_permission": "shipments.read",
        "required_permissions": ["shipments.read"],
        "approval_mode": "NEVER",
        "handler_key": "get_shipment",
        "timeout_seconds": 10,
        "max_retries": 3,
        "version": "v1",
    },
    {
        "name": "get_return",
        "display_name": "Get Return",
        "description": "Retrieve return request details. Read-only.",
        "category": "RETURN",
        "risk_level": "LOW",
        "required_permission": "returns.read",
        "required_permissions": ["returns.read"],
        "approval_mode": "NEVER",
        "handler_key": "get_return",
        "timeout_seconds": 10,
        "max_retries": 3,
        "version": "v1",
    },
    {
        "name": "get_refund",
        "display_name": "Get Refund",
        "description": "Retrieve refund record details. Read-only.",
        "category": "REFUND",
        "risk_level": "LOW",
        "required_permission": "refunds.read",
        "required_permissions": ["refunds.read"],
        "approval_mode": "NEVER",
        "handler_key": "get_refund",
        "timeout_seconds": 10,
        "max_retries": 3,
        "version": "v1",
    },
    {
        "name": "search_knowledge",
        "display_name": "Search Knowledge Base",
        "description": "Search company knowledge base for policies, SOPs, FAQs. Read-only.",
        "category": "READ",
        "risk_level": "LOW",
        "required_permission": "knowledge.read",
        "required_permissions": ["knowledge.read"],
        "approval_mode": "NEVER",
        "handler_key": "search_knowledge",
        "timeout_seconds": 15,
        "max_retries": 2,
        "version": "v1",
    },
    {
        "name": "get_support_ticket",
        "display_name": "Get Support Ticket",
        "description": "Retrieve support ticket details. Read-only.",
        "category": "SUPPORT",
        "risk_level": "LOW",
        "required_permission": "support.read",
        "required_permissions": ["support.read"],
        "approval_mode": "NEVER",
        "handler_key": "get_support_ticket",
        "timeout_seconds": 10,
        "max_retries": 3,
        "version": "v1",
    },
    {
        "name": "get_vendor",
        "display_name": "Get Vendor",
        "description": "Retrieve vendor profile. Read-only.",
        "category": "VENDOR",
        "risk_level": "LOW",
        "required_permission": "vendors.read",
        "required_permissions": ["vendors.read"],
        "approval_mode": "NEVER",
        "handler_key": "get_vendor",
        "timeout_seconds": 10,
        "max_retries": 3,
        "version": "v1",
    },
    {
        "name": "get_purchase_order",
        "display_name": "Get Purchase Order",
        "description": "Retrieve purchase order details. Read-only.",
        "category": "PURCHASE",
        "risk_level": "LOW",
        "required_permission": "purchase_orders.read",
        "required_permissions": ["purchase_orders.read"],
        "approval_mode": "NEVER",
        "handler_key": "get_purchase_order",
        "timeout_seconds": 10,
        "max_retries": 3,
        "version": "v1",
    },
    # -----------------------------------------------------------------------
    # SUPPORT — Medium risk
    # -----------------------------------------------------------------------
    {
        "name": "create_support_ticket",
        "display_name": "Create Support Ticket",
        "description": "Create a new customer support ticket. Customer must exist in same org.",
        "category": "SUPPORT",
        "risk_level": "MEDIUM",
        "required_permission": "support.create",
        "required_permissions": ["support.create"],
        "approval_mode": "NEVER",
        "handler_key": "create_support_ticket",
        "timeout_seconds": 15,
        "max_retries": 0,
        "version": "v1",
    },
    {
        "name": "update_support_ticket",
        "display_name": "Update Support Ticket",
        "description": "Update ticket status or add resolution notes.",
        "category": "SUPPORT",
        "risk_level": "MEDIUM",
        "required_permission": "support.update",
        "required_permissions": ["support.update"],
        "approval_mode": "NEVER",
        "handler_key": "update_support_ticket",
        "timeout_seconds": 15,
        "max_retries": 0,
        "version": "v1",
    },
    {
        "name": "assign_support_ticket",
        "display_name": "Assign Support Ticket",
        "description": "Assign a support ticket to a user.",
        "category": "SUPPORT",
        "risk_level": "MEDIUM",
        "required_permission": "support.update",
        "required_permissions": ["support.update"],
        "approval_mode": "NEVER",
        "handler_key": "assign_support_ticket",
        "timeout_seconds": 15,
        "max_retries": 0,
        "version": "v1",
    },
    {
        "name": "create_internal_task",
        "display_name": "Create Internal Task",
        "description": "Create an internal operations task.",
        "category": "SUPPORT",
        "risk_level": "MEDIUM",
        "required_permission": "tasks.create",
        "required_permissions": ["tasks.create"],
        "approval_mode": "NEVER",
        "handler_key": "create_internal_task",
        "timeout_seconds": 15,
        "max_retries": 0,
        "version": "v1",
    },
    # -----------------------------------------------------------------------
    # RETURN
    # -----------------------------------------------------------------------
    {
        "name": "request_return",
        "display_name": "Request Return",
        "description": "Initiate a return request for a customer order.",
        "category": "RETURN",
        "risk_level": "MEDIUM",
        "required_permission": "returns.create",
        "required_permissions": ["returns.create"],
        "approval_mode": "NEVER",
        "handler_key": "request_return",
        "timeout_seconds": 20,
        "max_retries": 0,
        "version": "v1",
    },
    {
        "name": "approve_return",
        "display_name": "Approve Return",
        "description": "Approve a pending return request. Requires explicit human approval.",
        "category": "RETURN",
        "risk_level": "HIGH",
        "required_permission": "returns.approve",
        "required_permissions": ["returns.approve"],
        "approval_mode": "ALWAYS",
        "handler_key": "approve_return",
        "timeout_seconds": 20,
        "max_retries": 0,
        "version": "v1",
    },
    {
        "name": "reject_return",
        "display_name": "Reject Return",
        "description": "Reject a pending return request with reason.",
        "category": "RETURN",
        "risk_level": "MEDIUM",
        "required_permission": "returns.approve",
        "required_permissions": ["returns.approve"],
        "approval_mode": "NEVER",
        "handler_key": "reject_return",
        "timeout_seconds": 20,
        "max_retries": 0,
        "version": "v1",
    },
    # -----------------------------------------------------------------------
    # REFUND
    # -----------------------------------------------------------------------
    {
        "name": "request_refund",
        "display_name": "Request Refund",
        "description": "Initiate a refund request. Amounts above ₹10,000 require approval.",
        "category": "REFUND",
        "risk_level": "HIGH",
        "required_permission": "refunds.request",
        "required_permissions": ["refunds.request"],
        "approval_mode": "ON_RISK",
        "handler_key": "request_refund",
        "timeout_seconds": 20,
        "max_retries": 0,
        "version": "v1",
    },
    {
        "name": "approve_refund",
        "display_name": "Approve Refund",
        "description": "Approve a pending refund. Always requires human approval.",
        "category": "REFUND",
        "risk_level": "HIGH",
        "required_permission": "refunds.approve",
        "required_permissions": ["refunds.approve"],
        "approval_mode": "ALWAYS",
        "handler_key": "approve_refund",
        "timeout_seconds": 20,
        "max_retries": 0,
        "version": "v1",
    },
    {
        "name": "execute_refund",
        "display_name": "Execute Refund",
        "description": "Execute an approved refund through payment provider. Always requires approval.",
        "category": "REFUND",
        "risk_level": "CRITICAL",
        "required_permission": "refunds.execute",
        "required_permissions": ["refunds.execute"],
        "approval_mode": "ALWAYS",
        "handler_key": "execute_refund",
        "timeout_seconds": 30,
        "max_retries": 0,
        "version": "v1",
    },
    # -----------------------------------------------------------------------
    # ORDER
    # -----------------------------------------------------------------------
    {
        "name": "cancel_order",
        "display_name": "Cancel Order",
        "description": "Cancel a customer order. Business rules enforced (no delivered order cancellation).",
        "category": "ORDER",
        "risk_level": "HIGH",
        "required_permission": "orders.cancel",
        "required_permissions": ["orders.cancel"],
        "approval_mode": "ON_RISK",
        "handler_key": "cancel_order",
        "timeout_seconds": 20,
        "max_retries": 0,
        "version": "v1",
    },
    {
        "name": "update_order",
        "display_name": "Update Order",
        "description": "Update shipping address or notes on a pending order.",
        "category": "ORDER",
        "risk_level": "MEDIUM",
        "required_permission": "orders.update",
        "required_permissions": ["orders.update"],
        "approval_mode": "NEVER",
        "handler_key": "update_order",
        "timeout_seconds": 15,
        "max_retries": 0,
        "version": "v1",
    },
    # -----------------------------------------------------------------------
    # INVENTORY
    # -----------------------------------------------------------------------
    {
        "name": "reserve_inventory",
        "display_name": "Reserve Inventory",
        "description": "Reserve stock for an order or workflow.",
        "category": "INVENTORY",
        "risk_level": "MEDIUM",
        "required_permission": "inventory.reserve",
        "required_permissions": ["inventory.reserve"],
        "approval_mode": "NEVER",
        "handler_key": "reserve_inventory",
        "timeout_seconds": 15,
        "max_retries": 1,
        "version": "v1",
    },
    {
        "name": "release_inventory",
        "display_name": "Release Inventory",
        "description": "Release previously reserved inventory back to available stock.",
        "category": "INVENTORY",
        "risk_level": "LOW",
        "required_permission": "inventory.release",
        "required_permissions": ["inventory.release"],
        "approval_mode": "NEVER",
        "handler_key": "release_inventory",
        "timeout_seconds": 15,
        "max_retries": 1,
        "version": "v1",
    },
    # -----------------------------------------------------------------------
    # COMMUNICATION
    # -----------------------------------------------------------------------
    {
        "name": "send_customer_email",
        "display_name": "Send Customer Email",
        "description": "Send a transactional email to a customer. Recipient resolved server-side from customer_id.",
        "category": "COMMUNICATION",
        "risk_level": "MEDIUM",
        "required_permission": "communication.send",
        "required_permissions": ["communication.send"],
        "approval_mode": "NEVER",
        "handler_key": "send_customer_email",
        "timeout_seconds": 15,
        "max_retries": 0,
        "version": "v1",
    },
    {
        "name": "send_internal_notification",
        "display_name": "Send Internal Notification",
        "description": "Send an in-app notification to an internal user.",
        "category": "COMMUNICATION",
        "risk_level": "LOW",
        "required_permission": "communication.internal",
        "required_permissions": ["communication.internal"],
        "approval_mode": "NEVER",
        "handler_key": "send_internal_notification",
        "timeout_seconds": 10,
        "max_retries": 1,
        "version": "v1",
    },
    # -----------------------------------------------------------------------
    # PURCHASE
    # -----------------------------------------------------------------------
    {
        "name": "create_purchase_order",
        "display_name": "Create Purchase Order",
        "description": "Create a draft purchase order for a vendor.",
        "category": "PURCHASE",
        "risk_level": "HIGH",
        "required_permission": "purchase_orders.create",
        "required_permissions": ["purchase_orders.create"],
        "approval_mode": "ON_RISK",
        "handler_key": "create_purchase_order",
        "timeout_seconds": 20,
        "max_retries": 0,
        "version": "v1",
    },
    {
        "name": "submit_purchase_order",
        "display_name": "Submit Purchase Order",
        "description": "Submit a draft purchase order to vendor. Requires approval.",
        "category": "PURCHASE",
        "risk_level": "HIGH",
        "required_permission": "purchase_orders.submit",
        "required_permissions": ["purchase_orders.submit"],
        "approval_mode": "ALWAYS",
        "handler_key": "submit_purchase_order",
        "timeout_seconds": 20,
        "max_retries": 0,
        "version": "v1",
    },
]


def seed_tool_registry():
    db = SessionLocal()
    try:
        created = 0
        updated = 0
        for defn in TOOL_DEFINITIONS:
            existing = db.query(Tool).filter(Tool.name == defn["name"]).first()
            if existing:
                # Update fields
                for k, v in defn.items():
                    if hasattr(existing, k):
                        setattr(existing, k, v)
                updated += 1
            else:
                tool = Tool(**defn, enabled=True)
                db.add(tool)
                created += 1

        db.commit()
        print(f"✅ Tool Registry Seed Complete: {created} created, {updated} updated")
        print(f"   Total tools: {len(TOOL_DEFINITIONS)}")

        # Print summary
        by_risk = {}
        for d in TOOL_DEFINITIONS:
            r = d["risk_level"]
            by_risk[r] = by_risk.get(r, 0) + 1
        for risk, count in sorted(by_risk.items()):
            print(f"   {risk}: {count} tools")

    finally:
        db.close()


if __name__ == "__main__":
    seed_tool_registry()
