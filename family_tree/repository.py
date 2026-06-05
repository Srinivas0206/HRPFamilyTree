"""CSV-backed repository for family tree people and relationships."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .models import Person, Relation


class FamilyTreeRepository:
    """Loads and indexes the family tree data from CSV files."""

    def __init__(self, persons_csv_path: Path | str, relations_csv_path: Path | str) -> None:
        self.persons_csv_path = Path(persons_csv_path)
        self.relations_csv_path = Path(relations_csv_path)
        self.people_by_id: dict[str, Person] = {}
        self.relations: list[Relation] = []
        self.relations_by_child_id: dict[str, list[Relation]] = {}
        self.relations_by_parent_id: dict[str, list[Relation]] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load people and relationship indexes into memory."""
        self.people_by_id = self._load_people()
        self.relations = self._load_relations()
        self.relations_by_child_id = self._group_relations_by_child(self.relations)
        self.relations_by_parent_id = self._group_relations_by_parent(self.relations)

    def _load_people(self) -> dict[str, Person]:
        with self.persons_csv_path.open(encoding="utf-8-sig", newline="") as persons_file:
            return {
                self._clean(row["id"]): Person(
                    person_id=self._clean(row["id"]),
                    name_kannada=self._clean(row.get("nameK")),
                    name_english=self._clean(row.get("nameE")),
                    place_kannada=self._clean(row.get("placeK")),
                    place_english=self._clean(row.get("placeE")),
                    generation=self._clean(row.get("gen")),
                    gotra=self._clean(row.get("gotra")),
                    notes=self._clean(row.get("nameR")),
                )
                for row in csv.DictReader(persons_file)
                if self._clean(row.get("id"))
            }

    def _load_relations(self) -> list[Relation]:
        with self.relations_csv_path.open(encoding="utf-8-sig", newline="") as relations_file:
            return [
                Relation(
                    parent_id=self._clean(row.get("pid")),
                    mother_id=self._clean(row.get("mid")),
                    child_id=self._clean(row.get("cid")),
                    child_sequence_label=self._clean(row.get("csl")),
                    relation_kannada=self._clean(row.get("relnK")),
                    relation_english=self._clean(row.get("relnE")),
                    who_kannada=self._clean(row.get("whoK")),
                    who_english=self._clean(row.get("whoE")),
                )
                for row in csv.DictReader(relations_file)
                if self._clean(row.get("cid"))
            ]

    def get_person(self, person_id: str) -> Person | None:
        """Return one person by identifier, if present."""
        return self.people_by_id.get(str(person_id))

    def search_people(self, query: str, limit: int = 50) -> list[Person]:
        """Search people by partial first name, last name, place, gotra, or notes."""
        normalized_terms = [term.casefold() for term in query.split() if term.strip()]
        if not normalized_terms:
            return []

        matches = [
            person
            for person in self.people_by_id.values()
            if all(term in person.searchable_text for term in normalized_terms)
        ]
        return sorted(matches, key=lambda person: (person.name_english.casefold(), person.person_id))[:limit]

    def get_parent_relations(self, child_id: str) -> list[Relation]:
        """Return relationship rows where the requested person is listed as a child."""
        return self.relations_by_child_id.get(str(child_id), [])

    def get_child_relations(self, parent_id: str) -> list[Relation]:
        """Return relationship rows where the requested person is listed as a parent/spouse."""
        return self.relations_by_parent_id.get(str(parent_id), [])

    @staticmethod
    def _group_relations_by_child(relations: Iterable[Relation]) -> dict[str, list[Relation]]:
        grouped: dict[str, list[Relation]] = {}
        for relation in relations:
            grouped.setdefault(relation.child_id, []).append(relation)
        return grouped

    @staticmethod
    def _group_relations_by_parent(relations: Iterable[Relation]) -> dict[str, list[Relation]]:
        grouped: dict[str, list[Relation]] = {}
        for relation in relations:
            for person_id in (relation.parent_id, relation.mother_id):
                if person_id:
                    grouped.setdefault(person_id, []).append(relation)
        return grouped

    @staticmethod
    def _clean(value: object | None) -> str:
        return str(value or "").strip()
