from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from .config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.SQLDB_URL,
    echo=True,
    future=True,
)

# Create async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    """Initialize database tables."""
    from ..models.user_model import DBUser
    from ..models.travel_model import DBProvince, DBTravelPlan
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Initialize provinces data if not exists
    await init_provinces_data()


async def close_db():
    """Close database connection."""
    await engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_provinces_data():
    """Initialize provinces data."""
    from ..models.travel_model import DBProvince
    from sqlmodel import select
    from decimal import Decimal
    
    async with async_session() as session:
        # Check if provinces already exist
        result = await session.exec(select(DBProvince))
        existing_provinces = result.all()
        
        if not existing_provinces:
            # Sample Thai provinces data with tax reduction info
            provinces_data = [
                # Secondary provinces (higher tax reduction)
                {"id": 1, "name_th": "แม่ฮ่องสอน", "name_en": "Mae Hong Son", "region": "North", "is_secondary_province": True, "tax_reduction_percentage": Decimal("15.00"), "description": "จังหวัดชายแดนภาคเหนือ"},
                {"id": 2, "name_th": "ตาก", "name_en": "Tak", "region": "North", "is_secondary_province": True, "tax_reduction_percentage": Decimal("12.00"), "description": "จังหวัดชายแดนภาคเหนือ"},
                {"id": 3, "name_th": "กาญจนบุรี", "name_en": "Kanchanaburi", "region": "West", "is_secondary_province": True, "tax_reduction_percentage": Decimal("10.00"), "description": "จังหวัดภาคตะวันตก"},
                {"id": 4, "name_th": "เพชรบุรี", "name_en": "Phetchaburi", "region": "Central", "is_secondary_province": True, "tax_reduction_percentage": Decimal("8.00"), "description": "จังหวัดภาคกลาง"},
                {"id": 5, "name_th": "ประจุมบคีรีขันธ์", "name_en": "Prachuap Khiri Khan", "region": "Central", "is_secondary_province": True, "tax_reduction_percentage": Decimal("10.00"), "description": "จังหวัดภาคกลางตอนล่าง"},
                
                # Primary provinces (lower tax reduction)
                {"id": 6, "name_th": "เชียงใหม่", "name_en": "Chiang Mai", "region": "North", "is_secondary_province": False, "tax_reduction_percentage": Decimal("5.00"), "description": "จังหวัดใหญ่ภาคเหนือ"},
                {"id": 7, "name_th": "กรุงเทพมหานคร", "name_en": "Bangkok", "region": "Central", "is_secondary_province": False, "tax_reduction_percentage": Decimal("0.00"), "description": "เมืองหลวง"},
                {"id": 8, "name_th": "ภูเก็ต", "name_en": "Phuket", "region": "South", "is_secondary_province": False, "tax_reduction_percentage": Decimal("3.00"), "description": "จังหวัดท่องเที่ยวภาคใต้"},
                {"id": 9, "name_th": "ขอนแก่น", "name_en": "Khon Kaen", "region": "Northeast", "is_secondary_province": False, "tax_reduction_percentage": Decimal("6.00"), "description": "จังหวัดใหญ่ภาคอีสาน"},
                {"id": 10, "name_th": "อุดรธานี", "name_en": "Udon Thani", "region": "Northeast", "is_secondary_province": True, "tax_reduction_percentage": Decimal("8.00"), "description": "จังหวัดชายแดนภาคอีสาน"},
            ]
            
            for province_data in provinces_data:
                province = DBProvince(**province_data)
                session.add(province)
            
            await session.commit()
