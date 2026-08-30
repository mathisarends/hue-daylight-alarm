from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from huerise.features.lighting.domain import HueBridgeRepository, HueBridgeSelection
from huerise.infrastructure.database import HueBridgeSelectionModel

_HUE_SELECTION_ID = UUID("0198f9b4-0000-7000-8000-000000000002")


class SQLHueBridgeRepository(HueBridgeRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_selected(self) -> HueBridgeSelection | None:
        async with self._session_factory() as session:
            orm = await session.get(HueBridgeSelectionModel, _HUE_SELECTION_ID)
        return self._to_domain(orm) if orm is not None else None

    async def save_selected(self, selection: HueBridgeSelection) -> HueBridgeSelection:
        async with self._session_factory.begin() as session:
            orm = await session.merge(
                HueBridgeSelectionModel(
                    id=_HUE_SELECTION_ID,
                    bridge_id=selection.bridge_id,
                    ip_address=selection.ip_address,
                    app_key=selection.app_key,
                )
            )
            await session.flush()
            await session.refresh(orm)
        return self._to_domain(orm)

    @staticmethod
    def _to_domain(orm: HueBridgeSelectionModel) -> HueBridgeSelection:
        return HueBridgeSelection(
            bridge_id=orm.bridge_id,
            ip_address=orm.ip_address,
            app_key=orm.app_key,
        )
