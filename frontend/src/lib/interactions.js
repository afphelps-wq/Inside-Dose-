// Interaction rules (spec §6.1).

const ENZYME_SEVERITY = {
  strong: { major: 'major', minor: 'moderate' },
  moderate: { major: 'moderate', minor: 'minor' },
  weak: { major: 'minor', minor: 'minor' },
}
const SEVERITY_ORDER = { major: 0, moderate: 1, minor: 2 }

function enzymeFindings(a, b) {
  const findings = []
  for (const actor of a.curated.enzymes) {
    if (actor.role === 'substrate') continue
    for (const target of b.curated.enzymes) {
      if (target.role !== 'substrate' || target.name !== actor.name) continue
      const verb = actor.role === 'inhibitor' ? 'raise' : 'lower'
      findings.push({
        drugs: [a.rxcui, b.rxcui],
        type: 'enzyme',
        severity: ENZYME_SEVERITY[actor.strength][target.importance],
        mechanism: `${a.generic} is a ${actor.strength} ${actor.role} of ${actor.name}, which clears ${b.generic}.`,
        plain_message: `${a.generic} can ${verb} ${b.generic} levels in the blood.`,
      })
    }
  }
  return findings
}

function effectFindings(a, b, rules) {
  const findings = []
  for (const rule of rules) {
    const matches =
      (a.curated.effects.includes(rule.a) && b.curated.effects.includes(rule.b)) ||
      (a.curated.effects.includes(rule.b) && b.curated.effects.includes(rule.a))
    if (matches) {
      findings.push({
        drugs: [a.rxcui, b.rxcui],
        type: 'effect',
        severity: rule.severity,
        mechanism: `${rule.a.replaceAll('_', ' ')} + ${rule.b.replaceAll('_', ' ')}`,
        plain_message: rule.plain_message,
      })
    }
  }
  return findings
}

export function checkInteractions(drugs, effectRules) {
  const checked = drugs.filter((drug) => drug.curated)
  const findings = []
  for (let i = 0; i < checked.length; i++) {
    for (let j = i + 1; j < checked.length; j++) {
      const [a, b] = [checked[i], checked[j]]
      findings.push(...enzymeFindings(a, b), ...enzymeFindings(b, a), ...effectFindings(a, b, effectRules))
    }
  }
  findings.sort((x, y) => SEVERITY_ORDER[x.severity] - SEVERITY_ORDER[y.severity])
  return {
    findings,
    unchecked: drugs.filter((drug) => !drug.curated).map((drug) => drug.rxcui),
  }
}
