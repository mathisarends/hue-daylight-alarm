# Release process

Huerise uses one semantic version for the API container and the CLI. A Git tag
such as `v2.1.0` starts the release workflow and produces both artifacts from
the tagged commit.

## Published artifacts

Each release publishes:

- a multi-platform container image for `linux/amd64` and `linux/arm64` at
  `ghcr.io/mathisarends/huerise`;
- CLI archives for Linux, macOS, and Windows on AMD64 and ARM64;
- `checksums.txt` containing SHA-256 checksums for the CLI archives;
- build provenance attestations for the CLI archives and container image;
- generated release notes in a GitHub Release.

For version `2.1.0`, the container receives these tags:

```text
ghcr.io/mathisarends/huerise:2.1.0
ghcr.io/mathisarends/huerise:2.1
ghcr.io/mathisarends/huerise:2
ghcr.io/mathisarends/huerise:latest
```

Deployments should pin the full version instead of `latest`.

## One-time repository setup

GitHub Actions uses the repository `GITHUB_TOKEN`; no personal access token is
required. In the repository settings, enable read and write workflow
permissions. After the first image has been published, set the
`ghcr.io/mathisarends/huerise` package visibility to public if anonymous pulls
should be allowed.

Do not create the `2`, `2.1`, or `latest` image tags manually. The release
workflow maintains them.

## Prepare a release

Start from an up-to-date, clean `main` branch. Choose the next version using
semantic versioning:

- increment PATCH for backward-compatible fixes;
- increment MINOR for backward-compatible features;
- increment MAJOR for incompatible API, CLI, or configuration changes.

Update `huerise/version.py` without the `v` prefix:

```python
__version__ = "2.1.0"
```

Run the same checks used by CI:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run python scripts/export_openapi.py
cd cli
go generate ./...
go test ./...
go vet ./...
cd ..
git diff --exit-code -- specs/openapi.json cli/internal/client
```

Optionally validate the CLI packaging locally with GoReleaser:

```bash
goreleaser check
goreleaser release --snapshot --clean --skip=publish
```

Commit and push the version change:

```bash
git add huerise/version.py
git commit -m "Release 2.1.0"
git push origin main
```

Wait for the `CI` workflow on `main` to succeed before creating the tag.

## Publish a release

Create an annotated tag on the verified release commit and push it:

```bash
git tag -a v2.1.0 -m "Huerise 2.1.0"
git push origin v2.1.0
```

Only tags matching `vMAJOR.MINOR.PATCH` are accepted. The workflow also checks
that the tag without its `v` prefix exactly matches `__version__`. It then:

1. repeats all Python, Go, OpenAPI, lint, and formatting checks;
2. builds and attests the CLI archives without publishing them;
3. builds, attests, and pushes the multi-platform container image;
4. creates the GitHub Release and attaches the CLI archives and checksums.

The GitHub Release is created last. A failed CLI or container build therefore
does not create a public release entry.

## Verify and install

Check the CLI archive after downloading it:

```bash
sha256sum --check checksums.txt
gh attestation verify huerise_2.1.0_linux_amd64.tar.gz \
  --repo mathisarends/huerise
```

Verify and pull the container:

```bash
gh attestation verify oci://ghcr.io/mathisarends/huerise:2.1.0 \
  --repo mathisarends/huerise
docker pull ghcr.io/mathisarends/huerise:2.1.0
```

Configure a deployment with the exact image version and update it with:

```yaml
services:
  daylight-alarm:
    image: ghcr.io/mathisarends/huerise:2.1.0
```

Replace the local `build:` section in `compose.yml` with `image:` for a
release deployment. Keep the existing environment, ports, and volume settings.
Then update the running service with:

```bash
docker compose pull
docker compose up -d
```

## Failed releases

If an infrastructure or upload step fails without any source change, rerun the
failed workflow from GitHub Actions. If code or generated artifacts must change,
do not move or reuse the published tag. Commit the fix, increment the version,
and create a new tag.
