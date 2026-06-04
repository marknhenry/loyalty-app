from fastapi import APIRouter

router = APIRouter()


@router.get("/accounts/{member_id}")
def get_member_loyalty(member_id: str) -> dict[str, str | int]:
    return {
        "member_id": member_id,
        "points_balance": 0,
        "message": "Placeholder loyalty route. Integrate with loyalty ledger service.",
    }
