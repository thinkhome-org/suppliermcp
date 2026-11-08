# SupDB 2.0.0

Stabilní rozsah tohoto vydání zahrnuje katalog, hledání a porovnávání nabídek eD PUBLIC, eD PRIVATE a 100MEGA. Katalog uchovává poslední dostupný stav. Ceny a dostupnost mají vlastní stáří a nemusí představovat aktuální objednávkovou nabídku.

Ověřeno 320 dodavatelských čtení, shoda 157 804 produktů v PostgreSQL a Typesense, REST a Python knihovna, nativní Codex i osobní ChatGPT přes MCP, oddělení katalogových a dokladových oprávnění, restart, záloha a obnova i návrat na v1 na serverové VM. Referenční stage.3 běží pod plnou správou Portaineru.

## Známá omezení

Těchto šest metod není součástí garantovaného stabilního rozsahu. Jejich neúspěšné výsledky zůstávají v úplné testovací evidenci.

- X-ASM-StiRelation.delta a X-ASM-StiRelation_El.delta vracejí chybu dodavatele. Úplné exporty souvisejících produktů fungují. [Issue #3](https://github.com/thinkhome-org/suppliermcp/issues/3).
- GetXCompany, GetXCompanyListChanged a GetXCompanyListId pro firemní a kontaktní údaje vyžadují dořešení přístupu nebo parametrů s dodavatelem. [Issue #4](https://github.com/thinkhome-org/suppliermcp/issues/4).
- GetStatus nebylo možné ověřit, protože účet dosud nemá žádnou objednávku. Je potřeba testovací objednávka nebo účet od dodavatele. [Issue #4](https://github.com/thinkhome-org/suppliermcp/issues/4).

Tato omezení neblokují vydání katalogu, hledání a porovnávání nabídek. Ostatní neúspěšná čtení, odlišný obraz nebo neúplné akceptační kontroly nadále blokují povýšení. Úplná evidence je v operations.json a acceptance.json u tohoto vydání.

Použije se již ověřený obraz a distribuční balíčky stage.3 bez nového sestavení aplikace. Majetek ThinkHome s.r.o.; bez udělení licence.

## Zjištění po produkčním nasazení

Volání katalogu, hledání, detailu a porovnání prošla v běžném Codexu i osobním ChatGPT. Přesná shoda produkční databáze a indexu byla ověřena pro 157 804 položek, revizi 652. Podrobnosti v [deployment.json](deployment.json).

Dodatečné ověření obsahu porovnání odhalilo chybějící normalizaci `pack_count`: žádná z aktivních položek nemá doložený počet kusů v balení ve společném modelu. Párovač proto nabídky různých dodavatelů bezpečně nespojí ani při kandidátní shodě EAN/MPN. Úspěšný návrat `compare_offers` není dokladem funkčního automatického srovnání eD a 100MEGA. Samostatné nabídky a jejich nejistoty jsou dostupné; automatické porovnání napříč dodavateli čeká na [opravu #32](https://github.com/thinkhome-org/suppliermcp/issues/32). Toto zjištění je dodatečné vůči šesti dříve schváleným omezením. Již vydaný obraz se nemění.
