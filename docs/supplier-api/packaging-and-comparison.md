# Balení a porovnávání nabídek

## Ověřený význam dodavatelských polí

Kontrola 2026-11-08 vychází z dodaných dokumentů eD PUBLIC/PRIVATE, živé dokumentace 100MEGA a šesti nových cílených čtení skutečných produktů. Nedošlo k vytvoření ani změně objednávky.

| Pole | Význam | Použití v porovnání |
| --- | --- | --- |
| eD `EANCode` | EAN obchodní položky | Platný shodný GTIN identifikuje stejnou obchodní položku. |
| eD `MultipleQuantity` | Minimální násobek objednávaného množství | `order_multiple`; není to počet kusů uvnitř prodejní jednotky. |
| eD `ValuePackQty` | Množství nutné pro množstevní slevu | Hranice slevy; není to velikost balení. |
| eD `LogisticDataList/ProductLogisticData` | `typ` rozlišuje JEDN a PACK; `count` je počet kusů v dané logistické jednotce | Logistické obaly mohou mít několik různých velikostí; nepřepisují cenovou jednotku ani identitu produktu. |
| 100MEGA `QtyPack` | Počet produktů v balení; ve StoItemBase může být výchozí hodnota 1 vynechaná | Zachovává se jako nativní údaj; není doloženým objednacím ani cenovým násobkem. |
| 100MEGA `NonDivQty` | Exportované numerické pole; přesná sémantika není v ověřeném veřejném průvodci vyložena | Nepoužívá se k domýšlení objednacího násobku ani počtu kusů v ceně. |
| 100MEGA `PriceDea` | Cena produktu bez recyklačních/autorských poplatků a bez DPH | Jednotková cena; nesmí se automaticky násobit či dělit `QtyPack`. |

U eD PUBLIC je význam MultipleQuantity a ValuePack uveden v kapitole getProductList dodaného PUBLICdoc; u PRIVATE v popisu ProductComplete a LogisticDataList dodaného PRIVATEdoc. Živé čtení stejného kabelu potvrdilo eD objednací násobek 10 a zároveň logistickou jednotku JEDN s count 1; 100MEGA pro stejný EAN vrací QtyPack 1. Záměna těchto polí by vytvořila nesprávné porovnání.

Zdroje: [100MEGA průvodce, StoItemBase](https://i6ws.100mega.cz/WebServiceInfoMail.txt), [eD PUBLIC WSDL](https://public-ws-cz.elinkx.biz/service.asmx?WSDL), [eD PRIVATE WSDL](https://private-ws-cz.elinkx.biz/service.asmx?WSDL), dodané PUBLICdoc a PRIVATEdoc. Přístupové údaje ani obsah účtových exportů nejsou součástí dokumentace.

## Oprava #32 v 2.0.1

Původní univerzální požadavek na společný `pack_count` blokoval i dvojice se shodným platným GTIN. Nejde o chybějící povinný údaj dodavatele a oprava nevytváří umělé balení 1 kus. Samostatná databázová tabulka observations a společná mapování se načítají při sestavení produktu; samotný JSON v source_items není úplný seznam jeho pozorování.

Podle [GS1 GTIN Management Standard](https://ref.gs1.org/standards/gtin-management/) identifikuje GTIN konkrétní obchodní položku a úroveň balení. Párovač proto přijme shodný GTIN s platnou délkou 8/12/13/14 a kontrolní číslicí, pokud nejsou výslovné rozpory ve výrobci, MPN, balení nebo variantě. Nulový či neplatný kód nestačí. Různé platné GTIN se nespojují ani při shodném MPN. Bez shodného platného GTIN zůstává konzervativní cesta výrobce + MPN + doložené shodné balení.

Objednací množství a ceny se počítají až po určení shodné položky. Rozdílná objednatelná množství se nesmí seřadit podle celkové ceny. Chybějící poplatky, měna či objednací násobek zůstávají neznámé; neověřené datum ceny nevytváří „čerstvého vítěze“. Oprava párování tyto kontroly neobchází. Platná kontrolní číslice není ověření vlastnictví GTIN v registru GS1; stále vycházíme z identifikátorů deklarovaných dodavateli a odmítáme zjištěné rozpory.

## Skutečné produkty pro akceptaci

Přes obě API znovu načteny stejné EAN/MPN; zachovány hashe šesti odpovědí v chráněných lokálních podkladech. Ceny ani přístupy se nezveřejňují.

| MPN | EAN | Poznatek |
| --- | --- | --- |
| 8489A002 | 4960999201719 | eD objednací násobek 1, logistická jednotka JEDN 1; 100MEGA QtyPack 1. |
| 7737A001 | 4960999047034 | eD JEDN 1 a logistické PACK 10 i 50 současně; 100MEGA QtyPack 1. |
| PK_6ASFTP003blue | 8592457132943 | eD objednací násobek 10, JEDN 1; 100MEGA QtyPack 1. |

Na původní 2.0.0 všechny tři dvojice vracely jen nabídku výchozího dodavatele. Automatické testy opravy ověřují shodný GTIN, odmítnutí jiného GTIN a výslovného rozdílu balení/varianty, i nezávislé zaokrouhlení objednacích množství. Po nasazení přesného obrazu 2.0.1 prošly všechny tři skutečné dvojice ve stage, produkci, běžném Codexu i osobním ChatGPT: vždy oba dodavatelé. Negativní kontrola různých skutečných produktů spojení odmítla. Podrobnosti v [záznamu 2.0.1](../releases/2.0.1/deployment.json).
