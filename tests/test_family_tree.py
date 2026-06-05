"""Tests for the HRP family tree application."""

from app import app
from family_tree import FamilyTreeRepository, FamilyTreeService


repository = FamilyTreeRepository("personsData.csv", "relation.csv")
service = FamilyTreeService(repository)


def test_search_people_supports_partial_english_name() -> None:
    matches = service.search_people("Kiran")

    assert any(person.person_id == "113" for person in matches)


def test_person_details_include_parents_spouse_and_children() -> None:
    details = service.get_person_details("112")

    assert details is not None
    assert {parent.person.person_id for parent in details.parents} == {"116", "115"}
    assert any(spouse.person.person_id == "111" for spouse in details.spouses)
    assert {child.person.person_id for child in details.children}.issuperset({"113", "114", "125"})


def test_index_route_renders_search_results() -> None:
    with app.test_client() as client:
        response = client.get("/?q=Kiran")

    assert response.status_code == 200
    assert b"Kiran H P" in response.data


def test_person_detail_route_renders_selected_person() -> None:
    with app.test_client() as client:
        response = client.get("/person/112")

    assert response.status_code == 200
    assert b"Prabhakar H R" in response.data


def test_person_details_include_ordered_father_mother_child_rows() -> None:
    details = service.get_person_details("112")

    assert details is not None
    child_order = [(row.relation.child_sequence_label, row.child.person_id) for row in details.ordered_family_rows[:3]]

    assert child_order == [
        ("1", "113"),
        ("f1", "125"),
        ("2", "114"),
    ]
    assert all(
        row.father is not None and row.mother is not None and row.child is not None
        for row in details.ordered_family_rows
    )


def test_person_details_include_navigation_and_root_relationship_context() -> None:
    with app.test_client() as client:
        response = client.get("/person/112")

    assert response.status_code == 200
    assert b"Family rows by child serial number" in response.data
    assert b"Father (pid)" in response.data
    assert b"Mother (mid)" in response.data
    assert b"Child (cid)" in response.data
    assert b"Relationship to family root" in response.data
    assert b"Person with no parent available" in response.data
    assert b"\xe2\x86\x90 Back" in response.data
    assert b"\xe2\x8c\x82 Home" in response.data
