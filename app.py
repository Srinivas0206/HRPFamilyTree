"""Flask entry point for the HRP family tree web application."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, url_for

from family_tree import FamilyTreeRepository, FamilyTreeService

BASE_DIR = Path(__file__).resolve().parent
PERSONS_CSV_PATH = BASE_DIR / "personsData.csv"
RELATIONS_CSV_PATH = BASE_DIR / "relation.csv"


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "family-tree-development-secret")
    repository = FamilyTreeRepository(PERSONS_CSV_PATH, RELATIONS_CSV_PATH)
    family_tree_service = FamilyTreeService(repository)

    @app.context_processor
    def inject_display_settings() -> dict[str, str]:
        return {"current_language": session.get("language", "en")}

    @app.get("/")
    def index() -> str:
        query = request.args.get("q", "").strip()
        matching_people = family_tree_service.search_people(query) if query else []
        return render_template(
            "index.html",
            query=query,
            matching_people=matching_people,
            total_people=len(repository.people_by_id),
        )

    @app.get("/person/<person_id>")
    def person_detail(person_id: str) -> str:
        language = session.get("language", "en")
        person_details = family_tree_service.get_person_details(person_id, language=language)
        if person_details is None:
            abort(404)
        return render_template("person_detail.html", details=person_details)

    @app.post("/language")
    def set_language():
        selected_language = request.form.get("language", "en")
        session["language"] = "kn" if selected_language == "kn" else "en"
        return redirect(request.form.get("next") or url_for("index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
