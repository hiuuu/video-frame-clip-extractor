# Contributing

Thanks for your interest! Contributions, bug reports, and feature requests are welcome.

## Reporting bugs

Please open an issue and include:

1. Your **OS** and version (Windows 11, macOS 14, Ubuntu 24.04, …)
2. Your **Python version** (`python --version`)
3. Your **FFmpeg version** (`ffmpeg -version`)
4. The **app version** (visible in the title bar, e.g. `v4.7`)
5. **Steps to reproduce** — what you clicked, what you expected, what happened
6. Any **console output** (run the app from a terminal to see logs)

For video-processing bugs, also include the **ffprobe summary** of the input
file (copy the `Video Information` panel text, or run
`ffprobe -v error -show_format -show_streams input.mp4`).

## Suggesting features

Open an issue with the tag `enhancement` and describe:

- The use case (what problem are you trying to solve?)
- How you imagine the UI would look
- Any alternatives you've considered

## Submitting pull requests

1. Fork the repo and create a branch: `git checkout -b feature/my-improvement`
2. Keep changes focused — one feature or fix per PR
3. Match the existing code style (PEP 8, 4-space indent, type hints where helpful)
4. Test manually on at least one platform
5. Open the PR with a clear description and a screenshot if the UI changed

## Code style

- **Python**: PEP 8, black-compatible, 4-space indent
- **Commits**: short imperative subject (`Add custom FPS presets`)
- **Comments**: only where the code isn't self-explanatory
- **Version bumping**: increment `APP_VERSION` in the source, add a
  `CHANGELOG.md` entry, and use the same version in the built filename

## License

By submitting a pull request, you agree that your contributions will be
licensed under the **GNU General Public License v3.0 (GPL-3.0)**, the same
license that covers this project. See [`LICENSE`](LICENSE) for the full text.

Please make sure that any code, assets, or dependencies you introduce are
**compatible with GPL-3.0**. In particular:

- ✅ MIT, BSD, Apache-2.0, LGPL code can be included (with attribution)
- ❌ Proprietary or GPL-incompatible code cannot be merged
- ⚠️ If you copy code from another GPL-3.0 project, credit it in the PR
