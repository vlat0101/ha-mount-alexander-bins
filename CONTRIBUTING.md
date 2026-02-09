# Contributing to Mount Alexander Bins Integration

Thank you for your interest in contributing!

## Development Setup

1. Clone the repository
2. Install Home Assistant in development mode
3. Symlink the `custom_components/mount_alexander_bins` folder to your HA config
4. Make changes and test

## Code Standards

- Follow Home Assistant's code style guidelines
- Use `black` for Python formatting
- Add type hints where possible
- Write clear commit messages

## Testing

- Test with your own Home Assistant instance
- Verify all sensors update correctly
- Check error handling with invalid addresses

## Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a PR with a clear description

## Reporting Issues

When reporting issues, please include:
- Home Assistant version
- Integration version
- Error logs (if any)
- Steps to reproduce

Thank you for contributing!
```

---

That's all 13 files! Now create this folder structure and copy/paste the contents:
```
ha-mount-alexander-bins/
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── hacs.json
├── info.md
└── custom_components/
    └── mount_alexander_bins/
        ├── __init__.py
        ├── api.py
        ├── config_flow.py
        ├── const.py
        ├── manifest.json
        ├── sensor.py
        └── strings.json