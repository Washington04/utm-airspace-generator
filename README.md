**UTM Orchestrator**

_A lightweight, standards-aligned UAS Traffic Management (UTM) simulation environment_

**Note**: UTM Orchestrator is a hands-on learning project for exploring UTM technical challenges, geospatial approaches, and airspace interoperability. Contributions, suggestions, and discussions are welcome, please add any to UTM-orchestrator/community_notes. 


---

**Overview**

**UTM Orchestrator** is a developing simulation framework designed to model a full UAS Traffic Management (UTM) ecosystem in the Seattle metropolitan area.

The system generates:
- Geographical operating areas
- Operational intents (merchant → customer → hub)
- Static & dynamic constraints
- POIs and route generation
- Basic strategic deconfliction workflows

The goal is to provide a safe environment to explore how UTM services, implemented in accordance with industry consensus standards, enable safe, scalable, and transparent shared airspace operations.

This project is not intended to be an operational USS, but rather a research and learning tool that mirrors the structure of basic UTM systems.

---

**Objectives**

- Model BVLOS delivery operations in dense urban airspace
- Implement the foundational elements of a UAS Service Supplier (USS) / Airspace Data Service Provider (ADSP)
- Support simulation of strategic conflict detection, intent sharing, and inter-USS coordination
- Provide a platform for evaluating shared airspace concepts inspired by the US UTM Implementation
- Allow users to visualize routes, grids, and constraints directly within the workflow

---

**Standards & Guidance Referenced**

UTM Orchestrator is designed with reference to the FAA, ASTM, and international guidance that shapes basic UTM systems:
- ASTM F3548-21 – USS Interoperability
- 14 CFR Part 108 – UAS Operating Rules (proposed)
- 14 CFR Part 146 & AC 146-1 – Airspace Data Service Providers (proposed)
- U-Space regulatory guidance (EU)
- Shared Airspace / Strategic Coordination concepts from the US UTM Implementation

---

**Current Capabilities**

**Geospatial Grid Generation**
- Generates a meter-accurate grid over Seattle using:
  - Dynamic UTM projection
  - Polygon clipping
  - Unique cell_ids
  - Rounded centroid coordinates
- Outputs clean GeoJSON for UTM-style visualization

**Points of Interest (POI) System**
- Generates synthetic:
  - hub locations
  - merchant pickup sites
  - customer delivery points
- Outputs both CSV and GeoJSON for visual overlays

**Visualization Support**
- Native preview inside VS Code
- Layered visualization using GeoJSON standards
- Supports grid + POI overlays for operational alignment

---

**In Development (Roadmap)**

**Flight Generator** 
- Create realistic delivery missions:
  - hub → merchant → customer → hub
- Associate each flight with grid cells + coordinates
- Output per-flight operational intent objects

**Strategic Coordination Simulation**
- Identify conflicts using:
  - Spatial overlap
  - Time windows
  - Prioritization rules
- Apply “US Shared Airspace” guiding principles

**Constraint Modeling**
- Add:
  - No-fly zones / Special Use Airspace
  - Temporary flight restrictions
  - Weather constraints

---

**Long-Term** 
- UTM Orchestrator aims to serve as a sandbox environment for:
  - Simulation studies
  - Strategic coordination testing
  - Rapid prototyping of UTM concepts

Goal is to provide a simplified environment mirroring the ecosystem emerging from UTM Shared Airspace Implementation and ASTM interoperability standards.




