from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.auth.credential_service import (
    load_google_credentials,
)
from app.database.database import SessionLocal
from app.models import EmailAccount
from app.services.email.email_sync_service import (
    sync_gmail_emails,
)


scheduler = BackgroundScheduler()


# ============================================================
# Sync all Gmail accounts
# ============================================================

def sync_all_google_accounts():
    """
    Synchronize all connected Gmail accounts.
    """

    db: Session = SessionLocal()

    try:

        accounts = (
            db.query(EmailAccount)
            .filter(
                EmailAccount.provider
                == "gmail"
            )
            .all()
        )

        print(
            f"Automatic Gmail sync: "
            f"found {len(accounts)} account(s)"
        )

        for account in accounts:

            try:

                credentials = (
                    load_google_credentials(
                        account
                    )
                )

                result = sync_gmail_emails(
                    db=db,
                    email_account=account,
                    credentials=credentials,
                    max_results=10,
                )

                print(
                    "Automatic Gmail sync:",
                    account.id,
                    result,
                )

            except Exception as error:

                print(
                    "Automatic Gmail sync failed "
                    f"for account {account.id}: "
                    f"{error}"
                )

    except Exception as error:

        print(
            "Automatic Gmail sync failed: "
            f"{error}"
        )

    finally:

        db.close()


# ============================================================
# Start scheduler
# ============================================================

def start_scheduler():
    """
    Start automatic Gmail synchronization.
    """

    if scheduler.running:
        return

    scheduler.add_job(
        sync_all_google_accounts,
        "interval",
        minutes=5,
        id="gmail_sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    print(
        "Email scheduler started. "
        "Gmail sync runs every 5 minutes."
    )


# ============================================================
# Stop scheduler
# ============================================================

def stop_scheduler():
    """
    Stop automatic Gmail synchronization.
    """

    if not scheduler.running:
        return

    scheduler.shutdown(
        wait=False
    )

    print(
        "Email scheduler stopped."
    )