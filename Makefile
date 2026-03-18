.PHONY: monitor run health

monitor:
	uvicorn monitor.api.main:app --reload --port 8000

run:
	python3 run.py $(ARGS)

health:
	python3 run.py --health-check
