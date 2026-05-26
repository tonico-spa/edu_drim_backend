import os
import urllib.parse
import httpx

SANITY_PROJECT_ID = os.getenv("SANITY_PROJECT_ID", "")
SANITY_DATASET = os.getenv("SANITY_DATASET", "production")
SANITY_API_VERSION = "2024-01-01"


def _sanity_url(query: str) -> str:
    encoded = urllib.parse.quote(query)
    return (
        f"https://{SANITY_PROJECT_ID}.api.sanity.io"
        f"/v{SANITY_API_VERSION}/data/query/{SANITY_DATASET}"
        f"?query={encoded}"
    )


def fetch_classes(tag_names: list[str] | None = None, resource: str | None = None) -> list[dict]:
    filters = ['_type == "class"']

    if resource:
        filters.append(f'resources == "{resource}"')

    if tag_names:
        tag_conditions = " || ".join(
            [f'"{t}" in tags[]->name.current' for t in tag_names]
        )
        filters.append(f"({tag_conditions})")

    filter_str = " && ".join(filters)

    groq = f"""
    *[{filter_str}]{{
        _id,
        title,
        description,
        duration_minutes,
        level,
        resources,
        "tags": tags[]->{{ "name": name.current, label }},
        "main_tag": main_tag->{{ "name": name.current, label, color }}
    }}
    """
    url = _sanity_url(groq.strip())
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json().get("result", [])


def fetch_class_by_sanity_id(sanity_id: str) -> dict | None:
    groq = f"""
    *[_type == "class" && _id == "{sanity_id}"][0]{{
        _id,
        title,
        description,
        duration_minutes,
        level,
        resources,
        materials,
        "tags": tags[]->{{ "name": name.current, label }},
        "main_tag": main_tag->{{ "name": name.current, label, color }},
        video_link,
        unidad,
        semestre,
        duration,
        class_name,
        type,
        recursos,
        closing,
        "images": images[]{{ "url": asset->url }},
        "files": files[]{{ "url": asset->url, "name": asset->originalFilename }}
    }}
    """
    url = _sanity_url(groq.strip())
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json().get("result")


def fetch_courses(tag_names: list[str] | None = None) -> list[dict]:
    if tag_names:
        tag_filter = " && ".join(
            [f'"{t}" in tags[]->name.current' for t in tag_names]
        )
        groq = f"""
        *[_type == "course" && ({tag_filter})]{{
            _id,
            title,
            description,
            "tags": tags[]->{{ "name": name.current, label }},
            "classes": classes[]->{{
                _id,
                title,
                description,
                duration_minutes,
                level,
                "tags": tags[]->{{ "name": name.current, label }}
            }}
        }}
        """
    else:
        groq = """
        *[_type == "course"]{
            _id,
            title,
            description,
            "tags": tags[]->{ "name": name.current, label },
            "classes": classes[]->{
                _id,
                title,
                description,
                duration_minutes,
                level,
                "tags": tags[]->{ "name": name.current, label }
            }
        }
        """

    url = _sanity_url(groq.strip())
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json().get("result", [])


def fetch_professors() -> list[dict]:
    groq = """
    *[_type == "professor"]{
        _id,
        name,
        title,
        "photo_url": photo.asset->url,
        bio
    }
    """
    url = _sanity_url(groq.strip())
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json().get("result", [])


def fetch_professor_by_id(sanity_id: str) -> dict | None:
    groq = f"""
    *[_type == "professor" && _id == "{sanity_id}"][0]{{
        _id,
        name,
        title,
        "photo_url": photo.asset->url,
        bio
    }}
    """
    url = _sanity_url(groq.strip())
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json().get("result")


def fetch_course_by_id(sanity_id: str) -> dict | None:
    groq = f"""
    *[_type == "course" && _id == "{sanity_id}"][0]{{
        _id,
        title,
        description,
        "tags": tags[]->{{ "name": name.current, label }},
        "classes": classes[]->{{
            _id,
            title,
            description,
            duration_minutes,
            level,
            "tags": tags[]->{{ "name": name.current, label }}
        }}
    }}
    """
    url = _sanity_url(groq.strip())
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json().get("result")
