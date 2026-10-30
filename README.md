# PodPulse AI — Podcast Summarizer Studio

## Included Files
- `index.html`: Main application interface (links to `styles.css` and `app.js`).
- `styles.css`: Custom dark-mode studio styles and timestamp chip animations.
- `app.js`: Core application logic (YouTube IFrame player controller, local audio/video/SRT parser, Web Audio demo WAV synthesizer, Gemini API integration, and Markdown/JSON exporter).
- `sample-podcast.srt`: A sample subtitle file you can drag-and-drop into the Local File Upload tab.

## How to Run
1. Open `index.html` directly in any modern browser (Chrome, Edge, Brave, Firefox), or serve the folder using VS Code Live Server / `python -m http.server 8000`.
2. Choose **YouTube Link** or **Local File Upload**.
3. (Optional) Paste a Gemini API key in the top bar for live `gemini-2.5-flash` analysis, or use the built-in offline analyzer immediately.
