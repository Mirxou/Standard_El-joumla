# CI/CD Release Guide — v5.1.0

This guide outlines two options to automate publishing a GitHub Release.

## Option A: GitHub CLI (manual trigger)
Prereq: `gh` authenticated and `origin` set.

```powershell
# Push tag first (if not pushed)
git push origin v5.1.0

# Create release from local file body
$body = Get-Content -Raw .\GITHUB_RELEASE_BODY_v5.1.0.md
$body | gh release create v5.1.0 --title "v5.1.0 — UX Polish" --notes-file -
```

## Option B: GitHub Actions workflow (on tag)
Create `.github/workflows/release.yml`:

```yaml
name: Release
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          body_path: GITHUB_RELEASE_BODY_${{ github.ref_name }}.md
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Notes:
- Ensure a matching `GITHUB_RELEASE_BODY_<tag>.md` exists (e.g., `GITHUB_RELEASE_BODY_v5.1.0.md`).
- Alternatively set `body_path: RELEASE_v5.1.0_FINAL.md` for a fixed file.
