"""End-to-end dedupe test using the real SQLite-backed session store.

These use the real DBOperator/Database stack (no mocks) because the original
bug was an interaction between them, and it only showed up across real runs.
"""

import pytest

from smartmailer.core.template import (
    JinjaTemplateParser,
    JinjaTemplateRenderer,
    TemplateEngine,
    TemplateModel,
    TemplateValidator,
)
from smartmailer.session_management.db_operator import DBOperator
from smartmailer.session_management.session_manager import SessionManager
from smartmailer.smartmailer import SmartMailer
from jinja2 import Environment


class Person(TemplateModel):
    name: str
    email: str


@pytest.fixture(autouse=True)
def clean_db_operator(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield
    for op in list(DBOperator._instances.values()):
        op.shutdown()
    DBOperator._instances.clear()


@pytest.fixture
def template():
    env = Environment()
    return TemplateEngine(
        parser=JinjaTemplateParser(env),
        validator=TemplateValidator(),
        renderer=JinjaTemplateRenderer(env),
        subject="Hi {{ name }}",
        text="Hello {{ name }}",
    )


def _people():
    return [
        Person(name="A", email="a@example.com"),
        Person(name="B", email="b@example.com"),
    ]


def test_first_run_sends_everyone(template):
    sm = SmartMailer("sender@gmail.com", "pw", "gmail", "s")
    people = _people()

    assert sm.session_manager.filter_unsent_recipients(people) == people


def test_same_recipients_are_skipped_on_reload(template):
    """A new SessionManager pointed at the same session sees prior sends."""
    people = _people()

    first = SessionManager("resume")
    for person in people:
        first.add_recipient(person)
    first.db_op.shutdown()

    second = SessionManager("resume")
    assert second.filter_unsent_recipients(people) == []
    second.db_op.shutdown()


def test_only_unseen_recipients_are_returned(template):
    people = _people()

    first = SessionManager("partial")
    first.add_recipient(people[0])
    first.db_op.shutdown()

    second = SessionManager("partial")
    assert second.filter_unsent_recipients(people) == [people[1]]
    second.db_op.shutdown()


def test_sessions_in_same_process_do_not_share_database(tmp_path):
    """The second half of the bug: B must not write into A's file."""
    a = SessionManager("alpha")
    b = SessionManager("beta")

    assert a.dbfile_path != b.dbfile_path
    assert a.db_op is not b.db_op
    assert a.db_op.dbfile_path == a.dbfile_path
    assert b.db_op.dbfile_path == b.dbfile_path

    person = Person(name="A", email="a@example.com")
    b.add_recipient(person)
    b.db_op.shutdown()

    # Person recorded in beta only; alpha must still think it's unsent.
    assert SessionManager("beta").filter_unsent_recipients([person]) == []
    assert SessionManager("alpha").filter_unsent_recipients([person]) == [person]
