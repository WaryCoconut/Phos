#!/usr/bin/env python3
"""
Inject nation_brief fields into the default_2016.json scenario file.

Each brief is historically accurate for January 2016.
Major powers get 5-6 bullet points; others get 3-4.
"""

import json
import pathlib

SCENARIO_PATH = pathlib.Path(__file__).resolve().parent.parent / "backend" / "app" / "data" / "scenarios" / "default_2016.json"

NATION_BRIEFS: dict[str, str] = {
    # ────────────────────────── MAJOR POWERS ──────────────────────────
    "USA": (
        "[NATION BRIEF — United States of America]\n"
        "- Political landscape: President Barack Obama in his final year; divisive 2016 presidential primaries underway with Donald Trump and Hillary Clinton as frontrunners.\n"
        "- Key challenges: Mass shootings debate, Affordable Care Act implementation, racial tensions following Ferguson and Baltimore protests, opioid epidemic escalating.\n"
        "- Regional tensions: Leading coalition against ISIS in Iraq and Syria; managing fallout from 2015 JCPOA nuclear deal with Iran; pivot to Asia strategy.\n"
        "- Economic situation: Steady recovery from 2008 crisis, unemployment at 5%, Fed raised interest rates in December 2015 for the first time in nearly a decade.\n"
        "- Strategic assets: World's largest military budget (~$600B), 11 carrier strike groups, global network of ~800 overseas bases, nuclear triad, dominant tech sector.\n"
        "- 2016 context: JCPOA Implementation Day on January 16 lifts Iran sanctions; TPP signed but not ratified; Flint water crisis gaining national attention."
    ),
    "CHN": (
        "[NATION BRIEF — China]\n"
        "- Political landscape: President Xi Jinping consolidating power, anti-corruption campaign intensifying; one-child policy officially ended January 1, 2016.\n"
        "- Key challenges: Economic growth slowing to ~6.9% (lowest in 25 years), stock market turmoil with circuit breakers triggered in early January 2016, capital flight concerns.\n"
        "- Regional tensions: Aggressive island-building in South China Sea, tensions with Japan over Senkaku/Diaoyu Islands, growing assertiveness toward Taiwan.\n"
        "- Economic situation: World's second-largest economy transitioning from export-led to consumption-driven growth; yuan devaluation concerns roiling global markets.\n"
        "- Strategic assets: 2.3 million active military personnel (world's largest), rapidly modernizing navy, growing nuclear arsenal, space program, massive foreign reserves (~$3.3T).\n"
        "- 2016 context: One Belt One Road initiative expanding; AIIB launched in January 2016; first overseas military base being built in Djibouti; new aircraft carrier under construction."
    ),
    "RUS": (
        "[NATION BRIEF — Russia]\n"
        "- Political landscape: President Vladimir Putin with high domestic approval; opposition marginalized; state media dominance; Nemtsov assassination in 2015 still reverberating.\n"
        "- Key challenges: Western sanctions over Crimea annexation, oil price collapse devastating budget revenues, ruble devaluation, international isolation deepening.\n"
        "- Regional tensions: Military intervention in Syria since September 2015 supporting Assad; ongoing hybrid war in eastern Ukraine (Donbass); frozen conflicts in Georgia and Moldova.\n"
        "- Economic situation: GDP contracted ~3.7% in 2015, deep recession from combined sanctions and oil price crash; inflation above 12%; reserves declining.\n"
        "- Strategic assets: World's largest nuclear arsenal (~7,300 warheads), modernizing military, permanent UNSC seat, vast energy resources, advanced air defense systems (S-400).\n"
        "- 2016 context: Syria intervention reshaping Middle East dynamics; Turkey relations in crisis after November 2015 shoot-down of Russian jet; Minsk II ceasefire largely holding but unresolved."
    ),
    "DEU": (
        "[NATION BRIEF — Germany]\n"
        "- Political landscape: Chancellor Angela Merkel (CDU) under intense pressure over refugee policy; 'Wir schaffen das' stance dividing the country; AfD gaining support.\n"
        "- Key challenges: Over 1 million refugees arrived in 2015, integration and housing crisis; Cologne New Year's Eve mass assaults dominating headlines in January 2016.\n"
        "- Regional tensions: Leading EU response to Ukraine crisis, key interlocutor with Russia; balancing solidarity within EU as eastern members resist refugee quotas.\n"
        "- Economic situation: Europe's largest economy performing well with ~1.7% growth, low unemployment (~4.5%), budget surplus, strong exports; Volkswagen emissions scandal impact.\n"
        "- Strategic assets: EU's economic engine, major NATO contributor, strong manufacturing and export base, diplomatic influence as EU de facto leader.\n"
        "- 2016 context: Refugee crisis reshaping European politics; Merkel negotiating EU-Turkey deal; NSA surveillance scandal straining US-German relations; Deutsche Bank facing massive legal fines."
    ),
    "FRA": (
        "[NATION BRIEF — France]\n"
        "- Political landscape: President Francois Hollande deeply unpopular; state of emergency extended after November 2015 Bataclan/Paris attacks; Front National gaining ground.\n"
        "- Key challenges: Terrorism threat at highest level; unemployment stubbornly above 10%; social divisions over secularism and Muslim integration; labor law reform planned.\n"
        "- Regional tensions: Active military operations in Mali (Barkhane) and Central Africa; participating in anti-ISIS coalition; maintaining presence in francophone Africa.\n"
        "- Economic situation: Sluggish growth (~1.3%), high public debt (~96% GDP), persistent budget deficits; struggling to meet EU fiscal rules.\n"
        "- Strategic assets: Independent nuclear deterrent (~300 warheads), aircraft carrier Charles de Gaulle, permanent UNSC seat, significant overseas territories, strong defense industry.\n"
        "- 2016 context: Post-attack security overhaul; COP21 Paris Agreement just adopted December 2015; labor law protests brewing; 2017 presidential campaign beginning to take shape."
    ),
    "GBR": (
        "[NATION BRIEF — United Kingdom]\n"
        "- Political landscape: PM David Cameron (Conservative majority); EU referendum promised for June 2016; Cameron negotiating reforms with Brussels; Labour under new leader Jeremy Corbyn.\n"
        "- Key challenges: Brexit debate dominating politics; Scottish independence pressure after 2014 referendum; NHS funding crisis; austerity measures ongoing.\n"
        "- Regional tensions: Active in anti-ISIS coalition; parliamentary vote authorized airstrikes in Syria December 2015; maintaining Falklands defense; Northern Ireland peace fragile.\n"
        "- Economic situation: Growth around 2.2%, outperforming most EU peers; low unemployment; London as global financial center; significant current account deficit.\n"
        "- Strategic assets: Nuclear deterrent (Trident), permanent UNSC seat, Five Eyes intelligence alliance, global financial center, special relationship with US, strong soft power.\n"
        "- 2016 context: EU referendum campaign about to intensify; Trident renewal debate; immigration a top voter concern; House of Lords reform stalled; flooding in northern England."
    ),
    "JPN": (
        "[NATION BRIEF — Japan]\n"
        "- Political landscape: PM Shinzo Abe (LDP) with strong parliamentary majority; pursuing 'Abenomics' economic revitalization and security normalization agenda.\n"
        "- Key challenges: Aging population crisis (26% over 65), persistent deflationary pressures, public debt over 230% GDP, Fukushima decommissioning ongoing.\n"
        "- Regional tensions: Territorial disputes with China (Senkaku) and South Korea (Dokdo/Takeshima); North Korean nuclear/missile threat; comfort women agreement with South Korea December 2015.\n"
        "- Economic situation: Third-largest world economy with ~0.5% growth; Bank of Japan considering negative interest rates; TPP trade deal signed but unratified.\n"
        "- Strategic assets: Technologically advanced Self-Defense Forces, US alliance with ~50,000 troops stationed, world-class navy, advanced missile defense, strong tech/manufacturing base.\n"
        "- 2016 context: New security laws allowing limited collective self-defense effective; reinterpreting Article 9; hosting G7 summit in Ise-Shima in May 2016; Okinawa base relocation disputes."
    ),
    "IND": (
        "[NATION BRIEF — India]\n"
        "- Political landscape: PM Narendra Modi (BJP) in second year; pursuing economic reforms and Hindu nationalist agenda; opposition Congress party weakened.\n"
        "- Key challenges: Poverty and inequality, inadequate infrastructure, air pollution crisis, communal tensions, Naxalite-Maoist insurgency in rural areas.\n"
        "- Regional tensions: Ongoing tensions with Pakistan over Kashmir; Chinese border disputes; growing concern over Chinese String of Pearls encirclement; influence competition in Indian Ocean.\n"
        "- Economic situation: World's fastest-growing major economy (~7.5% growth), 'Make in India' initiative, FDI liberalization, but rural distress and banking NPAs a concern.\n"
        "- Strategic assets: 1.3 million active military, nuclear arsenal (~120 warheads), space program with Mars orbiter, growing navy, large diaspora, IT sector powerhouse.\n"
        "- 2016 context: Modi's diplomatic outreach including surprise visit to Pakistan in December 2015; Pathankot airbase attack January 2, 2016 straining India-Pakistan ties; GST reform pending."
    ),
    "BRA": (
        "[NATION BRIEF — Brazil]\n"
        "- Political landscape: President Dilma Rousseff (PT) facing impeachment proceedings; massive Petrobras corruption scandal (Operation Car Wash) engulfing political class.\n"
        "- Key challenges: Deep political crisis, Zika virus outbreak declared emergency, crumbling infrastructure, rising crime, environmental degradation in Amazon.\n"
        "- Regional tensions: Regional leadership contested; Mercosur stagnating; Venezuela crisis creating diplomatic tensions; border security concerns.\n"
        "- Economic situation: Severe recession with GDP contracting ~3.8%, inflation above 10%, unemployment rising rapidly, real depreciating, credit rating downgraded to junk.\n"
        "- Strategic assets: Largest economy and military in Latin America, vast natural resources, pre-salt oil reserves, agricultural superpower, soft power through cultural exports.\n"
        "- 2016 context: Rio Olympics in August 2016 amid infrastructure concerns; impeachment of Rousseff looming; Zika threatening Olympics; Lula under investigation; fiscal crisis deepening."
    ),
    "SAU": (
        "[NATION BRIEF — Saudi Arabia]\n"
        "- Political landscape: King Salman bin Abdulaziz in power since January 2015; Deputy Crown Prince Mohammed bin Salman (MBS) rising rapidly; power consolidation underway.\n"
        "- Key challenges: Oil price crash (below $30/barrel) devastating revenues; execution of Shia cleric Nimr al-Nimr on January 2, 2016 sparking regional crisis with Iran.\n"
        "- Regional tensions: Leading military intervention in Yemen (since March 2015); bitter rivalry with Iran intensifying; diplomatic relations severed with Iran January 2016; supporting Syrian rebels.\n"
        "- Economic situation: Budget deficit of ~15% GDP due to oil crash; beginning austerity measures; subsidy cuts; Vision 2030 economic diversification being planned.\n"
        "- Strategic assets: World's largest oil exporter, custodian of Mecca and Medina, massive sovereign wealth fund, modern US-supplied military, strategic location.\n"
        "- 2016 context: MBS preparing Vision 2030 reform plan; mass execution of 47 people on January 2 including Nimr al-Nimr; Saudi embassy in Tehran attacked; OPEC strategy of maintaining production to crush competitors."
    ),
    "TUR": (
        "[NATION BRIEF — Turkey]\n"
        "- Political landscape: President Recep Tayyip Erdogan (AKP) consolidating power after November 2015 election victory; pushing for presidential system; crackdown on media.\n"
        "- Key challenges: Renewed Kurdish conflict with PKK, ISIS attacks (Ankara bombings October 2015), managing 2.5 million Syrian refugees, press freedom deteriorating.\n"
        "- Regional tensions: Shot down Russian jet November 2015, severe Russia-Turkey crisis; fighting Kurdish groups in Syria; complex relationship with ISIS on border; EU refugee deal negotiations.\n"
        "- Economic situation: Growth around 4% but vulnerabilities emerging; lira weakening; tourism sector threatened by terrorism and Russian sanctions; current account deficit.\n"
        "- Strategic assets: NATO's second-largest army, strategic Bosphorus control, Incirlik Air Base used by US coalition, bridge between Europe and Middle East.\n"
        "- 2016 context: EU-Turkey refugee deal being negotiated; Erdogan demanding visa liberalization; ISIS suicide bombing in Istanbul Sultanahmet Square January 12, 2016; academics purge beginning."
    ),
    "IRN": (
        "[NATION BRIEF — Iran]\n"
        "- Political landscape: President Hassan Rouhani (moderate); Supreme Leader Ayatollah Khamenei maintaining ultimate authority; reformists vs. hardliners struggle; parliamentary elections upcoming February 2016.\n"
        "- Key challenges: Implementation of JCPOA nuclear deal, reintegrating into global economy after sanctions, high youth unemployment, human rights concerns, regional overextension.\n"
        "- Regional tensions: Supporting Assad in Syria, Hezbollah in Lebanon, Houthis in Yemen; rivalry with Saudi Arabia escalating after Nimr execution; influence in Iraq through Shia militias.\n"
        "- Economic situation: Sanctions relief about to unlock ~$100B in frozen assets; economy contracted under sanctions; inflation declining; oil exports set to increase; population of 80 million.\n"
        "- Strategic assets: Regional military power, ballistic missile program, Revolutionary Guards (IRGC) and Quds Force, proxy network across Middle East, significant oil/gas reserves.\n"
        "- 2016 context: JCPOA Implementation Day January 16, 2016 — sanctions lifted, prisoners exchanged; Saudi diplomatic break; positioning to increase oil exports; Rouhani seeking economic dividends from deal."
    ),
    "ISR": (
        "[NATION BRIEF — Israel]\n"
        "- Political landscape: PM Benjamin Netanyahu leading right-wing coalition; settlement expansion continuing; relations with Obama administration strained over Iran deal.\n"
        "- Key challenges: Wave of lone-wolf Palestinian stabbing attacks ('Knife Intifada' since October 2015), Gaza blockade tensions, internal divisions over settlements, BDS movement growing.\n"
        "- Regional tensions: Strongly opposed JCPOA Iran deal; monitoring Hezbollah and Iran in Syria; quiet coordination with Gulf Arab states against Iran; periodic Gaza escalations.\n"
        "- Economic situation: Strong tech-driven economy (~2.5% growth), low unemployment, but high cost of living and inequality; natural gas discoveries (Leviathan field).\n"
        "- Strategic assets: Qualitative military edge in region, undeclared nuclear arsenal (~80 warheads), Iron Dome missile defense, elite intelligence services (Mossad, Shin Bet), US $3B annual military aid.\n"
        "- 2016 context: Knife Intifada continuing; Netanyahu lobbying against Iran deal; Syrian civil war on doorstep with Hezbollah and Iran presence; UN Resolution 2334 on settlements will come later in 2016."
    ),
    "PAK": (
        "[NATION BRIEF — Pakistan]\n"
        "- Political landscape: PM Nawaz Sharif (PML-N) governing; military under Gen. Raheel Sharif maintaining significant influence; civil-military tensions over foreign policy and counterterrorism.\n"
        "- Key challenges: Terrorism (TTP, sectarian groups), endemic corruption, energy crisis with chronic power shortages, poverty, education deficit, Balochistan insurgency.\n"
        "- Regional tensions: Complex relationship with Afghanistan and Taliban; India tensions spiking after Pathankot attack (January 2016); China-Pakistan Economic Corridor (CPEC) developing; nuclear arsenal growing.\n"
        "- Economic situation: GDP growth around 4.2%, IMF program improving macroeconomic stability, but structural issues persist; CPEC investment promising $46B in infrastructure.\n"
        "- Strategic assets: Nuclear arsenal (~130 warheads, fastest-growing), 650,000 active military, strategic location between South and Central Asia, intelligence services (ISI).\n"
        "- 2016 context: National Action Plan against terrorism after 2014 Peshawar school massacre; Zarb-e-Azb military operation in tribal areas; Pathankot attack January 2 threatens India-Pakistan dialogue."
    ),
    "KOR": (
        "[NATION BRIEF — South Korea]\n"
        "- Political landscape: President Park Geun-hye (Saenuri Party) in office; political landscape stable but growing discontent over economic inequality and chaebol dominance.\n"
        "- Key challenges: North Korean nuclear threat, aging population, youth unemployment ('Hell Joseon' sentiment), chaebol reform needed, MERS outbreak aftermath from 2015.\n"
        "- Regional tensions: North Korea's 4th nuclear test on January 6, 2016 heightening security concerns; THAAD missile defense deployment under discussion angering China; comfort women deal with Japan.\n"
        "- Economic situation: 11th largest economy, ~2.6% growth, export-dependent with Samsung/Hyundai dominant, low inflation, household debt rising.\n"
        "- Strategic assets: Modern military (625,000 active), US alliance with 28,500 troops stationed, advanced defense industry, top-tier shipbuilding, semiconductor dominance.\n"
        "- 2016 context: North Korea's January 6 nuclear test triggers emergency response; Kaesong Industrial Complex closure imminent; THAAD negotiations with US accelerating; Park scandal will erupt later in 2016."
    ),
    "PRK": (
        "[NATION BRIEF — North Korea]\n"
        "- Political landscape: Supreme Leader Kim Jong-un consolidating power through purges including execution of uncle Jang Song-thaek (2013); cult of personality maintained.\n"
        "- Key challenges: International isolation, chronic food insecurity, decrepit infrastructure, human rights abuses documented by UN Commission of Inquiry (2014), sanctions pressure.\n"
        "- Regional tensions: Conducted 4th nuclear test on January 6, 2016 (claimed hydrogen bomb); provocative missile launches; threatening rhetoric toward South Korea and US; Six-Party Talks defunct.\n"
        "- Economic situation: Command economy heavily dependent on China for trade and aid; black markets growing; sanctions limiting foreign exchange; GDP estimated under $30B.\n"
        "- Strategic assets: Nuclear weapons program (est. 10-20 warheads), ballistic missile development (Musudan, KN-08), 1.2 million active military, massive artillery aimed at Seoul, cyber warfare capabilities.\n"
        "- 2016 context: January 6 nuclear test dominates headlines; preparing satellite launch (February 2016); 7th Workers' Party Congress planned for May 2016 (first since 1980); UN Security Council pursuing new sanctions."
    ),
    "UKR": (
        "[NATION BRIEF — Ukraine]\n"
        "- Political landscape: President Petro Poroshenko and PM Arseniy Yatsenyuk governing uneasily; reform fatigue and corruption scandals; Maidan revolution promises partially unfulfilled.\n"
        "- Key challenges: War in Donbass (over 9,000 dead), Crimea annexed by Russia (2014), massive internal displacement (~1.5M), corruption endemic, economic collapse.\n"
        "- Regional tensions: Frontline of Russia-West confrontation; Minsk II ceasefire largely holding but no political resolution; energy dependence on Russia; EU Association Agreement being implemented.\n"
        "- Economic situation: GDP contracted ~9.9% in 2015, currency lost two-thirds of value, inflation ~43%, IMF bailout program with strict conditions, poverty increasing sharply.\n"
        "- Strategic assets: Strategic location between Russia and EU, significant agricultural potential (breadbasket of Europe), educated workforce, defense industry legacy, gas transit infrastructure.\n"
        "- 2016 context: EU visa liberalization process advancing; trade provisions of EU Association Agreement entering force January 1, 2016; Russia retaliating with trade embargo; Donbass conflict at stalemate."
    ),
    "EGY": (
        "[NATION BRIEF — Egypt]\n"
        "- Political landscape: President Abdel Fattah el-Sisi consolidating authoritarian rule after 2013 military coup; Muslim Brotherhood crushed; mass political imprisonments.\n"
        "- Key challenges: Sinai insurgency (ISIS affiliate Wilayat Sinai), human rights crackdown, youth unemployment, water security (Ethiopian GERD dam dispute), press freedom eliminated.\n"
        "- Regional tensions: Sinai insurgency including downing of Russian Metrojet Flight 9268 (October 2015); Libya instability on western border; mediating in Palestinian affairs; supporting Haftar in Libya.\n"
        "- Economic situation: Growth ~4.2% but unsustainable subsidy regime, currency overvaluation, foreign reserves declining, tourism devastated by terrorism and Russian flight ban.\n"
        "- Strategic assets: Largest Arab military, Suez Canal (expanded August 2015), US military aid (~$1.3B/year), strategic location, diplomatic weight as most populous Arab state.\n"
        "- 2016 context: Italian researcher Giulio Regeni disappeared January 25, 2016 (found murdered); new Suez Canal channel operating; currency devaluation looming; mega-projects to boost economy."
    ),
    "NGA": (
        "[NATION BRIEF — Nigeria]\n"
        "- Political landscape: President Muhammadu Buhari (APC) in first year after historic democratic transition from Goodluck Jonathan; anti-corruption drive launched.\n"
        "- Key challenges: Boko Haram insurgency in northeast (Chibok girls still missing), Niger Delta militancy threatening oil production, electricity crisis, endemic corruption.\n"
        "- Regional tensions: Leading multinational force against Boko Haram; tensions in oil-rich Niger Delta; competition with South Africa for continental leadership; Lake Chad humanitarian crisis.\n"
        "- Economic situation: Africa's largest economy but oil price crash devastating revenues (oil = 70% government income); naira under pressure; inflation rising; diversification urgently needed.\n"
        "- Strategic assets: Largest population in Africa (~180M), largest African economy, significant oil reserves, regional military power (ECOWAS leadership), large diaspora.\n"
        "- 2016 context: Buhari's anti-corruption campaign targeting predecessor's allies; Boko Haram weakened but still deadly; fuel shortages; budget delayed by oil revenue shortfall; Niger Delta Avengers emerging."
    ),
    "ZAF": (
        "[NATION BRIEF — South Africa]\n"
        "- Political landscape: President Jacob Zuma (ANC) embroiled in scandals; 'Nkandla' homestead corruption ruling pending; #ZumaMustFall movement; opposition DA and EFF gaining ground.\n"
        "- Key challenges: Extreme inequality (Gini coefficient among world's highest), 25% unemployment, electricity load-shedding crisis (Eskom), violent crime, xenophobic attacks.\n"
        "- Regional tensions: Diplomatic heavyweight in African Union; mediating in regional conflicts; hosting ICC-wanted Omar al-Bashir controversy in 2015; BRICS membership.\n"
        "- Economic situation: Near-recession with growth under 1.3%, rand at record lows, ratings downgrade threat, mining sector struggling, structural reform paralysis.\n"
        "- Strategic assets: Africa's most industrialized economy, advanced financial sector, strategic minerals (platinum, gold, chrome), strong judiciary and constitution, continental diplomatic weight.\n"
        "- 2016 context: Zuma's finance minister reshuffle in December 2015 caused rand crash; Constitutional Court Nkandla ruling coming (March 2016); student #FeesMustFall protests; drought affecting agriculture."
    ),

    # ────────────────────────── ALL OTHER COUNTRIES ──────────────────────────
    "AFG": (
        "[NATION BRIEF — Afghanistan]\n"
        "- Political landscape: President Ashraf Ghani in fragile national unity government with CEO Abdullah Abdullah; Taliban insurgency intensifying after NATO combat mission ended 2014.\n"
        "- Key challenges: Taliban controlling or contesting large swathes of territory, ISIS-Khorasan emerging, opium production at record levels, weak governance and corruption.\n"
        "- Regional tensions: Pakistan border tensions, Taliban safe havens in Pakistan, India-Pakistan rivalry playing out in Afghanistan, reduced US/NATO troop presence (~13,000 remaining).\n"
        "- Economic situation: One of the world's poorest countries, heavily aid-dependent, GDP ~$20B, unemployment widespread, capital flight as foreign forces withdraw."
    ),
    "AGO": (
        "[NATION BRIEF — Angola]\n"
        "- Political landscape: President Jose Eduardo dos Santos in power since 1979; MPLA one-party dominance; civil war ended 2002 but political freedoms limited.\n"
        "- Key challenges: Oil price collapse devastating economy (oil = 95% exports), extreme inequality despite oil wealth, press freedom restrictions, corruption.\n"
        "- Economic situation: GDP growth crashed from 4.8% to near-zero as oil revenues collapsed; kwanza devaluation; foreign reserves depleted; IMF assistance being considered."
    ),
    "ARE": (
        "[NATION BRIEF — United Arab Emirates]\n"
        "- Political landscape: Federation of seven emirates led by Abu Dhabi's Sheikh Khalifa bin Zayed (incapacitated; de facto rule by Crown Prince Mohammed bin Zayed); Dubai as commercial hub.\n"
        "- Key challenges: Oil price decline affecting Abu Dhabi revenues, diversification through Dubai model, labor rights concerns for migrant workers, regional instability.\n"
        "- Regional tensions: Participating in Saudi-led Yemen coalition, strong anti-Iran stance, supporting Haftar in Libya, part of anti-ISIS coalition.\n"
        "- Economic situation: Diversified by Gulf standards; Dubai's tourism, finance, and logistics sectors growing; Abu Dhabi oil wealth providing fiscal buffer; Expo 2020 preparations."
    ),
    "ARG": (
        "[NATION BRIEF — Argentina]\n"
        "- Political landscape: President Mauricio Macri (Cambiemos) inaugurated December 10, 2015, ending 12 years of Kirchnerism; promising market-friendly reforms and international reengagement.\n"
        "- Key challenges: Currency controls (cepo cambiario) being dismantled, inflation above 25%, holdout creditor dispute ('vulture funds'), drug trafficking, poverty at ~30%.\n"
        "- Economic situation: Macri immediately devalued peso by ~40%, lifted capital controls, cut export taxes; seeking to resolve debt holdout crisis and attract investment; GDP stagnant.\n"
        "- Regional tensions: Falklands/Malvinas sovereignty claim; shifting away from Kirchner-era alliances with Venezuela; rejoining Western-oriented economic policies."
    ),
    "ARM": (
        "[NATION BRIEF — Armenia]\n"
        "- Political landscape: President Serzh Sargsyan (Republican Party); constitutional referendum in December 2015 approved shift to parliamentary system; opposition alleging power consolidation.\n"
        "- Key challenges: Nagorno-Karabakh frozen conflict with Azerbaijan, economic stagnation, emigration (population declining), Russian dependence, blockaded borders with Turkey and Azerbaijan.\n"
        "- Regional tensions: Nagorno-Karabakh Line of Contact incidents increasing; member of Russian-led CSTO and Eurasian Economic Union; Turkish border closed since 1993.\n"
        "- Economic situation: Small economy (~$10.5B GDP), remittance-dependent, hit by Russian recession reducing remittances; mining sector important; poverty around 30%."
    ),
    "AUS": (
        "[NATION BRIEF — Australia]\n"
        "- Political landscape: PM Malcolm Turnbull (Liberal) took over from Tony Abbott in September 2015 leadership spill; promising innovation-focused agenda.\n"
        "- Key challenges: End of mining boom, housing affordability crisis in Sydney/Melbourne, asylum seeker policy (offshore detention controversy), climate change impacts on Great Barrier Reef.\n"
        "- Regional tensions: Balancing economic ties with China against security alliance with US; contributing to anti-ISIS coalition; South China Sea freedom of navigation; Five Eyes member.\n"
        "- Economic situation: 25th consecutive year without recession, transitioning from mining to services, GDP growth ~2.4%, unemployment around 6%, terms of trade declining."
    ),
    "AUT": (
        "[NATION BRIEF — Austria]\n"
        "- Political landscape: Coalition government (SPO-OVP) under Chancellor Werner Faymann; far-right FPO surging in polls over refugee crisis; presidential election upcoming.\n"
        "- Key challenges: Refugee influx (90,000 asylum applications in 2015 for population of 8.7M), border controls reimposed, rising anti-immigration sentiment.\n"
        "- Economic situation: Stable economy with ~1% growth, well-developed welfare state, banking sector exposed to Eastern Europe, tourism important sector.\n"
        "- Regional tensions: Key transit country on Balkan refugee route; tensions with Hungary over border management; Brenner Pass border controls with Italy being discussed."
    ),
    "AZE": (
        "[NATION BRIEF — Azerbaijan]\n"
        "- Political landscape: President Ilham Aliyev in authoritarian rule since 2003; crackdown on civil society, journalists, and opposition activists intensified.\n"
        "- Key challenges: Oil price collapse devastating petro-state economy, manat devaluation, Nagorno-Karabakh conflict with Armenia, human rights deterioration.\n"
        "- Economic situation: Manat lost half its value in 2015 devaluations; oil revenues (90% of exports) collapsing; sovereign wealth fund (SOFAZ) being drawn down; banking crisis emerging.\n"
        "- Regional tensions: Nagorno-Karabakh ceasefire line increasingly volatile; energy corridor to Europe (BTC pipeline, TANAP); balancing Russia, Turkey, and Iran relations."
    ),
    "BDI": (
        "[NATION BRIEF — Burundi]\n"
        "- Political landscape: President Pierre Nkurunziza seized controversial third term in July 2015 despite constitutional limits; failed coup attempt; mass violence and repression.\n"
        "- Key challenges: Political crisis triggering humanitarian emergency, over 200,000 refugees fled, extrajudicial killings, risk of ethnic violence (Hutu-Tutsi), media shut down.\n"
        "- Regional tensions: Tensions with Rwanda (accused of supporting rebels), East African Community mediation failing, AU peacekeeping force rejected by Nkurunziza.\n"
        "- Economic situation: One of the world's poorest countries, aid-dependent, economic collapse as donors suspend aid over political crisis."
    ),
    "BEL": (
        "[NATION BRIEF — Belgium]\n"
        "- Political landscape: PM Charles Michel (MR) leading center-right coalition; heightened security after November 2015 Brussels lockdown linked to Paris attacks; Molenbeek under scrutiny.\n"
        "- Key challenges: Terrorism threat (Paris attackers had Belgian connections), linguistic community divisions (Flemish-Walloon), radicalization in Brussels neighborhoods.\n"
        "- Economic situation: Moderate growth (~1.4%), high public debt (~106% GDP), complex federal structure raising governance costs; NATO and EU headquarters host.\n"
        "- Regional tensions: Heart of EU institutions, Belgium increasingly focused on domestic security; Salah Abdeslam (Paris attacks suspect) being hunted in Brussels as of January 2016."
    ),
    "BEN": (
        "[NATION BRIEF — Benin]\n"
        "- Political landscape: President Thomas Boni Yayi completing second term; presidential election scheduled for March 2016; democratic tradition relatively strong for region.\n"
        "- Key challenges: Poverty (one of world's least developed countries), infrastructure deficit, cotton-dependent agriculture vulnerable to commodity prices, corruption.\n"
        "- Economic situation: GDP growth ~5%, heavily dependent on trade with Nigeria and cotton exports; port of Cotonou important for regional trade; informal economy dominant."
    ),
    "BFA": (
        "[NATION BRIEF — Burkina Faso]\n"
        "- Political landscape: President Roch Marc Christian Kabore just elected November 2015 in first democratic transition after October 2014 popular uprising ousted Blaise Compaore.\n"
        "- Key challenges: Terrorism from Sahel jihadist groups (AQIM, Ansar Dine), extreme poverty, food insecurity, gold mining governance; hotel attack in Ouagadougou January 15, 2016.\n"
        "- Economic situation: Low-income country with ~4% growth; gold and cotton main exports; heavily aid-dependent; one of the youngest populations in the world.\n"
        "- Regional tensions: Jihadist threat spreading from Mali; part of G5 Sahel security cooperation; French military presence (Operation Barkhane)."
    ),
    "BGD": (
        "[NATION BRIEF — Bangladesh]\n"
        "- Political landscape: PM Sheikh Hasina (Awami League) governing firmly after controversial 2014 elections boycotted by opposition; crackdown on Islamist groups and opposition BNP.\n"
        "- Key challenges: Garment factory safety (post-Rana Plaza 2013), climate change vulnerability (sea level rise), overpopulation, Islamist extremism rising, Rohingya refugee influx.\n"
        "- Economic situation: Strong GDP growth (~6.5%), garment exports driving economy (80% of exports), remittances important, improving human development indicators.\n"
        "- Regional tensions: Rohingya crisis at Myanmar border, tensions with Myanmar, close ties with India, China investing in infrastructure."
    ),
    "BGR": (
        "[NATION BRIEF — Bulgaria]\n"
        "- Political landscape: PM Boyko Borisov (GERB) leading coalition; EU's poorest member state struggling with corruption and judicial reform; refugee pressure on Turkish border.\n"
        "- Key challenges: Population decline (emigration and low birth rate), corruption, organized crime, Roma minority marginalization, energy dependence on Russia.\n"
        "- Economic situation: Modest growth (~3%), low wages (EU's lowest), currency board pegged to euro, fiscal discipline maintained, EU funds important for development."
    ),
    "BHS": (
        "[NATION BRIEF — Bahamas]\n"
        "- Political landscape: PM Perry Christie (PLP); archipelagic nation heavily dependent on tourism and financial services; democratic governance stable.\n"
        "- Key challenges: Drug trafficking transit route, illegal immigration from Haiti, vulnerability to hurricanes, economic dependence on US tourism, high cost of living.\n"
        "- Economic situation: Upper-middle-income country, GDP growth ~1%, tourism (60% GDP) and offshore banking driving economy; national debt rising."
    ),
    "BLR": (
        "[NATION BRIEF — Belarus]\n"
        "- Political landscape: President Alexander Lukashenko in power since 1994 ('Europe's last dictator'); released political prisoners in August 2015 leading to partial EU sanctions relief.\n"
        "- Key challenges: Authoritarian governance, economic dependence on Russia, limited diversification, brain drain of educated youth, human rights concerns.\n"
        "- Economic situation: GDP contracting (~-3.8%), heavily subsidized by Russian energy discounts, state-dominated economy, inflation concerns, currency instability.\n"
        "- Regional tensions: Mediating role in Ukraine conflict (Minsk agreements hosted in Belarus); balancing between Russia and cautious EU reengagement; member of Eurasian Economic Union."
    ),
    "BLZ": (
        "[NATION BRIEF — Belize]\n"
        "- Political landscape: PM Dean Barrow (UDP) governing; small Central American nation; democratic institutions functioning; territorial dispute with Guatemala ongoing.\n"
        "- Key challenges: Drug trafficking transit point, high violent crime rate, poverty, vulnerability to hurricanes, limited economic diversification, debt burden.\n"
        "- Economic situation: Small economy dependent on tourism, agriculture (sugar, citrus, bananas), and services; GDP growth ~1%; public debt above 75% GDP."
    ),
    "BOL": (
        "[NATION BRIEF — Bolivia]\n"
        "- Political landscape: President Evo Morales (MAS) in power since 2006; referendum on allowing fourth term scheduled for February 2016; indigenous rights agenda.\n"
        "- Key challenges: Poverty despite improvements, coca/cocaine trade, infrastructure gaps, dependence on gas exports, water scarcity in some regions.\n"
        "- Economic situation: Strong growth (~4.8%) driven by natural gas exports, significant poverty reduction under Morales, but commodities downturn threatening fiscal stability.\n"
        "- Regional tensions: Landlocked; long-standing maritime dispute with Chile at ICJ; aligned with Venezuela and Cuba in ALBA bloc; tense relations with US after DEA expulsion."
    ),
    "BWA": (
        "[NATION BRIEF — Botswana]\n"
        "- Political landscape: President Ian Khama (BDP); one of Africa's most stable democracies; BDP in power since independence 1966; good governance reputation.\n"
        "- Key challenges: HIV/AIDS prevalence among world's highest (~22%), economic dependence on diamonds, income inequality, unemployment especially among youth, drought.\n"
        "- Economic situation: Upper-middle-income country, diamond exports (70-80% of export earnings), growth slowing to ~3% as diamond demand weakens; Debswana partnership with De Beers."
    ),
    "CAF": (
        "[NATION BRIEF — Central African Republic]\n"
        "- Political landscape: Transitional government after 2013 Seleka coup and anti-Balaka reprisals; presidential elections held December 2015/February 2016 runoff pending.\n"
        "- Key challenges: Ongoing sectarian violence between Muslim Seleka and Christian anti-Balaka militias, mass displacement (~1M), state collapse outside capital, humanitarian crisis.\n"
        "- Regional tensions: UN peacekeeping mission MINUSCA deployed (~12,000 troops); French forces (Sangaris) withdrawing; regional spillover of conflict; natural resources fueling conflict.\n"
        "- Economic situation: One of world's poorest countries, GDP under $2B, diamond and timber resources exploited by armed groups, infrastructure virtually nonexistent outside Bangui."
    ),
    "CAN": (
        "[NATION BRIEF — Canada]\n"
        "- Political landscape: PM Justin Trudeau (Liberal) newly elected October 2015 with majority government; promising progressive agenda, reconciliation with Indigenous peoples, and climate action.\n"
        "- Key challenges: Oil price collapse hitting Alberta hard, Indigenous reconciliation (Truth and Reconciliation Commission report 2015), housing costs in Vancouver/Toronto, refugee resettlement.\n"
        "- Economic situation: GDP growth slowing to ~1% due to oil price crash; two-speed economy (struggling Alberta vs. growing Ontario/Quebec); Canadian dollar at 12-year low.\n"
        "- Regional tensions: Close US ally (NATO, Five Eyes, NORAD); committed to resettling 25,000 Syrian refugees; withdrawing fighter jets from anti-ISIS combat mission."
    ),
    "CHE": (
        "[NATION BRIEF — Switzerland]\n"
        "- Political landscape: Federal Council consensus government; direct democracy system; 2014 immigration initiative complicating EU relations; SVP (right-wing populist) largest party.\n"
        "- Key challenges: Managing immigration quotas vs. EU bilateral agreements, strong franc hurting exporters, banking secrecy under international pressure, aging population.\n"
        "- Economic situation: Wealthy nation (~$80K GDP per capita), SNB maintaining negative interest rates after January 2015 franc shock; pharmaceuticals, banking, and precision manufacturing dominant.\n"
        "- Regional tensions: Neutral status; hosting international organizations (UN Geneva, ICRC); negotiating with EU on immigration framework agreement."
    ),
    "CHL": (
        "[NATION BRIEF — Chile]\n"
        "- Political landscape: President Michelle Bachelet (PS) pushing education and tax reforms; approval ratings declining; corruption scandals (Caval affair involving her son).\n"
        "- Key challenges: Education system reform demands, copper price decline, income inequality despite prosperity, Mapuche indigenous tensions in south, earthquake vulnerability.\n"
        "- Economic situation: Copper price slump slowing growth to ~2.1%; inflation above target; peso weakening; Chile remains Latin America's most credit-worthy economy.\n"
        "- Regional tensions: Maritime border dispute with Bolivia at ICJ; Pacific Alliance member; TPP signatory; stable relations with neighbors."
    ),
    "CIV": (
        "[NATION BRIEF — Cote d'Ivoire]\n"
        "- Political landscape: President Alassane Ouattara re-elected October 2015; post-civil war recovery since 2011; reconciliation process ongoing but incomplete.\n"
        "- Key challenges: Post-conflict reconciliation (2010-2011 crisis), youth unemployment, cocoa sector governance, northern-southern divide, security sector reform.\n"
        "- Economic situation: Fastest-growing economies in West Africa (~8.5% growth); world's largest cocoa producer; infrastructure investment program; Abidjan as regional commercial hub.\n"
        "- Regional tensions: UN peacekeeping mission (UNOCI) drawing down; terrorist attack on Grand-Bassam beach resort will occur in March 2016; French military presence maintained."
    ),
    "CMR": (
        "[NATION BRIEF — Cameroon]\n"
        "- Political landscape: President Paul Biya in power since 1982; authoritarian governance; Anglophone minority grievances growing in northwest and southwest regions.\n"
        "- Key challenges: Boko Haram attacks in Far North region, Anglophone crisis brewing, poverty, corruption, aging autocratic leadership, limited press freedom.\n"
        "- Economic situation: Central Africa's largest economy, oil production declining, agriculture (cocoa, coffee) important, growth ~5.5%; planning for 2019 Africa Cup of Nations.\n"
        "- Regional tensions: Frontline state against Boko Haram with military operations in Far North; Central African refugee influx; maritime border dispute with Nigeria resolved at ICJ."
    ),
    "COD": (
        "[NATION BRIEF — Democratic Republic of the Congo]\n"
        "- Political landscape: President Joseph Kabila approaching constitutional two-term limit (2016); widespread fears of attempt to stay in power; opposition mobilizing.\n"
        "- Key challenges: Eastern Congo armed groups (M23 defeated but ADF, FDLR active), Kabila third-term crisis, massive humanitarian needs, Ebola preparedness, mineral exploitation.\n"
        "- Regional tensions: UN peacekeeping mission MONUSCO (~20,000 troops, largest in world); tensions with Rwanda and Uganda over eastern Congo; Burundi crisis spillover.\n"
        "- Economic situation: Rich in minerals (cobalt, coltan, copper, diamonds) but one of world's poorest countries; growth ~6.9%; Chinese mining investments; infrastructure devastated."
    ),
    "COG": (
        "[NATION BRIEF — Republic of the Congo]\n"
        "- Political landscape: President Denis Sassou Nguesso engineered constitutional referendum in October 2015 to remove term limits; planning re-election; opposition crackdown.\n"
        "- Key challenges: Oil dependence (90% exports), post-referendum tensions, poverty despite oil wealth, lack of diversification, youth unemployment.\n"
        "- Economic situation: Oil-dependent economy hit by price crash; growth slowing sharply; Brazzaville arms depot explosion in March 2012 reconstruction ongoing; debt rising."
    ),
    "COL": (
        "[NATION BRIEF — Colombia]\n"
        "- Political landscape: President Juan Manuel Santos pursuing historic peace negotiations with FARC guerrillas in Havana; ELN talks also being explored; public opinion divided.\n"
        "- Key challenges: FARC peace process at critical stage, coca cultivation rising, displaced population (~6.9M, world's largest), paramilitary successor groups (BACRIM).\n"
        "- Economic situation: Growth slowing to ~3.1% from oil price decline (oil = major export); peso depreciating sharply; inflation rising; Pacific Alliance member.\n"
        "- Regional tensions: Venezuelan border tensions (border closed August-December 2015); US partner in counter-narcotics (Plan Colombia legacy); Ecuador border management."
    ),
    "CRI": (
        "[NATION BRIEF — Costa Rica]\n"
        "- Political landscape: President Luis Guillermo Solis (PAC) governing with minority in legislature; corruption investigations into predecessors; democratic tradition strong.\n"
        "- Key challenges: Fiscal deficit growing, Cuban migrant crisis (stranded migrants on route to US), drug trafficking, inequality rising, infrastructure gaps.\n"
        "- Economic situation: Stable middle-income economy, ~3.7% growth, ecotourism and tech (Intel) important, but fiscal deficit reaching 6% GDP; no military since 1948."
    ),
    "CUB": (
        "[NATION BRIEF — Cuba]\n"
        "- Political landscape: President Raul Castro leading gradual reforms; historic US-Cuba normalization underway since December 2014; Obama planning visit (March 2016).\n"
        "- Key challenges: Economic reform pace slow, dual currency system, crumbling infrastructure, internet access limited, political freedoms restricted, emigration pressure.\n"
        "- Economic situation: GDP growth ~4.3% but from low base; tourism booming due to US normalization; remittances important; state still controls most economy; Venezuela oil subsidies declining.\n"
        "- Regional tensions: Hosting FARC peace talks; improving US relations but embargo largely intact pending Congress; declining Venezuelan support as Maduro regime struggles."
    ),
    "CZE": (
        "[NATION BRIEF — Czech Republic]\n"
        "- Political landscape: PM Bohuslav Sobotka (CSSD) leading coalition; President Milos Zeman making controversial pro-Russian and anti-refugee statements; strong anti-immigration sentiment.\n"
        "- Key challenges: Refusing EU refugee quotas, Zeman's divisive presidency, brain drain to Western Europe, housing shortage in Prague, cybersecurity threats.\n"
        "- Economic situation: Strong performer with ~4.5% GDP growth, low unemployment (~4.5%), automotive industry (Skoda) driving exports, resisting euro adoption."
    ),
    "DJI": (
        "[NATION BRIEF — Djibouti]\n"
        "- Political landscape: President Ismail Omar Guelleh in power since 1999; authoritarian rule; strategic location at Bab el-Mandeb Strait attracting foreign military bases.\n"
        "- Key challenges: Extreme poverty, water scarcity, limited arable land, youth unemployment, one-party dominance, press freedom restricted.\n"
        "- Economic situation: Strategic rent economy from foreign military bases; US (Camp Lemonnier), France, Japan bases present; China constructing first overseas base; port expansion underway.\n"
        "- Regional tensions: Ethiopia-Djibouti railway under construction; monitoring Yemen conflict across strait; hosting refugees from Somalia and Eritrea."
    ),
    "DNK": (
        "[NATION BRIEF — Denmark]\n"
        "- Political landscape: PM Lars Lokke Rasmussen (Venstre) leading minority government with Danish People's Party support; anti-immigration policies tightening.\n"
        "- Key challenges: Refugee crisis response, integration of immigrants, welfare state sustainability, Greenland self-governance aspirations, Arctic strategy.\n"
        "- Economic situation: Wealthy economy (~$53K GDP per capita), ~1.2% growth, strong welfare state, low unemployment; passed controversial law allowing seizure of asylum seekers' valuables."
    ),
    "DOM": (
        "[NATION BRIEF — Dominican Republic]\n"
        "- Political landscape: President Danilo Medina (PLD) preparing for May 2016 re-election after constitutional amendment; popular for economic management.\n"
        "- Key challenges: Haitian immigration tensions, statelessness crisis affecting Dominican-born Haitians, corruption, inequality, drug trafficking transit.\n"
        "- Economic situation: Fastest-growing economy in Latin America/Caribbean (~7% growth), tourism and remittances driving growth; mining (Pueblo Viejo gold mine) contributing."
    ),
    "DZA": (
        "[NATION BRIEF — Algeria]\n"
        "- Political landscape: President Abdelaziz Bouteflika in poor health (rarely seen publicly since 2013 stroke); power exercised by military/security establishment ('le pouvoir').\n"
        "- Key challenges: Youth unemployment, housing crisis, governance opacity, Bouteflika succession question, terrorism risk from Sahel instability, south Libya spillover.\n"
        "- Economic situation: Oil and gas revenues (95% exports) collapsing; foreign reserves declining rapidly; budget deficit; resistance to IMF-style reforms; large hydrocarbon reserves.\n"
        "- Regional tensions: Rivalry with Morocco over Western Sahara; border security concerns from Libya and Mali; In Amenas gas plant attack (2013) legacy; not joining regional military operations."
    ),
    "ECU": (
        "[NATION BRIEF — Ecuador]\n"
        "- Political landscape: President Rafael Correa (PAIS Alliance) in power since 2007; leftist agenda, citizens' revolution; constitutional amendment allowing indefinite re-election passed 2015.\n"
        "- Key challenges: Oil price drop devastating economy (oil = 50% exports), dollarized economy limiting policy tools, press freedom concerns, Julian Assange in London embassy.\n"
        "- Economic situation: GDP contracting as oil revenues collapse; dollarization preventing currency devaluation; Chinese loans filling financing gap; fiscal austerity needed."
    ),
    "ERI": (
        "[NATION BRIEF — Eritrea]\n"
        "- Political landscape: President Isaias Afwerki ruling since independence (1993) with no elections, no constitution implemented, no free press; often called 'Africa's North Korea.'\n"
        "- Key challenges: Indefinite military conscription driving mass emigration (one of top sources of Mediterranean migrants), extreme repression, poverty, isolation.\n"
        "- Economic situation: One of the poorest countries; mining (gold, copper) providing some revenue; remittances from diaspora crucial; UN Commission of Inquiry found crimes against humanity.\n"
        "- Regional tensions: Unresolved border conflict with Ethiopia; tense relations with Djibouti; UN sanctions for alleged support to Somali extremists; thousands fleeing monthly."
    ),
    "ESP": (
        "[NATION BRIEF — Spain]\n"
        "- Political landscape: PM Mariano Rajoy (PP) lost majority in December 2015 elections; Podemos and Ciudadanos disrupted two-party system; government formation crisis; Catalonia independence push.\n"
        "- Key challenges: Political fragmentation (no government can be formed), Catalonia secession movement, 20.9% unemployment (46% youth), austerity fatigue, corruption scandals.\n"
        "- Economic situation: Recovery from deep recession with ~3.2% growth, but unemployment still among EU's highest; housing market stabilizing; tourism sector strong.\n"
        "- Regional tensions: Catalonia declared independence roadmap in November 2015; Basque ETA ceasefire holding; managing migration from Morocco; Gibraltar dispute with UK."
    ),
    "EST": (
        "[NATION BRIEF — Estonia]\n"
        "- Political landscape: PM Taavi Roivas (Reform Party) leading coalition; digital governance pioneer (e-Residency program); strong Atlanticist and EU orientation.\n"
        "- Key challenges: Russian-speaking minority integration (25% of population), Russian hybrid warfare concerns, emigration, defense spending pressure from NATO commitment.\n"
        "- Economic situation: Small open economy, ~1.4% growth, eurozone member, strong IT sector, low public debt; transitioning from low-cost to innovation economy."
    ),
    "ETH": (
        "[NATION BRIEF — Ethiopia]\n"
        "- Political landscape: PM Hailemariam Desalegn (EPRDF) governing; ruling coalition won 100% of parliamentary seats in 2015; authoritarian developmental state model.\n"
        "- Key challenges: Oromo protests erupting since November 2015 over Addis Ababa master plan (land grabs), ethnic tensions, press freedom crackdown, drought emergency.\n"
        "- Economic situation: One of world's fastest-growing economies (~10% growth), but from low base; Grand Ethiopian Renaissance Dam (GERD) under construction; Chinese-funded infrastructure boom.\n"
        "- Regional tensions: Troops in Somalia (AMISOM peacekeeping), GERD dispute with Egypt and Sudan over Nile waters, hosting ~700,000 refugees (South Sudan, Eritrea, Somalia)."
    ),
    "FIN": (
        "[NATION BRIEF — Finland]\n"
        "- Political landscape: PM Juha Sipila (Centre Party) leading center-right government; implementing austerity and competitiveness reforms; social compact under strain.\n"
        "- Key challenges: Economic stagnation (Nokia decline, Russia sanctions impact, paper industry decline), asylum seeker influx (32,000 in 2015), aging population, competitiveness gap.\n"
        "- Economic situation: GDP growth near zero; recession in 2012-2014 lingering; tech sector rebuilding post-Nokia; forestry and engineering exports still important; eurozone member."
    ),
    "GAB": (
        "[NATION BRIEF — Gabon]\n"
        "- Political landscape: President Ali Bongo Ondimba succeeding his father who ruled 42 years; presidential election upcoming August 2016; opposition organizing.\n"
        "- Key challenges: Oil dependence, youth unemployment despite oil wealth, inequality, governance concerns, diversification need, declining oil production.\n"
        "- Economic situation: Upper-middle-income by African standards but highly unequal; oil revenues declining; timber and manganese also important; growth slowing to ~4%."
    ),
    "GEO": (
        "[NATION BRIEF — Georgia]\n"
        "- Political landscape: PM Irakli Garibashvili (Georgian Dream); EU Association Agreement signed, pro-Western orientation; Saakashvili-era UNM in opposition.\n"
        "- Key challenges: Russian occupation of Abkhazia and South Ossetia (20% of territory), NATO membership aspiration blocked by Russia, judicial reform, poverty.\n"
        "- Economic situation: Growth ~2.8%, hit by Russian recession reducing remittances and trade; tourism growing; lari depreciation; EU DCFTA being implemented.\n"
        "- Regional tensions: 'Borderization' by Russia in occupied territories; NATO aspirations without Membership Action Plan; transit role for Caucasus energy corridor (BTC, BTE pipelines)."
    ),
    "GHA": (
        "[NATION BRIEF — Ghana]\n"
        "- Political landscape: President John Mahama (NDC) facing December 2016 election; fiscal crisis and power outages ('dumsor') eroding support; opposition NPP strengthening.\n"
        "- Key challenges: Power crisis (chronic electricity shortages), fiscal deficit, public debt rising sharply, corruption, illegal mining (galamsey), Ebola preparedness.\n"
        "- Economic situation: Growth slowed to ~3.8% from double digits in 2011; IMF bailout program since 2015; cedi depreciating; oil production from Jubilee field helping; cocoa and gold exports."
    ),
    "GIN": (
        "[NATION BRIEF — Guinea]\n"
        "- Political landscape: President Alpha Conde re-elected October 2015 amid opposition protests; recovering from Ebola epidemic that killed ~2,500 Guineans.\n"
        "- Key challenges: Ebola aftermath (declared free in December 2015), extreme poverty, ethnic political tensions, mining governance, weak infrastructure.\n"
        "- Economic situation: Rich in bauxite (world's largest reserves) and iron ore but extremely poor; growth recovering to ~3.5% post-Ebola; Simandou iron ore project stalled."
    ),
    "GMB": (
        "[NATION BRIEF — Gambia]\n"
        "- Political landscape: President Yahya Jammeh in power since 1994 coup; increasingly erratic and authoritarian; declared Gambia an Islamic republic in 2015.\n"
        "- Key challenges: Authoritarian rule, human rights abuses, press freedom eliminated, poverty, youth emigration (many among Mediterranean boat migrants), HIV/AIDS.\n"
        "- Economic situation: Tiny economy dependent on tourism, groundnut exports, and remittances; one of Africa's smallest countries; re-export trade important."
    ),
    "GNB": (
        "[NATION BRIEF — Guinea-Bissau]\n"
        "- Political landscape: President Jose Mario Vaz and PM Carlos Correia in power but political instability chronic; military has staged multiple coups since independence.\n"
        "- Key challenges: Drug trafficking hub (Latin American cocaine transits through), political instability, extreme poverty, military interference in politics, cashew nut monoculture.\n"
        "- Economic situation: One of world's poorest countries, cashew nuts are primary export, heavily aid-dependent, limited infrastructure outside Bissau."
    ),
    "GNQ": (
        "[NATION BRIEF — Equatorial Guinea]\n"
        "- Political landscape: President Teodoro Obiang Nguema in power since 1979 (Africa's longest-serving leader); authoritarian rule, family dynasty, sham elections.\n"
        "- Key challenges: Extreme inequality despite oil wealth, oil production declining, no political freedom, corruption (Obiang family wealth), human rights abuses.\n"
        "- Economic situation: High GDP per capita from oil but vast majority live in poverty; oil production past peak; attempting to host international events for legitimacy."
    ),
    "GRC": (
        "[NATION BRIEF — Greece]\n"
        "- Political landscape: PM Alexis Tsipras (Syriza) won September 2015 snap election; implementing third bailout despite anti-austerity mandate; opposition weakened.\n"
        "- Key challenges: Debt crisis (debt ~175% GDP), third bailout implementation, refugee crisis (over 850,000 arrivals in 2015 via islands), 25% unemployment, brain drain.\n"
        "- Economic situation: GDP contracted ~0.2%, six years of depression wiped out 25% of GDP; capital controls since June 2015; banking sector fragile; tourism providing lifeline.\n"
        "- Regional tensions: Primary entry point for refugees into EU; tensions with Turkey over Aegean; Cyprus dispute; Macedonia naming dispute; NATO member despite economic crisis."
    ),
    "GTM": (
        "[NATION BRIEF — Guatemala]\n"
        "- Political landscape: President Jimmy Morales (FCN) just inaugurated January 14, 2016; comedian-turned-politician elected on anti-corruption wave after predecessor jailed.\n"
        "- Key challenges: Corruption, drug trafficking, gang violence (one of world's highest homicide rates), poverty (60%), malnutrition especially among indigenous Maya, impunity.\n"
        "- Economic situation: Central America's largest economy, ~4.1% growth, remittances from US (~10% GDP), coffee and textile exports; CICIG anti-corruption commission supported by UN."
    ),
    "GUY": (
        "[NATION BRIEF — Guyana]\n"
        "- Political landscape: President David Granger (APNU-AFC) took office May 2015, ending 23 years of PPP rule; ethnic politics (Afro-Guyanese vs Indo-Guyanese) still dominant.\n"
        "- Key challenges: Poverty, emigration (more Guyanese abroad than in country), ethnic tensions, infrastructure deficit, deforestation, drug trafficking transit.\n"
        "- Economic situation: Small economy dependent on sugar, rice, gold, and bauxite; ExxonMobil discovered massive offshore oil reserves (Liza field, 2015) — transformative potential."
    ),
    "HND": (
        "[NATION BRIEF — Honduras]\n"
        "- Political landscape: President Juan Orlando Hernandez (National Party); controversial re-election bid despite constitutional single-term limit; Berta Caceres environmental activism.\n"
        "- Key challenges: Among world's highest homicide rates, gang violence (MS-13, Barrio 18), drug trafficking, poverty (~65%), corruption, mass emigration to US.\n"
        "- Economic situation: Low-income country, ~3.6% growth, dependent on remittances (18% GDP) and maquila exports; coffee important; US aid tied to migration cooperation."
    ),
    "HRV": (
        "[NATION BRIEF — Croatia]\n"
        "- Political landscape: PM Tihomir Oreskovic newly appointed January 2016 as technocratic PM in HDZ-MOST coalition; political instability from fragmented parliament.\n"
        "- Key challenges: High unemployment (~16%), brain drain to Western EU, war legacy issues with Serbia, refugee transit route management, Adriatic tourism dependence.\n"
        "- Economic situation: EU's newest member (2013), emerging from six-year recession with ~1.6% growth; tourism driving recovery; public debt above 85% GDP; not yet in eurozone."
    ),
    "HTI": (
        "[NATION BRIEF — Haiti]\n"
        "- Political landscape: Electoral crisis; disputed October 2015 election results; President Michel Martelly's term expiring February 2016 without elected successor; UN stabilization mission MINUSTAH present.\n"
        "- Key challenges: Poorest country in Western Hemisphere, 2010 earthquake recovery still incomplete, cholera epidemic (UN-linked), deforestation, gang violence, political instability.\n"
        "- Economic situation: GDP per capita under $800, heavily dependent on remittances and international aid; garment assembly for US market; chronic food insecurity."
    ),
    "HUN": (
        "[NATION BRIEF — Hungary]\n"
        "- Political landscape: PM Viktor Orban (Fidesz) pursuing 'illiberal democracy'; built border fence against refugees in 2015; clashing with EU over rule of law and refugee quotas.\n"
        "- Key challenges: Rule of law concerns (media control, judicial independence), refugee policy confrontation with EU, Roma marginalization, brain drain, demographic decline.\n"
        "- Economic situation: Growth ~3.1%, manufacturing (automotive) strong, unemployment low but wages stagnant; Orban's economic nationalism including bank levies and utility price cuts.\n"
        "- Regional tensions: Blocking EU refugee quotas; close ties with Putin's Russia (Paks nuclear deal, South Stream); advocating for ethnic Hungarian minorities in neighbors."
    ),
    "IDN": (
        "[NATION BRIEF — Indonesia]\n"
        "- Political landscape: President Joko Widodo ('Jokowi') in second year; reformist agenda facing resistance from old-guard politicians and military; PDI-P coalition governing.\n"
        "- Key challenges: Deforestation and haze crisis (2015 fires worst in decades), terrorism (ISIS-linked groups), maritime security, Papua separatism, infrastructure deficit, corruption.\n"
        "- Economic situation: Southeast Asia's largest economy, ~4.9% growth, moderate reforms to attract FDI, infrastructure push, but commodity downturn hurting; rupiah under pressure.\n"
        "- Regional tensions: South China Sea (Natuna Islands tensions with China), ASEAN's largest member, counter-terrorism cooperation, executing drug traffickers despite international protests."
    ),
    "IRL": (
        "[NATION BRIEF — Ireland]\n"
        "- Political landscape: Taoiseach Enda Kenny (Fine Gael) in coalition with Labour; general election imminent (February 2016); Celtic Tiger recovery boosting government popularity.\n"
        "- Key challenges: Housing crisis and homelessness in Dublin, healthcare system strain, rural-urban divide, water charges controversy, Northern Ireland border post-Brexit concerns.\n"
        "- Economic situation: EU's fastest-growing economy (~26% GDP growth in 2015, partly statistical artifact from corporate relocations); tech multinationals' European hub; exited bailout in 2013."
    ),
    "IRQ": (
        "[NATION BRIEF — Iraq]\n"
        "- Political landscape: PM Haider al-Abadi leading fragile government; ISIS controlling Mosul and western Anbar; Shia-Sunni-Kurdish power-sharing under extreme strain.\n"
        "- Key challenges: ISIS insurgency (second-largest city Mosul under ISIS since June 2014), sectarian divisions, Kurdish autonomy push, Shia militia power, massive displacement (~3.3M IDPs).\n"
        "- Economic situation: Oil-dependent economy devastated by war and low oil prices; budget crisis; reconstruction needs enormous; southern oil fields still producing.\n"
        "- Regional tensions: US-led coalition conducting airstrikes; Iran-backed militias fighting ISIS alongside army; Kurdish Peshmerga holding frontlines; Turkey's unauthorized military presence in Bashiqa."
    ),
    "ITA": (
        "[NATION BRIEF — Italy]\n"
        "- Political landscape: PM Matteo Renzi (PD) pushing constitutional reform referendum; Five Star Movement rising in polls; anti-establishment sentiment growing.\n"
        "- Key challenges: Economic stagnation, banking crisis (€360B in non-performing loans), migration (170,000 Mediterranean arrivals in 2015), youth unemployment ~37%, mafia influence.\n"
        "- Economic situation: Third-largest eurozone economy but barely growing (~0.7%); public debt ~132% GDP; banking sector fragility; north-south divide persistent.\n"
        "- Regional tensions: Frontline of Mediterranean migration crisis (Libya route); NATO ally; Renzi clashing with EU over fiscal flexibility; same-sex civil unions debate."
    ),
    "JAM": (
        "[NATION BRIEF — Jamaica]\n"
        "- Political landscape: PM Portia Simpson-Miller (PNP) heading into February 2016 election; democratic governance stable; IMF program shaping economic policy.\n"
        "- Key challenges: High crime and gang violence, public debt (~125% GDP), poverty, brain drain (emigration), vulnerability to hurricanes, marijuana policy reform.\n"
        "- Economic situation: Slow growth (~1%), IMF Extended Fund Facility driving fiscal discipline, tourism and remittances as economic pillars; bauxite/alumina exports declining."
    ),
    "JOR": (
        "[NATION BRIEF — Jordan]\n"
        "- Political landscape: King Abdullah II ruling with appointed government; PM Abdullah Ensour; limited political reforms since Arab Spring; key Western ally in region.\n"
        "- Key challenges: Hosting ~650,000 Syrian refugees (1.3M total Syrians, huge burden for 9.5M population), water scarcity, unemployment, energy import dependence, ISIS threat.\n"
        "- Economic situation: Limited natural resources, growth ~2.4%, heavily dependent on foreign aid (especially US, Gulf), tourism hurt by regional instability; hosting Zaatari refugee camp.\n"
        "- Regional tensions: Border with Syria and Iraq; participating in anti-ISIS coalition; managing refugee burden; Palestine issue; close military cooperation with US."
    ),
    "KAZ": (
        "[NATION BRIEF — Kazakhstan]\n"
        "- Political landscape: President Nursultan Nazarbayev in power since 1989 (Soviet era); authoritarian stability; Astana as showcase capital; succession question unaddressed.\n"
        "- Key challenges: Oil price collapse hitting economy, tenge dramatically devalued August 2015, diversification from oil, corruption, political freedom absent, labor unrest.\n"
        "- Economic situation: Central Asia's largest economy; growth slowed to ~1.2% from oil crash; tenge lost 45% in 2015; major oil producer (Kashagan field finally starting); Chinese investment growing.\n"
        "- Regional tensions: Balancing between Russia and China; member of Eurasian Economic Union; hosting Syria peace talks in Astana; Baikonur Cosmodrome leased to Russia."
    ),
    "KEN": (
        "[NATION BRIEF — Kenya]\n"
        "- Political landscape: President Uhuru Kenyatta (Jubilee Alliance); ICC charges dropped in 2014; governance concerns but democratic institutions functioning; opposition CORD active.\n"
        "- Key challenges: Al-Shabaab terrorism (Garissa University attack April 2015, 148 dead), corruption, ethnic tensions, drought cycles, rapid urbanization, refugee hosting (Dadaab).\n"
        "- Economic situation: East Africa's economic hub, ~5.7% growth, mobile money (M-Pesa) success story, Standard Gauge Railway under construction (Chinese-funded), tourism recovering.\n"
        "- Regional tensions: Troops in Somalia (AMISOM, since 2011 against Al-Shabaab), hosting ~500,000 refugees (mostly Somali), Lake Turkana wind project, East African Community integration."
    ),
    "KHM": (
        "[NATION BRIEF — Cambodia]\n"
        "- Political landscape: PM Hun Sen (CPP) in power since 1985; crackdown on opposition CNRP intensifying; opposition leader Sam Rainsy in self-imposed exile.\n"
        "- Key challenges: Authoritarian backsliding, land grabbing, deforestation, garment worker rights, Khmer Rouge tribunal ongoing, extreme poverty in rural areas.\n"
        "- Economic situation: Growth ~7%, garment manufacturing and tourism driving economy; rice exports growing; Chinese investment and aid increasing; heavy dependence on foreign aid."
    ),
    "KWT": (
        "[NATION BRIEF — Kuwait]\n"
        "- Political landscape: Emir Sabah Al-Ahmad Al-Jaber Al-Sabah ruling; relatively open parliament for Gulf but recurring government-parliament tensions; Bidun stateless issue.\n"
        "- Key challenges: Oil price crash straining generous welfare state, diversification needed, Bidun (stateless residents) rights, ISIS attack on Shia mosque in June 2015, labor rights.\n"
        "- Economic situation: Oil-rich with massive sovereign wealth fund (KIA, ~$600B); budget moving into deficit from oil crash; 6% of world's proven oil reserves."
    ),
    "LBN": (
        "[NATION BRIEF — Lebanon]\n"
        "- Political landscape: Presidential vacuum since May 2014 (no agreement between March 14 and March 8 blocs); PM Tammam Salam heading caretaker government; parliament extending own mandate.\n"
        "- Key challenges: Syrian refugee crisis (~1.5M refugees for population of 4.5M), political paralysis, Hezbollah's dual role (party and militia), garbage crisis ('You Stink' movement), sectarian tensions.\n"
        "- Economic situation: Growth near zero, tourism devastated, banking sector under pressure, public debt ~140% GDP; infrastructure crumbling; Syrian refugees straining services.\n"
        "- Regional tensions: Hezbollah fighting in Syria for Assad; spillover bombings and kidnappings; Saudi-Iran rivalry playing out through Lebanese politics; Sunni radicalization in Tripoli/Sidon."
    ),
    "LBR": (
        "[NATION BRIEF — Liberia]\n"
        "- Political landscape: President Ellen Johnson Sirleaf (UP) in second term; post-Ebola recovery; UNMIL peacekeeping drawing down ahead of 2017 elections.\n"
        "- Key challenges: Ebola aftermath (4,800+ deaths, 2014-2015), rebuilding health system, poverty, unemployment, corruption, infrastructure devastated by civil wars.\n"
        "- Economic situation: Economy shrank ~0.7% due to Ebola and commodity price declines; iron ore and rubber exports struggling; heavily aid-dependent; development indicators among world's lowest."
    ),
    "LBY": (
        "[NATION BRIEF — Libya]\n"
        "- Political landscape: Two rival governments — UN-backed GNA (Tripoli) being formed under Fayez al-Sarraj, and House of Representatives (Tobruk) under Khalifa Haftar's influence; ISIS presence in Sirte.\n"
        "- Key challenges: State collapse since 2011, civil war between rival factions, ISIS controlling Sirte, migrant trafficking hub for Mediterranean crossings, oil infrastructure damaged.\n"
        "- Economic situation: Oil production crashed from 1.6M to ~400K barrels/day; economy in freefall; central bank reserves depleting; currency black market; hyperinflation in some areas.\n"
        "- Regional tensions: UN brokering Libyan Political Agreement (December 2015); Egypt and UAE backing Haftar; Turkey and Qatar backing Tripoli factions; weapons flowing to Sahel."
    ),
    "LKA": (
        "[NATION BRIEF — Sri Lanka]\n"
        "- Political landscape: President Maithripala Sirisena and PM Ranil Wickremesinghe in uneasy coalition after defeating Rajapaksa in 2015; reconciliation process after civil war.\n"
        "- Key challenges: Post-civil war reconciliation with Tamil minority, transitional justice, Chinese debt trap concerns (Hambantota port), political reform, religious extremism.\n"
        "- Economic situation: Growth ~4.8%, tourism recovering, tea and garment exports, but debt burden growing; EU GSP+ trade preferences being pursued; Chinese infrastructure loans."
    ),
    "LSO": (
        "[NATION BRIEF — Lesotho]\n"
        "- Political landscape: PM Pakalitha Mosisili in power after 2015 snap elections; political instability and military factionalism; SADC mediating political crisis.\n"
        "- Key challenges: HIV/AIDS prevalence among world's highest (~23%), poverty, political instability, complete economic dependence on South Africa, unemployment.\n"
        "- Economic situation: Tiny landlocked economy entirely surrounded by South Africa; diamond mining, garment exports, and water exports (Lesotho Highlands Water Project); heavily remittance-dependent."
    ),
    "LTU": (
        "[NATION BRIEF — Lithuania]\n"
        "- Political landscape: President Dalia Grybauskaite; PM Algirdas Butkevicius (Social Democrats); strong Euro-Atlantic orientation; adopted euro January 2015.\n"
        "- Key challenges: Russian security threat (Kaliningrad proximity), emigration (population dropped from 3.5M to 2.9M since independence), demographic decline, energy independence.\n"
        "- Economic situation: Growth ~1.8%, eurozone's newest member, building Klaipeda LNG terminal to reduce Russian gas dependence; IT sector growing."
    ),
    "LVA": (
        "[NATION BRIEF — Latvia]\n"
        "- Political landscape: PM Laimdota Straujuma (Unity) leading coalition; large Russian-speaking minority (~25%); strong NATO and EU orientation.\n"
        "- Key challenges: Russian-speaking minority integration, Russian hybrid warfare concerns, emigration and population decline, income inequality, banking sector (non-resident deposits).\n"
        "- Economic situation: Post-crisis recovery with ~2.7% growth; eurozone member since 2014; IT and logistics sectors; Riga as regional hub; EU structural funds important."
    ),
    "MAR": (
        "[NATION BRIEF — Morocco]\n"
        "- Political landscape: King Mohammed VI as executive monarch; PM Abdelilah Benkirane (PJD, moderate Islamist); relatively stable after limited Arab Spring reforms.\n"
        "- Key challenges: Youth unemployment, rural poverty, education quality, Western Sahara dispute, terrorism risk, irregular migration to Europe.\n"
        "- Economic situation: Growth ~4.5%, phosphate exports, agriculture, automotive and aerospace industry growing (Renault, Bombardier), tourism; Tangier Med port expanding.\n"
        "- Regional tensions: Western Sahara sovereignty dispute with Polisario Front (backed by Algeria); UN peacekeeping mission MINURSO; Morocco left African Union in 1984 (rejoined 2017)."
    ),
    "MDG": (
        "[NATION BRIEF — Madagascar]\n"
        "- Political landscape: President Hery Rajaonarimampianina restoring democratic governance after 2009 crisis; weak institutions, political elite factionalism.\n"
        "- Key challenges: Extreme poverty (~75% below poverty line), deforestation threatening unique biodiversity, cyclone vulnerability, food insecurity, plague outbreaks.\n"
        "- Economic situation: One of world's poorest countries despite natural resources; ~3.1% growth; vanilla and clove exports; mining (nickel, cobalt) growing; tourism potential unrealized."
    ),
    "MEX": (
        "[NATION BRIEF — Mexico]\n"
        "- Political landscape: President Enrique Pena Nieto (PRI) facing declining popularity; Ayotzinapa 43 students disappearance (2014) scandal; structural reforms enacted.\n"
        "- Key challenges: Drug cartel violence (~17,000 homicides in 2015), corruption, impunity, inequality, Chapo Guzman recaptured January 8, 2016; energy reform implementation.\n"
        "- Economic situation: GDP growth ~2.5%, peso weakening significantly, oil production declining (Pemex struggling), energy reform opening sector to foreign investment; automotive sector booming.\n"
        "- Regional tensions: US-Mexico relations complicated by Trump candidacy rhetoric; Central American migration through Mexico; cartel violence in border states."
    ),
    "MKD": (
        "[NATION BRIEF — Macedonia (FYROM)]\n"
        "- Political landscape: PM Nikola Gruevski (VMRO-DPMNE) clinging to power amid political crisis; wiretapping scandal revealed massive surveillance; EU-brokered Przino Agreement.\n"
        "- Key challenges: Political crisis from 2015 wiretapping scandal, name dispute with Greece blocking EU/NATO accession, ethnic Albanian minority tensions, corruption.\n"
        "- Economic situation: Small economy with ~3.7% growth, high unemployment (~26%), EU candidate since 2005 but no start of accession talks; foreign investment limited by political instability."
    ),
    "MLI": (
        "[NATION BRIEF — Mali]\n"
        "- Political landscape: President Ibrahim Boubacar Keita governing after 2013 French intervention restored order; peace agreement with northern rebel groups signed June 2015.\n"
        "- Key challenges: Jihadist insurgency in north (AQIM, Ansar Dine, MUJAO), Tuareg separatism, implementation of Algiers peace accord, extreme poverty, food insecurity.\n"
        "- Economic situation: Low-income country, ~6% growth driven by gold mining and agriculture (cotton); heavily aid-dependent; French military and UN peacekeeping (MINUSMA) present.\n"
        "- Regional tensions: Key Sahel security concern; French Operation Barkhane headquartered in Bamako; UN peacekeeping mission MINUSMA is the deadliest active mission; hotel attack in Bamako November 2015."
    ),
    "MMR": (
        "[NATION BRIEF — Myanmar]\n"
        "- Political landscape: Aung San Suu Kyi's NLD won landmark November 2015 elections in landslide; transitioning from military rule; military retains 25% of parliament and key ministries.\n"
        "- Key challenges: Military still controls defense, border, and home affairs; Rohingya persecution in Rakhine State; ethnic armed conflicts in Kachin and Shan States; poverty.\n"
        "- Economic situation: Rapid growth (~7%) as economy opens after decades of isolation; foreign investment surging; gas exports, garments, agriculture; infrastructure severely underdeveloped.\n"
        "- Regional tensions: Rohingya crisis generating regional tensions; ethnic armed groups along Chinese and Thai borders; opium production; Chinese investment (Myitsone Dam suspended)."
    ),
    "MNG": (
        "[NATION BRIEF — Mongolia]\n"
        "- Political landscape: President Tsakhiagiin Elbegdorj (DP) and PM Chimed Saikhanbileg; democracy in challenging neighborhood; 'third neighbor' policy balancing Russia and China.\n"
        "- Key challenges: Mining-dependent economy in commodity downturn, Oyu Tolgoi copper/gold mine disputes with Rio Tinto, poverty, harsh climate, air pollution in Ulaanbaatar.\n"
        "- Economic situation: Growth crashed from 17% (2011) to ~2.4% as commodity prices fell; fiscal deficit widening; debt rising; IMF assistance being considered."
    ),
    "MOZ": (
        "[NATION BRIEF — Mozambique]\n"
        "- Political landscape: President Filipe Nyusi (Frelimo) in office since January 2015; hidden debt scandal about to emerge; Renamo opposition threatening renewed conflict.\n"
        "- Key challenges: Hidden $2B in undisclosed government debt about to be revealed, Renamo armed opposition, poverty (~46%), natural gas development delays, corruption.\n"
        "- Economic situation: Growth ~6.6% but built on unsustainable borrowing; massive natural gas reserves (Rovuma basin) attracting investment; coal exports; agricultural base.\n"
        "- Regional tensions: Renamo leader Afonso Dhlakama in bush threatening conflict; government forces clashing with Renamo militias; Southern African development partner."
    ),
    "MRT": (
        "[NATION BRIEF — Mauritania]\n"
        "- Political landscape: President Mohamed Ould Abdel Aziz, former coup leader turned elected president; authoritarian governance; slavery legacy and racial tensions.\n"
        "- Key challenges: Slavery persists despite legal prohibition, extreme poverty, desertification, Sahelian security threats, ethnic tensions (Arab-Berber vs. Black African).\n"
        "- Economic situation: Low-income country dependent on iron ore, fishing, and livestock; mining revenues declining with commodity prices; offshore gas potential."
    ),
    "MWI": (
        "[NATION BRIEF — Malawi]\n"
        "- Political landscape: President Peter Mutharika (DPP) governing; 'Cashgate' corruption scandal (theft of $32M in government funds) damaging donor relations.\n"
        "- Key challenges: Extreme poverty, HIV/AIDS prevalence (~10%), chronic food insecurity, Cashgate fallout reducing donor aid, tobacco dependence, climate vulnerability (floods and droughts).\n"
        "- Economic situation: One of world's poorest countries (GDP per capita ~$350); tobacco main export; heavily aid-dependent; growth ~2.9%; kwacha depreciation driving inflation."
    ),
    "MYS": (
        "[NATION BRIEF — Malaysia]\n"
        "- Political landscape: PM Najib Razak (UMNO/BN) embroiled in 1MDB scandal (billions allegedly siphoned from state fund); opposition weakened after Anwar Ibrahim imprisonment.\n"
        "- Key challenges: 1MDB corruption scandal ($681M found in Najib's personal accounts), ethnic tensions (Malay-Chinese-Indian), GST implementation backlash, press freedom declining.\n"
        "- Economic situation: Growth ~5% but ringgit fell sharply; oil and palm oil exports declining; manufacturing and electronics strong; middle-income trap concerns.\n"
        "- Regional tensions: South China Sea claimant; MH370 mystery unresolved; hosting Rohingya refugees; ASEAN member; IS-linked extremism concerns."
    ),
    "NAM": (
        "[NATION BRIEF — Namibia]\n"
        "- Political landscape: President Hage Geingob (SWAPO) took office March 2015; SWAPO dominant since independence 1990; relatively good governance by regional standards.\n"
        "- Key challenges: Extreme inequality (one of world's highest Gini coefficients), land reform pressures (colonial-era imbalances), drought, unemployment (~28%), HIV/AIDS.\n"
        "- Economic situation: Upper-middle-income country; mining (diamonds, uranium) key sector; tourism growing; growth ~5%; drought threatening agriculture."
    ),
    "NER": (
        "[NATION BRIEF — Niger]\n"
        "- Political landscape: President Mahamadou Issoufou seeking re-election February 2016; opposition leader Hama Amadou arrested; democratic governance fragile.\n"
        "- Key challenges: World's highest fertility rate (~7.6 children/woman), extreme poverty, Boko Haram attacks in southeast (Diffa region), food insecurity, uranium price decline.\n"
        "- Economic situation: One of world's least developed countries; uranium mining (Areva/Orano), agriculture, livestock; growth ~3.5%; French military presence."
    ),
    "NIC": (
        "[NATION BRIEF — Nicaragua]\n"
        "- Political landscape: President Daniel Ortega (FSLN) consolidating power; Supreme Court removed opposition leaders; wife Rosario Murillo as de facto co-ruler; 2016 re-election planned.\n"
        "- Key challenges: Democratic backsliding, poverty, corruption, interoceanic canal project (Chinese-backed, controversial), deforestation, emigration.\n"
        "- Economic situation: Growth ~4.9% (Central America's strongest), Venezuelan oil subsidies (Petrocaribe), garment and coffee exports; second-poorest in Western Hemisphere."
    ),
    "NLD": (
        "[NATION BRIEF — Netherlands]\n"
        "- Political landscape: PM Mark Rutte (VVD) in coalition with PvdA; EU referendum on Ukraine Association Agreement coming April 2016; PVV (Geert Wilders) rising in polls.\n"
        "- Key challenges: Integration of migrants, housing crisis, MH17 investigation (shot down over Ukraine July 2014), Geert Wilders on trial for incitement, climate vulnerability (below sea level).\n"
        "- Economic situation: Strong recovery with ~2% growth, low unemployment, major trading nation (Rotterdam port), gas revenues declining (Groningen earthquakes limiting production).\n"
        "- Regional tensions: Leading MH17 investigation implicating Russia; hosting International Criminal Court and tribunals; EU founding member; Curacao/Aruba/Sint Maarten kingdom relations."
    ),
    "NOR": (
        "[NATION BRIEF — Norway]\n"
        "- Political landscape: PM Erna Solberg (Conservative) in minority coalition; oil price drop testing Norwegian model; refugee arrivals surged in 2015.\n"
        "- Key challenges: Oil-dependent economy adjusting to lower prices, Arctic strategy, refugee integration, maintaining welfare state, climate change commitments.\n"
        "- Economic situation: Wealthy ($74K GDP per capita) but mainland GDP growth slowing to ~1%; Government Pension Fund Global (world's largest sovereign wealth fund, ~$830B) providing buffer."
    ),
    "NZL": (
        "[NATION BRIEF — New Zealand]\n"
        "- Political landscape: PM John Key (National) popular; third term; TPP signatory; considering flag change referendum in 2016; strong governance indicators.\n"
        "- Key challenges: Housing affordability crisis (especially Auckland), dairy price slump, Christchurch earthquake rebuild ongoing, Maori inequality, distance from markets.\n"
        "- Economic situation: Growth ~3.4%, dairy and tourism pillars, net migration at record highs driving growth; New Zealand dollar softening with dairy prices."
    ),
    "OMN": (
        "[NATION BRIEF — Oman]\n"
        "- Political landscape: Sultan Qaboos bin Said in power since 1970; aging and in poor health (cancer treatment in Germany 2014-2015); succession planning opaque.\n"
        "- Key challenges: Sultan's health and unclear succession, oil price drop stressing budget, diversification need, youth unemployment, water scarcity.\n"
        "- Economic situation: Oil-dependent but more diversified than Gulf peers; budget deficit from oil crash; tourism and logistics (Duqm port) being developed; moderate debt levels."
    ),
    "PAN": (
        "[NATION BRIEF — Panama]\n"
        "- Political landscape: President Juan Carlos Varela (Panamenista) governing; Panama Canal expansion nearing completion (inaugurated June 2016); democratic governance stable.\n"
        "- Key challenges: Inequality despite strong growth, corruption, drug trafficking transit, Panama Papers leak (will break April 2016), Colon free zone decline.\n"
        "- Economic situation: One of Latin America's fastest-growing economies (~5.8% growth); canal revenues, banking center, real estate boom; Tocumen airport expansion."
    ),
    "PER": (
        "[NATION BRIEF — Peru]\n"
        "- Political landscape: President Ollanta Humala (Partido Nacionalista) completing term; April 2016 election upcoming with Keiko Fujimori as frontrunner; corruption investigations.\n"
        "- Key challenges: Illegal mining and deforestation in Amazon, cocaine production, El Nino impact, inequality, informal economy (~70%), corruption.\n"
        "- Economic situation: Growth slowed to ~3.3% from copper price decline; mining still key sector; stable macroeconomics; Pacific Alliance member; sol relatively stable."
    ),
    "PHL": (
        "[NATION BRIEF — Philippines]\n"
        "- Political landscape: President Benigno Aquino III in final year; May 2016 elections upcoming (Duterte, Poe, Roxas, Binay competing); good governance reform agenda.\n"
        "- Key challenges: South China Sea dispute (arbitration case pending at PCA), Mindanao insurgencies (MILF peace process, Abu Sayyaf), typhoon vulnerability, poverty, corruption.\n"
        "- Economic situation: Strong growth ~5.9%, BPO sector booming, remittances from ~10M overseas workers vital, infrastructure deficit, rising middle class.\n"
        "- Regional tensions: South China Sea arbitration case against China expected ruling July 2016; US alliance strengthening; Enhanced Defense Cooperation Agreement with US."
    ),
    "POL": (
        "[NATION BRIEF — Poland]\n"
        "- Political landscape: President Andrzej Duda and PM Beata Szydlo (PiS, Law and Justice) newly in power since late 2015; pushing conservative nationalist agenda; Constitutional Tribunal crisis.\n"
        "- Key challenges: Rule of law concerns (packing Constitutional Tribunal), EU confrontation over democratic backsliding, refusing refugee quotas, media law changes, brain drain.\n"
        "- Economic situation: Largest Central European economy, ~3.6% growth, unemployment declining, EU structural funds driving investment; not in eurozone; manufacturing and services strong.\n"
        "- Regional tensions: Pushing for stronger NATO eastern presence against Russia; requesting permanent US bases; close Visegrad Group (V4) cooperation; Lithuania and Ukraine solidarity."
    ),
    "PRT": (
        "[NATION BRIEF — Portugal]\n"
        "- Political landscape: PM Antonio Costa (PS) newly in government since November 2015 with Left Bloc and Communist support; reversing austerity measures; President Cavaco Silva skeptical.\n"
        "- Key challenges: High public debt (~129% GDP), unemployment ~12.4%, emigration (especially youth), banking sector fragility, aging population, forest fire vulnerability.\n"
        "- Economic situation: Post-bailout recovery with ~1.5% growth; tourism booming (Lisbon, Porto); exited EU/IMF bailout 2014 but debt sustainability concerns persist."
    ),
    "PRY": (
        "[NATION BRIEF — Paraguay]\n"
        "- Political landscape: President Horacio Cartes (Colorado Party) in power since 2013; conservative businessman-politician; democratic governance but weak institutions.\n"
        "- Key challenges: Inequality, corruption, EPP guerrilla group (small), deforestation in Chaco, soy monoculture, contraband/smuggling, indigenous rights.\n"
        "- Economic situation: Growth ~3% (slowed from soy and hydroelectric sectors); world's fourth-largest soy exporter; Itaipu and Yacyreta hydroelectric dams; large informal economy."
    ),
    "QAT": (
        "[NATION BRIEF — Qatar]\n"
        "- Political landscape: Emir Tamim bin Hamad Al Thani ruling since 2013; small but outsized diplomatic influence; Al Jazeera media network as soft power tool.\n"
        "- Key challenges: 2022 FIFA World Cup construction (migrant worker deaths and exploitation), kafala labor system, oil/gas price decline, diplomatic balancing act.\n"
        "- Economic situation: World's highest GDP per capita; LNG exports cushioning oil price decline better than neighbors; massive infrastructure spending for World Cup; QIA sovereign wealth fund."
    ),
    "ROU": (
        "[NATION BRIEF — Romania]\n"
        "- Political landscape: PM Dacian Ciolos leading technocratic government after PM Ponta resigned November 2015 following Colectiv nightclub fire protests; anti-corruption momentum.\n"
        "- Key challenges: Corruption (anti-corruption agency DNA active), emigration (~3M abroad), infrastructure deficit, Roma marginalization, judicial reform, poverty in rural areas.\n"
        "- Economic situation: Growth ~3.7%, EU's fastest-growing large economy; IT sector booming (Bucharest, Cluj); EU structural funds underutilized; fiscal space from low debt."
    ),
    "RWA": (
        "[NATION BRIEF — Rwanda]\n"
        "- Political landscape: President Paul Kagame (RPF) in power since 2000; December 2015 referendum approved constitutional changes allowing him to potentially rule until 2034.\n"
        "- Key challenges: Authoritarian governance despite development success, press freedom absent, ethnic reconciliation (Hutu-Tutsi), regional meddling accusations, limited political space.\n"
        "- Economic situation: Strong growth (~6.9%), 'Africa's Singapore' aspirations, services and agriculture driving economy, aid-dependent but efficient use of resources; Kigali clean city model."
    ),
    "SDN": (
        "[NATION BRIEF — Sudan]\n"
        "- Political landscape: President Omar al-Bashir in power since 1989 coup; ICC arrest warrant for Darfur genocide; authoritarian Islamist governance; April 2015 re-election boycotted.\n"
        "- Key challenges: Darfur conflict continuing, South Kordofan and Blue Nile conflicts, Bashir ICC warrant, US sanctions, isolation, ethnic and religious tensions.\n"
        "- Economic situation: Lost 75% of oil revenue when South Sudan seceded (2011); inflation high; gold mining partially compensating; Chinese investment in remaining oil sector.\n"
        "- Regional tensions: Supporting Saudi-led coalition in Yemen; rapprochement with Gulf states; Nile water disputes with Egypt and Ethiopia; hosting Eritrean refugees."
    ),
    "SEN": (
        "[NATION BRIEF — Senegal]\n"
        "- Political landscape: President Macky Sall (APR) consolidating democratic governance; constitutional referendum planned (March 2016) to reduce presidential term to 5 years.\n"
        "- Key challenges: Casamance separatist conflict (low-level), youth unemployment, energy costs, fishing sector decline (foreign overfishing), poverty, Ebola preparedness.\n"
        "- Economic situation: Growth ~6.5%, Plan Senegal Emergent driving investment, offshore oil and gas discoveries (Sangomar field) promising future revenues; tourism and agriculture important."
    ),
    "SLE": (
        "[NATION BRIEF — Sierra Leone]\n"
        "- Political landscape: President Ernest Bai Koroma (APC) managing post-Ebola recovery; democratic gains since civil war (ended 2002); governance challenges.\n"
        "- Key challenges: Ebola aftermath (3,955 deaths), health system devastated, extreme poverty, infrastructure gaps, youth unemployment, iron ore price collapse.\n"
        "- Economic situation: Economy contracted ~21% in 2015 due to Ebola and iron ore price crash; mining (diamonds, iron ore, rutile), agriculture; heavily aid-dependent."
    ),
    "SLV": (
        "[NATION BRIEF — El Salvador]\n"
        "- Political landscape: President Salvador Sanchez Ceren (FMLN) governing; former guerrilla commander; gang truce collapsed; Supreme Court declared gangs terrorist organizations.\n"
        "- Key challenges: World's highest homicide rate (103 per 100,000 in 2015), MS-13 and Barrio 18 gang warfare, poverty, emigration to US, remittance dependence.\n"
        "- Economic situation: Dollarized economy, slow growth (~2.5%), remittances (17% GDP), maquila sector, coffee; smallest and most densely populated Central American country."
    ),
    "SOM": (
        "[NATION BRIEF — Somalia]\n"
        "- Political landscape: President Hassan Sheikh Mohamud heading Federal Government with limited territorial control; clan politics dominant; Al-Shabaab insurgency ongoing.\n"
        "- Key challenges: Al-Shabaab controlling large rural areas, state-building in failed state context, piracy declining but not eliminated, famine risk, displacement (~1.1M IDPs).\n"
        "- Economic situation: Among world's poorest countries; livestock, remittances, and telecoms (mobile money) as economic base; diaspora remittances crucial (~$1.4B/year).\n"
        "- Regional tensions: African Union peacekeeping force AMISOM (~22,000 troops) supporting government; Somaliland de facto independent; Puntland semi-autonomous; Kenya and Ethiopia military operations."
    ),
    "SRB": (
        "[NATION BRIEF — Serbia]\n"
        "- Political landscape: PM Aleksandar Vucic (SNS) dominating politics; EU accession negotiations opened; balancing Western integration with Russian and Chinese ties.\n"
        "- Key challenges: Kosovo status unresolved, EU accession conditions (rule of law, Kosovo normalization), media freedom concerns, unemployment, brain drain.\n"
        "- Economic situation: Growth ~0.7%, IMF program supporting reforms, FDI increasing, automotive sector growing; public debt ~76% GDP; gradual recovery from years of stagnation.\n"
        "- Regional tensions: Kosovo normalization dialogue (Brussels process); not joining EU sanctions on Russia; refugee transit route; Vucic consolidating media control."
    ),
    "SSD": (
        "[NATION BRIEF — South Sudan]\n"
        "- Political landscape: President Salva Kiir and VP Riek Machar in nominal unity government under August 2015 peace agreement; deep mistrust; ethnic Dinka-Nuer divide.\n"
        "- Key challenges: Civil war since December 2013 (tens of thousands killed, 2.2M displaced), famine risk, ethnic violence, oil production crashed, state failure.\n"
        "- Economic situation: World's newest country (2011) in economic collapse; oil production (sole revenue source) halved by conflict; hyperinflation; 85% living below poverty line.\n"
        "- Regional tensions: UN peacekeeping mission UNMISS deployed; IGAD mediating; refugees in Uganda, Sudan, Ethiopia, Kenya; oil transit dependence on Sudan."
    ),
    "SUR": (
        "[NATION BRIEF — Suriname]\n"
        "- Political landscape: President Desi Bouterse (NDP) in second term; convicted drug trafficker and former military dictator; November 2015 military tribunal convicted him of 1982 murders.\n"
        "- Key challenges: Commodity dependence (gold, oil, bauxite), drug trafficking, deforestation, ethnic diversity management, small population (~550K), judicial independence.\n"
        "- Economic situation: Recession from commodity price declines; gold and oil revenues falling; suriname dollar devaluing; fiscal crisis; Dutch colonial legacy infrastructure."
    ),
    "SVK": (
        "[NATION BRIEF — Slovakia]\n"
        "- Political landscape: PM Robert Fico (Smer-SD) heading into March 2016 elections; strongly opposing EU refugee quotas; anti-immigration rhetoric intensifying.\n"
        "- Key challenges: Anti-Muslim/refugee sentiment despite minimal refugee presence, Roma marginalization, corruption, brain drain, automotive industry over-dependence.\n"
        "- Economic situation: Growth ~3.6%, automotive industry driving exports (VW, Kia, Peugeot), eurozone member, low unemployment; Visegrad Group coordination on EU policy."
    ),
    "SVN": (
        "[NATION BRIEF — Slovenia]\n"
        "- Political landscape: PM Miro Cerar (SMC) leading coalition; small but stable EU member; refugee transit route causing tensions in 2015.\n"
        "- Key challenges: Banking sector restructured after 2013 bailout, refugee transit management (fence built on Croatian border), aging population, fiscal consolidation.\n"
        "- Economic situation: Recovery with ~2.3% growth after deep banking crisis; export-oriented (pharmaceuticals, automotive); eurozone member; tourism (Ljubljana, Lake Bled) growing."
    ),
    "SWE": (
        "[NATION BRIEF — Sweden]\n"
        "- Political landscape: PM Stefan Lofven (Social Democrats) leading minority government; record 163,000 asylum seekers in 2015 overwhelming capacity; border controls reimposed.\n"
        "- Key challenges: Refugee integration crisis, housing shortage, gang violence in suburbs, maintaining welfare state with migration costs, defense spending debate (Russian submarine incidents).\n"
        "- Economic situation: Strong growth (~4.1%), tech and innovation hub (Spotify, Ericsson), but welfare model strained; not in eurozone; low public debt."
    ),
    "SWZ": (
        "[NATION BRIEF — Eswatini (Swaziland)]\n"
        "- Political landscape: King Mswati III ruling as Africa's last absolute monarch; political parties banned; traditional governance system; youth frustration growing.\n"
        "- Key challenges: World's highest HIV/AIDS prevalence (~27%), poverty (~63%), absolute monarchy limiting freedoms, youth unemployment, dependence on South Africa.\n"
        "- Economic situation: Small economy tied to South Africa (Southern African Customs Union revenues); sugar and soft drink concentrate exports; textile industry; growth ~1.7%."
    ),
    "SYR": (
        "[NATION BRIEF — Syria]\n"
        "- Political landscape: President Bashar al-Assad controlling ~20% of territory with Russian and Iranian support; opposition fragmented; ISIS holding large eastern territories.\n"
        "- Key challenges: Catastrophic civil war (250,000+ dead, half population displaced), ISIS territorial control, humanitarian crisis, chemical weapons use, refugee exodus (4.5M abroad).\n"
        "- Economic situation: Economy destroyed (GDP contracted ~60% since 2011); infrastructure devastated; besieged populations facing starvation; war economy and sanctions.\n"
        "- Regional tensions: Russia intervening militarily since September 2015; Iran and Hezbollah supporting Assad; Turkey, Gulf states backing rebels; US-led coalition targeting ISIS; Vienna peace talks ongoing."
    ),
    "TCD": (
        "[NATION BRIEF — Chad]\n"
        "- Political landscape: President Idriss Deby in power since 1990; authoritarian rule; presidential election April 2016; key Western counterterrorism ally despite poor governance.\n"
        "- Key challenges: Boko Haram attacks, poverty, landlocked, oil dependence, food insecurity, Lake Chad shrinking, authoritarian governance, humanitarian crises from neighbors.\n"
        "- Economic situation: Oil revenues devastated by price crash; budget crisis; French military hub (Operation Barkhane); among world's least developed countries.\n"
        "- Regional tensions: Chadian forces fighting Boko Haram in Nigeria and Niger; contributing to UN peacekeeping in Mali; hosting refugees from CAR, Nigeria, Sudan."
    ),
    "TGO": (
        "[NATION BRIEF — Togo]\n"
        "- Political landscape: President Faure Gnassingbe in power since 2005, continuing father's dynasty (in power since 1967); contested April 2015 re-election; opposition protests.\n"
        "- Key challenges: Political dynasty, poverty, limited infrastructure, phosphate mining governance, constitutional reform demands (term limits), youth unemployment.\n"
        "- Economic situation: Low-income country, growth ~5.3%, phosphate mining, port of Lome as regional trade hub, agriculture dominant; West African franc zone member."
    ),
    "THA": (
        "[NATION BRIEF — Thailand]\n"
        "- Political landscape: Military junta (NCPO) under PM Prayut Chan-o-cha since May 2014 coup; martial law replaced by Article 44; constitution drafting; King Bhumibol Adulyadej ailing.\n"
        "- Key challenges: Stalled democracy, lese-majeste law enforcement, southern Malay-Muslim insurgency, aging king creating succession anxiety, political polarization (Red vs Yellow).\n"
        "- Economic situation: Growth ~2.9% recovering slowly from coup disruption; tourism resilient; automotive and electronics manufacturing; rice exports; baht relatively stable.\n"
        "- Regional tensions: Mekong River dam disputes with Laos and China; South China Sea not direct claimant but ASEAN implications; military ties with both US and China."
    ),
    "TTO": (
        "[NATION BRIEF — Trinidad and Tobago]\n"
        "- Political landscape: PM Keith Rowley (PNM) took office September 2015; energy-dependent economy; democratic governance stable; dealing with ISIS recruitment concerns.\n"
        "- Key challenges: Oil and gas price decline, crime and gang violence, ISIS recruitment (highest per capita Caribbean contributor to foreign fighters), diversification needed.\n"
        "- Economic situation: Recession from energy price collapse; gas (LNG) and petrochemicals dominant; budget deficit widening; previously high-income Caribbean economy facing adjustment."
    ),
    "TUN": (
        "[NATION BRIEF — Tunisia]\n"
        "- Political landscape: President Beji Caid Essebsi (Nidaa Tounes) and PM Habib Essid governing; only Arab Spring democracy surviving; Nobel Peace Prize to National Dialogue Quartet 2015.\n"
        "- Key challenges: Terrorism (Sousse and Bardo museum attacks in 2015), youth unemployment (~30%), regional inequality (interior vs. coast), ISIS recruitment, Ben Guerdane border threat.\n"
        "- Economic situation: Growth ~0.8%, tourism devastated by terrorist attacks, IMF program, unemployment high especially among educated youth; democratic transition economic costs."
    ),
    "TWN": (
        "[NATION BRIEF — Taiwan]\n"
        "- Political landscape: Tsai Ing-wen (DPP) won presidential election January 16, 2016 in landslide; first female president; Beijing concerned about independence-leaning DPP.\n"
        "- Key challenges: Cross-strait relations uncertainty with DPP victory, economic slowdown, stagnant wages, housing costs, aging population, declining birth rate.\n"
        "- Economic situation: Export-dependent economy (~$530B GDP), semiconductor industry (TSMC world leader), growth slowed to ~0.7%; trade with China dominant but diversification sought.\n"
        "- Regional tensions: China demanding acknowledgment of '1992 Consensus'; US arms sales; South China Sea claims; Trans-Pacific Partnership ambitions."
    ),
    "TZA": (
        "[NATION BRIEF — Tanzania]\n"
        "- Political landscape: President John Magufuli (CCM) newly inaugurated October 2015; 'The Bulldozer' reputation for anti-corruption drive; cutting government waste dramatically.\n"
        "- Key challenges: Poverty despite growth, governance in Zanzibar (disputed election rerun), infrastructure deficit, wildlife poaching (elephants), natural gas development planning.\n"
        "- Economic situation: Growth ~7%, agriculture (70% employment), gold mining, tourism (Serengeti, Kilimanjaro), offshore natural gas discoveries promising; port of Dar es Salaam regional gateway."
    ),
    "UGA": (
        "[NATION BRIEF — Uganda]\n"
        "- Political landscape: President Yoweri Museveni (NRM) in power since 1986; February 2016 elections upcoming; opposition leader Kizza Besigye repeatedly arrested; authoritarian drift.\n"
        "- Key challenges: Museveni's 30-year rule, term limit removal, anti-homosexuality legislation controversy, population boom (~3.2% growth rate), Lord's Resistance Army remnants.\n"
        "- Economic situation: Growth ~5%, oil production expected to start (Albertine Graben), agriculture dominant, hosting ~500,000 refugees (South Sudan, Burundi, DRC); aid-dependent."
    ),
    "URY": (
        "[NATION BRIEF — Uruguay]\n"
        "- Political landscape: President Tabare Vazquez (Frente Amplio) in second non-consecutive term; progressive social policies (marijuana legalization, same-sex marriage).\n"
        "- Key challenges: Economic slowdown from regional downturn (Argentina, Brazil), rising fiscal deficit, education reform needs, aging population relative to Latin America.\n"
        "- Economic situation: High-income country for Latin America (~$15K GDP per capita), growth slowing to ~1%, strong institutions, low corruption, beef and soy exports, wind energy investment."
    ),
    "UZB": (
        "[NATION BRIEF — Uzbekistan]\n"
        "- Political landscape: President Islam Karimov ruling since 1989; Central Asia's most authoritarian state; no genuine elections; forced labor in cotton harvest.\n"
        "- Key challenges: Authoritarian repression, forced labor (cotton), Aral Sea environmental disaster, Islamist extremism concerns (IMU), economic isolation, border tensions.\n"
        "- Economic situation: Central Asia's most populous country (~31M); gold and cotton exports; state-controlled economy; officially ~8% growth but data unreliable; currency black market."
    ),
    "VEN": (
        "[NATION BRIEF — Venezuela]\n"
        "- Political landscape: President Nicolas Maduro (PSUV) facing hostile National Assembly after opposition MUD won supermajority in December 2015 elections; constitutional crisis brewing.\n"
        "- Key challenges: Economic collapse (hyperinflation emerging, severe shortages of food and medicine), crime (world's highest murder rate), political polarization, oil dependence.\n"
        "- Economic situation: GDP contracting ~6%, inflation above 180%, currency in freefall, oil revenues collapsed, foreign reserves critical; humanitarian crisis emerging.\n"
        "- Regional tensions: OAS tensions over democratic governance; Cuba ally under pressure; Colombian border disputes; losing Petrocaribe leverage as oil revenues collapse."
    ),
    "VNM": (
        "[NATION BRIEF — Vietnam]\n"
        "- Political landscape: Communist Party Congress upcoming January 2016 to select new leadership; General Secretary Nguyen Phu Trong consolidating; one-party state with factional politics.\n"
        "- Key challenges: South China Sea confrontation with China (oil rig crisis 2014), corruption, environmental degradation, SOE reform, press freedom, rapid urbanization.\n"
        "- Economic situation: Growth ~6.7%, manufacturing hub (Samsung largest exporter), FDI flowing in (TPP signatory), young workforce, poverty reduction success story.\n"
        "- Regional tensions: Major South China Sea claimant; US rapprochement accelerating (arms embargo lifted partially); ASEAN member; balancing China and US relations."
    ),
    "YEM": (
        "[NATION BRIEF — Yemen]\n"
        "- Political landscape: President Hadi in exile (Riyadh); Houthi rebels and Saleh forces controlling Sanaa; country split between multiple factions; UN peace talks attempted.\n"
        "- Key challenges: Catastrophic civil war (Saudi-led coalition bombing since March 2015), humanitarian crisis (21M need aid, 80% population), AQAP and ISIS exploiting chaos, cholera risk.\n"
        "- Economic situation: Economy destroyed by war; infrastructure devastated; famine conditions in multiple areas; ports blockaded limiting imports; pre-war already Arab world's poorest.\n"
        "- Regional tensions: Saudi-led coalition (including UAE, Bahrain, Sudan) fighting Houthi-Saleh alliance; Iran accused of supporting Houthis; AQAP controlling territory in south; Bab el-Mandeb strait security."
    ),
    "ZMB": (
        "[NATION BRIEF — Zambia]\n"
        "- Political landscape: President Edgar Lungu (PF) in power after January 2015 special election following President Sata's death; election scheduled August 2016; opposition UPND competitive.\n"
        "- Key challenges: Copper price collapse devastating economy, electricity crisis (drought reducing hydropower from Kariba Dam), kwacha depreciation, poverty, Chinese mining concerns.\n"
        "- Economic situation: Copper-dependent economy in crisis; growth slowed to ~3%; kwacha lost 45% in 2015; IMF discussions; electricity rationing cutting production; Eurobond debt concerns."
    ),
    "ZWE": (
        "[NATION BRIEF — Zimbabwe]\n"
        "- Political landscape: President Robert Mugabe (ZANU-PF) aged 91, in power since 1980; succession battle between VP Mnangagwa and wife Grace Mugabe; opposition MDC-T weakened.\n"
        "- Key challenges: Mugabe succession crisis, cash shortages in dollarized economy, drought and food insecurity, land reform aftermath, international isolation, unemployment (~90% informal).\n"
        "- Economic situation: Stagnant GDP (~1.1% growth), deflation, liquidity crisis (bond notes being considered), diamond revenues opaque, agriculture collapsed from land reform; Chinese loans."
    ),
}


def main() -> None:
    print(f"Reading scenario from: {SCENARIO_PATH}")
    with open(SCENARIO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    countries = data.get("countries", {})
    injected = 0
    skipped = 0

    for country_id, country in countries.items():
        brief = NATION_BRIEFS.get(country_id, "")
        country["nation_brief"] = brief
        if brief:
            injected += 1
        else:
            skipped += 1

    print(f"Injected nation_brief for {injected} countries, {skipped} countries had no brief available.")

    with open(SCENARIO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Wrote updated scenario to: {SCENARIO_PATH}")


if __name__ == "__main__":
    main()
