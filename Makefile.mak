.PHONY: install test run-all clean

install:
	conda env create -f environment.yml
	conda activate cro-trilemma
	pip install -e .

test:
	pytest tests/ -v --cov=src

run-all:
	python scripts/run_all_experiments.py
	python scripts/generate_tables.py
	python scripts/create_figures.py

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf data/processed/*
	rm -rf data/results/*

reproduce:
	make clean
	make install
	make test
	make run-all