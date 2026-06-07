import { useState, memo } from 'react'
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  ZoomableGroup,
  type GeoRecord,
} from 'react-simple-maps'
import { Plus, Minus, RotateCcw } from 'lucide-react'
import type { MouseEvent } from 'react'
import type { Country, MapPOI, RegionState } from '@/types'

const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json'
const GEO_ADMIN1_URL = '/ne_admin1.json'

// Complete ISO 3166-1 numeric → alpha-3 mapping for all 174 countries in world-atlas 110m
const NUMERIC_TO_ALPHA3: Record<string, string> = {
  // Game scenario countries
  '840': 'USA', '156': 'CHN', '643': 'RUS', '276': 'DEU', '250': 'FRA',
  '826': 'GBR', '392': 'JPN', '356': 'IND', '076': 'BRA', '124': 'CAN',
  '036': 'AUS', '410': 'KOR', '484': 'MEX', '360': 'IDN', '682': 'SAU',
  '792': 'TUR', '380': 'ITA', '724': 'ESP', '032': 'ARG', '710': 'ZAF',
  '364': 'IRN', '376': 'ISR', '408': 'PRK', '804': 'UKR', '616': 'POL',
  '528': 'NLD', '756': 'CHE', '752': 'SWE', '578': 'NOR', '586': 'PAK',
  '566': 'NGA', '818': 'EGY', '704': 'VNM', '608': 'PHL', '170': 'COL',
  '862': 'VEN', '368': 'IRQ', '760': 'SYR', '784': 'ARE', '634': 'QAT',
  '192': 'CUB', '398': 'KAZ', '764': 'THA', '458': 'MYS', '231': 'ETH',
  '300': 'GRC', '203': 'CZE', '348': 'HUN', '642': 'ROU',
  // Rest of the world
  '004': 'AFG', '008': 'ALB', '010': 'ATA', '012': 'DZA', '024': 'AGO',
  '031': 'AZE', '040': 'AUT', '044': 'BHS', '050': 'BGD', '051': 'ARM',
  '056': 'BEL', '064': 'BTN', '068': 'BOL', '070': 'BIH', '072': 'BWA',
  '084': 'BLZ', '090': 'SLB', '096': 'BRN', '100': 'BGR', '104': 'MMR',
  '108': 'BDI', '112': 'BLR', '116': 'KHM', '120': 'CMR', '140': 'CAF',
  '144': 'LKA', '148': 'TCD', '152': 'CHL', '158': 'TWN', '178': 'COG',
  '180': 'COD', '188': 'CRI', '191': 'HRV', '196': 'CYP', '204': 'BEN',
  '208': 'DNK', '214': 'DOM', '218': 'ECU', '222': 'SLV', '226': 'GNQ',
  '232': 'ERI', '233': 'EST', '238': 'FLK', '242': 'FJI', '246': 'FIN',
  '260': 'ATF', '262': 'DJI', '266': 'GAB', '268': 'GEO', '270': 'GMB',
  '275': 'PSE', '288': 'GHA', '304': 'GRL', '320': 'GTM', '324': 'GIN',
  '328': 'GUY', '332': 'HTI', '340': 'HND', '352': 'ISL', '372': 'IRL',
  '384': 'CIV', '388': 'JAM', '400': 'JOR', '404': 'KEN', '414': 'KWT',
  '417': 'KGZ', '418': 'LAO', '422': 'LBN', '426': 'LSO', '428': 'LVA',
  '430': 'LBR', '434': 'LBY', '440': 'LTU', '442': 'LUX', '450': 'MDG',
  '454': 'MWI', '466': 'MLI', '478': 'MRT', '496': 'MNG', '498': 'MDA',
  '499': 'MNE', '504': 'MAR', '508': 'MOZ', '512': 'OMN', '516': 'NAM',
  '524': 'NPL', '540': 'NCL', '548': 'VUT', '554': 'NZL', '558': 'NIC',
  '562': 'NER', '591': 'PAN', '598': 'PNG', '600': 'PRY', '604': 'PER',
  '620': 'PRT', '624': 'GNB', '626': 'TLS', '630': 'PRI', '646': 'RWA',
  '686': 'SEN', '688': 'SRB', '694': 'SLE', '703': 'SVK', '705': 'SVN',
  '706': 'SOM', '716': 'ZWE', '728': 'SSD', '729': 'SDN', '732': 'ESH',
  '740': 'SUR', '748': 'SWZ', '762': 'TJK', '768': 'TGO', '780': 'TTO',
  '788': 'TUN', '795': 'TKM', '800': 'UGA', '807': 'MKD', '834': 'TZA',
  '854': 'BFA', '858': 'URY', '860': 'UZB', '887': 'YEM', '894': 'ZMB',
}

