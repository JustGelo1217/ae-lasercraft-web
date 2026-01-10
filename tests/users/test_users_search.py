def test_users_search_returns_result(login_admin):
    res = login_admin.get("/api/users?search=admin")
    assert res.status_code == 200

    data = res.get_json()
    assert data is not None
    assert data["total"] >= 1


def test_users_search_no_result(login_admin):
    res = login_admin.get("/api/users?search=nonexistent123")
    assert res.status_code == 200

    data = res.get_json()
    assert data["total"] == 0


def test_users_pagination(login_admin):
    res = login_admin.get("/api/users?page=1")
    assert res.status_code == 200
