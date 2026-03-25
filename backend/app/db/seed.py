import asyncio
import bcrypt
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.models import ApprovedTicker, User

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://fintech_app:localpassword123@db:5432/fintech_bmv",
)

CORE_BMV_TICKERS = [
    {
        "symbol": "AC.MX",
        "display_name_es": "Arca Continental",
        "display_name_en": "Arca Continental",
        "category": "mx_equity",
        "is_default_visible": True,
        "description_es": (
            "Segundo embotellador mas grande de Coca-Cola en Latinoamerica. "
            "Ingresos de refrescos y botanas en Mexico, Ecuador y el suroeste de EE.UU."
        ),
        "description_en": (
            "Second-largest Coca-Cola bottler in Latin America. "
            "Revenue from soft drinks and snacks across Mexico, Ecuador, and the US Southwest."
        ),
        "fetch_status": "ready",
    },
    {
        "symbol": "AMX",
        "display_name_es": "America Movil",
        "display_name_en": "America Movil",
        "category": "mx_equity",
        "is_default_visible": True,
        "description_es": (
            "Operadora de telefonia movil dominante bajo las marcas Telcel y Claro "
            "en 18 paises de Latinoamerica."
        ),
        "description_en": (
            "Dominant mobile carrier under Telcel and Claro brands "
            "across 18 countries in Latin America."
        ),
        "fetch_status": "ready",
    },
    {
        "symbol": "ASURB.MX",
        "display_name_es": "Grupo Aeroportuario del Sureste",
        "display_name_en": "Grupo Aeroportuario del Sureste",
        "category": "mx_equity",
        "is_default_visible": True,
        "description_es": (
            "Concesionaria de nueve aeropuertos incluyendo Cancun Internacional. "
            "Ingresos de tarifas TUA y arrendamiento comercial."
        ),
        "description_en": (
            "Concession holder for nine airports including Cancun International. "
            "Revenue from TUA passenger fees and commercial leasing."
        ),
        "fetch_status": "ready",
    },
    {
        "symbol": "CEMEXCPO.MX",
        "display_name_es": "Cemex",
        "display_name_en": "Cemex",
        "category": "mx_equity",
        "is_default_visible": True,
        "description_es": (
            "Uno de los mayores productores de cemento del mundo con operaciones "
            "en mas de 50 paises."
        ),
        "description_en": (
            "One of the world's largest cement producers with operations "
            "in over 50 countries."
        ),
        "fetch_status": "ready",
    },
    {
        "symbol": "FEMSAUBD.MX",
        "display_name_es": "FEMSA",
        "display_name_en": "FEMSA",
        "category": "mx_equity",
        "is_default_visible": True,
        "description_es": (
            "Opera la cadena OXXO, farmacias y tiene participacion estrategica "
            "en Heineken. Ingresos diversificados en retail, combustible y salud."
        ),
        "description_en": (
            "Operates the OXXO convenience chain, pharmacies, and holds "
            "a strategic stake in Heineken. Revenue diversified across retail, fuel, and health."
        ),
        "fetch_status": "ready",
    },
    {
        "symbol": "GAPB.MX",
        "display_name_es": "Grupo Aeroportuario del Pacifico",
        "display_name_en": "Grupo Aeroportuario del Pacifico",
        "category": "mx_equity",
        "is_default_visible": True,
        "description_es": (
            "Concesionaria de aeropuertos en el corredor Pacifico de Mexico "
            "incluyendo Guadalajara, Tijuana y Los Cabos."
        ),
        "description_en": (
            "Concession holder for airports in Mexico's Pacific corridor "
            "including Guadalajara, Tijuana, and Los Cabos."
        ),
        "fetch_status": "ready",
    },
    {
        "symbol": "GFNORTEO.MX",
        "display_name_es": "Grupo Financiero Banorte",
        "display_name_en": "Grupo Financiero Banorte",
        "category": "mx_equity",
        "is_default_visible": True,
        "description_es": (
            "Segundo banco mas grande de Mexico por activos totales. "
            "Ingresos de margen financiero, comisiones, seguros y pensiones."
        ),
        "description_en": (
            "Mexico's second-largest bank by total assets. "
            "Revenue from net interest margin, fees, insurance, and pension management."
        ),
        "fetch_status": "ready",
    },
    {
        "symbol": "GMEXICOB.MX",
        "display_name_es": "Grupo Mexico",
        "display_name_en": "Grupo Mexico",
        "category": "mx_equity",
        "is_default_visible": True,
        "description_es": (
            "Tercer productor de cobre mas grande del mundo. "
            "Opera ademas la red ferroviaria Ferromex en Mexico."
        ),
        "description_en": (
            "World's third-largest copper producer. "
            "Also operates the Ferromex railway network across Mexico."
        ),
        "fetch_status": "ready",
    },
    {
        "symbol": "PENOLES.MX",
        "display_name_es": "Industrias Penoles",
        "display_name_en": "Industrias Penoles",
        "category": "mx_equity",
        "is_default_visible": True,
        "description_es": (
            "Mayor productor de plata de Mexico y principal refinador de oro. "
            "Ingresos ligados a precios spot de plata, oro, zinc y plomo."
        ),
        "description_en": (
            "Mexico's top silver producer and leading gold refiner. "
            "Revenue tied to spot prices for silver, gold, zinc, and lead."
        ),
        "fetch_status": "ready",
    },
    {
        "symbol": "WALMEX.MX",
        "display_name_es": "Walmart de Mexico",
        "display_name_en": "Walmart de Mexico",
        "category": "mx_equity",
        "is_default_visible": True,
        "description_es": (
            "Mayor minorista de Latinoamerica por ingresos. "
            "Opera Walmart, Sam's Club, Bodega Aurrera y Superama en Mexico."
        ),
        "description_en": (
            "Largest retailer in Latin America by revenue. "
            "Operates Walmart, Sam's Club, Bodega Aurrera, and Superama in Mexico."
        ),
        "fetch_status": "ready",
    },
]

