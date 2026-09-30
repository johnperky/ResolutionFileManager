# Chocolatey submission template

Publish the official GitHub release before creating the community package. The Chocolatey install script should download the immutable Windows release ZIP from that page, verify its SHA-256 checksum, extract it, and create a Start-menu shim for the executable.

Suggested package ID: `resolution-file-manager`

The public package description should link back to the official source/release page, identify GPL-3.0-or-later licensing, disclose bundled FFmpeg, and use the exact checksum produced after any code signing is complete.
