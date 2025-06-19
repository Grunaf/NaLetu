from flaskr import db
from sqlalchemy import select
from collections import Counter
from typing import Any
from models.trip import TripParticipant, TripVote

def get_winners_day_variants(votes, day_count):
    winner_days_variant = [ c[0] for c in Counter([v.day_variant for v in votes]).most_common(day_count)]
    return sorted(winner_days_variant, key=lambda dv: dv.day.day_order)

def get_participant_and_votes(participants: TripParticipant) -> list[dict[str, Any]]:
    """
    Создает словарь участников и их голосов
    {
        "participant_name": name
        "votes": 
        [
        "1": name_day_variant,
        ...
        ]
    }
    """
    return [{
                "participant_name": p.user.name,
                "votes": {f"{v.day_order}": f"{v.day_variant.name}"
                            for v in sorted(p.votes, key=lambda v:v.day_order) }
            } for p in participants if len(p.votes)]

def get_voting_attributes(session_id: int, day_count, get_detailed_votes=False) -> dict[str, Any]:
    stmt = select(TripParticipant).where(TripParticipant.session_id==session_id)
    participants = db.session.execute(stmt).scalars().all()

    stmt = select(TripVote).where(TripVote.session_id==session_id)
    votes = db.session.execute(stmt).scalars().all()

    winner_variants = get_winners_day_variants(votes, day_count)        

    return {"is_completed_vote": len(participants) == len(votes),
            "votes": get_participant_and_votes(participants) if get_detailed_votes else votes,
            "winner_variants": winner_variants}
