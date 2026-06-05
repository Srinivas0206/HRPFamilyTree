"""Application services that assemble family tree details for the UI."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Person, Relation
from .repository import FamilyTreeRepository


@dataclass(frozen=True)
class RelatedPerson:
    """A person with the relation row that connected them to the selected person."""

    person: Person
    relation: Relation


@dataclass(frozen=True)
class PersonDetails:
    """Full detail view model for a selected person."""

    person: Person
    parents: tuple[RelatedPerson, ...]
    spouses: tuple[RelatedPerson, ...]
    children: tuple[RelatedPerson, ...]
    relationship_notes: tuple[str, ...]


class FamilyTreeService:
    """Provides use-case oriented operations for the Flask routes."""

    def __init__(self, repository: FamilyTreeRepository) -> None:
        self.repository = repository

    def search_people(self, query: str, limit: int = 50) -> list[Person]:
        """Search for matching people using partial words."""
        return self.repository.search_people(query=query, limit=limit)

    def get_person_details(self, person_id: str, language: str = "en") -> PersonDetails | None:
        """Build a complete family summary for the selected person."""
        selected_person = self.repository.get_person(person_id)
        if selected_person is None:
            return None

        parent_relations = self.repository.get_parent_relations(person_id)
        child_relations = self.repository.get_child_relations(person_id)

        parents = self._collect_parents(parent_relations)
        spouses = self._collect_spouses(person_id, child_relations)
        children = self._collect_children(child_relations)
        relationship_notes = self._collect_relationship_notes(parent_relations + child_relations, language)

        return PersonDetails(
            person=selected_person,
            parents=tuple(parents),
            spouses=tuple(spouses),
            children=tuple(children),
            relationship_notes=tuple(relationship_notes),
        )

    def _collect_parents(self, relations: list[Relation]) -> list[RelatedPerson]:
        related_people: list[RelatedPerson] = []
        seen_ids: set[str] = set()
        for relation in relations:
            for parent_id in (relation.parent_id, relation.mother_id):
                self._append_related_person(related_people, seen_ids, parent_id, relation)
        return related_people

    def _collect_spouses(self, person_id: str, relations: list[Relation]) -> list[RelatedPerson]:
        related_people: list[RelatedPerson] = []
        seen_ids: set[str] = set()
        for relation in relations:
            spouse_id = relation.mother_id if relation.parent_id == person_id else relation.parent_id
            self._append_related_person(related_people, seen_ids, spouse_id, relation)
        return related_people

    def _collect_children(self, relations: list[Relation]) -> list[RelatedPerson]:
        related_people: list[RelatedPerson] = []
        seen_ids: set[str] = set()
        sorted_relations = sorted(relations, key=lambda relation: self._sequence_sort_key(relation.child_sequence_label))
        for relation in sorted_relations:
            self._append_related_person(related_people, seen_ids, relation.child_id, relation)
        return related_people

    def _append_related_person(
        self,
        related_people: list[RelatedPerson],
        seen_ids: set[str],
        person_id: str,
        relation: Relation,
    ) -> None:
        if not person_id or person_id in seen_ids:
            return
        person = self.repository.get_person(person_id)
        if person is None:
            return
        related_people.append(RelatedPerson(person=person, relation=relation))
        seen_ids.add(person_id)

    @staticmethod
    def _collect_relationship_notes(relations: list[Relation], language: str) -> list[str]:
        notes: list[str] = []
        for relation in relations:
            relation_note = relation.display_note(language)
            relation_description = relation.display_relation(language)
            combined_note = " — ".join(value for value in (relation_description, relation_note) if value)
            if combined_note and combined_note not in notes:
                notes.append(combined_note)
        return notes

    @staticmethod
    def _sequence_sort_key(sequence_label: str) -> tuple[int, str]:
        if sequence_label.isdigit():
            return (int(sequence_label), sequence_label)
        return (10_000, sequence_label)
