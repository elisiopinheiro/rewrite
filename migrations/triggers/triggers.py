from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger


def create_trigger(tablename: str):
    return PGTrigger(
        schema="public",
        signature=f"{tablename}_set_updated_at_on_update",
        on_entity=tablename,
        definition=f"""
        BEFORE UPDATE ON {tablename}
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at()
        """,
    )


set_updated_at_trigger_function = PGFunction(
    schema="public",
    signature="set_updated_at()",
    definition="""
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := now();
    return NEW;
END;
$$ language 'plpgsql'
""",
)
