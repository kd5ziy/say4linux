---
name: say-test
description: Test a text-to-speech voice by speaking sample text
argument-hint: [voice-name] [optional text]
user-invocable: true
disable-model-invocation: true
allowed-tools: Bash
---

# Test a Voice

Speak sample text using a specific voice to preview how it sounds.

If a voice name is provided as `$0`, use it. Otherwise default to `en_US-amy-medium`.
If sample text is provided as remaining arguments, use it. Otherwise use "Hello! This is a test of the say4linux text to speech system. How do I sound?"

```bash
say -v "$0" "$1"
```

After playing, tell the user:
- Which voice was used
- How to set it as their default: `alias say='say -v VOICE_NAME'`
- How to see all voices: `say -v list`
