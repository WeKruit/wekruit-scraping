## 第一性原理
请使用第一性原理思考。你不能总是假设我非常清楚自己想要什么和该怎么得到。请保持审慎，从原始需求和问题出发，如果动机和目标不清晰，停下来和我讨论。

## 方案规范
当需要你给出修改或重构方案时必须符合以下规范：
不允许给出兼容性或补丁性的方案
不允许过度设计，保持最短路径实现且不能违反第一条要求
不允许自行给出我提供的需求以外的方案，例如一些兜底和降级方案，这可能导致业务逻辑偏移问题
必须确保方案的逻辑正确，必须经过全链路的逻辑验证

## Design Context

### Users
- Primary users are WeKruit operators reviewing sourced records from researcher, GitHub, Devpost, and future scraping pipelines before those records feed outbound workflows.
- Their working context is a dense internal console, not a marketing page: they need to inspect provenance, understand why two records may refer to the same person, approve or reject merges, and keep only reviewed entities.
- The job to be done is operational judgment under uncertainty: see the source run, inspect paper/person evidence, understand merge reasoning quickly, and move clean reviewed entities downstream into outbound.

### Brand Personality
- Three-word personality: high-judgment, restrained, trustworthy.
- Emotional target: calm confidence over excitement. The interface should feel serious, composed, and operationally clear.
- Voice and presentation should feel human and premium, not flashy, robotic, developer-terminal-like, or generic enterprise SaaS.

### Aesthetic Direction
- Use the existing WeKruit operator-console mode as the default visual language: warm ivory page surfaces, dark espresso ink, structured cards, and restrained accent color.
- Typography should follow the established WeKruit pair when practical: Halant for display moments and Geist (or closest existing body sans) for interface/body text.
- Prefer composed operator UI over debug UI. Evidence, counts, and review actions should surface first; raw JSON belongs behind disclosure.
- Anti-references: neon AI startup visuals, cold dashboard blue as the dominant color, generic admin templates, and raw JSON / terminal aesthetics as the main experience.

### Design Principles
- Show operational truth first: real source runs, record counts, merge reasons, and reviewed outcomes should be visible before manual upload/debug affordances.
- Evidence before internals: provenance, contact fields, paper metadata, and merge reasoning take priority over raw payload dumps.
- Calm density: support dense review work without feeling cluttered; use clear grouping, strong hierarchy, and restrained status color.
- One screen, one loop: the default screen should help operators move through fetch -> inspect -> review -> approved without mentally switching tools.
- Warm, not soft: keep the UI premium and human through typography, spacing, and color, but never decorative at the cost of throughput.
