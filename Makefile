.PHONY: monitor run health

monitor:
	python3 -c "from memory import get_redis; r=get_redis(); [r.delete(k) for k in r.keys('aurelinth:*')]" 2>/dev/null || true
	uvicorn monitor.api.main:app --reload --port 8000

run:
	python3 run.py $(ARGS)

health:
	python3 run.py --health-check
