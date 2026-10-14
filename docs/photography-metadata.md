# Photography metadata

Gallery records live in `_data/photography.yml`, in display and lightbox order. `_includes/photo-tile.html` renders them; no per-photo HTML or JavaScript is needed.

Keep existing IDs and image references intact. Give each new record a unique `id`. `src` is the thumbnail/source image; `href` is the full-size link and defaults to `src` when omitted. `alt`, `title` (lightbox title), `description`, `label` (existing tile label), `date`, and `location` preserve the original separate fields.

Add any combination of these optional camera fields:

```yaml
camera:
  body: "Sony a7R III"
  shutter_speed: ""
  aperture: ""
  iso: ""
  focal_length: ""
```

This is a future-record template, not an EXIF claim about an existing photograph. Fill settings only from information you actually have. Omit unknown keys or leave them empty; absent values have no label, placeholder, or inferred default. ISO may be a number or text. Other settings are displayed exactly as entered, including their units—provide `s`, `f/`, or `mm` yourself where appropriate.

The same source metadata appears in hover/keyboard/touch-hold details and the GLightbox caption. Date/location and camera settings are grouped separately. Existing camera models were migrated as `camera.body`; no exposure values were added to existing photographs.

The current gallery includes intentionally missing media and copied/generic metadata. Adding this structure does not verify those values or correct the `photograph73.webp` / `photography73.webp` mismatch.
