from agentbetta.settings import AppSettings, ModelCatalog, ModelProfile


def test_uid_and_tier_label():
    model = ModelProfile(provider_id="p1", model_id="m1", tier=0)
    assert model.uid == "p1::m1"
    assert model.tier_label == "economical"
    assert ModelProfile(provider_id="p", model_id="m", tier=2).tier_label == "high capability"


def test_catalog_add_remove_lookup():
    catalog = ModelCatalog()
    model = ModelProfile(provider_id="p1", model_id="m1")
    catalog.add(model)
    assert catalog.get("p1::m1") is not None
    assert [m.model_id for m in catalog.for_provider("p1")] == ["m1"]
    catalog.remove("p1::m1")
    assert catalog.get("p1::m1") is None


def test_catalog_dedupes_by_uid():
    catalog = ModelCatalog()
    catalog.add(ModelProfile(provider_id="p", model_id="m", display_name="A"))
    catalog.add(ModelProfile(provider_id="p", model_id="m", display_name="B"))
    assert len(catalog.all()) == 1
    assert catalog.get("p::m").display_name == "B"


def test_tier_mapping_resolves_to_model():
    model = ModelProfile(provider_id="p", model_id="m", tier=2)
    settings = AppSettings(models=[model], tier_map={"2": "p::m"})
    assert settings.model_for_tier(2).model_id == "m"
    assert settings.model_for_tier(0) is None
