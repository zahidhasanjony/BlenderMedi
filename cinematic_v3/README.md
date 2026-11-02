# 5-second cinematic benchmark

This independent test preserves the earlier BlenderMedi scenes. It renders the opening **5.0 seconds / 150 frames at 30 fps**, with the uploaded SRT untouched and burned-in subtitle timings.

### Scenes
- 0–1.5 seconds: 2:00 AM digital clock in a furnished dark-blue bedroom, with a forward camera move
- 1.5–3.1 seconds: an adult male waking with a headache, a subtly moving head and camera
- 3.1–5.0 seconds: the medicine cabinet and amber painkiller bottle, moving camera, warm light and mirror door

### Character licensing
The character uses real 3D mesh parts from [kblood/CharacterCreator](https://github.com/kblood/CharacterCreator), pinned at [commit 852e48f](https://github.com/kblood/CharacterCreator/commit/852e48f316b90a0937234886630e4fb4cdfd1f78). Upstream asset license details: [asset_licenses.json](https://github.com/kblood/CharacterCreator/blob/852e48f316b90a0937234886630e4fb4cdfd1f78/output/asset_licenses.json). Review those per-asset terms before any commercial distribution. The workflow downloads six components directly from upstream. The original bedroom, clock, cabinet, bottle and cameras are created with Blender Python.

### Run
GitHub automatically starts [5s cinematic animation 1080p 30fps](https://github.com/zahidhasanjony/BlenderMedi/actions/workflows/cinematic_5s.yml) after a change. The initial **look-development render is 50% of 1920×1080** (960×540) for faster quality testing. Frame rate is 30 fps. A verified 1920×1080 render can be requested by setting `SCALE: '100'` in the workflow after inspecting the reference stills.

The 5-second MP4 and native Blender scene are uploaded in the workflow artifact `BlenderMedi-5s-cinematic-v3` after completion. SRT is not synthesized narration: **no recorded voiceover is included**, as only an SRT was supplied.

### Honest limitations
The character components are rigged source meshes, but importing separate GLBs and generating camera animation is not equivalent to a hand-polished studio character performance. Review the actual video and stills before approving any full-length 5.5-minute production. If the character imported incorrectly or the cinematic lighting is insufficient, correct the assets rather than trying to hide the defects with camera movement.
