.PHONY: all 

serve: all
	@cd static && python -m http.server

all:
	@python generate.py

