# SupDB 2.0.2

Opravuje [#35](https://github.com/thinkhome-org/suppliermcp/issues/35): zastavený worker už nesmí ponechat opuštěnou COPY relaci a publikační zámek blokující index. Po 30 sekundách řádného dokončování se synchronní úlohy aktivně přeruší přes jejich vlastní DB spojení; rollback a zavření provedou kontextové správce. TCP detekce mrtvého protějšku pokrývá i ztrátu sítě bez čistého odpojení. Worker má omezenou nečinnost HTTP čtení, nikoli celkovou délku zdravého stahování nebo SQL/COPY. [Provozní postup a přesné limity](../../worker-lifecycle.md).

Opravu přináší [PR #37](https://github.com/thinkhome-org/suppliermcp/pull/37). Prošlo 608 testů, Docker akceptace, CodeQL a nezávislé review. Stejný neměnný obraz prošel izolovanou akceptací na serverové VM: dva cykly COPY/stop/retry, čekání na zámek, HTTP server bez odpovědi, síťový blackhole a následné bezpečné dokončení. Zdravá dlouhá COPY zůstala funkční.

Stage ověřila skutečný indexový job zablokovaný řízeným testovacím zámkem; worker skončil za 31,976 s, uvolnil všechna spojení a zámky a stejný job po restartu uspěl. Produkční worker skončil za 32,733 s, také bez zbylých DB relací/zámků a bez ručního ukončování backendů; po restartu pokračoval ve zpracování outboxu. Data, přihlášení i volumes zůstaly zachované, schéma se nemění. [Sanitizované výsledky](deployment.json).

Finální kontrola po importu ověřila přesnou shodu 158023 aktivních produktů a jejich revizí (katalogová revize 940); backlog, chybějící, nadbytečné i zastaralé položky byly nulové. Kontrola proběhla 2026-11-09T12:55:59.419198+00:00 pod sdílenými publikačními/indexovými zámky.

Pro konečný snapshot byly dočasně pozastavené nové automatické refreshe; rozpracovaná práce a index pokračovaly. Obnovení plánování má samostatný [provozní záznam u vydání](https://github.com/thinkhome-org/suppliermcp/releases/download/v2.0.2/refresh-resumed.json).

Běžný Codex i osobní ChatGPT ověřily katalog, hledání, detail a porovnání tří skutečných výrobků mezi eD a 100MEGA s počty dodavatelů 2/2/2. Codex plugin je aktualizovaný na 2.0.2.

Celá matice 326 dodavatelských operací nebyla pro tento patch opakována; její starší výsledky nejsou vydávány za nové. Šest přijatých omezení #3/#4 a neznámý objednací násobek 100MEGA zůstávají. Ceny jsou poslední známé; oprava neodstraňuje chybějící dodavatelská data.

Majetek ThinkHome s.r.o.; bez udělení licence.
