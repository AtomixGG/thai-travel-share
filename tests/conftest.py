import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from thaitravelshare.main import app
from thaitravelshare.core.database import get_session
from thaitravelshare import models


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    future=True,
)

test_session = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture
async def async_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async with test_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(async_session):
    
    async def get_test_session():
        yield async_session
    
    app.dependency_overrides[get_session] = get_test_session
    
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(async_session):
    from thaitravelshare.core.security import get_password_hash
    import uuid
    
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "email": f"test{unique_id}@example.com",
        "username": f"testuser{unique_id}",
        "hashed_password": get_password_hash("testpassword"),
        "first_name": "Test",
        "last_name": "User"
    }
    
    db_user = models.DBUser(**user_data)
    async_session.add(db_user)
    await async_session.commit()
    await async_session.refresh(db_user)
    
    return db_user


@pytest_asyncio.fixture
async def authenticated_client(client, test_user):
    login_data = {
        "username": test_user.username,
        "password": "testpassword"
    }
    
    response = await client.post("/v1/users/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    token = token_data["access_token"]
    
    client.headers["Authorization"] = f"Bearer {token}"
    
    return client


@pytest_asyncio.fixture
async def test_provinces(async_session):
    from decimal import Decimal
    
    from sqlmodel import select
    from thaitravelshare import models
    
    result = await async_session.exec(select(models.DBProvince).where(models.DBProvince.id == 1001))
    existing = result.first()
    
    if existing:
        result = await async_session.exec(select(models.DBProvince).where(models.DBProvince.id.in_([1001, 1002])))
        provinces = result.all()
        return [
            {
                "id": p.id,
                "name_th": p.name_th,
                "name_en": p.name_en,
                "region": p.region,
                "is_secondary_province": p.is_secondary_province,
                "tax_reduction_percentage": p.tax_reduction_percentage,
                "description": p.description
            } for p in provinces
        ]
    
    provinces_data = [
        {
            "id": 1001,
            "name_th": "แม่ฮ่องสอน",
            "name_en": "Mae Hong Son",
            "region": "North",
            "is_secondary_province": True,
            "tax_reduction_percentage": Decimal("15.00"),
            "description": "จังหวัดชายแดนภาคเหนือ"
        },
        {
            "id": 1002,
            "name_th": "กรุงเทพมหานคร",
            "name_en": "Bangkok",
            "region": "Central",
            "is_secondary_province": False,
            "tax_reduction_percentage": Decimal("0.00"),
            "description": "เมืองหลวง"
        }
    ]
    
    for province_data in provinces_data:
        province = models.DBProvince(**province_data)
        async_session.add(province)
    
    await async_session.commit()
    
    return provinces_data
