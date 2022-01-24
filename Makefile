test:
	python -m unittest tests/*.py

Readme.md: data_provider/*
	python -c "import re; import data_provider;  doc = data_provider.DataProvider.__doc__.lstrip('\n'); pre=re.search('^[ \t]*', doc, re.M)[0]; print(re.sub(f'^{pre}(\t*)', lambda match: '    ' * len(match[1]), doc, flags=re.M))" > $@
