from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert


metadata = MetaData()


class WrappedTable:
    def __init__(self, name: str, engine, *columns):
        self.name = name
        self.engine = engine
        self.table = Table(name, metadata, *columns)
        self.columns = {c.name: i for i, c in enumerate(self.table.c)}

    def _add_cond(self, query, where: dict):
        for k, v in where.items():
            query = query.where(getattr(self.table.c, k) == v)
        return query

    async def _select(self, where: dict = {}) -> list:
        query = self._add_cond(self.table.select(), where)
        async with self.engine.connect() as conn:
            return (await conn.execute(query)).all()

    def _extract(self, response: list, columns: list) -> list:
        columns = [self.columns[name] for name in columns] or range(len(self.columns))
        return [tuple(row[i] for i in columns) for row in response]

    async def select(self, *what, **where) -> list:
        return self._extract(await self._select(where), what)

    async def insert(self, values=None, **kw_values) -> None:
        if values is not None:
            values = {col.name: val for col, val in zip(self.table.c, values)}
            values.update(kw_values)
        else:
            values = kw_values
        async with self.engine.begin() as conn:
            await conn.execute(self.table.insert(), values)

    async def update(self, what: dict, where: dict):
        query = self._add_cond(self.table.update(), where)
        async with self.engine.begin() as conn:
            await conn.execute(query, what)

    async def delete(self, **where):
        query = self._add_cond(self.table.delete(), where)
        async with self.engine.begin() as conn:
            await conn.execute(query)

    async def upsert(self, **values) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                insert(self.table).on_conflict_do_update(
                    constraint=self.table.primary_key, set_=values
                ),
                values,
            )
