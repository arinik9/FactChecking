-- Le chômage a augmenté de 422 000 personnes pendant le mandat de Sarkozy.
-- Q1

-- debut de mandat: 15 Mai 2007 
	-- On prend annee=2007 AND trimestre=1 pour le debut
	-- afin de comparer le valeur dernier semstre de Chirac
	-- le chmage dans (annee=2007 AND trimestre=2) nous donne la valeur de la fin de semstre 2
-- fin de mandat: 16 Mai 2012	

SELECT (fin.millier-debut.millier)*1000 FROM 
(SELECT millier FROM chomage 
WHERE annee=2012 AND trimestre=1) AS fin,
(SELECT millier FROM chomage 
WHERE annee=2007 AND trimestre=1) AS debut; 
-- r = 350000


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
