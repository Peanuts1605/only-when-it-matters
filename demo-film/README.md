# Only When It Matters — narrated review film

110 seconds, 1920×1080, 30fps. Six editorial scenes; the public fixture and separately recorded
model evidence are labeled. The model-results panel reads the saved fictional evaluation JSON,
not a fabricated terminal. It is a visualization of recorded results, not live screen capture.

Install the pinned package dependencies, then `npm run check`, `npm run studio`, and
`npm run render`. Locally, the already-installed sibling contest Remotion dependency directory
is reused by a git-ignored symlink; no CALL-E assets are modified.

Master the rendered v1 into the v2 review file using FFmpeg (video stream copied without
re-encoding; narration gain +5.5dB, no timing change):

```sh
ffmpeg -i out/only-when-it-matters-v1.mp4 -c:v copy -af volume=5.5dB -c:a aac -b:a 192k -movflags +faststart out/only-when-it-matters-v2.mp4
```

Narration: one completed AI Doc Maker Clear voice request, 1.0×, 107.424 seconds, 24kHz mono MP3.
No time stretching. Provider title Effective Contest Alerts; generated September13,2026.
Attribution visible throughout: Voiceover Generated with AIDOCMAKER.COM.
Provider attribution link: https://www.aidocmaker.com/docs/attribution-guidelines .
Free Starter commercial-use attribution requirement: https://www.aidocmaker.com/pricing .
Generated audio remains subject to provider terms, not a claim that its engine is MIT licensed.

Caption timings derive from local Whisper tiny.en transcription of this exact MP3, with spelling
and punctuation corrected against the supplied narration. ASR is a content/timing check, not
subjective listening acceptance. Render/decode/frame QA and independent full audiovisual review
must be recorded separately before calling this a final accepted contest film.

## September 13 verification

Mastered v2:110.000s,1920×1080,30fps,H.264/AAC,6,047,944bytes.
SHA256:`e9f9cfde4d3ea0662ecee750eedea2627a2da5a326decc0c708b08cf9df17efc`.
MP3 source SHA256:`957d28b03d61848483a5915ad5cfdefa5250a251ed83f18daa63bb0e314acdd0`.
TypeScript and complete FFmpeg decode pass. Mastered mean-19.8dB/peak-2.3dB.
Six sampled rendered frames inspected; no clipping or overlay collision observed.
Independent source review accepted scene/caption timing, audio identity, source-bound model results,
factual limits and attribution. These checks alone were not listening acceptance.

Exact upload https://youtu.be/0SPfU4ZGwm4 is verified unlisted on Naumio; signed-out player reads1:50
and shows the AI disclosure. Full-video review job `job_cfd8e4cf-c091-432d-ac34-28bf75298fb9`
completed with REVIEW_PASS: tool-reported intelligible narration, aligned captions, readable
results/credit and clean ending, no material audiovisual defect. This is tool-reported perceptual
review, not direct parent listening or independent proof of software/contest claims. The burned-in
captions were reviewed; the tool's wording "closed captions" does not prove a separate subtitle track.

Media review is complete. Entrant verification, registration and contest submission remain separate.
