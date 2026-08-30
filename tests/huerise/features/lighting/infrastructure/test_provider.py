from huerise.features.lighting.infrastructure import (
    HueifyClientFactory,
    HueifyOnboarding,
    LightingProvider,
)


def test_provider_uses_hueify_adapters() -> None:
    provider = LightingProvider()

    assert isinstance(provider.client_factory(), HueifyClientFactory)
    assert isinstance(provider.onboarding_gateway(), HueifyOnboarding)