GLOBAL_TICKERS = [
    {
        "symbol": "GC=F",
        "display_name_es": "Oro (Futuros)",
        "display_name_en": "Gold (Futures)",
        "category": "global_commodity",
        "is_default_visible": False,
        "description_es": "Contrato de futuros de oro. Relevante para el sector de metales preciosos mexicano.",
        "description_en": "Gold futures contract. Relevant to the Mexican precious metals sector.",
        "fetch_status": "pending",
    },
    {
        "symbol": "SI=F",
        "display_name_es": "Plata (Futuros)",
        "display_name_en": "Silver (Futures)",
        "category": "global_commodity",
        "is_default_visible": False,
        "description_es": "Contrato de futuros de plata. Mexico es el mayor productor mundial de plata.",
        "description_en": "Silver futures contract. Mexico is the world's largest silver producer.",
        "fetch_status": "pending",
    },
    {
        "symbol": "SPY",
        "display_name_es": "S&P 500 ETF",
        "display_name_en": "S&P 500 ETF",
        "category": "us_equity",
        "is_default_visible": False,
        "description_es": "ETF que replica el indice S&P 500. Referencia global de renta variable.",
        "description_en": "ETF tracking the S&P 500 index. Global equity benchmark.",
        "fetch_status": "pending",
    },
    {
        "symbol": "QQQ",
        "display_name_es": "Nasdaq 100 ETF",
        "display_name_en": "Nasdaq 100 ETF",
        "category": "us_equity",
        "is_default_visible": False,
        "description_es": "ETF que replica el Nasdaq 100. Exposicion al sector tecnologico de EE.UU.",
        "description_en": "ETF tracking the Nasdaq 100. Exposure to US technology sector.",
        "fetch_status": "pending",
    },
    {
        "symbol": "KO",
        "display_name_es": "Coca-Cola (NYSE)",
        "display_name_en": "Coca-Cola (NYSE)",
        "category": "us_equity",
        "is_default_visible": False,
        "description_es": "Socio principal de Arca Continental. Correlacion directa con AC.MX.",
        "description_en": "Primary partner of Arca Continental. Direct correlation with AC.MX.",
        "fetch_status": "pending",
    },
]


def hash_password(plain: str) -> str:
    sha256_hash = hashlib.sha256(plain.encode()).hexdigest()
    hashed = bcrypt.hashpw(sha256_hash.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        all_tickers = CORE_BMV_TICKERS + GLOBAL_TICKERS
        inserted_tickers = 0
        skipped_tickers = 0

        for ticker_data in all_tickers:
            result = await session.execute(
                select(ApprovedTicker).where(
                    ApprovedTicker.symbol == ticker_data["symbol"]
                )
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                session.add(ApprovedTicker(**ticker_data))
                inserted_tickers += 1
            else:
                skipped_tickers += 1

        await session.commit()
        print(f"Tickers: {inserted_tickers} inserted, {skipped_tickers} skipped")

        admin_username = os.getenv("ADMIN_DEFAULT_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_DEFAULT_PASSWORD", "adminlocalpass123")

        result = await session.execute(
            select(User).where(User.username == admin_username.lower())
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin is None:
            admin_user = User(
                username=admin_username.lower(),
                password_hash=hash_password(admin_password),
                role="admin",
                preferred_language="es",
                theme="dark",
            )
            session.add(admin_user)
            await session.commit()
            print(f"Admin user '{admin_username.lower()}' created")
        else:
            print(f"Admin user '{admin_username.lower()}' already exists, skipping")

    await engine.dispose()
    print("Seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
