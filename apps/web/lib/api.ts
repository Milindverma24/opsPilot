const API_BASE = typeof window !== "undefined"
  ? "/api/v1"
  : (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1");

export function getToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("opspilot_token");
  }
  return null;
}

export function setToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("opspilot_token", token);
  }
}

export function removeToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("opspilot_token");
    localStorage.removeItem("opspilot_user");
  }
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // If body is not FormData, default to JSON content-type
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
  const response = await fetch(url, { ...options, headers });

  if (response.status === 401 && typeof window !== "undefined" && !endpoint.includes("/auth/login")) {
    removeToken();
    window.location.href = "/login";
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || errorData.message || "An unexpected error occurred");
  }

  return response.json();
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      apiFetch<{ access_token: string; refresh_token: string; user: any }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    me: () => apiFetch<any>("/auth/me"),
    logout: () => apiFetch<any>("/auth/logout", { method: "POST" }),
    refresh: (refresh_token: string) =>
      apiFetch<any>("/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token }),
      }),
    changePassword: (current_password: string, new_password: string) =>
      apiFetch<any>("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ current_password, new_password }),
      }),
    forgotPassword: (email: string) =>
      apiFetch<any>("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      }),
    resetPassword: (token: string, new_password: string) =>
      apiFetch<any>("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, new_password }),
      }),
    sessions: () => apiFetch<any[]>("/auth/sessions"),
    revokeSession: (id: string) =>
      apiFetch<any>(`/auth/sessions/${id}`, { method: "DELETE" }),
  },
  users: {
    list: () => apiFetch<any>("/users"),
    get: (id: string) => apiFetch<any>(`/users/${id}`),
    create: (data: any) =>
      apiFetch<any>("/users", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: string, data: any) =>
      apiFetch<any>(`/users/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    suspend: (id: string) =>
      apiFetch<any>(`/users/${id}/suspend`, { method: "POST" }),
    activate: (id: string) =>
      apiFetch<any>(`/users/${id}/activate`, { method: "POST" }),
    delete: (id: string) =>
      apiFetch<any>(`/users/${id}`, { method: "DELETE" }),
  },
  roles: {
    list: () => apiFetch<any>("/roles"),
    get: (id: string) => apiFetch<any>(`/roles/${id}`),
    update: (id: string, data: any) =>
      apiFetch<any>(`/roles/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    permissions: () => apiFetch<any>("/permissions"),
  },
  organization: {
    get: () => apiFetch<any>("/organization"),
    update: (data: any) =>
      apiFetch<any>("/organization", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
  },
  dashboard: {
    get: () => apiFetch<any>("/dashboard"),
  },
  events: {
    list: (params?: { event_type?: string; source?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/events${qs ? `?${qs}` : ""}`);
    },
    create: (data: { title: string; content: string; source?: string; event_type?: string }) =>
      apiFetch<any>("/events", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
  documents: {
    list: (params?: { classification?: string; status?: string; document_type?: string; search?: string; page?: number; page_size?: number }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/documents${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/documents/${id}`),
    upload: (formData: FormData) =>
      apiFetch<any>("/documents/upload", {
        method: "POST",
        body: formData,
      }),
  },
  workflows: {
    list: (params?: { status?: string; workflow_type?: string; enabled?: boolean }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/workflows${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/workflows/${id}`),
    trigger: (data: { title: string; content: string; source?: string }) =>
      apiFetch<any>("/workflows", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    toggleEnabled: (id: string, enabled: boolean) =>
      apiFetch<any>(`/workflows/${id}/enable`, {
        method: "POST",
        body: JSON.stringify({ enabled }),
      }),
    test: (id: string, data: { test_mode: string; input_data?: any }) =>
      apiFetch<any>(`/workflows/${id}/test`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
  approvals: {
    list: (params?: string | { status?: string; risk_level?: string; approval_type?: string }) => {
      const obj = typeof params === "string" ? { status: params } : (params || {});
      const qs = new URLSearchParams(obj as any).toString();
      return apiFetch<any>(`/approvals${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/approvals/${id}`),
    approve: (id: string, comment?: string) =>
      apiFetch<any>(`/approvals/${id}/approve`, {
        method: "POST",
        body: JSON.stringify({ comment: comment || "" }),
      }),
    reject: (id: string, reason: string) =>
      apiFetch<any>(`/approvals/${id}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
    cancel: (id: string) => apiFetch<any>(`/approvals/${id}/cancel`, { method: "POST" }),
    addComment: (id: string, comment: string) =>
      apiFetch<any>(`/approvals/${id}/comments`, {
        method: "POST",
        body: JSON.stringify({ comment }),
      }),
  },
  agents: {
    list: () => apiFetch<any>("/agents"),
    getRuns: (agentCode: string) => apiFetch<any>(`/agents/${agentCode}/runs`),
  },
  policies: {
    list: () => apiFetch<any>("/policies"),
    create: (data: any) =>
      apiFetch<any>("/policies", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    toggleRule: (ruleId: string) =>
      apiFetch<any>(`/policies/rule/${ruleId}`, {
        method: "PUT",
      }),
    delete: (policyId: string) =>
      apiFetch<any>(`/policies/${policyId}`, {
        method: "DELETE",
      }),
  },
  knowledge: {
    list: () => apiFetch<any>("/knowledge"),
    upload: (data: { title: string; category: string; content: string }) =>
      apiFetch<any>("/knowledge/upload", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    search: (query: string) =>
      apiFetch<any>("/knowledge/search", {
        method: "POST",
        body: JSON.stringify({ query }),
      }),
    ask: (question: string) =>
      apiFetch<any>("/knowledge/ask", {
        method: "POST",
        body: JSON.stringify({ question }),
      }),
    syncCatalog: () =>
      apiFetch<any>("/knowledge/sync-catalog", {
        method: "POST",
      }),
  },
  audit: {
    list: (params?: { action?: string; actor_type?: string; resource_type?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/audit-logs${qs ? `?${qs}` : ""}`);
    },
  },
  command: {
    execute: (query: string) =>
      apiFetch<any>("/command", {
        method: "POST",
        body: JSON.stringify({ query }),
      }),
  },
  testLab: {
    getScenarios: () => apiFetch<any>("/test-lab/scenarios"),
    run: (scenario_id: string) =>
      apiFetch<any>("/test-lab/run", {
        method: "POST",
        body: JSON.stringify({ scenario_id }),
      }),
    evaluate: (data?: any) =>
      apiFetch<any>("/test-lab/evaluate", {
        method: "POST",
        body: JSON.stringify(data || {}),
      }),
    performance: (data?: any) =>
      apiFetch<any>("/test-lab/performance", {
        method: "POST",
        body: JSON.stringify(data || {}),
      }),
    failureInjection: (failure_type?: string, params?: any) =>
      apiFetch<any>("/test-lab/failure-injection", {
        method: "POST",
        body: JSON.stringify({ failure_type: failure_type || "database_timeout", params: params || {} }),
      }),
  },
  products: {
    list: (params?: { page?: number; page_size?: number; search?: string; status?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/products${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/products/${id}`),
    create: (data: any) =>
      apiFetch<any>("/products", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
  categories: {
    list: () => apiFetch<any>("/categories"),
  },
  inventory: {
    list: (params?: { page?: number; page_size?: number; low_stock_only?: boolean }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/inventory${qs ? `?${qs}` : ""}`);
    },
    adjust: (data: { product_variant_id: string; warehouse_id: string; quantity: number; operation: string }) =>
      apiFetch<any>("/inventory/adjust", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
  orders: {
    list: (params?: { page?: number; page_size?: number; status?: string; search?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/orders${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/orders/${id}`),
    cancel: (id: string) =>
      apiFetch<any>(`/orders/${id}/cancel`, {
        method: "POST",
      }),
    markShipped: (id: string) =>
      apiFetch<any>(`/orders/${id}/mark-shipped`, {
        method: "POST",
      }),
    markDelivered: (id: string) =>
      apiFetch<any>(`/orders/${id}/mark-delivered`, {
        method: "POST",
      }),
  },
  customers: {
    list: (params?: { page?: number; page_size?: number; search?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/customers${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/customers/${id}`),
    create: (data: { name: string; email: string; phone?: string; status?: string }) =>
      apiFetch<any>("/customers", { method: "POST", body: JSON.stringify(data) }),
  },
  shipments: {
    list: (params?: { page?: number; page_size?: number; status?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/shipments${qs ? `?${qs}` : ""}`);
    },
    create: (data: { order_id: string; carrier?: string }) =>
      apiFetch<any>("/shipments", { method: "POST", body: JSON.stringify(data) }),
    updateStatus: (id: string, data: { status: string; last_location?: string }) =>
      apiFetch<any>(`/shipments/${id}/status`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
  },
  returns: {
    list: (params?: { page?: number; page_size?: number; status?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/returns${qs ? `?${qs}` : ""}`);
    },
    request: (data: { order_id: string; customer_id: string; items: any[]; reason: string }) =>
      apiFetch<any>("/returns", { method: "POST", body: JSON.stringify(data) }),
    approve: (id: string) =>
      apiFetch<any>(`/returns/${id}/approve`, {
        method: "POST",
      }),
    reject: (id: string) =>
      apiFetch<any>(`/returns/${id}/reject`, {
        method: "POST",
      }),
  },
  refunds: {
    list: (params?: { page?: number; page_size?: number; status?: string; limit?: number }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/refunds${qs ? `?${qs}` : ""}`);
    },
    execute: (id: string) =>
      apiFetch<any>(`/refunds/${id}/execute`, {
        method: "POST",
      }),
    request: (data: { order_id: string; amount: number; reason: string }) =>
      apiFetch<any>("/refunds", { method: "POST", body: JSON.stringify(data) }),
    approve: (id: string) => apiFetch<any>(`/refunds/${id}/approve`, { method: "POST" }),
  },
  coupons: {
    list: () => apiFetch<any>("/coupons"),
    create: (data: any) => apiFetch<any>("/coupons", { method: "POST", body: JSON.stringify(data) }),
    validate: (data: { code: string; subtotal: number }) =>
      apiFetch<any>("/coupons/validate", { method: "POST", body: JSON.stringify(data) }),
  },
  support: {
    tickets: (params?: { page?: number; page_size?: number; status?: string; priority?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/support/tickets${qs ? `?${qs}` : ""}`);
    },
    createTicket: (data: { customer_id: string; subject: string; description: string; priority?: string; order_id?: string }) =>
      apiFetch<any>("/support/tickets", { method: "POST", body: JSON.stringify(data) }),
    conversation: (customerId: string) => apiFetch<any>(`/support/conversations/${customerId}`),
    addMessage: (conversationId: string, data: { sender_type: string; content: string; message_type?: string }) =>
      apiFetch<any>(`/support/conversations/${conversationId}/messages`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    resolve: (ticketId: string) => apiFetch<any>(`/support/tickets/${ticketId}/resolve`, { method: "POST" }),
  },
  websites: {
    list: () => apiFetch<any>("/websites"),
    get: (id: string) => apiFetch<any>(`/websites/${id}`),
    create: (data: any) => apiFetch<any>("/websites", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: any) => apiFetch<any>(`/websites/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    crawl: (id: string) => apiFetch<any>(`/websites/${id}/crawl`, { method: "POST" }),
    pages: (id: string, params?: { page?: number; page_size?: number }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/websites/${id}/pages${qs ? `?${qs}` : ""}`);
    },
  },
  emails: {
    list: (params?: { page?: number; page_size?: number; search?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/emails${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/emails/${id}`),
    testConnector: () => apiFetch<any>("/emails/test-connector", { method: "POST" }),
    inbound: (data: any) =>
      apiFetch<any>("/emails/inbound", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
  imports: {
    list: (params?: { page?: number; page_size?: number; entity_type?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/imports${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/imports/${id}`),
    create: (formData: FormData) =>
      apiFetch<any>("/imports", {
        method: "POST",
        body: formData,
      }),
  },
  workflowRuns: {
    list: (params?: { workflow_id?: string; status?: string; page?: number; page_size?: number }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/workflows/runs${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/workflows/runs/${id}`),
    pause: (id: string) => apiFetch<any>(`/workflows/runs/${id}/pause`, { method: "POST" }),
    resume: (id: string) => apiFetch<any>(`/workflows/runs/${id}/resume`, { method: "POST" }),
    cancel: (id: string) => apiFetch<any>(`/workflows/runs/${id}/cancel`, { method: "POST" }),
    retry: (id: string) => apiFetch<any>(`/workflows/runs/${id}/retry`, { method: "POST" }),
  },
  escalations: {
    list: (params?: { status?: string; level?: string; severity?: string; assigned_team?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/escalations${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/escalations/${id}`),
    create: (data: { reason: string; level?: string; severity?: string; assigned_team?: string; workflow_run_id?: string }) =>
      apiFetch<any>("/escalations", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    acknowledge: (id: string) => apiFetch<any>(`/escalations/${id}/acknowledge`, { method: "POST" }),
    resolve: (id: string, resolution: string) =>
      apiFetch<any>(`/escalations/${id}/resolve`, {
        method: "POST",
        body: JSON.stringify({ resolution }),
      }),
    escalate: (id: string, reason?: string) =>
      apiFetch<any>(`/escalations/${id}/escalate`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
    promote: (id: string, reason?: string) =>
      apiFetch<any>(`/escalations/${id}/escalate`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
    checkSla: () => apiFetch<any>("/escalations/check-sla", { method: "POST" }),
  },
  customer: {
    startConversation: (data?: { channel?: string; customer_id?: string; organization_slug?: string; order_id?: string; order_details?: any }) =>
      apiFetch<any>("/customer/conversations", {
        method: "POST",
        body: JSON.stringify(data || {}),
      }),
    listConversations: () => apiFetch<any>("/customer/conversations"),
    getConversation: (id: string) => apiFetch<any>(`/customer/conversations/${id}`),
    sendMessage: (id: string, content: string) =>
      apiFetch<any>(`/customer/conversations/${id}/messages`, {
        method: "POST",
        body: JSON.stringify({ content }),
      }),
    closeConversation: (id: string) =>
      apiFetch<any>(`/customer/conversations/${id}/close`, { method: "POST" }),
    submitFeedback: (id: string, data: { rating: number; feedback?: string; was_helpful?: boolean }) =>
      apiFetch<any>(`/customer/conversations/${id}/feedback`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    requestHandoff: (id: string) =>
      apiFetch<any>(`/customer/conversations/${id}/handoff`, { method: "POST" }),
  },
  commandCenter: {
    getSummary: () => apiFetch<any>("/command-center/summary"),
    getWorkforce: () => apiFetch<any>("/command-center/workforce"),
    getActivity: (limit?: number) => apiFetch<any>(`/command-center/activity?limit=${limit || 20}`),
  },
  aiEmployees: {
    list: () => apiFetch<any>("/ai/employees"),
    get: (id: string) => apiFetch<any>(`/ai/employees/${id}`),
    create: (data: { name: string; role: string; description?: string; permissions?: string[]; llm_model?: string }) =>
      apiFetch<any>("/ai/employees", { method: "POST", body: JSON.stringify(data) }),
    heartbeat: (id: string, data?: { current_task?: string; queue_size?: number }) =>
      apiFetch<any>(`/ai/employees/${id}/heartbeat`, {
        method: "POST",
        body: JSON.stringify(data || {}),
      }),
    recover: (id: string) => apiFetch<any>(`/ai/employees/${id}/recover`, { method: "POST" }),
  },
  alerts: {
    list: (params?: { status?: string; severity?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/alerts${qs ? `?${qs}` : ""}`);
    },
    create: (data: { alert_type: string; severity?: string; title: string; description?: string; source_type?: string; source_id?: string }) =>
      apiFetch<any>("/alerts", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    acknowledge: (id: string) => apiFetch<any>(`/alerts/${id}/acknowledge`, { method: "POST" }),
    resolve: (id: string) => apiFetch<any>(`/alerts/${id}/resolve`, { method: "POST" }),
  },
  observability: {
    traces: (params?: { operation?: string; status?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/observability/traces${qs ? `?${qs}` : ""}`);
    },
    trace: (id: string) => apiFetch<any>(`/observability/traces/${id}`),
    errors: () => apiFetch<any>("/errors"),
  },
    analytics: {
    business: (timeRange?: string) => apiFetch<any>(`/analytics/business?time_range=${timeRange || "7d"}`),
    ai: () => apiFetch<any>("/analytics/ai"),
    workflows: () => apiFetch<any>("/analytics/workflows"),
  },
  memory: {
    list: (params?: { target?: string; customer_id?: string; memory_type?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/memory${qs ? `?${qs}` : ""}`);
    },
    store: (data: { target: string; customer_id?: string; agent_id?: string; memory_type: string; key: string; value: any; confidence?: number; ttl_days?: number }) =>
      apiFetch<any>("/memory", { method: "POST", body: JSON.stringify(data) }),
    delete: (id: string) => apiFetch<any>(`/memory/${id}`, { method: "DELETE" }),
  },
  feedback: {
    list: (params?: { agent_id?: string; feedback_type?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/feedback${qs ? `?${qs}` : ""}`);
    },
    submitAgent: (data: { agent_id: string; feedback_type: string; rating: number; correction?: string; comment?: string; expected_behavior?: string; actual_behavior?: string }) =>
      apiFetch<any>("/feedback/agent", { method: "POST", body: JSON.stringify(data) }),
    submitCustomer: (data: { conversation_id: string; rating: number; was_helpful: boolean; comment?: string }) =>
      apiFetch<any>("/feedback/customer", { method: "POST", body: JSON.stringify(data) }),
  },
  learning: {
    examples: (params?: { category?: string; approved?: boolean }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/learning/examples${qs ? `?${qs}` : ""}`);
    },
    createExample: (data: any) =>
      apiFetch<any>("/learning/examples", { method: "POST", body: JSON.stringify(data) }),
    exportJsonlUrl: (category?: string) => {
      const token = getToken();
      return `${API_BASE}/learning/export${category ? `?category=${category}` : ""}${token ? `${category ? "&" : "?"}token=${token}` : ""}`;
    },
  },
  improvements: {
    list: (params?: { status?: string; agent_id?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/improvements${qs ? `?${qs}` : ""}`);
    },
    create: (data: { agent_id: string; candidate_type: string; title: string; description: string; proposed_change: any; expected_impact?: string; risk?: string }) =>
      apiFetch<any>("/improvements", { method: "POST", body: JSON.stringify(data) }),
    approve: (id: string) => apiFetch<any>(`/improvements/${id}/approve`, { method: "POST" }),
    reject: (id: string) => apiFetch<any>(`/improvements/${id}/reject`, { method: "POST" }),
    deploy: (id: string) => apiFetch<any>(`/improvements/${id}/deploy`, { method: "POST" }),
    rollback: (id: string) => apiFetch<any>(`/improvements/${id}/rollback`, { method: "POST" }),
  },
  evaluations: {
    list: (params?: { agent_id?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/evaluations${qs ? `?${qs}` : ""}`);
    },
    run: (data: { agent_id: string; version_id?: string; dataset_version?: string }) =>
      apiFetch<any>("/evaluations/run", { method: "POST", body: JSON.stringify(data) }),
  },
  experiments: {
    list: (params?: { agent_id?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/experiments${qs ? `?${qs}` : ""}`);
    },
    create: (data: { name: string; agent_id: string; baseline_version: string; candidate_version: string; traffic_percentage: number }) =>
      apiFetch<any>("/experiments", { method: "POST", body: JSON.stringify(data) }),
  },
  agentVersions: {
    list: (agentId: string) => apiFetch<any>(`/agents/${agentId}/versions`),
  },
  security: {
    getStatus: () => apiFetch<any>("/security/status"),
    toggleKillSwitch: (active: boolean, reason?: string) =>
      apiFetch<any>("/security/ai-kill-switch", { method: "POST", body: JSON.stringify({ active, reason }) }),
    listEvents: (params?: { event_type?: string; severity?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/security/events${qs ? `?${qs}` : ""}`);
    },
    listIncidents: (params?: { status?: string }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/security/incidents${qs ? `?${qs}` : ""}`);
    },
    resolveIncident: (id: string, resolution_notes: string) =>
      apiFetch<any>(`/security/incidents/${id}/resolve`, { method: "POST", body: JSON.stringify({ resolution_notes }) }),
    scan: (text: string) =>
      apiFetch<any>("/security/scan", { method: "POST", body: JSON.stringify({ text }) }),
  },
  tasks: {
    list: (params?: { status?: string; task_type?: string; priority?: string; limit?: number }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/tasks${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/tasks/${id}`),
    create: (data: { title: string; description?: string; task_type?: string; priority?: string; assigned_to?: string; order_id?: string; customer_name?: string }) =>
      apiFetch<any>("/tasks", { method: "POST", body: JSON.stringify(data) }),
    claim: (id: string, user_id?: string) =>
      apiFetch<any>(`/tasks/${id}/claim`, { method: "POST", body: JSON.stringify({ user_id }) }),
    updateProgress: (id: string, progress_percent: number, current_step?: string) =>
      apiFetch<any>(`/tasks/${id}/progress`, {
        method: "POST",
        body: JSON.stringify({ progress_percent, current_step }),
      }),
    complete: (id: string, resolution_notes?: string, result_payload?: any) =>
      apiFetch<any>(`/tasks/${id}/complete`, {
        method: "POST",
        body: JSON.stringify({ resolution_notes, result_payload }),
      }),
    fail: (id: string, reason: string) =>
      apiFetch<any>(`/tasks/${id}/fail`, { method: "POST", body: JSON.stringify({ reason }) }),
    recoverStale: () => apiFetch<any>("/tasks/recover-stale-leases", { method: "POST" }),
    seedDemoQueue: () => apiFetch<any>("/tasks/seed-demo-queue", { method: "POST" }),
  },
  tools: {
    list: () => apiFetch<any[]>("/tools"),
    get: (id: string) => apiFetch<any>(`/tools/${id}`),
    health: () => apiFetch<any>("/tools/health"),
    enable: (id: string) => apiFetch<any>(`/tools/${id}/enable`, { method: "POST" }),
    disable: (id: string) => apiFetch<any>(`/tools/${id}/disable`, { method: "POST" }),
    test: (tool: string, input: any) =>
      apiFetch<any>("/tools/test", { method: "POST", body: JSON.stringify({ tool, input, dry_run: true }) }),
    executions: (params?: { tool_name?: string; status?: string; limit?: number }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/tool-executions${qs ? `?${qs}` : ""}`);
    },
  },
  purchaseOrders: {
    list: (params?: { status?: string; limit?: number }) => {
      const qs = new URLSearchParams(params as any).toString();
      return apiFetch<any>(`/purchase-orders${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => apiFetch<any>(`/purchase-orders/${id}`),
    create: (data: { vendor_name?: string; department?: string; total: number; items?: any[] }) =>
      apiFetch<any>("/purchase-orders", { method: "POST", body: JSON.stringify(data) }),
    approve: (id: string) =>
      apiFetch<any>(`/purchase-orders/${id}/approve`, { method: "POST" }),
  },
};
