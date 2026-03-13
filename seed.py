"""
Seed script — populates tags, quiz questions, options, and tag weights.
Run with: uv run python seed.py
"""

from database import SessionLocal, engine
from models import *  # noqa: registers all models


def seed():
    db = SessionLocal()
    try:
        # ── Tags ─────────────────────────────────────────────────────────────
        tags_data = [
            # Subject areas
            {"name": "matematica",   "label": "Matemática"},
            {"name": "lenguaje",     "label": "Lenguaje y Comunicación"},
            {"name": "ciencias",     "label": "Ciencias Naturales"},
            {"name": "historia",     "label": "Historia y Geografía"},
            {"name": "arte",         "label": "Arte y Creatividad"},
            # Student level
            {"name": "inicial",      "label": "Educación Inicial"},
            {"name": "basico",       "label": "Educación Básica"},
            {"name": "medio",        "label": "Educación Media"},
            # Teacher experience
            {"name": "principiante", "label": "Docente Principiante"},
            {"name": "experto",      "label": "Docente Experto"},
            # Context
            {"name": "rural",                  "label": "Zona Rural"},
            {"name": "urbano",                 "label": "Zona Urbana"},
            # Resource types (map to class `resources` field via tag_matcher)
            {"name": "sin_tecnologia",         "label": "Sin tecnología"},
            {"name": "computador",             "label": "Computador"},
            {"name": "computador_internet",    "label": "Computador + internet"},
        ]

        tags = {}
        for t in tags_data:
            existing = db.query(Tag).filter(Tag.name == t["name"]).first()
            if not existing:
                obj = Tag(name=t["name"], label=t["label"])
                db.add(obj)
                db.flush()
                tags[t["name"]] = obj
            else:
                tags[t["name"]] = existing

        # ── Questions ────────────────────────────────────────────────────────
        questions_data = [
            {
                "text": "¿Qué área quieres trabajar principalmente?",
                "order": 1,
                "options": [
                    {"text": "Matemática",               "weights": {"matematica": 3}},
                    {"text": "Lenguaje y Comunicación",  "weights": {"lenguaje": 3}},
                    {"text": "Ciencias Naturales",       "weights": {"ciencias": 3}},
                    {"text": "Historia y Geografía",     "weights": {"historia": 3}},
                    {"text": "Arte",                     "weights": {"arte": 3}},
                ],
            },
            {
                "text": "¿Qué nivel de experiencia tienes en esa área?",
                "order": 2,
                "options": [
                    {"text": "Estoy comenzando",         "weights": {"principiante": 3}},
                    {"text": "Tengo experiencia básica", "weights": {"principiante": 1}},
                    {"text": "Soy experto/a",            "weights": {"experto": 3}},
                ],
            },
            {
                "text": "¿Para qué nivel?",
                "order": 3,
                "options": [
                    {"text": "Educación Parvularia",     "weights": {"inicial": 3}},
                    {"text": "Educación Básica",         "weights": {"basico": 3}},
                    {"text": "Educación Media",          "weights": {"medio": 3}},
                ],
            },
            {
                "text": "¿Qué recursos tienes en tu aula?",
                "order": 4,
                "options": [
                    {"text": "Solo pizarrón y cuadernos",         "weights": {"sin_tecnologia": 3}},
                    {"text": "Computadores sin internet",          "weights": {"computador": 3}},
                    {"text": "Computadores con internet",          "weights": {"computador_internet": 3}},
                ],
            },
            {
                "text": "¿En qué zona de Chile trabajas?",
                "order": 5,
                "options": [
                    {"text": "Zona urbana",                  "weights": {"urbano": 3}},
                    {"text": "Zona rural",                   "weights": {"rural": 3}},
                    {"text": "Zona extrema (norte o sur)",   "weights": {"rural": 2}},
                ],
            },
        ]

        for q_data in questions_data:
            existing_q = db.query(QuizQuestion).filter(QuizQuestion.text == q_data["text"]).first()
            if existing_q:
                print(f"  Skipping existing question: {q_data['text'][:50]}")
                continue

            question = QuizQuestion(text=q_data["text"], order=q_data["order"])
            db.add(question)
            db.flush()

            for opt_data in q_data["options"]:
                option = QuizOption(question_id=question.id, text=opt_data["text"])
                db.add(option)
                db.flush()

                for tag_name, weight in opt_data["weights"].items():
                    db.add(QuizOptionTagWeight(
                        option_id=option.id,
                        tag_id=tags[tag_name].id,
                        weight=weight,
                    ))

            print(f"  ✓ {q_data['text'][:60]}")

        db.commit()
        print("\nSeed complete.")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
