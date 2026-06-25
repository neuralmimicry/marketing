# Webots

## Positioning

Webots is the browser-only embodiment surface for AARNN users on the commercial platform. It allows authenticated users to select a world profile, hand off identity from the shared commercial login, and launch a browser simulation that remains tied to AARNN sensory and actuator assets.

## Best fit

- Demonstration workflows for AARNN
- Internal enablement and sales engineering
- Embodied AI researchers who need a browser-first launch path
- Buyers who want a visible, testable embodiment rather than abstract runtime claims

## Proof themes

- Central auth handoff matters because the user is not asked to manage another tool-specific account.
- Browser-only launch lowers friction for demonstrations and evaluations.
- World profiles should stay explicit: C. elegans, Drosophila BANC, Drosophila FAFB, and NAO.
- Every world should be described as tied back to generated AARNN alignment metadata.

## Capture ideas

- the Webots launch page and world cards from the commercial website
- browser launch flow and workspace naming
- AARNN-to-Webots relationship in the wider product story

## Training angle

Show sign-in state, world selection, workspace naming, launch handoff, and what the user should verify once the browser simulation opens.

## Source of truth

- Website: `/home/pbisaacs/Developer/neuralmimicry.ai-website/src/webots.jsx`
- Auth helpers: `/home/pbisaacs/Developer/neuralmimicry.ai-website/src/lib/webotsAuth.js`
- Deployment: `/home/pbisaacs/Developer/swarmhpc/swarmhpc/ansible/continuum_tenant_webots_site.yml`
- Host/runtime settings: `/home/pbisaacs/Developer/swarmhpc/swarmhpc/ansible/host_vars/spirit.yml`
