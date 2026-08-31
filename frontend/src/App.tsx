import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  api,
  type DashboardResponse,
  type Email,
} from "./api/client";

import "./App.css";


const CATEGORY_OPTIONS = [
  "All",
  "Work",
  "Personal",
  "Finance",
  "Promotions",
  "Social",
  "Updates",
  "Spam",
  "Other",
];


type FilterMode =
  | "all"
  | "unread"
  | "high-risk";


type ViewMode =
  | "inbox"
  | "jobs";


function App() {

  /* =========================================================
     AUTHENTICATION
     ========================================================= */

  const [authenticated, setAuthenticated] =
    useState(false);

  const [userEmail, setUserEmail] =
    useState<string | null>(null);

  const [emailAccountId, setEmailAccountId] =
    useState<number | null>(null);

  const [authLoading, setAuthLoading] =
    useState(true);

  const [loggingOut, setLoggingOut] =
    useState(false);


  /* =========================================================
     APPLICATION STATE
     ========================================================= */

  const [dashboard, setDashboard] =
    useState<DashboardResponse | null>(
      null
    );


  const [emails, setEmails] =
    useState<Email[]>([]);


  const [selectedEmail, setSelectedEmail] =
    useState<Email | null>(null);


  const [selectedCategory, setSelectedCategory] =
    useState("All");


  const [viewMode, setViewMode] =
    useState<ViewMode>("inbox");


  const [filterMode, setFilterMode] =
    useState<FilterMode>("all");


  const [search, setSearch] =
    useState("");


  const [loading, setLoading] =
    useState(true);


  const [loadingEmail, setLoadingEmail] =
    useState(false);


  const [syncing, setSyncing] =
    useState(false);


  const [classifying, setClassifying] =
    useState(false);


  const [actionLoading, setActionLoading] =
    useState(false);


  const [error, setError] =
    useState<string | null>(null);


  /* =========================================================
     CHECK AUTHENTICATION
     ========================================================= */

  async function checkAuthentication() {

    try {

      setAuthLoading(true);

      setError(null);

      const auth =
        await api.getCurrentUser();

      if (
        !auth.authenticated ||
        !auth.user ||
        !auth.email_account_id
      ) {

        setAuthenticated(false);

        setUserEmail(null);

        setEmailAccountId(null);

        return;
      }


      setAuthenticated(true);

      setUserEmail(
        auth.user.email
      );

      setEmailAccountId(
        auth.email_account_id
      );

    } catch (err) {

      setAuthenticated(false);

      setUserEmail(null);

      setEmailAccountId(null);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to check authentication"
      );

    } finally {

      setAuthLoading(false);

    }

  }


  useEffect(() => {

    checkAuthentication();

  }, []);


  /* =========================================================
     HANDLE GOOGLE LOGIN
     ========================================================= */

  function handleLogin() {

    api.loginWithGoogle();

  }


  /* =========================================================
     HANDLE LOGOUT
     ========================================================= */

  async function handleLogout() {

    try {

      setLoggingOut(true);

      setError(null);

      await api.logout();

      setAuthenticated(false);

      setUserEmail(null);

      setEmailAccountId(null);

      setDashboard(null);

      setEmails([]);

      setSelectedEmail(null);

      setSelectedCategory("All");

      setViewMode("inbox");

      setFilterMode("all");

      setSearch("");

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Logout failed"
      );

    } finally {

      setLoggingOut(false);

    }

  }


  /* =========================================================
     LOAD DASHBOARD + EMAILS
     ========================================================= */

  async function loadData() {

    if (!emailAccountId) {
      return;
    }

    try {

      setLoading(true);

      setError(null);


      const [
        dashboardData,
        emailData,
      ] = await Promise.all([

        api.getDashboard(
          emailAccountId
        ),

        api.getEmails(
          emailAccountId,
          1,
          100
        ),

      ]);


      setDashboard(
        dashboardData
      );


      setEmails(
        emailData.emails
      );


      setSelectedEmail(
        current => {

          if (!current) {

            return (
              emailData.emails[0] ??
              null
            );

          }


          return (
            emailData.emails.find(
              email =>
                email.id ===
                current.id
            ) ?? null
          );

        }
      );

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Failed to load data"
      );

    } finally {

      setLoading(false);

    }

  }


  /* =========================================================
     LOAD DATA AFTER AUTHENTICATION
     ========================================================= */

  useEffect(() => {

    if (
      authenticated &&
      emailAccountId
    ) {

      loadData();

    }

  }, [
    authenticated,
    emailAccountId,
  ]);


  /* =========================================================
     LOAD FULL EMAIL
     ========================================================= */

  async function handleEmailSelect(
    email: Email
  ) {

    try {

      setLoadingEmail(true);

      setError(null);


      const fullEmail =
        await api.getEmail(
          email.id
        );


      setSelectedEmail(
        fullEmail
      );

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Failed to load email"
      );

    } finally {

      setLoadingEmail(false);

    }

  }


  /* =========================================================
     SYNC EMAILS
     ========================================================= */

  async function handleSync() {

    if (!emailAccountId) {
      return;
    }

    try {

      setSyncing(true);

      setError(null);


      const result =
        await api.syncEmails(
          emailAccountId
        );


      if (result.error) {

        throw new Error(
          result.details ||
          result.error
        );

      }


      await loadData();

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Email synchronization failed"
      );

    } finally {

      setSyncing(false);

    }

  }


  /* =========================================================
     RUN AI
     ========================================================= */

  async function handleClassify() {

    if (!emailAccountId) {
      return;
    }

    try {

      setClassifying(true);

      setError(null);


      const result =
        await api.classifyEmails(
          emailAccountId
        );


      if (result.error) {

        throw new Error(
          result.details ||
          result.error
        );

      }


      await loadData();

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Classification failed"
      );

    } finally {

      setClassifying(false);

    }

  }


  /* =========================================================
     EMAIL ACTIONS
     ========================================================= */

  async function handleEmailAction(
    action:
      | "read"
      | "unread"
      | "archive"
      | "delete",
    emailId: number
  ) {

    try {

      setActionLoading(true);

      setError(null);


      if (action === "read") {

        await api.markEmailRead(
          emailId
        );

      } else if (
        action === "unread"
      ) {

        await api.markEmailUnread(
          emailId
        );

      } else if (
        action === "archive"
      ) {

        await api.archiveEmail(
          emailId
        );

      } else {

        await api.deleteEmail(
          emailId
        );

      }


      if (
        action === "read" ||
        action === "unread"
      ) {

        const isRead =
          action === "read";


        setEmails(current =>
          current.map(item =>
            item.id === emailId
              ? {
                  ...item,
                  is_read: isRead,
                }
              : item
          )
        );


        setSelectedEmail(current =>
          current &&
          current.id === emailId
            ? {
                ...current,
                is_read: isRead,
              }
            : current
        );

      } else {

        setSelectedEmail(
          null
        );

        await loadData();

      }

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Email action failed"
      );

    } finally {

      setActionLoading(
        false
      );

    }

  }


  /* =========================================================
     FILTER EMAILS
     ========================================================= */

  const filteredEmails = useMemo(() => {

    const query =
      search
        .trim()
        .toLowerCase();


    return emails.filter(
      email => {

        const searchableText = [

          email.sender,

          email.sender_name,

          email.subject,

          email.snippet,

          email.classification
            ?.category,

          email.classification
            ?.keywords,

        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();


        const matchesSearch =
          !query ||
          searchableText.includes(
            query
          );


        const matchesCategory =
          selectedCategory ===
            "All" ||

          email.classification
            ?.category ===
            selectedCategory;


        const matchesView =
          viewMode === "inbox" ||
          email.classification
            ?.is_job_related === true;


        let matchesFilter =
          true;


        if (
          filterMode ===
          "unread"
        ) {

          matchesFilter =
            !email.is_read;

        }


        if (
          filterMode ===
          "high-risk"
        ) {

          matchesFilter =
            email.classification
              ?.risk_level ===
            "High";

        }


        return (
          matchesView &&
          matchesSearch &&
          matchesCategory &&
          matchesFilter
        );

      }
    );

  }, [
    emails,
    search,
    selectedCategory,
    filterMode,
    viewMode,
  ]);


  /* =========================================================
     JOB EMAIL COUNT
     ========================================================= */

  const jobEmailCount =
    useMemo(
      () =>
        emails.filter(
          email =>
            email.classification
              ?.is_job_related === true
        ).length,
      [emails]
    );


  /* =========================================================
     AUTH LOADING
     ========================================================= */

  if (authLoading) {

    return (

      <div
        className="app-loading"
      >

        <div
          className="loading-spinner"
        />

        Checking authentication...

      </div>

    );

  }


  /* =========================================================
     LOGIN SCREEN
     ========================================================= */

  if (!authenticated) {

    return (

      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#f8fafc",
          padding: "24px",
        }}
      >

        <div
          style={{
            width: "100%",
            maxWidth: "440px",
            background: "white",
            borderRadius: "20px",
            padding: "40px",
            boxShadow:
              "0 20px 50px rgba(15, 23, 42, 0.12)",
            textAlign: "center",
          }}
        >

          <div
            style={{
              width: "64px",
              height: "64px",
              margin: "0 auto 20px",
              borderRadius: "16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "#111827",
              color: "white",
              fontSize: "20px",
              fontWeight: 700,
            }}
          >
            AI
          </div>


          <h1
            style={{
              margin: "0 0 8px",
              fontSize: "28px",
              color: "#111827",
            }}
          >
            AI Mail Manager
          </h1>


          <p
            style={{
              margin: "0 0 28px",
              color: "#6b7280",
              lineHeight: 1.6,
            }}
          >
            Sign in with Google to
            intelligently organize and
            analyze your Gmail.
          </p>


          {error && (

            <div
              style={{
                marginBottom: "20px",
                padding: "12px 14px",
                borderRadius: "10px",
                background: "#fef2f2",
                color: "#b91c1c",
                fontSize: "14px",
              }}
            >
              {error}
            </div>

          )}


          <button
            type="button"
            onClick={handleLogin}
            style={{
              width: "100%",
              padding: "13px 18px",
              borderRadius: "10px",
              border:
                "1px solid #d1d5db",
              background: "white",
              color: "#111827",
              fontSize: "15px",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "10px",
            }}
          >

            <span
              style={{
                fontSize: "18px",
                fontWeight: 700,
              }}
            >
              G
            </span>

            Continue with Google

          </button>


          <p
            style={{
              marginTop: "24px",
              marginBottom: 0,
              fontSize: "12px",
              color: "#9ca3af",
              lineHeight: 1.5,
            }}
          >
            Gmail access is currently
            limited to authorized users.
          </p>

        </div>

      </div>

    );

  }


  /* =========================================================
     APPLICATION LOADING
     ========================================================= */

  if (loading) {

    return (

      <div
        className="app-loading"
      >

        <div
          className="loading-spinner"
        />

        Loading AI Mail Manager...

      </div>

    );

  }


  /* =========================================================
     MAIN UI
     ========================================================= */

  return (

    <div className="app">


      {/* =====================================================
          HEADER
          ===================================================== */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-mark">
            AI
          </div>


          <div>

            <h1>
              AI Mail Manager
            </h1>

            <p>
              Intelligent email management
            </p>

          </div>

        </div>


        <div
          className="topbar-actions"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            flexWrap: "wrap",
          }}
        >

          {userEmail && (

            <span
              style={{
                fontSize: "13px",
                color: "#6b7280",
                maxWidth: "240px",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
              title={userEmail}
            >
              {userEmail}
            </span>

          )}


          <button
            className="secondary-button"
            onClick={handleSync}
            disabled={
              syncing ||
              classifying
            }
          >

            {syncing
              ? "Syncing..."
              : "Sync Emails"}

          </button>


          <button
            className="primary-button"
            onClick={handleClassify}
            disabled={
              classifying ||
              syncing
            }
          >

            {classifying
              ? "Classifying..."
              : "Run AI"}

          </button>


          <button
            className="secondary-button"
            onClick={handleLogout}
            disabled={
              loggingOut ||
              syncing ||
              classifying
            }
          >

            {loggingOut
              ? "Logging out..."
              : "Logout"}

          </button>

        </div>

      </header>


      {/* =====================================================
          ERROR
          ===================================================== */}

      {error && (

        <div className="error-banner">

          <span>
            {error}
          </span>


          <button
            onClick={() =>
              setError(null)
            }
          >
            ×
          </button>

        </div>

      )}


      <main className="content">


        {/* ===================================================
            STATISTICS
            =================================================== */}

        <section className="stats-grid">

          <StatCard
            title="Total Emails"
            value={
              dashboard
                ?.total_emails ??
              0
            }
          />


          <StatCard
            title="Unread"
            value={
              dashboard
                ?.unread_emails ??
              0
            }
          />


          <StatCard
            title="Classified"
            value={
              dashboard
                ?.classified_emails ??
              0
            }
          />


          <StatCard
            title="Job Applications"
            value={
              jobEmailCount
            }
          />

        </section>


        {/* ===================================================
            WORKSPACE
            =================================================== */}

        <section className="workspace">


          {/* =================================================
              SIDEBAR
              ================================================= */}

          <aside className="sidebar">


            <div className="sidebar-section">

              <div className="sidebar-title">
                MAIL
              </div>


              {/* =================================================
                  INBOX
                  ================================================= */}

              <button
                className={
                  viewMode === "inbox" &&
                  filterMode === "all" &&
                  selectedCategory === "All"
                    ? "nav-item active"
                    : "nav-item"
                }
                onClick={() => {

                  setViewMode(
                    "inbox"
                  );

                  setFilterMode(
                    "all"
                  );

                  setSelectedCategory(
                    "All"
                  );

                  setSelectedEmail(
                    null
                  );

                }}
              >

                <span>
                  Inbox
                </span>

                <span>
                  {emails.length}
                </span>

              </button>


              {/* =================================================
                  JOB APPLICATIONS
                  ================================================= */}

              <button
                className={
                  viewMode === "jobs"
                    ? "nav-item active"
                    : "nav-item"
                }
                onClick={() => {

                  setViewMode(
                    "jobs"
                  );

                  setFilterMode(
                    "all"
                  );

                  setSelectedCategory(
                    "All"
                  );

                  setSelectedEmail(
                    null
                  );

                }}
              >

                <span>
                  Job Applications
                </span>

                <span>
                  {jobEmailCount}
                </span>

              </button>


              {/* =================================================
                  UNREAD
                  ================================================= */}

              <button
                className={
                  filterMode ===
                  "unread"
                    ? "nav-item active"
                    : "nav-item"
                }
                onClick={() => {

                  setViewMode(
                    "inbox"
                  );

                  setFilterMode(
                    "unread"
                  );

                  setSelectedCategory(
                    "All"
                  );

                  setSelectedEmail(
                    null
                  );

                }}
              >

                <span>
                  Unread
                </span>

                <span>
                  {
                    dashboard
                      ?.unread_emails ??
                    0
                  }
                </span>

              </button>


              {/* =================================================
                  HIGH RISK
                  ================================================= */}

              <button
                className={
                  filterMode ===
                  "high-risk"
                    ? "nav-item active"
                    : "nav-item"
                }
                onClick={() => {

                  setViewMode(
                    "inbox"
                  );

                  setFilterMode(
                    "high-risk"
                  );

                  setSelectedCategory(
                    "All"
                  );

                  setSelectedEmail(
                    null
                  );

                }}
              >

                <span>
                  High Risk
                </span>

                <span>
                  {
                    dashboard
                      ?.risk_levels
                      ?.High ??
                    0
                  }
                </span>

              </button>

            </div>


            {/* =================================================
                CATEGORIES
                ================================================= */}

            <div className="sidebar-section">

              <div className="sidebar-title">
                CATEGORIES
              </div>


              {CATEGORY_OPTIONS
                .filter(
                  category =>
                    category !==
                    "All"
                )
                .map(
                  category => (

                    <button
                      key={category}
                      className={
                        viewMode === "inbox" &&
                        filterMode === "all" &&
                        selectedCategory ===
                          category
                          ? "nav-item active"
                          : "nav-item"
                      }
                      onClick={() => {

                        setViewMode(
                          "inbox"
                        );

                        setFilterMode(
                          "all"
                        );

                        setSelectedCategory(
                          category
                        );

                        setSelectedEmail(
                          null
                        );

                      }}
                    >

                      <span>
                        {category}
                      </span>

                      <span>
                        {
                          dashboard
                            ?.categories
                            ?.[
                              category
                            ] ??
                          0
                        }
                      </span>

                    </button>

                  )
                )}

            </div>

          </aside>


          {/* =================================================
              INBOX / JOB APPLICATIONS
              ================================================= */}

          <section className="inbox">

            <div className="inbox-toolbar">

              <div>

                <h2>

                  {viewMode === "jobs"
                    ? "Job Applications"
                    : "Inbox"}

                </h2>


                <span>

                  {
                    filteredEmails.length
                  }{" "}

                  emails

                </span>

              </div>


              <div className="search-box">

                <span>
                  🔎
                </span>


                <input
                  value={search}
                  onChange={
                    event =>
                      setSearch(
                        event.target.value
                      )
                  }
                  placeholder={
                    viewMode === "jobs"
                      ? "Search job emails..."
                      : "Search emails..."
                  }
                />

              </div>

            </div>


            {/* =================================================
                ACTIVE FILTERS
                ================================================= */}

            <div className="active-filters">


              {viewMode === "jobs" && (

                <FilterChip
                  label="Job Applications"
                  onRemove={() => {

                    setViewMode(
                      "inbox"
                    );

                    setSelectedCategory(
                      "All"
                    );

                    setFilterMode(
                      "all"
                    );

                  }}
                />

              )}


              {selectedCategory !==
                "All" && (

                <FilterChip
                  label={
                    selectedCategory
                  }
                  onRemove={() =>
                    setSelectedCategory(
                      "All"
                    )
                  }
                />

              )}


              {filterMode ===
                "unread" && (

                <FilterChip
                  label="Unread"
                  onRemove={() =>
                    setFilterMode(
                      "all"
                    )
                  }
                />

              )}


              {filterMode ===
                "high-risk" && (

                <FilterChip
                  label="High Risk"
                  onRemove={() =>
                    setFilterMode(
                      "all"
                    )
                  }
                />

              )}


              {search && (

                <FilterChip
                  label={
                    `Search: ${search}`
                  }
                  onRemove={() =>
                    setSearch("")
                  }
                />

              )}

            </div>


            {/* =================================================
                EMAIL LIST
                ================================================= */}

            <div className="email-list">

              {filteredEmails.length ===
              0 ? (

                <div className="empty-state">

                  <div className="empty-icon">
                    ✉
                  </div>


                  <h3>

                    {viewMode === "jobs"
                      ? "No job applications found"
                      : "No emails found"}

                  </h3>


                  <p>

                    {viewMode === "jobs"
                      ? "Run AI classification to identify job-related emails."
                      : "Try changing your filters or search."}

                  </p>

                </div>

              ) : (

                filteredEmails.map(
                  email => (

                    <EmailRow
                      key={email.id}
                      email={email}
                      selected={
                        selectedEmail
                          ?.id ===
                        email.id
                      }
                      onClick={() =>
                        handleEmailSelect(
                          email
                        )
                      }
                    />

                  )
                )

              )}

            </div>

          </section>


          {/* =================================================
              EMAIL DETAILS
              ================================================= */}

          <EmailDetails
            email={
              selectedEmail
            }
            loading={
              loadingEmail
            }
            actionLoading={
              actionLoading
            }
            onAction={
              handleEmailAction
            }
          />

        </section>

      </main>

    </div>

  );

}


