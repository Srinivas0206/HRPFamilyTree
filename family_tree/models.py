"""Data models for the family tree application."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Person:
    """A single person record loaded from the persons dataset."""

    person_id: str
    name_kannada: str
    name_english: str
    place_kannada: str
    place_english: str
    generation: str
    gotra: str
    notes: str

    @property
    def searchable_text(self) -> str:
        """Return normalized text used by repository search."""
        return " ".join(
            value
            for value in (
                self.person_id,
                self.name_english,
                self.name_kannada,
                self.place_english,
                self.place_kannada,
                self.gotra,
                self.notes,
            )
            if value
        ).casefold()

    def display_name(self, language: str = "en") -> str:
        """Return the preferred display name for the requested language."""
        if language == "kn" and self.name_kannada:
            return self.name_kannada
        return self.name_english or self.name_kannada or f"Person {self.person_id}"

    def display_place(self, language: str = "en") -> str:
        """Return the preferred place name for the requested language."""
        if language == "kn" and self.place_kannada:
            return self.place_kannada
        return self.place_english or self.place_kannada or "Unknown"


@dataclass(frozen=True)
class Relation:
    """A relationship row connecting parents, children, and contextual notes."""

    parent_id: str
    mother_id: str
    child_id: str
    child_sequence_label: str
    relation_kannada: str
    relation_english: str
    who_kannada: str
    who_english: str

    def display_relation(self, language: str = "en") -> str:
        """Return the relationship description for the requested language."""
        if language == "kn" and self.relation_kannada:
            return self.relation_kannada
        return self.relation_english or self.relation_kannada

    def display_note(self, language: str = "en") -> str:
        """Return the contextual note for the requested language."""
        if language == "kn" and self.who_kannada:
            return self.who_kannada
        return self.who_english or self.who_kannada
