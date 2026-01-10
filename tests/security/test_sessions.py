def test_login_success(client, admin_user):
    res = client.post("/login", data=admin_user, follow_redirects=True)
    assert res.status_code == 200