/* ============================================================
   STAT CARD
   ============================================================ */

function StatCard({
  title,
  value,
}: {
  title: string;
  value: number;
}) {

  return (

    <div className="stat-card">

      <span>
        {title}
      </span>


      <strong>
        {value}
      </strong>

    </div>

  );

}


/* ============================================================
   FILTER CHIP
   ============================================================ */

function FilterChip({
  label,
  onRemove,
}: {
  label: string;
  onRemove: () => void;
}) {

  return (

    <button
      className="filter-chip"
      onClick={
        onRemove
      }
    >

      {label}

      <span>
        ×
      </span>

    </button>

  );

}


/* ============================================================
   EMAIL ROW
   ============================================================ */

function EmailRow({
  email,
  selected,
  onClick,
}: {
  email: Email;
  selected: boolean;
  onClick: () => void;
}) {

  const classification =
    email.classification;


  return (

    <button
      className={
        selected
          ? "email-row selected"
          : email.is_read
            ? "email-row"
            : "email-row unread"
      }
      onClick={
        onClick
      }
    >

      <div className="email-avatar">

        {(
          email.sender_name ||
          email.sender ||
          "?"
        )
          .charAt(0)
          .toUpperCase()}

      </div>


      <div className="email-main">

        <div className="email-sender">

          <strong>

            {email.sender_name ||
              email.sender ||
              "Unknown sender"}

          </strong>


          {!email.is_read && (

            <span
              className="unread-dot"
            />

          )}

        </div>


        <h3>

          {email.subject ||
            "(No subject)"}

        </h3>


        <p>

          {email.snippet ||
            "No preview available."}

        </p>

      </div>


      <div className="email-ai">

        {classification ? (

          <>

            <span
              className="badge category"
            >

              {
                classification.category
              }

            </span>


            <span
              className={`badge risk ${
                classification
                  .risk_level
                  ?.toLowerCase() ??
                ""
              }`}
            >

              {
                classification
                  .risk_level
              }

            </span>


            <span
              className="confidence"
            >

              {Math.round(
                classification
                  .confidence *
                100
              )}

              %

            </span>


            {classification
              .is_job_related && (

              <span
                className="badge category"
              >
                Job
              </span>

            )}

          </>

        ) : (

          <span
            className="not-classified"
          >
            Not classified
          </span>

        )}

      </div>

    </button>

  );

}


