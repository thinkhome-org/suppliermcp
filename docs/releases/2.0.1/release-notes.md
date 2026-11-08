# SupDB 2.0.1

Opravuje #32: nabídky eD a 100MEGA se pro stejný platný GTIN spojují i bez dodatečného společného pack_count. Logistické balení, objednací násobek a množstevní sleva zůstávají oddělené. Výslovné rozpory výrobce, MPN, balení či varianty spojení dál blokují; jiné platné GTIN se nespojí. [Ověřené významy polí a zdroje](../../supplier-api/packaging-and-comparison.md).

Přesný obraz z commitu 685a3d4 je ověřený nejprve ve stage a potom v produkčním Portaineru. Bez změny DB schématu, bez nového importu a se zachováním dat i přihlášení. Prošlo 595 testů, CodeQL a nezávislé review.

Šest nových cílených API čtení ověřilo tři skutečné shodné výrobky (MPN 8489A002, 7737A001, PK_6ASFTP003blue). Před opravou každý vracel jen jednoho dodavatele; po opravě všechny tři vracejí oba. Běžný Codex i osobní ChatGPT potvrdily katalog, hledání, detail a porovnání s počty dodavatelů 2/2/2. Negativní kontrola skutečně odlišných výrobků spojení odmítla. [Sanitizované výsledky](deployment.json).

## Zachované nejistoty

Ceny jsou poslední známé, nejsou závaznou nabídkou. U 100MEGA zatím není doložený objednací násobek, proto zůstává order_multiple_unknown a nelze dopočítat garantovanou cenu celého objednatelného množství. Oprava umožňuje porovnat jednotkové nabídky obou shodných výrobků, tuto nejistotu neskrývá. Neověřené nebo konfliktní identity se nespojují. Šest dříve přijatých omezení #3/#4 zůstává.

Celá matice 326 dodavatelských operací nebyla pro tento patch znovu provedena; dodavatelské adaptéry se nemění. Pro změněné chování se ověřil společný párovač, nezávislé množstevní výpočty, živé produktové odpovědi a obě skutečné klientské cesty. Jednorázová náprava opuštěné DB relace při nasazení je evidována samostatně v [#35](https://github.com/thinkhome-org/suppliermcp/issues/35).

Majetek ThinkHome s.r.o.; bez udělení licence.
