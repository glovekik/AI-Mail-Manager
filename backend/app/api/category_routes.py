from fastapi import APIRouter


router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"],
)


CATEGORIES = [
    "Work",
    "Personal",
    "Finance",
    "Promotions",
    "Social",
    "Updates",
    "Spam",
    "Other",
]


@router.get("")
def get_categories():
    return {
        "categories": CATEGORIES
    }