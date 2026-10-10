# Helicopters in Hong Kong, 1998

Research notes behind the helicopters in the sim (`HELICOPTERS` section of `index.html`). The sim is set in early July 1998, the last days of Kai Tak.

## Operators and bases (what the sources say)

| Operator | What it did in 1998 | Base / helipad | In the sim |
|---|---|---|---|
| Government Flying Service (GFS) | Air ambulance, search and rescue, police and fire support, survey flights. 1997 fleet: 6 Sikorsky S-76, 3 Sikorsky S-70 (Black Hawk), 2 Beech Super King Air. Formed 1 April 1993 from the Royal Hong Kong Auxiliary Air Force (RHKAAF). | Kai Tak south apron (new premises from August 1992). It moved to Chek Lap Kok with the airport in 1998. | Two pads and the flight services building (already on the south apron), a Black Hawk and an S-76 that fly sorties, and two more parked beside the building. |
| East Asia Airlines / Helicopters Hong Kong | Macau shuttle since November 1990 (two Bell 222, six flights a day at first). 40,000+ passengers in 1996. Three S-76C bought in 1997 to replace the Bell 222s. | Shun Tak Heliport, Sheung Wan: on top of the Macau ferry terminal at Shun Tak Centre, one pad built in 1986. | The pad, and two S-76 that shuttle out past Lantau and back. |
| The Peninsula Hotel | Rooftop helipads on the 1994 tower, certified in 1994 (first landing by Dick Smith). | Tsim Sha Tsui | Both pads (No. 1 south-west, No. 2 north-east, modelled from photos in `buildPeninsula`), and one S-76 on pad No. 1 that flies the harbour sightseeing flight. |
| Heliservices (Kadoorie group) | Charter, sightseeing and lifting work; the company dates from 1978. | Base near Shek Kong; also uses the Peninsula pad. | Not modelled (no 1998 fleet in the sources). |
| RAF 28 Squadron | Wessex HC.2 from Sek Kong 1978-1996, then Kai Tak until the squadron disbanded in June 1997. | Sek Kong, Kai Tak | Gone by July 1998, so not in the sim. |
| People's Liberation Army garrison | Z-9 helicopters at Shek Kong from 1997. | Shek Kong | Not modelled. |

Queen Elizabeth Hospital and Queen Mary Hospital have no helipad today, so no hospital pads are modelled.

## The scenic tour

The Peninsula helicopter's flight is the passenger tour (`penTour()` in `index.html`): Tsim Sha Tsui, Central, the Shun Tak terminal, Wan Chai, Causeway Bay, Kai Tak in view across the bay, Hung Hom, back to the roof. Captions name landmarks that are in the sim (Bank of China Tower, HSBC, Jardine House, the Convention Centre extension, Central Plaza, the Coliseum) and the helicopter facts above. Central Plaza (373.9 m, completed August 1992) and the Convention Centre extension (completed 1997) are from the Wikipedia and e-architect pages in the sources. Their English and Cantonese text is in `penTour()`; each is shown from the moment the helicopter reaches its waypoint, as a function of the sim clock.

## What is made up

- Liveries. The GFS helicopters are red and white; the shuttle and hotel schemes are invented (no real brands).
- Flight routes, cycle times and heights. The shuttle is compressed: each helicopter goes out past Lantau and back in 1,300 s of sim time.
- Shun Tak pad height (about 30 m) and its deck on piers.

## Sources

- Government Flying Service, Hong Kong Yearbook 1997 (fleet and roles): https://www.yearbook.gov.hk/1997/ch18/e18k.htm
- GFS at Kai Tak, Gwulo: https://gwulo.com/node/62327
- RHKAAF aircraft types: https://www.helis.com/database/org/Royal-Hong-Kong-Auxiliary-Air-Force/
- Sky Shuttle / East Asia Airlines history: https://en.wikipedia.org/wiki/Sky_Shuttle and https://industrialhistoryhk.org/sky-shuttle-helicopters/
- East Asia Airlines S-76C order (Flight International, 26 March 1997): https://flightglobal.com/east-asia-buys-s-76cs/7665.article
- Shun Tak Heliport: https://industrialhistoryhk.org/shun-tak-macau-helicopter-terminal/ and https://industrialhistoryhk.org/?p=36094
- The Peninsula Hong Kong rooftop helipad: https://en.wikipedia.org/wiki/The_Peninsula_Hong_Kong
- Heliservices: https://en.wikipedia.org/wiki/Heliservices
- 28 Squadron in Hong Kong: https://www.helis.com/database/sqd/28-Squadron
- Shek Kong Airfield: https://en.wikipedia.org/wiki/Shek_Kong_Airfield
- Central Plaza: https://en.wikipedia.org/wiki/Central_Plaza_(Hong_Kong)
- Hong Kong Convention and Exhibition Centre: https://www.e-architect.com/hong-kong/hong-kong-convention-centre
