# Anytype Todo for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

`anytype-todo` is a Home Assistant custom integration that syncs checklist items from one Anytype object into Home Assistant Todo entities.

## What This Integration Does

- Connects to the local Anytype API or Anytype CLI (default host: `http://localhost:31009`)
- Reads one Anytype object (configured via object URL)
- Parses markdown checklist sections in that object
- Exposes each checklist section as a Home Assistant Todo list entity
- Syncs create, update, and delete operations from Home Assistant back to Anytype
- Polls Anytype regularly to reflect changes made outside Home Assistant

This integration currently provides the `todo` platform only.

## Requirements

- Home Assistant `2023.1.0` or newer (HACS metadata minimum)
- Anytype desktop app with API access
- A valid Anytype API key
- A target Anytype object URL that includes `spaceId`

## Install

### Option 1: HACS (Recommended)

1. Open HACS.
2. Go to Integrations.
3. Open the menu in the top right and choose Custom repositories.
4. Add `https://github.com/Encotric/hass-anytype` as category `Integration`.
5. Install `Anytype ToDo Lists`.
6. Restart Home Assistant.

### Option 2: Manual

1. Copy the folder `custom_components/anytype_todo` from this repository to your Home Assistant `custom_components` directory.
2. Keep the folder name as `anytype_todo`.
3. Restart Home Assistant.

## Configure In Home Assistant

1. Go to Settings -> Devices & Services -> Add Integration.
2. Search for `Anytype`.
3. Enter:
   - `API Key`
   - `Host URL` (optional, defaults to `http://localhost:31009`)
   - `Object URL` (required)
4. Submit.

If validation succeeds, the integration creates Todo entities based on the selected object's markdown content.

## Object URL Format

The object URL must contain both:

- object id in the path
- `spaceId` query parameter

Example shape:

```text
https://your.anytype/object_id_here?spaceId=space_id_here
```

## How Markdown Is Mapped To Todo Lists

Inside the configured Anytype object, checklist content is interpreted as follows:

- A heading starts a Todo list section.
- Checklist items under that section (`- [ ] task`, `- [x] done`) become Todo items.
- Each heading becomes a separate Home Assistant Todo entity.

If no valid heading + checklist structure exists, no usable Todo list entities are created.

## Using The Todo Entities

After setup, use standard Home Assistant Todo services:

- `todo.add_item`
- `todo.update_item`
- `todo.remove_item`

See [SERVICES.md](SERVICES.md) for YAML examples.

## Troubleshooting

### Integration Cannot Connect

- Ensure Anytype desktop app is running.
- Verify the API host is reachable (default `http://localhost:31009`).
- Recreate API key and retry setup.

### Setup Fails With Object URL Error

- Confirm URL includes `spaceId`.
- Confirm the object id in the path is valid for the same space.

### No Todo Entities Appear

- Ensure the object contains markdown headings followed by checklist items.
- Check Home Assistant logs for `custom_components.anytype_todo` errors.

## Development

Local helper scripts in this repository:

- `./scripts/setup`: install Python dependencies
- `./scripts/develop`: run Home Assistant in debug with local `config/`
- `./scripts/lint`: run formatting and lint autofixes (`ruff format` + `ruff check --fix`)

Typical flow:

```bash
./scripts/setup
./scripts/develop
```

In another terminal:

```bash
./scripts/lint
```

## Project Links

- Repository: https://github.com/Encotric/hass-anytype
- Issues: https://github.com/Encotric/hass-anytype/issues
- Anytype API docs: https://developers.anytype.io/docs/reference

## License

MIT. See [LICENSE](LICENSE).
