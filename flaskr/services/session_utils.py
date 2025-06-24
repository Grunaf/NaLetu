from collections import Counter
from typing import Any, List

from flaskr.db.participants import get_participants_by_session_id
from flaskr.db.trip_vote import get_trip_votes_by_uuid
from flaskr.schemas.route import DayRead, DayVariantRead, ParticipantVotesDTO

from flaskr.models.trip import TripParticipant, TripVote


def get_days_with_winner_variant(
    votes: list[TripVote], day_count
) -> List[DayRead]:
    """
    Возвращает `day_count` наиболее популярных DayVariant,
    отсортированных по порядку дня.
    """
    variants_id = [v.variant_id for v in votes]

    winner_variants_id = [
        variant_id
        for variant_id, _ in Counter(variants_id).most_common(day_count)
    ]
    winner_variants = {
        vote.day_variant
        for vote in votes
        if vote.variant_id in winner_variants_id
    }

    days_with_variant = []
    for variant in winner_variants:
        variant_read = DayVariantRead.model_validate(variant)
        days_with_variant.append(
            DayRead(
                id=variant.day_id,
                day_order=variant.day.day_order,
                variant=variant_read,
            )
        )

    return sorted(days_with_variant, key=lambda d: d.day_order)


def get_participants_votes(
    participants: list[TripParticipant],
) -> List[ParticipantVotesDTO]:
    """
    Возвращает список участников с их голосами (отсортировано по day_order)
    """
    participants_votes = []

    for participant in participants:
        have_vote = len(participant.votes) != 0
        if not have_vote:
            continue

        days_with_variant = []
        for vote in participant.votes:
            day_variant = vote.day_variant
            day_variant_read = DayVariantRead.model_validate(day_variant)

            days_with_variant.append(
                DayRead(
                    id=day_variant.day_id,
                    day_order=day_variant.day.day_order,
                    variant=day_variant_read,
                )
            )

        participant_read = ParticipantVotesDTO(
            name=participant.user.name, days_with_variant=days_with_variant
        )
        participants_votes.append(participant_read)

    return participants_votes


def get_voting_attributes(session_id: int, day_count) -> dict[str, Any]:
    participants = get_participants_by_session_id(session_id)

    votes: list[TripVote] = get_trip_votes_by_uuid(session_id)
    participants_that_vote = {vote.participant for vote in votes}

    is_all_voted = len(participants_that_vote) == len(participants)
    days_with_winner_variant = (
        get_days_with_winner_variant(votes, day_count) if is_all_voted else []
    )

    return {
        "is_completed_vote": is_all_voted,
        "days_with_winner_variant": days_with_winner_variant,
    }
