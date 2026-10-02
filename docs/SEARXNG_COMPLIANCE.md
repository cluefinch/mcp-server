# SearXNG integration and release requirements

## Current boundary

`mcp_search` calls the documented SearXNG HTTP `/search` API with JSON output.
SearXNG runs as a separate service, configured by `MCP_SEARCH_SEARXNG_URL`.
The core does not import SearXNG Python modules. Its page-fetching functionality
operates separately. The sample configuration selects upstream engine settings;
it is not a repository of SearXNG source code.

These facts support treating the core and SearXNG as separate programs. They do
not constitute a legal safe harbor: copied code, plugins, shared internal data
structures, or a redesigned combined program require renewed analysis. AGPL
section 5 distinguishes an aggregate of independent works from a larger program.
Separate repositories, processes, or containers do not alone determine that issue.

## Release scenarios

| Scenario | Required action |
|---|---|
| Own-code wheel/sdist; user obtains upstream services separately | Include core licensing, identify dependencies and separate upstream license; verify no third-party code was accidentally bundled. |
| Installer retrieves upstream image directly | Record exact reference and origin; identify upstream terms. Verify whether any cache, proxy, CDN, or installer actually conveys a copy on your behalf. |
| Image mirror, offline installer, appliance or bundled SearXNG | Inventory all shipped components; preserve licenses/notices; supply exact Corresponding Source using an applicable AGPL section 6 method, including build/install scripts where required. |
| Modified SearXNG offered over a network | Apply AGPL section 13: prominently offer interacting users free access to Corresponding Source of the deployed modified version. Include a usable route for API/front-end users; a hidden backend footer is not sufficient evidence. |
| Truly unmodified hosted SearXNG | Section 13 is expressly framed around modification; do not claim all hosting automatically triggers it. Preserve existing notices/offers and verify the actual image and deployment changes. Distribution to clients is a separate question. |
| Independent commercial control plane/support | Commercial activity is permitted, but do not impose proprietary restrictions on recipients' AGPL rights or present upstream authors as support providers. |
| SearXNG plugins, copied engines, imports or patches | Keep applicable upstream licensing and review the combined-work scope before distribution/network deployment. |

## Image and source evidence

The sample Compose configuration uses the upstream `searxng/searxng:latest`
image as a convenience default. It is not a reproducibility guarantee and does
not mean that every image later published under `latest` has been validated
with a particular Cluefinch release.

Operators that require a reproducible deployment can set `SEARXNG_IMAGE` to an
explicit version or digest and validate that image in their own environment.

If Cluefinch publishes, mirrors, bundles, or otherwise distributes a specific
SearXNG image as part of a supported deployment, record the exact registry
reference and digest, supported platform, upstream revision, applicable
licenses and notices, local modifications, source archive hash, build/install
instructions, and source download location. Do not claim an image as tested or
supported unless that exact image has actually been validated.

For an online object-code distribution under section 6(d), place clear source
directions next to the binary download and provide equivalent source access at
no additional charge. Third-party source hosting can be used under that
provision, but responsibility for continued availability stays with the
distributor. An upstream `master` link alone does not demonstrate source
correspondence. The three-year written-offer route in section 6(b) is not a
universal rule for every online release; choose the applicable method
deliberately.

Corresponding Source is broader than a patch: include the covered source and
scripts needed to generate, install, run and modify the covered work, subject
to the license's exclusions. Check installation-information obligations if
distributing a qualifying User Product. Do not publish real credentials or user
data; provide buildable examples and document configuration requirements.

## Commercial terms

Any future proprietary agreement must identify its covered components and leave
open-source license rights intact. Do not apply blanket restrictions on copying,
modification, redistribution or reverse engineering to AGPL components. Support,
warranties and indemnities are commitments of the named service provider alone.
Do not promise exclusive ownership of independently contributed Apache code.

The core license grants no rights to search-provider services or fetched content.
Assess provider terms, copyright/database rights, privacy, retention and customer
contracts for an actual hosted product. The local example is not a public-service
security or legal deployment profile.

## Primary sources

- [SearXNG API](https://docs.searxng.org/dev/search_api.html)
- [SearXNG upstream AGPL text](https://github.com/searxng/searxng/blob/master/LICENSE), sections 0–6, 10, 13
- [GNU FAQ: aggregation](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation), interpretive guidance rather than a court ruling
- [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0), sections 1–6 and 9

This policy describes the reviewed architecture. Release-specific ownership,
artifact and deployment evidence must still be completed by the maintainer.