// French names for non-game countries (game countries use scenario data)
const WORLD_NAMES: Record<string, string> = {
  AFG: 'Afghanistan',        ALB: 'Albanie',             ATA: 'Antarctique',
  DZA: 'Algérie',            AGO: 'Angola',              AZE: 'Azerbaïdjan',
  AUT: 'Autriche',           BGD: 'Bangladesh',
  ARM: 'Arménie',            BEL: 'Belgique',            BTN: 'Bhoutan',
  BOL: 'Bolivie',            BIH: 'Bosnie-Herzégovine',
  SLB: 'Îles Salomon',       BRN: 'Brunéi',
  BGR: 'Bulgarie',           MMR: 'Myanmar',
  BLR: 'Biélorussie',        KHM: 'Cambodge',            CMR: 'Cameroun',
  LKA: 'Sri Lanka',
  CHL: 'Chili',              TWN: 'Taïwan',
  CRI: 'Costa Rica',         HRV: 'Croatie',
  CYP: 'Chypre',             DNK: 'Danemark',
  DOM: 'Rép. Dominicaine',   ECU: 'Équateur',
  EST: 'Estonie',
  FLK: 'Îles Malouines',     FJI: 'Fidji',               FIN: 'Finlande',
  ATF: 'Terres australes fr.',
  GEO: 'Géorgie',            PSE: 'Palestine',
  GHA: 'Ghana',              GRL: 'Groenland',           GTM: 'Guatemala',
  ISL: 'Islande',
  IRL: 'Irlande',            CIV: "Côte d'Ivoire",       JOR: 'Jordanie',
  KEN: 'Kenya',              KWT: 'Koweït',              KGZ: 'Kirghizistan',
  LAO: 'Laos',               LBN: 'Liban',
  LVA: 'Lettonie',           LBY: 'Libye',
  LTU: 'Lituanie',           LUX: 'Luxembourg',
  MNG: 'Mongolie',           MDA: 'Moldavie',            MNE: 'Monténégro',
  MAR: 'Maroc',              OMN: 'Oman',
  NPL: 'Népal',              NCL: 'Nouvelle-Calédonie',
  VUT: 'Vanuatu',            NZL: 'Nouvelle-Zélande',
  PAN: 'Panama',             PNG: 'Papouasie-Nvl-Guinée',
  PRY: 'Paraguay',           PER: 'Pérou',               PRT: 'Portugal',
  TLS: 'Timor-Leste',        PRI: 'Porto Rico',
  SRB: 'Serbie',
  SVK: 'Slovaquie',          SVN: 'Slovénie',
  SOM: 'Somalie',            ZWE: 'Zimbabwe',
  SDN: 'Soudan',             ESH: 'Sahara occidental',
  TJK: 'Tadjikistan',
  TUN: 'Tunisie',            TKM: 'Turkménistan',
  MKD: 'Macédoine du Nord',  TZA: 'Tanzanie',
  URY: 'Uruguay',            UZB: 'Ouzbékistan',
  YEM: 'Yémen',              ZMB: 'Zambie',
}

