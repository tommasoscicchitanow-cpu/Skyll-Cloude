# KDP browser-automation workarounds

The KDP "create" form is a React app with custom widgets and protected file inputs. Naïve
Playwright/Puppeteer typing and `set_input_files` are unreliable on it. These are the
production-discovered workarounds the upload script encodes — none are documented by Amazon.

## 1. Drive a real, logged-in Chrome over CDP

Don't launch a fresh, cookieless browser. Attach to a Chrome started with remote debugging so the
existing KDP login/session is reused (2FA already passed):

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/kdp-chrome
# log into kdp.amazon.com once in that window, then run kdp_upload.py --cdp http://localhost:9222
```

`kdp_upload.py` connects with `playwright.chromium.connect_over_cdp(...)` and reuses the open page.

## 2. Fill fields with JS `evaluate`, not `.type()` / `.fill()`

KDP's controlled inputs often ignore or drop synthetic keystrokes (state desyncs, validation
doesn't fire). Instead set the value via the DOM and dispatch the events React listens for:

```js
(selector, value) => {
  const el = document.querySelector(selector);
  const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement : HTMLInputElement;
  const setter = Object.getOwnPropertyDescriptor(proto.prototype, 'value').set;
  setter.call(el, value);                                   // bypass React's value tracker
  el.dispatchEvent(new Event('input',  { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  el.blur();
}
```

Prefer **stable element IDs** over brittle CSS paths. Reload the KDP page before filling if the
form was left in a partial state — stale React state is a common failure.

## 3. Upload files via CDP `DOM.setFileInputFiles`, not Playwright

The interior/cover `<input type=file>` are hidden and wrapped by a custom uploader; Playwright's
`set_input_files` frequently fails to register. Use the raw CDP command against the input node:

```python
client = await page.context.new_cdp_session(page)
doc = await client.send("DOM.getDocument")
node = await client.send("DOM.querySelector",
                         {"nodeId": doc["root"]["nodeId"], "selector": file_input_selector})
await client.send("DOM.setFileInputFiles",
                  {"files": [abs_pdf_path], "nodeId": node["nodeId"]})
```

Then **wait for the upload-complete signal in the UI** (a checkmark / "Uploaded" / processing
spinner clearing) before proceeding — don't race the next step.

## 4. Select the AI-content disclosure

After metadata, KDP asks about AI-generated content. Click the "Yes" radio and tick the
applicable boxes (text / images / translation), then any required sub-questions. This is encoded
explicitly and must not be skipped.

## 5. Stop at review

The script fills everything and stops at the final review/preview. It only clicks "Publish" when
run with `--publish`, after a human has confirmed the preview.

## Maintenance

KDP changes selectors and flow periodically. When a step breaks, re-inspect the live DOM, update
the selector/ID map at the top of `kdp_upload.py`, and update this file. Treat selectors as
configuration, not constants.
