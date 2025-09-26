.PHONY: preprocessing

preprocessing:
	python -m misc_utils.recipe_processing --to-qdrant --qdrant-path "qdrantdb"