const CAPITALS: Record<string, { name: string; coords: [number, number] }> = {
  USA: { name: 'Washington D.C.', coords: [-77.0, 38.9] },
  CHN: { name: 'Pékin',           coords: [116.4, 39.9] },
  RUS: { name: 'Moscou',          coords: [37.6,  55.8] },
  DEU: { name: 'Berlin',          coords: [13.4,  52.5] },
  FRA: { name: 'Paris',           coords: [2.3,   48.9] },
  GBR: { name: 'Londres',         coords: [-0.1,  51.5] },
  JPN: { name: 'Tokyo',           coords: [139.7, 35.7] },
  IND: { name: 'New Delhi',       coords: [77.2,  28.6] },
  BRA: { name: 'Brasília',        coords: [-47.9,-15.8] },
  CAN: { name: 'Ottawa',          coords: [-75.7, 45.4] },
  AUS: { name: 'Canberra',        coords: [149.1,-35.3] },
  KOR: { name: 'Séoul',           coords: [127.0, 37.6] },
  MEX: { name: 'Mexico',          coords: [-99.1, 19.4] },
  IDN: { name: 'Jakarta',         coords: [106.8, -6.2] },
  SAU: { name: 'Riyad',           coords: [46.7,  24.7] },
  TUR: { name: 'Ankara',          coords: [32.9,  39.9] },
  ITA: { name: 'Rome',            coords: [12.5,  41.9] },
  ESP: { name: 'Madrid',          coords: [-3.7,  40.4] },
  ARG: { name: 'Buenos Aires',    coords: [-58.4,-34.6] },
  ZAF: { name: 'Pretoria',        coords: [28.2, -25.7] },
  IRN: { name: 'Téhéran',         coords: [51.4,  35.7] },
  ISR: { name: 'Jérusalem',       coords: [35.2,  31.8] },
  PRK: { name: 'Pyongyang',       coords: [125.7, 39.0] },
  UKR: { name: 'Kyiv',            coords: [30.5,  50.5] },
  POL: { name: 'Varsovie',        coords: [21.0,  52.2] },
  NLD: { name: 'Amsterdam',       coords: [4.9,   52.4] },
  CHE: { name: 'Berne',           coords: [7.4,   46.9] },
  SWE: { name: 'Stockholm',       coords: [18.1,  59.3] },
  NOR: { name: 'Oslo',            coords: [10.7,  59.9] },
  PAK: { name: 'Islamabad',       coords: [73.1,  33.7] },
  NGA: { name: 'Abuja',           coords: [7.5,    9.1] },
  EGY: { name: 'Le Caire',        coords: [31.2,  30.1] },
  VNM: { name: 'Hanoï',           coords: [105.8, 21.0] },
  PHL: { name: 'Manille',         coords: [121.0, 14.6] },
  COL: { name: 'Bogotá',          coords: [-74.1,  4.7] },
  VEN: { name: 'Caracas',         coords: [-66.9, 10.5] },
  IRQ: { name: 'Bagdad',          coords: [44.4,  33.3] },
  SYR: { name: 'Damas',           coords: [36.3,  33.5] },
  ARE: { name: 'Abou Dabi',       coords: [54.4,  24.5] },
  QAT: { name: 'Doha',            coords: [51.5,  25.3] },
  CUB: { name: 'La Havane',       coords: [-82.4, 23.1] },
  KAZ: { name: 'Astana',          coords: [71.4,  51.2] },
  THA: { name: 'Bangkok',         coords: [100.5, 13.8] },
  MYS: { name: 'Kuala Lumpur',    coords: [101.7,  3.1] },
  ETH: { name: 'Addis-Abeba',     coords: [38.7,   9.0] },
  GRC: { name: 'Athènes',         coords: [23.7,  37.9] },
  CZE: { name: 'Prague',          coords: [14.4,  50.1] },
  HUN: { name: 'Budapest',        coords: [19.0,  47.5] },
  ROU: { name: 'Bucarest',        coords: [26.1,  44.4] },
  // Added countries
  AFG: { name: 'Kaboul',          coords: [69.2,  34.5] },
  AGO: { name: 'Luanda',          coords: [13.2,  -8.8] },
  ARM: { name: 'Erevan',          coords: [44.5,  40.2] },
  AUT: { name: 'Vienne',          coords: [16.4,  48.2] },
  AZE: { name: 'Bakou',           coords: [49.9,  40.4] },
  BEL: { name: 'Bruxelles',       coords: [4.4,   50.8] },
  BGD: { name: 'Dacca',           coords: [90.4,  23.7] },
  BGR: { name: 'Sofia',           coords: [23.3,  42.7] },
  BLR: { name: 'Minsk',           coords: [27.6,  53.9] },
  BOL: { name: 'La Paz',          coords: [-68.1,-16.5] },
  CHL: { name: 'Santiago',        coords: [-70.7,-33.5] },
  CIV: { name: 'Yamoussoukro',    coords: [-5.3,   6.8] },
  CMR: { name: 'Yaoundé',         coords: [11.5,   3.9] },
  CRI: { name: 'San José',        coords: [-84.1,  9.9] },
  DNK: { name: 'Copenhague',      coords: [12.6,  55.7] },
  DOM: { name: 'Saint-Domingue',  coords: [-69.9, 18.5] },
  DZA: { name: 'Alger',           coords: [3.1,   36.7] },
  ECU: { name: 'Quito',           coords: [-78.5, -0.2] },
  EST: { name: 'Tallinn',         coords: [24.7,  59.4] },
  FIN: { name: 'Helsinki',        coords: [25.0,  60.2] },
  GEO: { name: 'Tbilissi',        coords: [44.8,  41.7] },
  GHA: { name: 'Accra',           coords: [-0.2,   5.6] },
  GTM: { name: 'Guatemala City',  coords: [-90.5, 14.6] },
  HRV: { name: 'Zagreb',          coords: [16.0,  45.8] },
  IRL: { name: 'Dublin',          coords: [-6.3,  53.3] },
  JOR: { name: 'Amman',           coords: [35.9,  31.9] },
  KEN: { name: 'Nairobi',         coords: [36.8,  -1.3] },
  KHM: { name: 'Phnom Penh',      coords: [104.9, 11.6] },
  KWT: { name: 'Koweït City',     coords: [47.9,  29.4] },
  LBN: { name: 'Beyrouth',        coords: [35.5,  33.9] },
  LBY: { name: 'Tripoli',         coords: [13.2,  32.9] },
  LKA: { name: 'Colombo',         coords: [79.9,   6.9] },
  LTU: { name: 'Vilnius',         coords: [25.3,  54.7] },
  LVA: { name: 'Riga',            coords: [24.1,  56.9] },
  MAR: { name: 'Rabat',           coords: [-6.8,  34.0] },
  MKD: { name: 'Skopje',          coords: [21.4,  42.0] },
  MMR: { name: 'Naypyidaw',       coords: [96.1,  19.8] },
  MNG: { name: 'Oulan-Bator',     coords: [106.9, 47.9] },
  NZL: { name: 'Wellington',      coords: [174.8,-41.3] },
  OMN: { name: 'Mascate',         coords: [58.6,  23.6] },
  PAN: { name: 'Panama City',     coords: [-79.5,  9.0] },
  PER: { name: 'Lima',            coords: [-77.0,-12.1] },
  PRT: { name: 'Lisbonne',        coords: [-9.1,  38.7] },
  PRY: { name: 'Asunción',        coords: [-57.7,-25.3] },
  SDN: { name: 'Khartoum',        coords: [32.5,  15.6] },
  SOM: { name: 'Mogadiscio',      coords: [45.3,   2.0] },
  SRB: { name: 'Belgrade',        coords: [20.5,  44.8] },
  SVK: { name: 'Bratislava',      coords: [17.1,  48.1] },
  SVN: { name: 'Ljubljana',       coords: [14.5,  46.1] },
  TUN: { name: 'Tunis',           coords: [10.2,  36.8] },
  TWN: { name: 'Taipei',          coords: [121.5, 25.0] },
  TZA: { name: 'Dodoma',          coords: [35.7,  -6.2] },
  URY: { name: 'Montevideo',      coords: [-56.2,-34.9] },
  UZB: { name: 'Tachkent',        coords: [69.3,  41.3] },
  YEM: { name: 'Sanaa',           coords: [44.2,  15.4] },
  ZMB: { name: 'Lusaka',          coords: [28.3, -15.4] },
  ZWE: { name: 'Harare',          coords: [31.0, -17.8] },
  // Caribbean
  HTI: { name: 'Port-au-Prince',  coords: [-72.3,  18.5] },
  JAM: { name: 'Kingston',        coords: [-76.8,  18.0] },
  TTO: { name: 'Port of Spain',   coords: [-61.5,  10.7] },
  BHS: { name: 'Nassau',          coords: [-77.3,  25.1] },
  BLZ: { name: 'Belmopan',        coords: [-88.8,  17.3] },
  GUY: { name: 'Georgetown',      coords: [-58.2,   6.8] },
  SUR: { name: 'Paramaribo',      coords: [-55.2,   5.8] },
  // Central America
  HND: { name: 'Tegucigalpa',     coords: [-87.2,  14.1] },
  SLV: { name: 'San Salvador',    coords: [-89.2,  13.7] },
  NIC: { name: 'Managua',         coords: [-86.3,  12.1] },
  // Africa – West
  SEN: { name: 'Dakar',           coords: [-17.4,  14.7] },
  MLI: { name: 'Bamako',          coords: [ -8.0,  12.6] },
  BFA: { name: 'Ouagadougou',     coords: [ -1.5,  12.4] },
  NER: { name: 'Niamey',          coords: [  2.1,  13.5] },
  TCD: { name: "N'Djamena",       coords: [ 15.0,  12.1] },
  GIN: { name: 'Conakry',         coords: [-13.7,   9.5] },
  SLE: { name: 'Freetown',        coords: [-13.2,   8.5] },
  LBR: { name: 'Monrovia',        coords: [-10.8,   6.3] },
  GNB: { name: 'Bissau',          coords: [-15.6,  11.9] },
  GMB: { name: 'Banjul',          coords: [-16.6,  13.5] },
  MRT: { name: 'Nouakchott',      coords: [-15.9,  18.1] },
  BEN: { name: 'Porto-Novo',      coords: [  2.6,   6.4] },
  TGO: { name: 'Lomé',            coords: [  1.2,   6.1] },
  // Africa – Central
  COD: { name: 'Kinshasa',        coords: [ 15.32, -4.32] },
  COG: { name: 'Brazzaville',     coords: [ 15.28, -4.26] },
  CAF: { name: 'Bangui',          coords: [ 18.6,   4.4] },
  GAB: { name: 'Libreville',      coords: [  9.4,   0.4] },
  GNQ: { name: 'Malabo',          coords: [  8.8,   3.8] },
  // Africa – East
  UGA: { name: 'Kampala',         coords: [ 32.6,   0.3] },
  RWA: { name: 'Kigali',          coords: [ 30.1,  -1.9] },
  BDI: { name: 'Bujumbura',       coords: [ 29.4,  -3.4] },
  SSD: { name: 'Juba',            coords: [ 31.6,   4.9] },
  ERI: { name: 'Asmara',          coords: [ 38.9,  15.3] },
  DJI: { name: 'Djibouti',        coords: [ 43.1,  11.6] },
  // Africa – Southern
  MOZ: { name: 'Maputo',          coords: [ 32.6, -25.9] },
  MDG: { name: 'Antananarivo',    coords: [ 47.5, -18.9] },
  MWI: { name: 'Lilongwe',        coords: [ 33.8, -14.0] },
  NAM: { name: 'Windhoek',        coords: [ 17.1, -22.6] },
  BWA: { name: 'Gaborone',        coords: [ 25.9, -24.7] },
  LSO: { name: 'Maseru',          coords: [ 27.5, -29.3] },
  SWZ: { name: 'Mbabane',         coords: [ 31.1, -26.3] },
}

