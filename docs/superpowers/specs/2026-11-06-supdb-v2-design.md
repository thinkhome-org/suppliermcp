# SupDB 2.0.0 — návrh ke schválení

SupDB je pracovní název. Vydání má zpřístupnit všechna doložená čtení 100MEGA a eD aplikacím ThinkHome i dalším samostatným instalacím. Hlavním klientem je vzdálené MCP v Codexu a osobním webovém ChatGPT. Druhým vstupem bude HTTP API s OpenAPI. Software je majetkem ThinkHome s.r.o., bez udělení licence. Přejmenování repozitáře a veřejných identifikátorů vyžaduje samostatné rozhodnutí.

## Rozhodnutí a alternativy

Uživatel zvolil B. PostgreSQL drží poslední katalog a vykonává úplné výběry. Typesense drží obnovitelný textový index. Varianta A pouze s PostgreSQL snižuje provozní náklady. Varianta C s OpenSearch nabízí český analyzér a větší prostor pro ladění za cenu další provozní složitosti. Kvalitu B změříme na katalogu v plném rozsahu. Historie cen ani dlouhodobý archiv dokladů do v2 nepatří.

## Hranice modulů

Importovatelná async Python knihovna poskytuje operace pro katalog, nabídky, schopnosti dodavatelů a živá čtení. Nezávisí na kontextu HTTP požadavku. FastAPI vystaví verziované REST API a OpenAPI. FastMCP používá stejné operace a společnou kontrolu oprávnění. Přímé nástroje pro hledání, detail a porovnání mají malé stránkované výsledky. Specifická čtení dodavatelů mají deklarované vstupy a výstupy. Každá povolená operace musí být dosažitelná přes REST i MCP. Zachovat otestované klientské postupy v1 nebo zveřejnit konkrétní migrační návod před přepnutím.

Každá instalace drží vlastní účty dodavatelů. i6ws (100MEGA) a ELINKX (eD PUBLIC a PRIVATE) mají oddělené adaptéry. Registr operací uvádí zdroj a verzi kontraktu, identifikátor operace a exportu, vstupy, schéma odpovědi, oprávnění účtu, povolené časy a vedlejší účinky. Podklady tvoří přiložené PDF, e-maily a výpisy, živé WSDL, katalog exportů účtu a oficiální weby. Nově objevené operace vyžadují klasifikaci před povolením. Zápisy zdokumentovat a vyřadit z volatelného rozhraní. Při nejasném účinku blokovat volání do vyjasnění. Zakázat předávání libovolné URL, SOAP action nebo exportu od klienta.

## Data a import

Worker sdílí image s API. HTTPX pro síťové I/O, Zeep dle složitosti SOAP, proudové čtení XML a ZIP s limity, Psycopg COPY do pracovních tabulek. Procrastinate v PostgreSQL pro trvalou frontu, zamykání a opakování ve správném okně. Poslední použitelná revize zůstane čitelná při chybě importu. Úplná baseline může odebrat chybějící položku pouze v ověřeném rozsahu. Dílčí export a delta aktualizují vlastní příspěvek. Po zveřejnění transakce worker obnoví index a eviduje obě revize. Doklady a adresy se čtou na dotaz s odděleným oprávněním, bez ukládání obsahu do indexu, fronty, logů či cache.

Identita dodavatele, SKU, EAN včetně úvodních nul, výrobce, MPN, varianta a balení zůstanou rozlišitelné. Nabídka nese měnu, množství, jednotku, poplatky, původ a známý čas platnosti odděleně od času stažení. Neznámá hodnota a nulová hodnota jsou různé stavy. Podobnost názvů smí navrhnout kandidáta na shodu. Automatické sloučení vyžaduje kompatibilní identitu, variantu a balení.

## Dotazy

Přesný kód a úplný výběr s filtry a cenovým řazením obsluhuje PostgreSQL. Pro zadané množství uvést objednatelné množství, zaokrouhlení na balení, slevu, měnu a známé složky ceny. Nevyhlásit nejlevnější nabídku při neporovnatelných podmínkách. Stabilní pořadí při shodě ceny, kurzor svázaný s dotazem, revizí a oprávněním. Typesense váží název, značku a model samostatně. Ověřené běžné filtry provede před omezením počtu kandidátů. U ostatních musí výstup uvést neúplnost nebo přepnout na úplný databázový dotaz. Vrátit stav indexu a rozsah pokrytí. Přesné a úplné výběry musejí fungovat i při obnově indexu.

## Nasazení a převzetí

Portainer Compose spouští API/MCP, worker, PostgreSQL a Typesense. Přístupové údaje ponechat v chráněném lokálním úložišti a dodat provozu jako tajné hodnoty. Surové přílohy, citlivé URL, ceny a doklady nepublikovat. HTTPS a oddělená oprávnění pro katalog a obchodní agendu. Pro osobní ChatGPT ověřit připojení a autorizaci na skutečném účtu. GitHub CI má kontrolovat testy, syntetické kontrakty, schémata, migrace a sestavení image. Release workflow má zveřejnit ověřený image v GHCR. Verzovaná dokumentace v repozitáři je zdrojem pro synchronizaci GitHub Wiki. GitHub Project sleduje operace a zbývající akceptační testy. Produkční aktualizace až po záloze, ověření obnovy a testu v odděleném stacku.

Pro každou čtecí operaci a každý režim exportu evidovat zdroj, autentizovaný test, datum, rozsah, výsledek a případný blokátor. Rozlišit WSDL, úspěšný prázdný výsledek a ověřený neprázdný výsledek. Test se spouští z povolené IP s dodržením časových oken. Při chybějícím oprávnění, vstupním dokladu nebo podpoře klienta uvést přesnou mezeru ve vydání. Plné pokrytí lze tvrdit až po průchodu celé matice.

Na pevné revizi katalogu ověřit přesný kód, diakritiku, podobná modelová čísla, filtr s výsledkem mimo původních 1000 kandidátů, shodné ceny, neznámé balení a porovnání pro množství 12. Úplné množiny a pořadí srovnat s nezávislým SQL výpočtem. Měřit kvalitu prvních pěti textových výsledků, odezvu pod souběžným importem, paměť a dobu obnovy. Samostatné akceptační testy pro Python, REST, vzdálené MCP v Codexu, osobní webový ChatGPT a restart Portainer stacku včetně záporných testů oprávnění.

Výběr tříd, názvů balíčků, detailu indexů a konkrétních verzí závislostí je ponechán implementaci. Nasazení a přejmenování se tímto návrhem neprovádí.

Pro označení 2.0.0 jako plně funkční jsou průchod osobního ChatGPT, Codexu a ověření všech podporovaných čtení požadavky zadání. Zbývající mezery dovolují vydat kandidáta s přehledem omezení. Pro relevanci navrhuji před měřením označit očekávané výsledky na pevné sadě českých dotazů. Počáteční výkonové měření zveřejnit s konfigurací stroje; konkrétní SLA zatím nebylo zadáno.

Otevřené rozhodnutí vlastníka: které identity a klienti smějí číst firemní doklady a dodací adresy. Bez přiřazeného oprávnění bude přístup zamítnut.
