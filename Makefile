.PHONY: all 

all:
	@python generate.py

serve: all
	@cd static && python -m http.server
