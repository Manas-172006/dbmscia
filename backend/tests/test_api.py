import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["database"]["engine"] == "MySQL 8 (InnoDB)"
    assert data["database"]["status"] == "healthy"


def test_categories_and_locations():
    cat_resp = client.get("/api/categories")
    assert cat_resp.status_code == 200
    categories = cat_resp.json()
    assert len(categories) == 10
    assert any(c["slug"] == "electronics" for c in categories)

    loc_resp = client.get("/api/locations")
    assert loc_resp.status_code == 200
    locations = loc_resp.json()
    assert len(locations) >= 15


def test_public_search_and_filter():
    # Test public search
    resp = client.get("/api/items?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) <= 10
    assert all(item["status"] == "available" for item in data["items"])

    # Test filter by category
    cat_resp = client.get("/api/categories")
    first_cat = cat_resp.json()[0]
    cat_filter_resp = client.get(f"/api/items?category_id={first_cat['id']}&page=1")
    assert cat_filter_resp.status_code == 200
    cat_data = cat_filter_resp.json()
    assert all(item["category"]["id"] == first_cat["id"] for item in cat_data["items"])


def test_user_registration_and_login():
    import uuid
    random_str = uuid.uuid4().hex[:6]
    test_email = f"testuser_{random_str}@campus.university.edu"
    test_pwd = "SecretPassword123!"

    # 1. Register
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "full_name": f"Test Student {random_str}",
            "email": test_email,
            "password": test_pwd,
            "department": "Computer Science",
            "phone": "+91 9999988888",
        },
    )
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == test_email
    assert reg_data["user"]["role"] == "user"

    # 2. Duplicate registration rejected
    dup_resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Duplicate User",
            "email": test_email,
            "password": test_pwd,
        },
    )
    assert dup_resp.status_code == 400

    # 3. Login
    login_resp = client.post(
        "/api/auth/login",
        json={"email": test_email, "password": test_pwd},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 4. Profile /me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == test_email


def test_admin_login_and_explorer():
    # Login with configured admin credentials
    admin_resp = client.post(
        "/api/auth/login",
        json={
            "email": settings.ADMIN_EMAIL,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    assert admin_resp.status_code == 200
    admin_token = admin_resp.json()["access_token"]
    assert admin_resp.json()["user"]["role"] == "admin"
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Test admin database overview
    overview_resp = client.get("/api/admin/database/overview", headers=headers)
    assert overview_resp.status_code == 200
    overview = overview_resp.json()
    assert overview["total_users"] >= 100
    assert overview["total_items"] >= 180
    assert overview["available_items"] > 0

    # Test admin tables inspection
    tables_resp = client.get("/api/admin/database/tables", headers=headers)
    assert tables_resp.status_code == 200
    tables = tables_resp.json()
    table_names = [t["name"] for t in tables]
    assert "found_items" in table_names
    assert "users" in table_names

    # Test admin table rows viewer
    rows_resp = client.get("/api/admin/database/tables/users/rows?page=1&page_size=5", headers=headers)
    assert rows_resp.status_code == 200
    users_page = rows_resp.json()
    assert len(users_page["rows"]) <= 5
    # Ensure password_hash is strictly redacted
    assert "password_hash" not in users_page["columns"]
    for row in users_page["rows"]:
        assert "password_hash" not in row

    # Test predefined SQL queries list
    queries_resp = client.get("/api/admin/sql/queries", headers=headers)
    assert queries_resp.status_code == 200
    queries = queries_resp.json()
    assert len(queries) >= 18

    invalid_limit_resp = client.post(
        "/api/admin/sql/queries/query_05_recent_reports/run",
        headers=headers,
        json={"params": {"limit": 101}},
    )
    assert invalid_limit_resp.status_code == 422

    unknown_parameter_resp = client.post(
        "/api/admin/sql/queries/query_01_total_reports/run",
        headers=headers,
        json={"params": {"unlisted": 1}},
    )
    assert unknown_parameter_resp.status_code == 422

    arbitrary_sql_resp = client.post(
        "/api/admin/sql/queries/query_01_total_reports/run",
        headers=headers,
        json={"sql": "SELECT 1"},
    )
    assert arbitrary_sql_resp.status_code == 422

    # Test running a predefined SQL query (Category Distribution)
    run_resp = client.post(
        "/api/admin/sql/queries/query_03_category_distribution/run",
        headers=headers,
    )
    if settings.SQL_EXPLORER_DATABASE_URL:
        assert run_resp.status_code == 200
        result = run_resp.json()
        assert result["query_id"] == "query_03_category_distribution"
        assert result["row_count"] == 10
        assert len(result["rows"]) == 10
        assert "category_name" in result["columns"]
    else:
        assert run_resp.status_code == 503


def test_non_admin_blocked_from_admin_api():
    # Register a normal user
    import uuid
    rand_id = uuid.uuid4().hex[:6]
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Normal Student",
            "email": f"student_{rand_id}@campus.edu",
            "password": "Password123!",
        },
    )
    normal_token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {normal_token}"}

    # Attempt to open admin database overview
    overview_resp = client.get("/api/admin/database/overview", headers=headers)
    assert overview_resp.status_code == 403

    # Attempt to run admin SQL query
    run_resp = client.post(
        "/api/admin/sql/queries/query_01_total_reports/run",
        headers=headers,
    )
    assert run_resp.status_code == 403


def test_create_and_manage_item():
    import uuid
    rand_id = uuid.uuid4().hex[:6]
    categories = client.get("/api/categories").json()
    original_category = next(category for category in categories if category["id"] == 1)
    other_category = next(category for category in categories if category["id"] != 1)
    original_subcategory = original_category["subcategories"][0]
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "full_name": f"Reporter {rand_id}",
            "email": f"reporter_{rand_id}@campus.edu",
            "password": "Password123!",
        },
    )
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create dummy PNG image bytes
    from PIL import Image
    img = Image.new("RGB", (100, 100), color="blue")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    # Post new item
    create_resp = client.post(
        "/api/items",
        data={
            "title": f"Lost Blue Calculator {rand_id}",
            "description": "Found on the table in Computer Lab 3 with blue protective case.",
            "category_id": 1,
            "subcategory_id": original_subcategory["id"],
            "location_id": 3,
            "found_at": "2026-11-14T10:30",
            "quantity": 1,
            "condition": "Excellent",
        },
        files={"image": ("test_calculator.png", img_bytes, "image/png")},
        headers=headers,
    )
    assert create_resp.status_code == 201
    item = create_resp.json()
    assert item["reference_code"].startswith("FI-")
    assert item["status"] == "available"
    assert len(item["images"]) == 1

    invalid_subcategory = client.patch(
        f"/api/items/{item['id']}",
        json={
            "category_id": other_category["id"],
            "subcategory_id": original_subcategory["id"],
        },
        headers=headers,
    )
    assert invalid_subcategory.status_code == 400
    category_update = client.patch(
        f"/api/items/{item['id']}",
        json={"category_id": other_category["id"]},
        headers=headers,
    )
    assert category_update.status_code == 200
    assert category_update.json()["subcategory"] is None

    # Verify item appears in public search
    search_resp = client.get(f"/api/items?q={item['reference_code']}")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total"] >= 1
    assert any(it["reference_code"] == item["reference_code"] for it in search_data["items"])

    # Update item status to returned
    status_resp = client.patch(
        f"/api/items/{item['id']}/status",
        json={"status": "returned", "note": "Claimed in person by student owner."},
        headers=headers,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "returned"

    # Verify resolved item no longer appears in public search
    search_after = client.get(f"/api/items?q={item['reference_code']}")
    assert search_after.status_code == 200
    assert search_after.json()["total"] == 0

    public_detail = client.get(f"/api/items/{item['reference_code']}")
    assert public_detail.status_code == 404
    owner_detail = client.get(
        f"/api/items/{item['reference_code']}",
        headers=headers,
    )
    assert owner_detail.status_code == 200
    assert owner_detail.json()["status"] == "returned"


def test_contact_request_enquiries_and_notifications():
    import uuid
    from PIL import Image

    def register_test_user(label):
        suffix = uuid.uuid4().hex[:8]
        response = client.post(
            "/api/auth/register",
            json={
                "full_name": f"{label} {suffix}",
                "email": f"{label.lower()}_{suffix}@campus.edu",
                "password": "ContactFlow123!",
            },
        )
        assert response.status_code == 201
        token = response.json()["access_token"]
        return response.json()["user"], {"Authorization": f"Bearer {token}"}

    reporter, reporter_headers = register_test_user("Reporter")
    _, sender_headers = register_test_user("Claimant")

    image = Image.new("RGB", (100, 100), color="green")
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    item_response = client.post(
        "/api/items",
        data={
            "title": "Contact workflow test item",
            "description": "A test item for the private contact workflow.",
            "category_id": 1,
            "location_id": 3,
            "found_at": "2026-11-14T10:30",
        },
        files={"image": ("contact-test.png", image_bytes.getvalue(), "image/png")},
        headers=reporter_headers,
    )
    assert item_response.status_code == 201
    item = item_response.json()

    contact_response = client.post(
        f"/api/items/{item['id']}/contact",
        json={"message": "I can identify a mark on the back of this item."},
        headers=sender_headers,
    )
    assert contact_response.status_code == 201
    contact_data = contact_response.json()
    assert contact_data["status"] == "new"
    assert "email" not in contact_data["recipient"]
    assert "phone" not in contact_data["recipient"]

    sent_response = client.get("/api/me/contact-requests/sent", headers=sender_headers)
    received_response = client.get("/api/me/contact-requests/received", headers=reporter_headers)
    assert sent_response.status_code == 200
    assert received_response.status_code == 200
    assert sent_response.json()[0]["id"] == contact_data["id"]
    assert received_response.json()[0]["id"] == contact_data["id"]

    denied_update = client.patch(
        f"/api/contact-requests/{contact_data['id']}/status",
        json={"status": "read"},
        headers=sender_headers,
    )
    assert denied_update.status_code == 403
    owner_update = client.patch(
        f"/api/contact-requests/{contact_data['id']}/status",
        json={"status": "read"},
        headers=reporter_headers,
    )
    assert owner_update.status_code == 200
    assert owner_update.json()["status"] == "read"

    notifications = client.get("/api/me/notifications", headers=reporter_headers)
    assert notifications.status_code == 200
    assert any(n["related_contact_request_id"] == contact_data["id"] for n in notifications.json())
