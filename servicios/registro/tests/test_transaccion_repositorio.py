"""Transaction boundary tests: a partial write must never be committed."""
from unittest.mock import Mock

import pytest

from app.repositorio.hallazgos import RepositorioHallazgos


@pytest.mark.parametrize("failure_at", range(5))
def test_each_failed_write_rolls_back_without_commit(datos, failure_at):
    session = Mock()
    failure = RuntimeError("injected write failure")
    session.execute.side_effect = [None] * failure_at + [failure]

    with pytest.raises(RuntimeError, match="injected write failure"):
        RepositorioHallazgos(session).registrar(datos, "Test species", {"temperaturaAgua": 18.5})

    assert session.execute.call_count == failure_at + 1
    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()


def test_commit_failure_rolls_back_and_propagates(datos):
    session = Mock()
    session.commit.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        RepositorioHallazgos(session).registrar(datos, "Test species", {})

    assert session.execute.call_count == 5
    session.rollback.assert_called_once_with()


def test_success_commits_once_without_rollback(datos):
    session = Mock()
    identifier = RepositorioHallazgos(session).registrar(datos, "Test species", {})

    assert identifier is not None
    assert session.execute.call_count == 5
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
