---
name: Schema or example bug
about: Report a schema that's wrong, an example that doesn't validate, or a real-world message the spec can't represent
labels: bug
---

**What's wrong**
One sentence: schema is too strict, schema is too permissive, example is incorrect, or real message can't be represented.

**Minimal reproduction**
The smallest JSON message that demonstrates the issue. If reporting a schema-too-strict bug, paste the message and the validation error you got. If reporting a real-message-can't-be-represented bug, paste a sanitized version of the real message and call out which field(s) don't have a home.

**Expected behavior**
What you think the spec should accept or reject, and why.
