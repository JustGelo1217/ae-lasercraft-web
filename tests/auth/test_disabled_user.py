import pytest

@pytest.mark.xfail(reason="Disabled accounts not implemented yet")
def test_disabled_user_cannot_login(client, disabled_user):
    res = client.post("/login", data=disabled_user, follow_redirects=True)
    assert False
