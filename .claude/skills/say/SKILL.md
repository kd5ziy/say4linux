---
name: say
description: Speak text aloud using say4linux text-to-speech
argument-hint: <text to speak>
user-invocable: true
disable-model-invocation: true
allowed-tools: Bash
---

# Say Text Aloud

Speak the provided text using the say4linux text-to-speech system.

If text is provided as `$0`, speak it:

```bash
echo "$0" | say
```

If no text is provided, speak a default greeting:

```bash
say "Hello from say4linux"
```

Do not add any commentary. Just run the command.
