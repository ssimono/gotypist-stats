.PHONY: check
check:
	mypy gotypist_stats
	pyflakes gotypist_stats
	black --check gotypist_stats
