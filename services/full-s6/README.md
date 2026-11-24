# Full-s6 service contract

This directory is a publication-safe service topology for an s6-rc based edge
image. It describes lifecycle ownership without shipping a device image,
network credentials, audio recordings, or host-specific configuration.

The dependency graph is intentionally small:

```text
seniorbot-audio-ready (oneshot)
           |
           v
seniorbot-voice (longrun)
           |
           v
seniorbot-online (bundle)
```

The `seniorbot-voice` `run` script invokes the package's hardware-agnostic
worker entry point. Audio drivers, model servers, and device-specific service
overrides belong in the hardware lab and are not part of this export.