/* ============================================================
   EMAIL DETAILS
   ============================================================ */

function EmailDetails({
  email,
  loading,
  actionLoading,
  onAction,
}: {
  email: Email | null;
  loading: boolean;
  actionLoading: boolean;
  onAction: (
    action:
      | "read"
      | "unread"
      | "archive"
      | "delete",
    emailId: number
  ) => Promise<void>;
}) {

  if (!email) {

    return (

      <aside
        className="details-panel"
      >

        <div
          className="details-header"
        >

          EMAIL DETAILS

        </div>


        <div
          className="details-empty"
        >

          Select an email to view
          its details.

        </div>

      </aside>

    );

  }


  const classification =
    email.classification;


  return (

    <aside
      className="details-panel"
    >

      <div
        className="details-header"
      >

        EMAIL DETAILS

      </div>


      {loading ? (

        <div
          className="details-loading"
        >

          <div
            className="loading-spinner"
          />

          Loading email...

        </div>

      ) : (

        <div
          className="details-content"
        >

          <div
            className="detail-avatar"
          >

            {(
              email.sender_name ||
              email.sender ||
              "?"
            )
              .charAt(0)
              .toUpperCase()}

          </div>


          <h2>

            {email.subject ||
              "(No subject)"}

          </h2>


          <div
            className="sender-details"
          >

            <strong>

              {email.sender_name ||
                "Unknown sender"}

            </strong>


            {email.sender && (

              <span>
                {email.sender}
              </span>

            )}

          </div>


          {email.received_at && (

            <div
              className="received-date"
            >

              {new Date(
                email.received_at
              ).toLocaleString()}

            </div>

          )}


          {/* ===============================================
              EMAIL ACTIONS
              =============================================== */}

          <div
            className="email-actions"
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "8px",
              margin: "18px 0",
            }}
          >

            <button
              type="button"
              disabled={
                actionLoading
              }
              onClick={() =>
                onAction(
                  email.is_read
                    ? "unread"
                    : "read",
                  email.id
                )
              }
              style={{
                padding:
                  "8px 12px",
                borderRadius:
                  "8px",
                border:
                  "1px solid #d1d5db",
                background:
                  "white",
                cursor:
                  actionLoading
                    ? "not-allowed"
                    : "pointer",
              }}
            >

              {actionLoading
                ? "Working..."
                : email.is_read
                  ? "Mark Unread"
                  : "Mark Read"}

            </button>


            <button
              type="button"
              disabled={
                actionLoading
              }
              onClick={() =>
                onAction(
                  "archive",
                  email.id
                )
              }
              style={{
                padding:
                  "8px 12px",
                borderRadius:
                  "8px",
                border:
                  "1px solid #d1d5db",
                background:
                  "white",
                cursor:
                  actionLoading
                    ? "not-allowed"
                    : "pointer",
              }}
            >

              Archive

            </button>


            <button
              type="button"
              disabled={
                actionLoading
              }
              onClick={() =>
                onAction(
                  "delete",
                  email.id
                )
              }
              style={{
                padding:
                  "8px 12px",
                borderRadius:
                  "8px",
                border:
                  "1px solid #fecaca",
                background:
                  "white",
                color:
                  "#b91c1c",
                cursor:
                  actionLoading
                    ? "not-allowed"
                    : "pointer",
              }}
            >

              Delete

            </button>

          </div>


          <div
            className="detail-divider"
          />


          {/* ===============================================
              AI CLASSIFICATION
              =============================================== */}

          <div
            className="ai-section"
          >

            <div
              className="ai-section-title"
            >

              AI CLASSIFICATION

            </div>


            {classification ? (

              <>

                <div
                  className="classification-main"
                >

                  <span
                    className="large-category"
                  >

                    {
                      classification.category
                    }

                  </span>


                  <span
                    className="confidence-large"
                  >

                    {Math.round(
                      classification
                        .confidence *
                      100
                    )}

                    % confidence

                  </span>

                </div>


                <DetailItem
                  label="Job Related"
                  value={
                    classification
                      .is_job_related
                      ? "Yes"
                      : "No"
                  }
                />


                <DetailItem
                  label="Recommended Action"
                  value={
                    classification
                      .recommended_action
                  }
                />


                <DetailItem
                  label="Risk Level"
                  value={
                    classification
                      .risk_level ||
                    "Unknown"
                  }
                />


                <div
                  className="detail-block"
                >

                  <span>
                    Keywords
                  </span>


                  <p>

                    {
                      classification
                        .keywords ||
                      "No keywords"
                    }

                  </p>

                </div>


                <div
                  className="detail-block"
                >

                  <span>
                    Why AI classified this
                  </span>


                  <p>

                    {
                      classification
                        .reason ||
                      "No explanation available."
                    }

                  </p>

                </div>

              </>

            ) : (

              <div
                className="not-classified-detail"
              >

                This email has not been
                classified by AI yet.

              </div>

            )}

          </div>


          <div
            className="detail-divider"
          />


          {/* ===============================================
              MESSAGE
              =============================================== */}

          <div
            className="email-body"
          >

            <div
              className="ai-section-title"
            >

              MESSAGE

            </div>


            {email.body ? (

              <div
                className="email-body-content"
              >

                {email.body}

              </div>

            ) : (

              <p>

                Email content is not
                available.

              </p>

            )}

          </div>

        </div>

      )}

    </aside>

  );

}


/* ============================================================
   DETAIL ITEM
   ============================================================ */

function DetailItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (

    <div
      className="detail-item"
    >

      <span>
        {label}
      </span>


      <strong>
        {value}
      </strong>

    </div>

  );

}


export default App;