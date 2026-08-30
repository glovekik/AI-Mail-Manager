const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";


async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {

  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,

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
   API
   ========================================================= */

export const api = {

  // ---------------------------------------------------------
  // Health
  // ---------------------------------------------------------

  getHealth: () =>
    request<{
      status: string;
      service?: string;
    }>("/health"),


  // ---------------------------------------------------------
  // Emails
  // ---------------------------------------------------------

  getEmails: (
    emailAccountId: number,
    page = 1,
    pageSize = 20,
    category?: string,
    isRead?: boolean,
    search?: string
  ) => {

    const params =
      new URLSearchParams();

    params.set(
      "email_account_id",
      String(emailAccountId)
    );

    params.set(
      "page",
      String(page)
    );

    params.set(
      "page_size",
      String(pageSize)
    );


    if (
      category &&
      category !== "All"
    ) {

      params.set(
        "category",
        category
      );
    }


    if (
      isRead !== undefined
    ) {

      params.set(
        "is_read",
        String(isRead)
      );
    }


    if (
      search &&
      search.trim()
    ) {

      params.set(
        "search",
        search.trim()
      );
    }


    return request<EmailListResponse>(
      `/api/emails?${params.toString()}`
    );
  },


  getEmail: (
    emailId: number
  ) =>
    request<Email>(
      `/api/emails/${emailId}`
    ),


  // ---------------------------------------------------------
  // Email actions
  // ---------------------------------------------------------

  markEmailRead: (
    emailId: number
  ) =>
    request<EmailActionResponse>(
      `/api/emails/${emailId}/read`,
      {
        method: "POST",
      }
    ),


  markEmailUnread: (
    emailId: number
  ) =>
    request<EmailActionResponse>(
      `/api/emails/${emailId}/unread`,
      {
        method: "POST",
      }
    ),


  archiveEmail: (
    emailId: number
  ) =>
    request<EmailActionResponse>(
      `/api/emails/${emailId}/archive`,
      {
        method: "POST",
      }
    ),


  deleteEmail: (
    emailId: number
  ) =>
    request<EmailActionResponse>(
      `/api/emails/${emailId}/delete`,
      {
        method: "POST",
      }
    ),


  // ---------------------------------------------------------
  // Dashboard
  // ---------------------------------------------------------

  getDashboard: (
    emailAccountId: number
  ) =>
    request<DashboardResponse>(
      `/api/dashboard?email_account_id=${emailAccountId}`
    ),


  // ---------------------------------------------------------
  // Categories
  // ---------------------------------------------------------

  getCategories: () =>
    request<{
      categories: string[];
    }>("/api/categories"),


  // ---------------------------------------------------------
  // Gmail sync
  // ---------------------------------------------------------

  syncEmails: (
    emailAccountId: number
  ) =>
    request<SyncResponse>(
      `/api/emails/sync?email_account_id=${emailAccountId}`,
      {
        method: "POST",
      }
    ),


  // ---------------------------------------------------------
  // AI classification
  // ---------------------------------------------------------

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
   TYPES
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

  email_account_id?: number;

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


export interface EmailActionResponse {

  status: string;

  message: string;

  email_id: number;

  is_read?: boolean;
}


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


export interface SyncResponse {

  fetched?: number;

  inserted?: number;

  updated?: number;

  error?: string;

  details?: string;
}


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