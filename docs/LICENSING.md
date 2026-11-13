# Licensing boundaries

These are separate licensing decisions and must not be conflated:

- **Repository source code:** proprietary, all rights reserved, as the root `LICENSE` states.
  Marius ruled this on 6 November 2026. Public repository visibility does not grant a licence.
- **Generated MPFB character assets:** the current receipt labels the selected MPFB-derived model
  output as CC0. Reconfirm the licence of every newly selected MPFB asset before publication.
- **Faceunits 01 expression assets:** the official MakeHuman Community pack page declares this
  functional asset pack CC0. The installed pack manifest and used target files are hashed in each
  reference-catch receipt.
- **Kit assets authored in this repository (`assets/kit/`):** meshes cut from the CC0 MakeHuman
  basemesh helpers by `scripts/author_netball_dress.py`, and images drawn by
  `scripts/make_bib_image.py`. They are the work of Braven Performance Lab, and all rights are
  reserved, as for the source code. Each one is hashed in every receipt that wears it.
  The label "own work, no licence selected" in the two `.mhclo` headers, in `config/kit/` and in
  receipts predates that ruling. The headers are part of the hashed meshes, so the label changes
  only when the kit is authored again. Until then the root `LICENSE` governs, not the label.
- **The shared athlete's build output (the files an `athlete-manifest.json` lists):** the MPFB
  body with the kit and the lettering, built by the Models lane. Marius ruled on 13 November 2026
  that it is the work of Braven Performance Lab, all rights reserved. The ruling covers the build
  file the manifest names as its master. Each external asset the manifest lists keeps its own
  determination above, and the renderer refuses one that has none.
- **Reference photographs:** the current photograph is not stored in Git. Its configured hash is
  provenance evidence, not a redistribution permission.
- **Cascadeur samples:** Cascy and UE5 Quinn were used only for internal mechanism/rig evaluation.
  Do not publish them without a written licence determination.

The root `LICENSE` records the owner's choice for the source code and the kit. A change to it is
the owner's decision.
