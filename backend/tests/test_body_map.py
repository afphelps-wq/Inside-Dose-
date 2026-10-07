from backend.app.services import body_map, hpa


def test_build_maps_target_to_organ(monkeypatch):
    monkeypatch.setattr(hpa, "tissue_levels", lambda gene: {"liver": {"level": "high", "basis": "rna"}})
    organs = body_map.build([{"gene": "F10"}])
    assert organs == {"liver": {"level": "high", "basis": "rna", "targets": ["F10"]}}


def test_build_skips_tissues_with_no_organ_mapping(monkeypatch):
    monkeypatch.setattr(hpa, "tissue_levels", lambda gene: {"testis": {"level": "high", "basis": "rna"}})
    assert body_map.build([{"gene": "SOME-GENE"}]) == {}


def test_build_normalizes_numbered_tissue_suffix(monkeypatch):
    monkeypatch.setattr(hpa, "tissue_levels", lambda gene: {"skin 1": {"level": "medium", "basis": "protein"}})
    assert body_map.build([{"gene": "G"}]) == {"skin": {"level": "medium", "basis": "protein", "targets": ["G"]}}


def test_build_uses_highest_level_across_multiple_targets(monkeypatch):
    def fake_levels(gene):
        return {
            "GENE_A": {"liver": {"level": "medium", "basis": "rna"}},
            "GENE_B": {"liver": {"level": "high", "basis": "protein"}},
        }[gene]
    monkeypatch.setattr(hpa, "tissue_levels", fake_levels)

    organs = body_map.build([{"gene": "GENE_A"}, {"gene": "GENE_B"}])
    assert organs == {"liver": {"level": "high", "basis": "protein", "targets": ["GENE_B"]}}


def test_build_collects_multiple_targets_at_the_same_level(monkeypatch):
    def fake_levels(gene):
        return {
            "GENE_A": {"liver": {"level": "high", "basis": "protein"}},
            "GENE_B": {"liver": {"level": "high", "basis": "rna"}},
        }[gene]
    monkeypatch.setattr(hpa, "tissue_levels", fake_levels)

    organs = body_map.build([{"gene": "GENE_A"}, {"gene": "GENE_B"}])
    assert organs["liver"]["level"] == "high"
    assert set(organs["liver"]["targets"]) == {"GENE_A", "GENE_B"}


def test_build_skips_targets_with_no_gene():
    assert body_map.build([{"gene": None}, {}]) == {}


def test_build_empty_for_no_targets():
    assert body_map.build([]) == {}
