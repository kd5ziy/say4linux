---
name: say-test
description: Test a text-to-speech voice by speaking sample text
argument-hint: [voice-name] [optional text]
user-invocable: true
allowed-tools: Bash
---

# Test a Voice

Speak sample text using a specific voice to preview how it sounds.

Parse the arguments from `$ARGUMENTS`:
- If the first word looks like a voice name (contains `en_US` or `en_GB`), use it as the voice. The rest is the text.
- If no voice name is detected, use `en_US-amy-medium` as the default voice.
- If no text is provided, use: "Hello! This is a test of the say4linux text to speech system. How do I sound?"

Run the say command with the resolved voice and text:

```bash
say -v VOICE "TEXT"
```

After playing, tell the user:
- Which voice was used
- How to set it as their default: `alias say='say -v VOICE_NAME'`
- How to see all voices: `say -v list`
