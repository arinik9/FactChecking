# FactChecking
Projet spécifique de 5IF, 1er semestre 2015-2016.

### Liens utiles

[Documentation du projet](https://drive.google.com/folderview?id=0B0WoFK-qoHSpSS1OenVPaURGakE)

[Données de chômage](http://travail-emploi.gouv.fr/etudes-recherches-statistiques-de,76/statistiques,78/chomage,79/les-demandeurs-d-emploi-inscrits-a,264/les-series-mensuelles-nationales,12769.html)

### Affirmation 1 (Window Agregate Comparison)
Pendant les 30 premiers mois du mandat de Hollande 310 900 chômeurs ont été enregistrés en plus par rapport aux 30 derniers mois du mandat de Sarkozy.

[Source](http://www.lemonde.fr/les-decodeurs/breve/2014/12/12/chomage-hollande-fait-il-pire-que-sarkozy_4539810_4355770.html)

## Prerequisite
Software specified in `prerequisite/soft-requirements.txt`

Python modules specified in `prerequisite/python-requirements.txt`

## Useful commands
### Setting up python environment
`virtualenv <your_venv_dir> -p python2`

`. <your_venv_dir>/bin/activate`

`pip install -r "prerequisite/python-requirements.txt"`

`mkdir ~/FactCheckingDocumentation`

`epydoc --html  qrs.py -o ~/FactCheckingDocumentation/`

[epydoc help](http://epydoc.sourceforge.net/epydoc.html#python-docstrings)

