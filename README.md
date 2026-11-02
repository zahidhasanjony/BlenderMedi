# BlenderMedi — Expired Medicine (3D opening)

This repository contains a scripted **10-second, 60 fps** Blender animation for the first cues of the original *What If You Eat a 3-Year-Expired Medicine?* SRT. The video is created in the cloud through GitHub Actions without installing Blender locally.

The first second uses fast camera cuts: a 2:00 AM clock, headache close-up and wider bedroom reveal. Later shots show the medicine cabinet, expired bottle, swallow action and a body-integrated cutaway of the stomach. All supplied SRT text and cue times remain unchanged. The animation is an illustrative scene, not a validated simulation of how expired medications behave.

Run **Actions → Blender 10-second cinematic render → Run workflow** to render on a GitHub runner. The MP4 and `.blend` scene are published as artifacts after the workflow completes. A push to `main` also starts a render automatically.

Narration is **not included** because only an SRT was provided. A subtle effects track is generated automatically. Do not interpret the source SRT's medical assertions as verified advice.
