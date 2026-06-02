# requirements.txt Audit Notes

Goal: keep `requirements.txt` aligned with runtime needs for:
- running FastAPI backend
- connecting to PostgreSQL via SQLAlchemy
- loading the CF recommendation pipeline from pickles

## What was included as runtime dependencies

- `fastapi`, `uvicorn`
- `python-dotenv`
- `sqlalchemy`, `psycopg2-binary`
- `pydantic` (+ `pydantic-core`)
- `numpy` (pipeline uses it for scoring + sigmoid)

## What was kept but may be model-unpickle dependent

- `scikit-learn`, `pandas`, `matplotlib`, `seaborn`, `implicit`
  - These may be imported indirectly by the unpickled CF wrapper implementation depending on training/inference code paths.

If the model pickle unpickling fails in a clean environment, re-add any missing packages based on the traceback.

