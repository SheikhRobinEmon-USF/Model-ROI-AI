.PHONY: install test studio api api-local demo web check-web screenshots

install:         ## install the package with development tools
	pip install -e ".[dev]"

test:            ## offline tests: no network, no models
	python -m pytest -q

studio:          ## check Ollama, set up a virtual environment and open the studio
	python scripts/start_local.py

api:             ## offline mock API
	python -m uvicorn modelroi.api.main:app

api-local:       ## studio API with local inference on port 8598 (for check-web and screenshots)
	MODELROI_ENABLE_LOCAL=true python -m uvicorn modelroi.api.main:app --port 8598

demo:            ## Streamlit preview
	python -m streamlit run src/modelroi/ui/Home.py

web:             ## rebuild the studio bundle in web/dist
	cd web && npm ci && npm run build

check-web:       ## browser checks at 1280, 390 and 320 px (needs api-local and Playwright)
	python web/check_browser.py

screenshots:     ## regenerate docs/images from sample data (needs api-local and Playwright)
	python web/capture_screens.py
