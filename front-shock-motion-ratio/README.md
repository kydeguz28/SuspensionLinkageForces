# Front Shock Motion Ratio Study

This project sweeps prescribed front-wheel vertical travel through the configured double-wishbone, pullrod, rocker, and shock geometry. It solves all six linkage-length constraints plus the requested wheel travel, then reports shock compression and motion ratio.

The default configuration uses an explicit wheel center 9.0 in above the contact patch (an 18 in nominal tire). Replace `assembly.wheel_center` with the measured loaded-radius position for the installed tire before using the results for design release.

The configured front shock is 200.0 mm node-to-node at full extension with 47.5 mm of travel, giving a 152.5 mm bottom-out length. The generated study reports node-to-node length and stroke usage at every pose, shades travel outside the physical shock range, and places the rebound preset at the nearest extension-safe solved pose.

## Generate

From the repository root:

```text
python front-shock-motion-ratio/generate_study.py
```

Open `front-shock-motion-ratio/index.html` directly or serve the repository with a local HTTP server.

## Conventions

- Positive wheel travel is bump/upward.
- CAD geometry retains its original basis, where −Z points upward.
- Shock compression is ride-height shock length minus current shock length.
- Instantaneous motion ratio is `d(vertical wheel travel) / d(shock compression)`.
- Wheel-rate factor is the inverse square of this wheel/shock motion ratio.
- The pullrod pickup follows the rigid lower A-arm about its two chassis pivots; it is not attached to the upright.

Edit `study_config.json` to change the hardpoints or travel sweep, then regenerate the site.
