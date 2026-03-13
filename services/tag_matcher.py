from sqlalchemy.orm import Session
from models.quiz import QuizOptionTagWeight
from models.tag import Tag
from uuid import UUID

# These map directly to the `resources` field on Sanity class documents
RESOURCE_TAGS = {'sin_tecnologia', 'computador', 'computador_internet'}


def compute_tags(answers: dict[str, str], db: Session, threshold: int = 2) -> tuple[list[str], str | None]:
    """
    answers: { question_id: option_id }
    Returns (topic_tags, resource) where:
      - topic_tags: tag names with score >= threshold, excluding resource tags
      - resource: the resource tag with highest score, or None
    """
    tag_scores: dict[str, int] = {}

    for question_id, option_id in answers.items():
        try:
            opt_uuid = UUID(option_id)
        except ValueError:
            continue

        weights = (
            db.query(QuizOptionTagWeight)
            .filter(QuizOptionTagWeight.option_id == opt_uuid)
            .all()
        )
        for w in weights:
            tag = db.query(Tag).filter(Tag.id == w.tag_id).first()
            if tag:
                tag_scores[tag.name] = tag_scores.get(tag.name, 0) + w.weight

    topic_tags = [
        tag for tag, score in tag_scores.items()
        if score >= threshold and tag not in RESOURCE_TAGS
    ]

    resource_scores = {tag: score for tag, score in tag_scores.items() if tag in RESOURCE_TAGS}
    resource = max(resource_scores, key=resource_scores.get) if resource_scores else None

    return topic_tags, resource
