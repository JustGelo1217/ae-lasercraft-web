def test_negative_stock_not_allowed(login_admin):
    res = login_admin.post("/inventory/add", json={
        "name": "Bad Item",
        "price": 10,
        "stock": -5,
        "category": "wood"
    })

    assert res.status_code == 400
    assert b"invalid" in res.data.lower()
