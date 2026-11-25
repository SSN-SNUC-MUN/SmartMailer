import time
import pytest
from unittest.mock import MagicMock, patch
from smartmailer.session_management.db_operator import DBOperator


@pytest.fixture(autouse=True)
def reset_registry():
    for op in list(DBOperator._instances.values()):
        op.shutdown()
    DBOperator._instances.clear()
    yield
    for op in list(DBOperator._instances.values()):
        op.shutdown()
    DBOperator._instances.clear()


@pytest.fixture
def mock_db():
    with patch("smartmailer.session_management.db_operator.Database") as mock_db_class:
        mock_db_instance = MagicMock()
        mock_db_class.return_value = mock_db_instance
        yield mock_db_instance


@pytest.fixture
def operator(mock_db):
    return DBOperator(":memory:")


# Singleton Behaviour

def test_same_instance_returned_for_same_path(mock_db):
    op1 = DBOperator(":memory:")
    op2 = DBOperator(":memory:")
    assert op1 is op2


def test_different_paths_get_separate_instances(mock_db):
    op1 = DBOperator("/tmp/session_a.db")
    op2 = DBOperator("/tmp/session_b.db")
    assert op1 is not op2
    assert op1.dbfile_path == "/tmp/session_a.db"
    assert op2.dbfile_path == "/tmp/session_b.db"


def test_different_paths_open_their_own_database():
    with patch("smartmailer.session_management.db_operator.Database") as db_cls:
        DBOperator("/tmp/session_a.db")
        DBOperator("/tmp/session_b.db")
        opened = [c.args[0] for c in db_cls.call_args_list]
    assert opened == ["/tmp/session_a.db", "/tmp/session_b.db"]


def test_shutdown_clears_instance(mock_db):
    op = DBOperator(":memory:")
    op.shutdown()
    assert DBOperator._instances == {}


def test_shutdown_only_removes_its_own_path(mock_db):
    op1 = DBOperator("/tmp/session_a.db")
    op2 = DBOperator("/tmp/session_b.db")
    op1.shutdown()
    assert DBOperator._instances == {"/tmp/session_b.db": op2}


def test_new_instance_after_shutdown(mock_db):
    op1 = DBOperator(":memory:")
    op1.shutdown()
    op2 = DBOperator(":memory:")
    assert op1 is not op2


# Buffering

def test_buffer_accumulates_multiple_entries(operator):
    for h in ["h1", "h2", "h3"]:
        operator.add_to_db(h)
    with operator._buffer_lock:
        assert operator._buffer == ["h1", "h2", "h3"]


def test_add_to_db_does_not_hit_database_immediately(operator, mock_db):
    operator.add_to_db("lazy_hash")
    mock_db.batch_insert_recipients.assert_not_called()


# check_recipient_sent

def test_found_in_buffer_returns_true_without_db(operator, mock_db):
    operator.add_to_db("buffered_hash")
    assert operator.check_recipient_sent("buffered_hash") is True
    mock_db.check_recipient_sent.assert_not_called()


def test_not_in_buffer_falls_through_to_db(operator, mock_db):
    mock_db.check_recipient_sent.return_value = True
    assert operator.check_recipient_sent("db_hash") is True
    mock_db.check_recipient_sent.assert_called_once_with("db_hash")


# Flush Behaviour

def test_flush_drains_buffer_to_db(operator, mock_db):
    operator.add_to_db("flush_me")
    operator._flush()
    mock_db.batch_insert_recipients.assert_called_once_with(["flush_me"])
    with operator._buffer_lock:
        assert operator._buffer == []


def test_flush_on_empty_buffer_is_a_noop(operator, mock_db):
    operator._flush()
    mock_db.batch_insert_recipients.assert_not_called()


def test_shutdown_performs_final_flush(operator, mock_db):
    operator.add_to_db("final_hash")
    operator.shutdown()
    all_calls = [args[0] for args, _ in mock_db.batch_insert_recipients.call_args_list]
    assert any("final_hash" in batch for batch in all_calls)


def test_flush_loop_flushes_periodically(mock_db):
    op = DBOperator(":memory:")
    op.add_to_db("periodic_hash")
    deadline = time.monotonic() + 2.0
    flushed = False
    while time.monotonic() < deadline:
        if mock_db.batch_insert_recipients.called:
            flushed = True
            break
        time.sleep(0.05)
    assert flushed, "Background flush loop did not fire within 2 s"


# Error Recovery

def test_failed_flush_requeues_batch(operator, mock_db):
    mock_db.batch_insert_recipients.side_effect = RuntimeError("DB down")
    operator.add_to_db("retry_me")
    operator._flush()
    with operator._buffer_lock:
        assert "retry_me" in operator._buffer


def test_failed_batch_prepended_to_preserve_order(operator, mock_db):
    operator.add_to_db("first")
    operator.add_to_db("second")

    def add_during_flush(batch):
        operator.add_to_db("arrived_during_flush")
        raise RuntimeError("DB down")

    mock_db.batch_insert_recipients.side_effect = add_during_flush
    operator._flush()

    with operator._buffer_lock:
        assert operator._buffer == ["first", "second", "arrived_during_flush"]


# Delegation

def test_get_sent_recipients_delegates(operator, mock_db):
    mock_db.get_sent_recipients.return_value = [{"recipient_hash": "x"}]
    result = operator.get_sent_recipients()
    mock_db.get_sent_recipients.assert_called_once()
    assert result == [{"recipient_hash": "x"}]


def test_delete_recipient_delegates(operator, mock_db):
    operator.delete_recipient("del_hash")
    mock_db.delete_recipient.assert_called_once_with("del_hash")


def test_clear_database_clears_buffer_and_db(operator, mock_db):
    operator.add_to_db("buffered")
    operator.clear_database()
    with operator._buffer_lock:
        assert operator._buffer == []
    mock_db.clear_database.assert_called_once()


# Context Manager

def test_context_manager_calls_shutdown(mock_db):
    with DBOperator(":memory:") as op:
        op.add_to_db("ctx_hash")
    assert DBOperator._instances == {}
    mock_db.close.assert_called()