const REGIONS: { name: string; coords: [number, number]; color: string }[] = [
  { name: 'AMÉRIQUE DU NORD',  coords: [-103, 52],  color: '#60a5fa' },
  { name: 'AMÉRIQUE DU SUD',   coords: [-60,  -22], color: '#34d399' },
  { name: 'EUROPE',            coords: [15,   58],  color: '#a78bfa' },
  { name: 'RUSSIE',            coords: [82,   65],  color: '#f472b6' },
  { name: 'ASIE CENTRALE',     coords: [67,   46],  color: '#fb923c' },
  { name: 'MOYEN-ORIENT',      coords: [47,   28],  color: '#fbbf24' },
  { name: 'AFRIQUE',           coords: [22,    2],  color: '#4ade80' },
  { name: 'ASIE DU SUD',       coords: [78,   22],  color: '#f87171' },
  { name: 'EXTRÊME-ORIENT',    coords: [122,  42],  color: '#38bdf8' },
  { name: 'ASIE DU SUD-EST',   coords: [114,   5],  color: '#e879f9' },
  { name: 'OCÉANIE',           coords: [138, -28],  color: '#86efac' },
]

// Game scenario country IDs
const GAME_COUNTRY_IDS = new Set([
  // Original 49
  'USA','CHN','RUS','DEU','FRA','GBR','JPN','IND','BRA','CAN',
  'AUS','KOR','MEX','IDN','SAU','TUR','ITA','ESP','ARG','ZAF',
  'IRN','ISR','PRK','UKR','POL','NLD','CHE','SWE','NOR','PAK',
  'NGA','EGY','VNM','PHL','COL','VEN','IRQ','SYR','ARE','QAT',
  'CUB','KAZ','THA','MYS','ETH','GRC','CZE','HUN','ROU',
  // Added countries
  'AFG','AGO','ARM','AUT','AZE','BEL','BGD','BGR','BLR','BOL',
  'CHL','CIV','CMR','CRI','DNK','DOM','DZA','ECU','EST','FIN',
  'GEO','GHA','GTM','HRV','IRL','JOR','KEN','KHM','KWT','LBN',
  'LBY','LKA','LTU','LVA','MAR','MKD','MMR','MNG','NZL','OMN',
  'PAN','PER','PRT','PRY','SDN','SOM','SRB','SVK','SVN','TUN',
  'TWN','TZA','URY','UZB','YEM','ZMB','ZWE',
  // Caribbean
  'HTI','JAM','TTO','BHS','BLZ','GUY','SUR',
  // Central America
  'HND','SLV','NIC',
  // Africa – West
  'SEN','MLI','BFA','NER','TCD','GIN','SLE','LBR','GNB','GMB','MRT','BEN','TGO',
  // Africa – Central
  'COD','COG','CAF','GAB','GNQ',
  // Africa – East
  'UGA','RWA','BDI','SSD','ERI','DJI',
  // Africa – Southern
  'MOZ','MDG','MWI','NAM','BWA','LSO','SWZ',
])

