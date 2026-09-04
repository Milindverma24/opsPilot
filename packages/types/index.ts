export type UserRole =
  | "SUPER_ADMIN"
  | "ADMIN"
  | "OPERATIONS_MANAGER"
  | "FINANCE_MANAGER"
  | "FINANCE_USER"
  | "SUPPORT_MANAGER"
  | "SUPPORT_AGENT"
  | "EMPLOYEE"
  | "AUDITOR"
  | "AI_AGENT";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type WorkflowStatus =
  | "PENDING"
  | "RUNNING"
  | "WAITING_APPROVAL"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED" | "CANCELLED";

export type DocumentStatus = "UPLOADED" | "PROCESSING" | "PROCESSED" | "FAILED" | "DUPLICATE";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  settings?: Record<string, unknown>;
  created_at: string;
}

export interface User {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  department?: string;
  created_at: string;
}

export interface BusinessEvent {
  event_id: string;
  organization_id: string;
  source: "MANUAL_UPLOAD" | "EMAIL" | "WEBHOOK" | "API";
  event_type: "INVOICE" | "COMPLAINT" | "PURCHASE_ORDER" | "SUPPORT_REQUEST" | "CONTRACT" | "REPORT" | "OTHER";
  title: string;
  content: string;
  attachments?: Array<{ name: string; path: string; size: number }>;
  metadata?: Record<string, unknown>;
  received_at: string;
}

export interface Document {
  id: string;
  organization_id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  file_hash: string;
  status: DocumentStatus;
  classification?: string;
  confidence?: number;
  extracted_fields?: Record<string, unknown>;
  risk_level?: RiskLevel;
  created_at: string;
}

export interface InvoiceLineItem {
  id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax: number;
  total: number;
}

export interface Invoice {
  id: string;
  organization_id: string;
  document_id?: string;
  vendor_id?: string;
  vendor_name?: string;
  vendor_tax_id?: string;
  invoice_number: string;
  invoice_date?: string;
  due_date?: string;
  currency: string;
  subtotal: number;
  tax: number;
  total: number;
  purchase_order_number?: string;
  payment_terms?: string;
  bank_details?: Record<string, string>;
  payment_status: "UNPAID" | "PAID" | "PENDING_APPROVAL" | "REJECTED";
  line_items: InvoiceLineItem[];
  created_at: string;
}

export interface Complaint {
  id: string;
  organization_id: string;
  customer_id?: string;
  customer_name?: string;
  order_id?: string;
  issue: string;
  category: "DELIVERY" | "PAYMENT" | "PRODUCT" | "REFUND" | "ACCOUNT" | "TECHNICAL" | "OTHER";
  sentiment: "POSITIVE" | "NEUTRAL" | "NEGATIVE";
  urgency: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  priority: "P1" | "P2" | "P3" | "P4";
  requested_resolution?: string;
  refund_amount?: number;
  status: "OPEN" | "INVESTIGATING" | "RESOLVED" | "CLOSED";
  created_at: string;
}

export interface WorkflowStep {
  step_id: string;
  workflow_id: string;
  step_type: string;
  status: WorkflowStatus;
  started_at?: string;
  completed_at?: string;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  error?: string;
  agent_run_id?: string;
}

export interface Workflow {
  id: string;
  organization_id: string;
  workflow_type: "INVOICE_PROCESSING" | "COMPLAINT_HANDLING" | "PURCHASE_ORDER_AUDIT" | "GENERAL_OPERATIONS";
  status: WorkflowStatus;
  idempotency_key: string;
  document_id?: string;
  context: Record<string, unknown>;
  steps: WorkflowStep[];
  started_at: string;
  completed_at?: string;
}

export interface Approval {
  id: string;
  organization_id: string;
  workflow_id: string;
  request_type: string;
  amount?: number;
  risk_level: RiskLevel;
  status: ApprovalStatus;
  requester_name: string;
  ai_recommendation: string;
  reason: string;
  affected_entity?: string;
  approved_by?: string;
  approved_at?: string;
  rejection_reason?: string;
  created_at: string;
}

export interface AuditLog {
  id: string;
  organization_id: string;
  actor_type: "USER" | "AI_AGENT" | "SYSTEM";
  actor_id: string;
  actor_name: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  workflow_id?: string;
  result: "SUCCESS" | "FAILURE" | "BLOCKED" | "PENDING";
  payload?: Record<string, unknown>;
  ip_address?: string;
  created_at: string;
}

export interface PolicyRule {
  id: string;
  organization_id: string;
  policy_id: string;
  name: string;
  condition_field: string;
  operator: "GREATER_THAN" | "LESS_THAN" | "EQUALS" | "CONTAINS" | "NOT_EQUALS";
  threshold_value: string;
  action: "REQUIRE_APPROVAL" | "BLOCK_EXECUTION" | "FLAG_HIGH_RISK" | "AUTO_APPROVE";
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  is_active: boolean;
}
