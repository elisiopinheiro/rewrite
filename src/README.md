# Clusters 4WM API


## Database changes

Add the fields and necessary constraints to the tables on the code. 
After the code changes, with docker-compose run:

```bash
docker compose up -d --build
# Generate new migration file
docker compose exec app poetry run alembic revision --autogenerate -m "<migration message>"
# Validate auto generated changes on the new version file
docker compose exec app poetry run alembic upgrade head
```


## Handling Alembic conflicts on Prod/Int

When upgrading and then downgrading versions, an error can occur:

```bash
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
ERROR [alembic.util.messaging] Can't locate revision identified by 'f1e574399590'
FAILED: Can't locate revision identified by 'f1e574399590'
```

When this happens the init_db pod won't be able to downgrade the version.

To resolve this issue enter the container of the App pod with:

```bash
k exec -it int-clusters-4wm-api-<...> -- bash
```

After entering the pod terminal, if you don't know the previous Alembic version:

```bash
poetry run alembic history
```

This will list all alembic versions. Get the correct Alembic version. 

> [!CAUTION]
> Careful to not chose the wrong alembic_version or it can remove tables/columns from the DB and lose important data!

Finally run:
```bash
poetry run alembic downgrade <previous_alembic_version>
```

After this the init_db container should be able to complete without problems.
