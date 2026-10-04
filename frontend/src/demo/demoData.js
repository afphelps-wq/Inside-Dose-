// FICTIONAL demo drugs. Every name and number here is made up to show the UI;
// none of it describes a real medicine. Real data arrives from the API in M2+.

export const DEMO_DRUGS = [
  {
    rxcui: 'demo1',
    generic: 'sampleol',
    brands: ['Samplor'],
    common_use: 'Demo: blood pressure',
    molecule: { formula: 'C10H12O2', weight: 164.2 },
    targets: [
      { gene: 'DEMO1R', name: 'Demo receptor 1', action: 'blocker',
        plain_description: 'A made-up receptor that, in this demo, speeds up the heart.' },
    ],
    body_map: {
      heart: { level: 'high', basis: 'protein', targets: ['DEMO1R'] },
      blood_vessels: { level: 'medium', basis: 'protein', targets: ['DEMO1R'] },
      kidneys: { level: 'low', basis: 'rna', targets: ['DEMO1R'] },
      brain: { level: 'low', basis: 'protein', targets: ['DEMO1R'] },
    },
    curated: {
      dose_mg: { min: 25, max: 200, typical: 50, intervals_h: [12, 24] },
      pk: { bioavailability: 0.5, half_life: 6, vd: 1.0, vd_unit: 'L/kg', tmax: 1.5 },
      enzymes: [{ name: 'DEMO-ENZYME-A', role: 'substrate', importance: 'major' }],
      effects: ['lowers_blood_pressure'],
      journey: [
        { step: 'absorption', organ: 'intestines', text: 'Demo: soaks in from the gut.' },
        { step: 'metabolism', organ: 'liver', text: 'Demo: broken down by Demo Enzyme A.' },
        { step: 'action', organ: 'heart', text: 'Demo: calms the heart.' },
        { step: 'elimination', organ: 'kidneys', text: 'Demo: leaves in urine.' },
      ],
    },
  },
  {
    rxcui: 'demo2',
    generic: 'examplatin',
    brands: ['Exampra'],
    common_use: 'Demo: blood thinner',
    molecule: { formula: 'C18H20N4O3', weight: 340.4 },
    targets: [
      { gene: 'DEMOF', name: 'Demo clotting factor', action: 'inhibitor',
        plain_description: 'A made-up protein that, in this demo, helps blood clot.' },
    ],
    body_map: {
      liver: { level: 'high', basis: 'protein', targets: ['DEMOF'] },
      blood_vessels: { level: 'medium', basis: 'rna', targets: ['DEMOF'] },
      lungs: { level: 'low', basis: 'protein', targets: ['DEMOF'] },
    },
    curated: {
      dose_mg: { min: 10, max: 40, typical: 20, intervals_h: [24] },
      pk: { bioavailability: 0.8, half_life: 12, vd: 50, vd_unit: 'L', tmax: 3 },
      enzymes: [],
      effects: ['anticoagulant'],
      journey: [
        { step: 'absorption', organ: 'stomach', text: 'Demo: absorbed in the stomach.' },
        { step: 'distribution', organ: 'blood_vessels', text: 'Demo: travels in the blood.' },
        { step: 'action', organ: 'liver', text: 'Demo: slows clotting factors made in the liver.' },
        { step: 'elimination', organ: 'intestines', text: 'Demo: leaves through the gut.' },
      ],
    },
  },
  {
    rxcui: 'demo3',
    generic: 'mockafen',
    brands: ['Mockeze'],
    common_use: 'Demo: pain relief',
    molecule: { formula: 'C13H18O2', weight: 206.3 },
    targets: [
      { gene: 'DEMOX1', name: 'Demo pain enzyme', action: 'inhibitor',
        plain_description: 'A made-up enzyme that, in this demo, makes pain signals.' },
    ],
    body_map: {
      stomach: { level: 'high', basis: 'protein', targets: ['DEMOX1'] },
      kidneys: { level: 'medium', basis: 'protein', targets: ['DEMOX1'] },
      muscle: { level: 'low', basis: 'rna', targets: ['DEMOX1'] },
      skin: { level: 'low', basis: 'protein', targets: ['DEMOX1'] },
    },
    curated: {
      dose_mg: { min: 200, max: 800, typical: 400, intervals_h: [6, 8] },
      pk: { bioavailability: 0.9, half_life: 2, vd: 0.15, vd_unit: 'L/kg', tmax: 1 },
      enzymes: [{ name: 'DEMO-ENZYME-A', role: 'inhibitor', strength: 'moderate' }],
      effects: ['nsaid'],
      journey: [
        { step: 'absorption', organ: 'stomach', text: 'Demo: absorbed quickly.' },
        { step: 'action', organ: 'muscle', text: 'Demo: quiets pain signals.' },
        { step: 'metabolism', organ: 'liver', text: 'Demo: broken down in the liver.' },
        { step: 'elimination', organ: 'kidneys', text: 'Demo: leaves in urine.' },
      ],
    },
  },
]

// Fictional subset of the spec §6.1 effect-rule table, enough for the demo.
export const DEMO_EFFECT_RULES = [
  { a: 'anticoagulant', b: 'nsaid', severity: 'major',
    plain_message: 'Together these can raise the risk of bleeding.' },
  { a: 'nsaid', b: 'lowers_blood_pressure', severity: 'moderate',
    plain_message: 'Pain-relief drugs like this can weaken blood pressure medicines.' },
]

export function findDemoDrug(rxcui) {
  return DEMO_DRUGS.find((drug) => drug.rxcui === rxcui)
}

export function displayName(drug) {
  return drug.brands.length ? `${drug.brands[0]} (${drug.generic})` : drug.generic
}
