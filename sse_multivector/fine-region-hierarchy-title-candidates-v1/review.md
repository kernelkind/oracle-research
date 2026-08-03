# Higher-subject title candidates

This is a review aid, not an accepted hierarchy.

The starting hierarchy mechanically merged 22 reviewed fine subjects. Before
generating titles, one useless transition was removed: `H000005` and its child
`H000003` contained the same six notes. `H000003` was collapsed into
`H000005`, while all four fine subjects remained represented. The root,
`H000020`, remains implicit and untitled.

That leaves 19 possible higher subjects. For each one, an isolated
`gpt-5.6-sol` call received every descendant fine-subject title as a separate
instance and this unchanged question:

> What is the most precise and concise title for the semantic similarity among these instances?

The candidates are listed in merge order, from narrower to broader. A later
candidate may contain an earlier one. Its complete fine-subject list is shown
instead of relying on the earlier candidate's generated title.

The proposed title does not validate the grouping. Review each candidate by
asking:

> If a user selected this title, would every listed fine subject be an expected result?

## Candidates

### H000000 — Coffee Culture and Enjoyment

5 notes. Fine subjects:

- Coffee consumption and preparation
- Coffee appreciation beyond caffeine

### H000001 — Integrity Over Approval

4 notes. Fine subjects:

- Staying True to Yourself
- Character and Integrity Over External Approval

### H000002 — Sovereign, Non-Coercive Openness

5 notes. Fine subjects:

- Free and Open-Source Software for Digital Sovereignty
- Openness without imposition

### H000004 — Solar Energy System Configurations

5 notes. Fine subjects:

- Solar Energy for Sustainable, Self-Sufficient Systems
- Solar Panel Setup Descriptions

### H000005 — Integrity Under Social Pressure

6 notes. Fine subjects:

- Social Conformity and Suppressed Dissent
- Authenticity Under Constraint
- Staying True to Yourself
- Character and Integrity Over External Approval

### H000006 — Coffee Culture and Consumption

6 notes. Fine subjects:

- Coffee consumption and preparation
- Coffee appreciation beyond caffeine
- Coffee Chain Mentions

### H000007 — Integrity Under Pressure to Conform

8 notes. Fine subjects:

- Fear and Scarcity of Critical Thinking Amid Conformity
- Social Conformity and Suppressed Dissent
- Authenticity Under Constraint
- Staying True to Yourself
- Character and Integrity Over External Approval

### H000008 — Solar-Powered Home Bitcoin Mining Setup

6 notes. Fine subjects:

- Starting Bitcoin Mining at Home with a BitAxe
- Solar Energy for Sustainable, Self-Sufficient Systems
- Solar Panel Setup Descriptions

### H000009 — Coffee Consumption and Culture

8 notes. Fine subjects:

- Coffee consumption and preparation
- Coffee appreciation beyond caffeine
- Coffee Chain Mentions
- Food preparation and eating

### H000010 — Slow burn

3 notes. Fine subjects:

- Book recommendations and reviews
- Gradual realization

### H000011 — DIY Energy and Equipment Setup

7 notes. Fine subjects:

- Starting Bitcoin Mining at Home with a BitAxe
- Solar Energy for Sustainable, Self-Sufficient Systems
- Solar Panel Setup Descriptions
- Jobsite Equipment and Supply Tasks

### H000012 — Digital Sovereignty and Freedom-Preserving Technology

7 notes. Fine subjects:

- Free and Open-Source Software for Digital Sovereignty
- Openness without imposition
- Government-Controlled Programmable Money vs. Financial Freedom

### H000013 — Digital Sovereignty and Freedom from Centralized Control

8 notes. Fine subjects:

- Free and Open-Source Software for Digital Sovereignty
- Digital Privacy and Surveillance
- Openness without imposition
- Government-Controlled Programmable Money vs. Financial Freedom

### H000014 — Food and Beverage Consumption

10 notes. Fine subjects:

- Coffee consumption and preparation
- Coffee appreciation beyond caffeine
- Coffee Chain Mentions
- Food Quantities by Weight
- Food preparation and eating

### H000015 — DIY Bitcoin Mining Infrastructure, Power, and Maintenance

9 notes. Fine subjects:

- Starting Bitcoin Mining at Home with a BitAxe
- Solar Energy for Sustainable, Self-Sufficient Systems
- Solar Panel Setup Descriptions
- Jobsite Equipment and Supply Tasks
- Increasing stock-fan noise and durability concerns in Bitcoin miners

### H000016 — Authenticity and Independent Thought Amid Conformity

10 notes. Fine subjects:

- Book recommendations and reviews
- Fear and Scarcity of Critical Thinking Amid Conformity
- Gradual realization
- Social Conformity and Suppressed Dissent
- Authenticity Under Constraint
- Staying True to Yourself
- Character and Integrity Over External Approval

### H000017 — Food, Beverages, and Plant Life

11 notes. Fine subjects:

- Coffee consumption and preparation
- Coffee appreciation beyond caffeine
- Coffee Chain Mentions
- Food Quantities by Weight
- Food preparation and eating
- Nature and Plant Life

### H000018 — Personal and Digital Sovereignty Against Control and Conformity

18 notes. Fine subjects:

- Free and Open-Source Software for Digital Sovereignty
- Digital Privacy and Surveillance
- Openness without imposition
- Book recommendations and reviews
- Fear and Scarcity of Critical Thinking Amid Conformity
- Gradual realization
- Social Conformity and Suppressed Dissent
- Authenticity Under Constraint
- Staying True to Yourself
- Character and Integrity Over External Approval
- Government-Controlled Programmable Money vs. Financial Freedom

### H000019 — DIY Projects, Sustainable Living, and Everyday Consumption

19 notes. Fine subjects:

- Starting Bitcoin Mining at Home with a BitAxe
- Solar Energy for Sustainable, Self-Sufficient Systems
- Coffee consumption and preparation
- Coffee appreciation beyond caffeine
- Coffee Chain Mentions
- Solar Panel Setup Descriptions
- Jobsite Equipment and Supply Tasks
- Food Quantities by Weight
- Food preparation and eating
- Increasing stock-fan noise and durability concerns in Bitcoin miners
- Nature and Plant Life

## Provenance

- `projection.json` records the source hashes, fine-title mapping, and mechanical collapse.
- `config.json` preserves the exact 19 prompts.
- `run/manifest.json` records the isolated execution settings.
- `run/output.json` and `run/results.jsonl` preserve the responses and per-call evidence.
- An independent audit confirmed that all 19 calls succeeded on their first attempt, used fresh sterile processes, and had web and tools disabled.
