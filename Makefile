.PHONY: test demo api
test:
	python -m pytest -q
demo:
	python -m streamlit run app/ui/Home.py
api:
	python -m uvicorn app.api.main:app
