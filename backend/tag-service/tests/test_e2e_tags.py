import pytest
import requests

pytestmark = pytest.mark.e2e


def _get_hierarchy(base_url: str):
    """
    Read-only: fetch hierarchy without altering DB.
    Compatible with either /tags or /tags/hierarchy.
    """
    r = requests.get(f"{base_url}/tags", timeout=5)
    if r.status_code == 404:
        r = requests.get(f"{base_url}/tags/hierarchy", timeout=5)
    r.raise_for_status()
    return r.json()


def test_service_reachable_or_skip(live_service_available):
    if not live_service_available:
        pytest.skip("tag-service not reachable at http://localhost:5007")


def test_readonly_hierarchy_shape(base_url, live_service_available):
    """
    Simple, stable, non-mutating E2E test:
    - fetch hierarchy
    - validate the nested shape:
        { Primary: { Secondary: [Tertiary, ...] } }
    """
    if not live_service_available:
        pytest.skip("tag-service not reachable")

    data = _get_hierarchy(base_url)

    # Expected container types
    assert isinstance(data, dict), "Hierarchy root should be an object/dict"

    for primary, secondaries in data.items():
        assert isinstance(primary, str), "Primary keys must be strings"
        assert isinstance(secondaries, dict), "Each primary value must be a dict (of secondaries)"

        for secondary, tertiaries in secondaries.items():
            assert isinstance(secondary, str), "Secondary keys must be strings"
            assert isinstance(tertiaries, list), "Each secondary value must be a list (of tertiaries)"

            for t in tertiaries:
                assert isinstance(t, str), "Tertiary entries must be strings"
