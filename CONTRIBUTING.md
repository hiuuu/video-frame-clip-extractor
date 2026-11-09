# Contributing

Thanks for your interest! Contributions, bug reports, and feature requests are welcome.

## Reporting bugs

Please open an issue and include:

1. Your **OS** and version (Windows 11, macOS 14, Ubuntu 24.04, …)
2. Your **Python version** (`python --version`)
3. Your **FFmpeg version** (`ffmpeg -version`)
4. The **app version** (visible in the title bar, e.g. `v4.2`)
5. **Steps to reproduce** — what you clicked, what you expected, what happened
6. Any **console output** (run the app from a terminal to see logs)

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

## License

By contributing, you agree that your code will be released under the [MIT License](LICENSE).
