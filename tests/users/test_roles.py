def test_admin_can_access_users_page(login_admin):
    res = login_admin.get("/users")
    assert res.status_code == 200


def test_normal_user_cannot_access_users_page(login_user):
    res = login_user.get("/users")
    assert res.status_code == 403
