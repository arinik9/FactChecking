-- Le chômage a augmenté de 422 000 personnes pendant le mandat de Sarkozy.
-- Pendant les 30 premiers mois du mandat de Hollande 310 900 chômeurs ont été enregistrés en plus par rapport aux 30 derniers mois de Sarkozy.
-- Q1
SET @w = 5;
SET @t= 5;
SET @d = 5;
SELECT (after.total - before.total) * 1000
FROM (	SELECT SUM(millier) AS total FROM chomage
		WHERE year BETWEEN t-@w-d+1 AND t-d) AS before,
	 (	SELECT SUM(millier) AS total FROM chomage
		WHERE year BETWEEN t-@w+1 AND t) AS after;
-- <Q1, (w=2, t=2001, d=6), 422000>
