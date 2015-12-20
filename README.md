# FactChecking
Le sujet du projet spécifique à l'INSA en 2015-2015 pendant le 1er semestre

La page Google Doc correspodante: [Doc](https://docs.google.com/document/d/1st0c-jgniiC2DMktNm5dBwBV52JOhaGyjfpp0Zl60hU)

Données de base:

[INSEE](http://www.bdm.insee.fr/bdm2/affichageSeries?bouton=T%E9l%E9charger&idbank=001688358&idbank=001688526&codeGroupe=1533)

[travail-emploi](http://travail-emploi.gouv.fr/etudes-recherches-statistiques-de,76/statistiques,78/chomage,79/les-demandeurs-d-emploi-inscrits-a,264/les-series-mensuelles-nationales,12769.html)

### Affirmation 1
Selon Sarkozy le chômage (def. BIT) a augmenté de 422 000 personnes pendant son mandat.

### Affirmation 2
Pendant les 30 premiers mois du mandat de Hollande 310 900 chômeurs ont été enregistrés en plus par rapport aux 30 derniers mois du mandat de Sarkozy.

[Article](http://www.lemonde.fr/les-decodeurs/breve/2014/12/12/chomage-hollande-fait-il-pire-que-sarkozy_4539810_4355770.html)

## Prerequisite
Software specified in `prerequisite/soft-requirements.txt`

Python modules specified in `prerequisite/python-requirements.txt`

### Useful commands
`virtualenv <your_venv_dir> -p python2`

`pip install -r "prerequisite/python-requirements.txt"`

### For Documentation: epydoc (sudo pip install epydoc)

mkdir ~/FactCheckingDocumentation (if it does not exist)
epydoc --html  qrs.py -o ~/FactCheckingDocumentation/ (generating a html files)

