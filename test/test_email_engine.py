import pytest
import email
import email.message
from src import email_engine


@pytest.fixture
def connections():
    conn = email_engine.IMAP_SSL()
    conn.init_mail('imap.gmail.com', 993,
                   'arnal.romain@gmail.com', 'jnihuxwnhnjshyuw',
                   max_conns=10)
    return conn


def test_connections(connections):
    assert len(connections.conns) == 10
    assert all(x.state == "SELECTED" for x in connections.conns)


def test_search_by_sender(connections):
    res = connections.search_by_sender('arnal.romain@gmail.com')
    assert res
    assert len(res) > 5
    assert isinstance(res[0], email.message.Message)



