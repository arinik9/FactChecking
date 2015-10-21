-- Le chômage a augmenté de 422 000 personnes pendant le mandat de Sarkozy.
-- Q1
SET @w = 5;
SET @t= 5;
SET @d = 5;
SELECT (after.total - before.total) * 1000
FROM (	SELECT SUM(millier) AS total FROM chomage
		WHERE year BETWEEN t-@w-d+1 AND t-d) AS before,
	 (	SELECT SUM(millier) AS total FROM chomage
		WHERE year BETWEEN t-@w+1 AND t) AS after;



-- Pendant les 30 premiers mois du mandat de Hollande 310 900 chômeurs ont été enregistrés en plus par rapport aux 30 derniers mois de Sarkozy.
-- Q2
SET @w = 30;
SET @t= '2014-10-01';
SET @d = 30;

SELECT hollande.chomage - sarkozy.chomage
FROM
-- Hollande
( SELECT bf.nb_chomeur - af.nb_chomeur AS chomage
FROM ( SELECT nb_chomeur FROM chomagePE
       WHERE mois = @t ) AS bf,
     ( SELECT nb_chomeur FROM chomagePE
       WHERE mois = @t - INTERVAL @w+1 MONTH ) AS af ) AS hollande,
-- Sarkozy
( SELECT bf.nb_chomeur - af.nb_chomeur AS chomage
FROM ( SELECT nb_chomeur FROM chomagePE
       WHERE mois = @t - INTERVAL @d MONTH ) AS bf,
     ( SELECT nb_chomeur FROM chomagePE
       WHERE mois = @t - INTERVAL @d+@w+1 MONTH ) AS af ) AS sarkozy;
-- <q=Q2, (w=30, t='2014-10-01', d=30), r0=310900>
-- r = 282500
