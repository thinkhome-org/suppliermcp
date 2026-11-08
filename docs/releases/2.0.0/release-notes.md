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
