---
name: list-voices
description: List all installed text-to-speech voices available to say4linux
user-invocable: true
allowed-tools: Bash
---

# List Installed Voices

Run the say command to list all available voices:

```bash
say -v list
```

Show the user the available voices grouped by language (US vs UK) and quality level (low, medium, high). Suggest good defaults for different use cases:
- **Notifications/hooks**: low quality voices (fastest synthesis)
- **General use**: medium quality (good balance)
- **Saved audio files**: high quality (best fidelity)
