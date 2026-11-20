# Stage 2 — computer voice preview and planned physical gadget

The computer prototype generates offline WAV speech from verified totals, with explicit generation, browser playback, pause/seek controls, audio download and a matching transcript. Device volume provides mute/volume adjustment. Speech uses macOS `say`, with an eSpeak adapter for later Linux testing. Missing engines, generation failures and timeouts are handled. A changed summary clears the previous audio. No Raspberry Pi or OLED has been connected; audible delivery and pronunciation still require listening tests.

1. Record the actual Raspberry Pi model, OS, Python version and connected speaker. Verify PyTorch/CPU compatibility on that device; the current installation was tested on macOS ARM64, not a Pi.
2. Choose whether inference runs on the Pi or on a paired computer. If using a network link, define the authenticated message format and error/retry behaviour before transmitting results.
3. Select and test an offline speech engine on the device. Send only the verified summary text to speech synthesis; do not let speech generation recalculate totals or invent observations.
4. Add an explicit user action to speak, a stop/mute control, volume control and a clear playback state. Avoid unsolicited public announcements of financial details, even in a simulation.
5. Test zero transactions, long summaries, pounds/pence pronunciation, repeated playback, device disconnection and failure recovery. Confirm playback on the actual connected speaker rather than equating generated audio files with successful delivery.
6. If adding incoming-payment simulation, extend and validate the transaction direction/type schema first. Do not announce a Stage 1 positive outgoing amount as an incoming payment.
7. Evaluate comprehension and control with consenting participants, comparing visual-only and visual-plus-speech presentations. Report actual tasks, observations, sample size and failures. Do not claim the gadget improves understanding before measuring it.

The OLED display, conversational interface and notifications remain stretch goals. A report should clearly distinguish implemented software, prepared text and tested hardware.
