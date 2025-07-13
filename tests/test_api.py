import pytest
from decimal import Decimal


class TestUserAuthentication:

    @pytest.mark.asyncio
    async def test_user_registration(self, client, test_provinces):
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User",
            "phone": "0812345678"
        }
        
        response = await client.post("/v1/users/register", json=user_data)
        assert response.status_code == 200
        
        response_data = response.json()
        user = response_data["user"]
        assert user["email"] == user_data["email"]
        assert user["username"] == user_data["username"]
        assert "id" in user
        assert "hashed_password" not in user  # Should not expose password
        assert response_data["message"] == "User registered successfully"

    @pytest.mark.asyncio
    async def test_user_login(self, client, test_user, test_provinces):
        """Test user login."""
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = await client.post("/v1/users/login", json=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, test_user, test_provinces):
        """Test login with invalid credentials."""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = await client.post("/v1/users/login", json=login_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, authenticated_client, test_user, test_provinces):
        """Test getting current user information."""
        response = await authenticated_client.get("/v1/users/me")
        assert response.status_code == 200
        
        user = response.json()
        assert user["username"] == test_user.username
        assert user["email"] == test_user.email  

    @pytest.mark.asyncio
    async def test_update_user_profile(self, authenticated_client, test_user, test_provinces):
        """Test updating user profile."""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "0987654321"
        }
        
        response = await authenticated_client.put(f"/v1/users/{test_user.id}/update", json=update_data)
        assert response.status_code == 200
        
        user = response.json()
        assert user["first_name"] == "Updated"
        assert user["last_name"] == "Name"
        assert user["phone"] == "0987654321"

    @pytest.mark.asyncio
    async def test_change_password(self, authenticated_client, test_user, test_provinces):
        """Test changing password."""
        password_data = {
            "old_password": "testpassword",
            "new_password": "newtestpassword123"
        }
        
        response = await authenticated_client.put(f"/v1/users/{test_user.id}/change_password", json=password_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert result["message"] == "Password updated successfully"


class TestProvinces:
    """Test province-related endpoints."""

    @pytest.mark.asyncio
    async def test_get_all_provinces(self, client, test_provinces):
        """Test getting all provinces."""
        response = await client.get("/v1/provinces/")
        assert response.status_code == 200
        
        data = response.json()
        provinces = data["provinces"]
        assert len(provinces) == 2
        assert provinces[0]["name_th"] in ["แม่ฮ่องสอน", "กรุงเทพมหานคร"]

    @pytest.mark.asyncio
    async def test_get_secondary_provinces(self, client, test_provinces):
        """Test getting secondary provinces only."""
        response = await client.get("/v1/provinces/secondary")
        assert response.status_code == 200
        
        data = response.json()
        provinces = data["provinces"]
        assert len(provinces) == 1
        assert provinces[0]["name_th"] == "แม่ฮ่องสอน"
        assert provinces[0]["is_secondary_province"] is True

    @pytest.mark.asyncio
    async def test_get_province_by_id(self, client, test_provinces):
        """Test getting specific province."""
        response = await client.get("/v1/provinces/1001")
        assert response.status_code == 200
        
        province = response.json()
        assert province["name_th"] == "แม่ฮ่องสอน"
        assert float(province["tax_reduction_percentage"]) == 15.0

    @pytest.mark.asyncio
    async def test_get_province_tax_benefits(self, client, test_provinces):
        """Test calculating tax benefits for a province."""
        budget = 10000.0
        response = await client.get(f"/v1/provinces/1001/tax-benefits?budget={budget}")
        assert response.status_code == 200
        
        benefits = response.json()
        assert benefits["budget"] == budget
        assert benefits["estimated_tax_reduction"] == 1500.0  # 15% of 10000
        assert benefits["tax_reduction_rate"] == 0.15
        assert "comparison_with_other_provinces" in benefits


class TestTravelPlans:
    """Test travel plan endpoints."""

    @pytest.mark.asyncio
    async def test_create_travel_plan(self, authenticated_client, test_provinces, test_user):
        """Test creating a travel plan."""
        travel_plan_data = {
            "province_id": 1001,
            "start_date": "2025-08-01T00:00:00",
            "end_date": "2025-08-07T00:00:00",
            "budget": 15000.0,
            "notes": "Summer vacation in Mae Hong Son"
        }
        
        response = await authenticated_client.post("/v1/travel-plans/", json=travel_plan_data)
        assert response.status_code == 200
        
        data = response.json()
        travel_plan = data["travel_plan"]
        assert travel_plan["province_id"] == 1001
        assert float(travel_plan["budget"]) == 15000.0
        assert float(travel_plan["estimated_tax_reduction"]) == 2250.0  # 15% of 15000
        assert travel_plan["status"] == "planned"

    @pytest.mark.asyncio
    async def test_get_user_travel_plans(self, authenticated_client, test_provinces, test_user):
        """Test getting user's travel plans."""
        # First create a travel plan
        travel_plan_data = {
            "province_id": 1001,
            "start_date": "2025-08-01T00:00:00",
            "end_date": "2025-08-07T00:00:00",
            "budget": 10000.0
        }
        
        create_response = await authenticated_client.post("/v1/travel-plans/", json=travel_plan_data)
        assert create_response.status_code == 200
        
        # Then get all plans
        response = await authenticated_client.get("/v1/travel-plans/")
        assert response.status_code == 200
        
        data = response.json()
        travel_plans = data["travel_plans"]
        assert len(travel_plans) >= 1
        assert travel_plans[0]["province"]["name_th"] == "แม่ฮ่องสอน"

    @pytest.mark.asyncio
    async def test_update_travel_plan(self, authenticated_client, test_provinces, test_user):
        """Test updating a travel plan."""
        # Create a travel plan first
        travel_plan_data = {
            "province_id": 1001,
            "start_date": "2025-08-01T00:00:00",
            "end_date": "2025-08-07T00:00:00",
            "budget": 10000.0
        }
        
        create_response = await authenticated_client.post("/v1/travel-plans/", json=travel_plan_data)
        data = create_response.json()
        travel_plan = data["travel_plan"]
        plan_id = travel_plan["id"]
        
        # Update the plan
        update_data = {
            "budget": 20000.0,
            "status": "confirmed",
            "notes": "Updated budget and confirmed trip"
        }
        
        response = await authenticated_client.put(f"/v1/travel-plans/{plan_id}", json=update_data)
        assert response.status_code == 200
        
        updated_plan = response.json()  # Update endpoint returns TravelPlan directly
        assert float(updated_plan["budget"]) == 20000.0
        assert updated_plan["status"] == "confirmed"
        assert float(updated_plan["estimated_tax_reduction"]) == 3000.0  # 15% of 20000

    @pytest.mark.asyncio
    async def test_get_travel_plan_tax_info(self, authenticated_client, test_provinces, test_user):
        """Test getting detailed tax information for a travel plan."""
        # Create a completed travel plan
        travel_plan_data = {
            "province_id": 1001,
            "start_date": "2025-07-01T00:00:00",
            "end_date": "2025-07-07T00:00:00",
            "budget": 12000.0
        }
        
        create_response = await authenticated_client.post("/v1/travel-plans/", json=travel_plan_data)
        data = create_response.json()
        travel_plan = data["travel_plan"]
        plan_id = travel_plan["id"]
        
        # Update status to completed
        await authenticated_client.put(f"/v1/travel-plans/{plan_id}", json={"status": "completed"})
        
        # Get tax info
        response = await authenticated_client.get(f"/v1/travel-plans/{plan_id}/tax-info")
        assert response.status_code == 200
        
        tax_info = response.json()
        assert float(tax_info["estimated_tax_reduction"]) == 1800.0  # 15% of 12000
        assert float(tax_info["actual_tax_savings"]) == 1800.0  # Same for completed trip


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_duplicate_email_registration(self, client, test_user, test_provinces):
        """Test registration with duplicate email."""
        user_data = {
            "email": test_user.email,  # Use the actual test user's email
            "username": "differentusername",
            "password": "password123",
            "first_name": "Different",
            "last_name": "User"
        }
        
        response = await client.post("/v1/users/register", json=user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_province_travel_plan(self, authenticated_client, test_provinces):
        """Test creating travel plan with invalid province."""
        travel_plan_data = {
            "province_id": 999,  # Non-existent province
            "start_date": "2025-08-01T00:00:00",
            "end_date": "2025-08-07T00:00:00",
            "budget": 10000.0
        }
        
        response = await authenticated_client.post("/v1/travel-plans/", json=travel_plan_data)
        assert response.status_code == 404
        assert "Province not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client, test_provinces):
        """Test accessing protected endpoints without authentication."""
        response = await client.get("/v1/users/me")
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 for missing auth

    @pytest.mark.asyncio
    async def test_access_other_user_travel_plan(self, authenticated_client, test_provinces):
        response = await authenticated_client.get("/v1/travel-plans/non-existent-id")
        assert response.status_code == 404
