# Cinematic 5-second style test — editable assets

This folder is an independent 3D asset library and does not modify the earlier 10-second render.

**Create the Blender assets in the cloud**: [GitHub Actions / Build cinematic 3D assets](https://github.com/zahidhasanjony/BlenderMedi/actions/workflows/build_cinematic_assets.yml). The workflow also starts on pushes to this folder.

The Python file `build_assets.py` builds the following original reusable geometry directly in Blender (rather than relying on flat images):

- **CHARACTER_MALE:** a stylized adult man with sculpted wavy hair, eyelids, separate irises, finger geometry, layered skin/clothes and root/head/right-hand pose controls. These are *basic object parenting controls*, **not** a skeletal or facial production rig.
- **BEDROOM_SET:** dressed bedroom with tufted headboard, quilt, pillows, nightstand, glowing 02:00 clock, lamp, window/moon, curtains, wood trim and flooring.
- **MEDICINE_CABINET:** medicine cabinet with multiple bottles, glass shelves, and the close-up hero bottle labeled EXP 2023.
- **LIGHTS_CAMERAS:** four camera angles with depth of field and separate cool/warm cinematic area lights.

The workflow exports `BlenderMedi_stylized_assets.blend`, optional `.glb` scene components and four review images. Results are uploaded as a workflow artifact. The images are quality checks only. This asset builder does **not** generate the 5-second MP4 yet.

**Important:** all geometry here is procedurally built from original shapes. The higher detail and camera rig improve on the earlier block-out, but cannot guarantee Pixar-level facial animation or studio-finished characters. We should inspect the four cloud-rendered stills before animating.

The original SRT remains untouched. The planned future animation is 1920x1080 at 30 FPS, with the same first 5 seconds of narration timestamps. No voiceover audio has been provided.

**Blender compatibility:** Blender 4.0+, rendered with Cycles at 8 samples for review, without OpenImageDenoiser (not available in the standard Ubuntu Blender build). Production render quality can be configured separately after reviewing stills.
