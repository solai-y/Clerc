import pytest

pytestmark = pytest.mark.integration


def _get_hierarchy(client):
    r = client.get("/tags")
    if r.status_code == 404:
        r = client.get("/tags/hierarchy")
    assert r.status_code == 200, r.text
    return r.json()


def test_importable_or_skip(client):
    # If the client fixture loads, the import worked. Otherwise conftest skips.
    assert client is not None


def test_readonly_hierarchy_shape_inprocess(client):
    """
    In-process (TestClient) read-only test that validates the same shape as E2E.
    """
    data = _get_hierarchy(client)

    assert isinstance(data, dict), "Hierarchy root should be an object/dict"

    for primary, secondaries in data.items():
        assert isinstance(primary, str)
        assert isinstance(secondaries, dict)

        for secondary, tertiaries in secondaries.items():
            assert isinstance(secondary, str)
            assert isinstance(tertiaries, list)

            for t in tertiaries:
                assert isinstance(t, str)