function getRelationColor(score: number): string {
  if (score >= 60)  return '#22c55e'
  if (score >= 20)  return '#86efac'
  if (score >= -20) return '#94a3b8'
  if (score >= -60) return '#f97316'
  return '#ef4444'
}

function getStabilityColor(stability: number): string {
  if (stability >= 70) return '#1d4ed8'
  if (stability >= 40) return '#2563eb'
  return '#1e40af'
}

interface Props {
  countries: Record<string, Country>
  playerCountryId: string
  selectedCountryId?: string
  onSelectCountry: (countryId: string) => void
  viewMode: 'relations' | 'stability' | 'ideology'
  pois?: MapPOI[]
  showCapitals?: boolean
  showRegions?: boolean
  regionState?: RegionState
  // Custom universe map
  customMapUrl?: string
  featureIdProp?: string
  initialTerritories?: Record<string, string>
}

const WorldMap = memo(function WorldMap({
  countries,
  playerCountryId,
  selectedCountryId,
  onSelectCountry,
  viewMode,
  pois = [],
  showCapitals = true,
  showRegions = true,
  regionState,
  customMapUrl,
  featureIdProp = 'id',
  initialTerritories = {},
}: Props) {
  const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null)

  // Focus on the player's capital on load
  const playerCapital = CAPITALS[playerCountryId]
  const LARGE_COUNTRIES = new Set(['RUS','CAN','USA','CHN','BRA','AUS'])
  const MID_COUNTRIES   = new Set(['IND','KAZ','ARG','MEX','IDN','SAU','IRN','NGA','EGY'])
  const initialZoom = LARGE_COUNTRIES.has(playerCountryId) ? 1.8
                    : MID_COUNTRIES.has(playerCountryId)   ? 2.5
                    : 3.5
  const [zoom, setZoom] = useState(playerCapital ? initialZoom : 1)
  const [center, setCenter] = useState<[number, number]>(playerCapital?.coords ?? [10, 20])

  const playerCountry = countries[playerCountryId]

  function getFillColor(numericId: string): string {
    const alpha3 = NUMERIC_TO_ALPHA3[numericId]
    if (!alpha3) return '#1e293b'

    if (alpha3 === playerCountryId) return '#f59e0b'
    if (alpha3 === selectedCountryId) return '#60a5fa'

    const country = countries[alpha3]

    if (!GAME_COUNTRY_IDS.has(alpha3)) {
      // Non-game country: neutral fill regardless of view mode
      return '#283548'
    }

    if (!country) return '#1e293b'

    if (viewMode === 'relations' && playerCountry) {
      return getRelationColor(playerCountry.relations[alpha3] ?? 0)
    }
    if (viewMode === 'stability') return getStabilityColor(country.stability ?? 50)
    return country.color || '#334155'
  }

  function getAdmin1Fill(geo: GeoRecord): string {
    const adm1Code = (geo.properties as Record<string, unknown>)?.adm1_code as string | undefined
    if (!adm1Code || !regionState) return 'none'
    const occupied = regionState.occupied[adm1Code]
    if (occupied) {
      if (viewMode === 'relations' && playerCountry) {
        return getRelationColor(playerCountry.relations[occupied.occupied_by] ?? 0)
      }
      return countries[occupied.occupied_by]?.color ?? '#ef4444'
    }
    const independent = regionState.independent[adm1Code]
    if (independent) {
      return countries[independent.country_id]?.color ?? '#7c3aed'
    }
    return 'none'
  }

  function getAdmin1Tooltip(geo: GeoRecord): string | null {
    const adm1Code = (geo.properties as Record<string, unknown>)?.adm1_code as string | undefined
    if (!adm1Code || !regionState) return null
    const occupied = regionState.occupied[adm1Code]
    if (occupied) {
      const occName = countries[occupied.occupied_by]?.name ?? occupied.occupied_by
      return `🚩 ${occupied.region_name} — Occupé par ${occName}`
    }
    const independent = regionState.independent[adm1Code]
    if (independent) {
      const newName = countries[independent.country_id]?.name ?? independent.country_id
      return `🆓 ${independent.region_name} → ${newName} (indépendant depuis ${independent.since_year})`
    }
    return null
  }

  function getCountryLabel(alpha3: string): string {
    const gameCountry = countries[alpha3]
    if (gameCountry) return `${gameCountry.flag || ''} ${gameCountry.name}`
    const worldName = WORLD_NAMES[alpha3]
    if (worldName) return worldName
    return alpha3
  }

  return (
    <div className="relative w-full h-full select-none">
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ scale: 130, center: [10, 20] }}
        style={{ width: '100%', height: '100%' }}
      >
        {/* react-simple-maps v3 removed onMoveEnd from types but the prop still works at runtime */}
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        <ZoomableGroup
          zoom={zoom}
          center={center}
          minZoom={0.8}
          maxZoom={12}
          {...({
            onMoveEnd: ({ zoom: z, coordinates }: { zoom: number; coordinates: [number, number] }) => {
              setZoom(z)
              setCenter(coordinates)
            },
          } as any)}
        >

          {customMapUrl ? (
            /* ── Custom universe map ── */
            <Geographies geography={customMapUrl}>
              {({ geographies }: { geographies: GeoRecord[] }) =>
                geographies.map((geo: GeoRecord) => {
                  const props = geo.properties as Record<string, unknown>
                  const featureId = String(
                    featureIdProp === '_feature_id'
                      ? (geo.id ?? '')
                      : (props[featureIdProp] ?? geo.id ?? '')
                  )
                  const factionId = initialTerritories[featureId] ?? featureId
                  const faction = countries[factionId]
                  const isPlayer = factionId === playerCountryId
                  const isSelected = factionId === selectedCountryId
                  const displayName = String(props.name ?? props.NAME ?? props.label ?? featureId)

                  let fill: string
                  if (isPlayer) fill = '#f59e0b'
                  else if (isSelected) fill = '#60a5fa'
                  else if (faction) {
                    if (viewMode === 'relations' && playerCountry)
                      fill = getRelationColor(playerCountry.relations[factionId] ?? 0)
                    else if (viewMode === 'stability')
                      fill = getStabilityColor(faction.stability ?? 50)
                    else fill = faction.color || '#334155'
                  } else fill = '#1e293b'

                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill={fill}
                      stroke="#0f172a"
                      strokeWidth={0.5}
                      style={{
                        default: { outline: 'none' },
                        hover: {
                          fill: isPlayer ? '#fbbf24' : isSelected ? '#93c5fd' : faction ? '#475569' : '#2e3f52',
                          outline: 'none',
                          cursor: faction ? 'pointer' : 'default',
                        },
                        pressed: { outline: 'none' },
                      }}
                      onMouseEnter={(e: MouseEvent<SVGPathElement>) =>
                        setTooltip({
                          x: e.clientX, y: e.clientY,
                          text: faction ? `${faction.flag || ''} ${faction.name} — ${displayName}` : displayName,
                        })
                      }
                      onMouseLeave={() => setTooltip(null)}
                      onClick={() => {
                        if (faction && factionId !== playerCountryId) onSelectCountry(factionId)
                      }}
                    />
                  )
                })
              }
            </Geographies>
          ) : (
            <>
              {/* Country fills */}
              <Geographies geography={GEO_URL}>
                {({ geographies }: { geographies: GeoRecord[] }) =>
                  geographies.map((geo: GeoRecord) => {
                    const numericId = String(geo.id)
                    const alpha3 = NUMERIC_TO_ALPHA3[numericId] || ''
                    const isGame = GAME_COUNTRY_IDS.has(alpha3)
                    const isPlayer = alpha3 === playerCountryId
                    const isSelected = alpha3 === selectedCountryId
                    return (
                      <Geography
                        key={geo.rsmKey}
                        geography={geo}
                        fill={getFillColor(numericId)}
                        stroke="#0f172a"
                        strokeWidth={0.3}
                        style={{
                          default: { outline: 'none' },
                          hover: {
                            fill: isPlayer ? '#fbbf24'
                              : isSelected ? '#93c5fd'
                              : isGame ? '#475569'
                              : '#2e3f52',
                            outline: 'none',
                            cursor: isGame ? 'pointer' : 'default',
                          },
                          pressed: { outline: 'none' },
                        }}
                        onMouseEnter={(e: MouseEvent<SVGPathElement>) => {
                          if (!alpha3) return
                          setTooltip({ x: e.clientX, y: e.clientY, text: getCountryLabel(alpha3) })
                        }}
                        onMouseLeave={() => setTooltip(null)}
                        onClick={() => {
                          if (alpha3 && isGame && alpha3 !== playerCountryId) onSelectCountry(alpha3)
                        }}
                      />
                    )
                  })
                }
              </Geographies>

              {/* Province/state internal borders — colored when occupied or independent */}
              <Geographies geography={GEO_ADMIN1_URL}>
                {({ geographies }: { geographies: GeoRecord[] }) =>
                  geographies.map((geo: GeoRecord) => {
                    const fill = getAdmin1Fill(geo)
                    const tip = getAdmin1Tooltip(geo)
                    const isActive = fill !== 'none'
                    return (
                      <Geography
                        key={geo.rsmKey}
                        geography={geo}
                        fill={fill}
                        stroke="#0f172a"
                        strokeWidth={0.45}
                        style={{
                          default: { outline: 'none' },
                          hover:   { fill: isActive ? fill : 'none', outline: 'none' },
                          pressed: { outline: 'none' },
                        }}
                        onMouseEnter={tip ? (e) => setTooltip({ x: e.clientX, y: e.clientY, text: tip }) : undefined}
                        onMouseLeave={tip ? () => setTooltip(null) : undefined}
                        onClick={isActive ? () => {
                          const adm1Code = (geo.properties as Record<string, unknown>)?.adm1_code as string
                          const ind = regionState?.independent[adm1Code]
                          const occ = regionState?.occupied[adm1Code]
                          const targetId = ind?.country_id ?? occ?.occupied_by
                          if (targetId && targetId !== playerCountryId) onSelectCountry(targetId)
                        } : undefined}
                      />
                    )
                  })
                }
              </Geographies>
            </>
          )}

          {/* Region labels — world map only */}
          {!customMapUrl && showRegions && REGIONS.map((region) => (
            <Marker key={region.name} coordinates={region.coords}>
              <text
                textAnchor="middle"
                style={{
                  fontSize: '7px',
                  fontWeight: '700',
                  letterSpacing: '0.08em',
                  fill: region.color,
                  opacity: 0.45,
                  pointerEvents: 'none',
                  userSelect: 'none',
                  fontFamily: 'Inter, system-ui, sans-serif',
                }}
              >
                {region.name}
              </text>
            </Marker>
          ))}

          {/* Capital markers — world map only */}
          {!customMapUrl && showCapitals && Object.entries(CAPITALS).map(([countryId, capital]) => {
            const country = countries[countryId]
            if (!country) return null
            const isPlayer = countryId === playerCountryId
            return (
              <Marker
                key={`cap-${countryId}`}
                coordinates={capital.coords}
                onMouseEnter={(e) => setTooltip({
                  x: e.clientX, y: e.clientY,
                  text: `🏛️ ${capital.name} · ${country.flag || ''} ${country.name}`,
                })}
                onMouseLeave={() => setTooltip(null)}
              >
                <circle
                  r={isPlayer ? 3.5 / zoom : 2 / zoom}
                  fill={isPlayer ? '#f59e0b' : 'white'}
                  stroke="#0f172a"
                  strokeWidth={0.8 / zoom}
                  opacity={0.85}
                />
                {isPlayer && (
                  <circle r={6 / zoom} fill="none" stroke="#f59e0b" strokeWidth={0.8 / zoom} opacity={0.4} />
                )}
              </Marker>
            )
          })}

          {/* Game-generated POI markers */}
          {pois.map((poi) => (
            <Marker
              key={poi.id}
              coordinates={poi.coordinates as [number, number]}
              onMouseEnter={(e) => setTooltip({ x: e.clientX, y: e.clientY, text: `${poi.icon} ${poi.name}` })}
              onMouseLeave={() => setTooltip(null)}
            >
              <circle r={4 / zoom} fill="#f59e0b" stroke="#0f172a" strokeWidth={1 / zoom} opacity={0.9} />
              <text
                textAnchor="middle"
                y={-6 / zoom}
                style={{ fontSize: `${10 / zoom}px`, pointerEvents: 'none', userSelect: 'none' }}
              >
                {poi.icon}
              </text>
            </Marker>
          ))}

        </ZoomableGroup>
      </ComposableMap>

      {/* Zoom controls */}
      <div className="absolute top-3 right-3 flex flex-col gap-1">
        <button
          onClick={() => setZoom((z) => Math.min(12, +(z * 1.5).toFixed(2)))}
          className="w-8 h-8 bg-pax-panel border border-pax-border rounded-lg flex items-center justify-center text-slate-300 hover:text-white hover:border-slate-500 transition-colors"
          title="Zoom in"
        >
          <Plus className="w-4 h-4" />
        </button>
        <button
          onClick={() => setZoom((z) => Math.max(0.8, +(z / 1.5).toFixed(2)))}
          className="w-8 h-8 bg-pax-panel border border-pax-border rounded-lg flex items-center justify-center text-slate-300 hover:text-white hover:border-slate-500 transition-colors"
          title="Zoom out"
        >
          <Minus className="w-4 h-4" />
        </button>
        <button
          onClick={() => { setZoom(1); setCenter([10, 20]) }}
          className="w-8 h-8 bg-pax-panel border border-pax-border rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:border-slate-500 transition-colors"
          title="Reset view"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 bg-pax-dark border border-pax-border rounded px-2 py-1 text-xs pointer-events-none"
          style={{ left: tooltip.x + 12, top: tooltip.y - 8 }}
        >
          {tooltip.text}
        </div>
      )}

      {/* Legend */}
      {viewMode === 'relations' && (
        <div className="absolute bottom-3 left-3 panel p-2 text-xs space-y-1">
          <div className="text-slate-400 font-medium mb-1">Relations</div>
          {[
            { color: '#f59e0b', label: 'Vous' },
            { color: '#22c55e', label: 'Allié (>60)' },
            { color: '#86efac', label: 'Ami (20-60)' },
            { color: '#94a3b8', label: 'Neutre' },
            { color: '#f97316', label: 'Hostile (-60–20)' },
            { color: '#ef4444', label: 'Ennemi (<-60)' },
            { color: '#283548', label: 'Hors scénario' },
          ].map(({ color, label }) => (
            <div key={label} className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm" style={{ background: color }} />
              <span className="text-slate-300">{label}</span>
            </div>
          ))}
          <div className="border-t border-pax-border mt-1.5 pt-1.5 space-y-1">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 flex items-center justify-center">
                <div className="w-2 h-2 rounded-full bg-white opacity-80" />
              </div>
              <span className="text-slate-400">Capitale</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 flex items-center justify-center">
                <div className="w-2.5 h-2.5 rounded-full bg-pax-gold opacity-90" />
              </div>
              <span className="text-slate-400">POI</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
})

export default WorldMap
