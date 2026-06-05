"""Application services that assemble family tree details for the UI."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .models import Person, Relation
from .repository import FamilyTreeRepository


@dataclass(frozen=True)
class RelatedPerson:
    """A person with the relation row that connected them to the selected person."""

    person: Person
    relation: Relation


@dataclass(frozen=True)
class FamilyRelationRow:
    """Display-ready father, mother, and child relationship row."""

    relation: Relation
    father: Person | None
    mother: Person | None
    child: Person | None


@dataclass(frozen=True)
class PersonDetails:
    """Full detail view model for a selected person."""

    person: Person
    parents: tuple[RelatedPerson, ...]
    spouses: tuple[RelatedPerson, ...]
    children: tuple[RelatedPerson, ...]
    ordered_family_rows: tuple[FamilyRelationRow, ...]
    root_person: Person | None
    relationship_to_root: tuple[Person, ...]
    earliest_known_people: tuple[Person, ...]
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
        related_relations = self._unique_relations(parent_relations + child_relations)

        parents = self._collect_parents(parent_relations)
        spouses = self._collect_spouses(person_id, child_relations)
        children = self._collect_children(child_relations)
        ordered_family_rows = self._collect_ordered_family_rows(related_relations)
        relationship_notes = self._collect_relationship_notes(related_relations, language)
        root_person = self._get_root_person()
        relationship_to_root = self._find_relationship_path_to_root(person_id)
        earliest_known_people = self._find_earliest_known_people(person_id)

        return PersonDetails(
            person=selected_person,
            parents=tuple(parents),
            spouses=tuple(spouses),
            children=tuple(children),
            ordered_family_rows=tuple(ordered_family_rows),
            root_person=root_person,
            relationship_to_root=tuple(relationship_to_root),
            earliest_known_people=tuple(earliest_known_people),
            relationship_notes=tuple(relationship_notes),
        )

    def _collect_parents(self, relations: list[Relation]) -> list[RelatedPerson]:
        related_people: list[RelatedPerson] = []
        seen_ids: set[str] = set()
        for relation in self._sort_relations(relations):
            for parent_id in (relation.parent_id, relation.mother_id):
                self._append_related_person(related_people, seen_ids, parent_id, relation)
        return related_people

    def _collect_spouses(self, person_id: str, relations: list[Relation]) -> list[RelatedPerson]:
        related_people: list[RelatedPerson] = []
        seen_ids: set[str] = set()
        for relation in self._sort_relations(relations):
            spouse_id = relation.mother_id if relation.parent_id == person_id else relation.parent_id
            self._append_related_person(related_people, seen_ids, spouse_id, relation)
        return related_people

    def _collect_children(self, relations: list[Relation]) -> list[RelatedPerson]:
        related_people: list[RelatedPerson] = []
        seen_ids: set[str] = set()
        for relation in self._sort_relations(relations):
            self._append_related_person(related_people, seen_ids, relation.child_id, relation)
        return related_people

    def _collect_ordered_family_rows(self, relations: list[Relation]) -> list[FamilyRelationRow]:
        return [
            FamilyRelationRow(
                relation=relation,
                father=self.repository.get_person(relation.parent_id),
                mother=self.repository.get_person(relation.mother_id),
                child=self.repository.get_person(relation.child_id),
            )
            for relation in self._sort_relations(relations)
        ]

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

    def _get_root_person(self) -> Person | None:
        if not self.repository.relations:
            return None
        return self.repository.get_person(self.repository.relations[0].parent_id)

    def _find_relationship_path_to_root(self, person_id: str) -> list[Person]:
        """Return the shortest known root-to-person path using parent/spouse-to-child rows."""
        if not self.repository.relations:
            return []
        root_id = self.repository.relations[0].parent_id
        target_id = str(person_id)
        queue: deque[tuple[str, list[str]]] = deque([(root_id, [root_id])])
        seen_ids = {root_id}

        while queue:
            current_id, path = queue.popleft()
            if current_id == target_id:
                return [person for path_id in path if (person := self.repository.get_person(path_id))]
            for relation in self.repository.get_child_relations(current_id):
                child_id = relation.child_id
                if child_id and child_id not in seen_ids:
                    seen_ids.add(child_id)
                    queue.append((child_id, path + [child_id]))
        return []

    def _find_earliest_known_people(self, person_id: str) -> list[Person]:
        """Return ancestors on this screen's lineage that have no parent row in the dataset."""
        ancestor_ids: set[str] = set()
        queue: deque[str] = deque([str(person_id)])
        seen_ids: set[str] = set()

        while queue:
            current_id = queue.popleft()
            if current_id in seen_ids:
                continue
            seen_ids.add(current_id)

            parent_relations = self.repository.get_parent_relations(current_id)
            parent_ids = [
                parent_id
                for relation in parent_relations
                for parent_id in (relation.parent_id, relation.mother_id)
                if parent_id and self.repository.get_person(parent_id)
            ]
            if not parent_ids:
                ancestor_ids.add(current_id)
                continue
            queue.extend(parent_ids)

        ancestors = [person for person_id in ancestor_ids if (person := self.repository.get_person(person_id))]
        return sorted(ancestors, key=lambda person: self._person_sort_key(person))

    def _sort_relations(self, relations: list[Relation]) -> list[Relation]:
        return sorted(
            relations,
            key=lambda relation: (
                self._sequence_sort_key(relation.child_sequence_label),
                self._id_sort_key(relation.parent_id),
                self._id_sort_key(relation.mother_id),
                self._id_sort_key(relation.child_id),
            ),
        )

    @staticmethod
    def _unique_relations(relations: list[Relation]) -> list[Relation]:
        unique_relations: list[Relation] = []
        seen_keys: set[tuple[str, str, str, str]] = set()
        for relation in relations:
            relation_key = (
                relation.parent_id,
                relation.mother_id,
                relation.child_id,
                relation.child_sequence_label,
            )
            if relation_key in seen_keys:
                continue
            seen_keys.add(relation_key)
            unique_relations.append(relation)
        return unique_relations

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
        numeric_part = "".join(character for character in sequence_label if character.isdigit())
        if numeric_part:
            return (int(numeric_part), sequence_label.casefold())
        return (10_000, sequence_label.casefold())

    @staticmethod
    def _id_sort_key(person_id: str) -> tuple[int, str]:
        if person_id.isdigit():
            return (int(person_id), person_id)
        return (10_000, person_id.casefold())

    def _person_sort_key(self, person: Person) -> tuple[int, str]:
        return (self._id_sort_key(person.person_id)[0], person.display_name("en").casefold())
