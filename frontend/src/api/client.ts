const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "https://ai-mail-manager-swart.vercel.app";


async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,

      credentials: "include",

      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    }
  );


  if (!response.ok) {
    let errorMessage =
      `Request failed: ${response.status}`;

    try {
      const errorData =
        await response.json();

      if (errorData.detail) {
        errorMessage =
          errorData.detail;
      } else if (errorData.error) {
        errorMessage =
          errorData.error;
      }
    } catch {
      // Ignore invalid JSON response
    }

    throw new Error(errorMessage);
  }


  return response.json();
}


/* =========================================================
   AUTH TYPES
   ========================================================= */

export interface AuthUser {
  id: number;
  email: string;
}


export interface AuthResponse {
  authenticated: boolean;

  user: AuthUser | null;

  email_account_id: number | null;
}


/* =========================================================
   API
   ========================================================= */

export const api = {

  /* =======================================================
     AUTH
     ======================================================= */

  getCurrentUser: () =>
    request<AuthResponse>(
      "/auth/me"
    ),


  loginWithGoogle: () => {
    window.location.href =
      `${API_BASE_URL}/auth/google`;
  },


  logout: () =>
    request<{
      message: string;
    }>(
      "/auth/logout",
      {
        method: "POST",
      }
    ),


  /* =======================================================
     HEALTH
     ======================================================= */

  getHealth: () =>
    request<{
      status: string;
      service: string;
    }>("/health"),


  /* =======================================================
     EMAILS
     ======================================================= */

  getEmails: (
    emailAccountId: number,
    page = 1,
    pageSize = 20,
    jobOnly = false
  ) =>
    request<EmailListResponse>(
      `/api/emails?email_account_id=${emailAccountId}` +
      `&page=${page}` +
      `&page_size=${pageSize}` +
      `&job_only=${jobOnly}`
    ),


  getEmail: (
    emailId: number
  ) =>
    request<Email>(
      `/api/emails/${emailId}`
    ),


  markEmailRead: (
    emailId: number
  ) =>
    request(
      `/api/emails/${emailId}/read`,
      {
        method: "POST",
      }
    ),


  markEmailUnread: (
    emailId: number
  ) =>
    request(
      `/api/emails/${emailId}/unread`,
      {
        method: "POST",
      }
    ),


  archiveEmail: (
    emailId: number
  ) =>
    request(
      `/api/emails/${emailId}/archive`,
      {
        method: "POST",
      }
    ),


  deleteEmail: (
    emailId: number
  ) =>
    request(
      `/api/emails/${emailId}/delete`,
      {
        method: "POST",
      }
    ),


  /* =======================================================
     DASHBOARD
     ======================================================= */

  getDashboard: (
    emailAccountId: number
  ) =>
    request<DashboardResponse>(
      `/api/dashboard?email_account_id=${emailAccountId}`
    ),


  /* =======================================================
     CATEGORIES
     ======================================================= */

  getCategories: () =>
    request<{
      categories: string[];
    }>("/api/categories"),


  /* =======================================================
     SYNC
     ======================================================= */

  syncEmails: (
    emailAccountId: number
  ) =>
    request<SyncResponse>(
      `/api/emails/sync?email_account_id=${emailAccountId}`,
      {
        method: "POST",
      }
    ),


  /* =======================================================
     AI
     ======================================================= */

  classifyEmails: (
    emailAccountId: number
  ) =>
    request<ClassificationResponse>(
      `/api/ai/classify?email_account_id=${emailAccountId}`,
      {
        method: "POST",
      }
    ),

};


/* =========================================================
   EMAIL TYPES
   ========================================================= */

export interface EmailClassification {
  category: string;

  is_job_related: boolean;

  confidence: number;

  recommended_action: string;

  keywords: string | null;

  reason: string | null;

  risk_level: string | null;
}


export interface Email {
  id: number;

  provider_message_id: string;

  thread_id: string | null;

  sender: string | null;

  sender_name: string | null;

  subject: string | null;

  received_at: string | null;

  snippet: string | null;

  body: string | null;

  is_read: boolean;

  classification:
    EmailClassification | null;
}


export interface EmailListResponse {
  total: number;

  page: number;

  page_size: number;

  emails: Email[];
}


/* =========================================================
   DASHBOARD TYPES
   ========================================================= */

export interface DashboardResponse {
  total_emails: number;

  unread_emails: number;

  classified_emails: number;

  categories:
    Record<string, number>;

  recommended_actions:
    Record<string, number>;

  risk_levels:
    Record<string, number>;
}


/* =========================================================
   SYNC TYPES
   ========================================================= */

export interface SyncResponse {
  fetched?: number;

  inserted?: number;

  updated?: number;

  error?: string;

  details?: string;
}


/* =========================================================
   CLASSIFICATION TYPES
   ========================================================= */

export interface ClassificationResponse {
  fetched?: number;

  classified?: number;

  inserted?: number;

  updated?: number;

  failed?: number;

  errors?: Array<{
    email_id: number;
    error: string;
  }>;

  error?: string;

  details?: string;
}