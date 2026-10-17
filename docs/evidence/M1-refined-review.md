# Refined Evidence in focus — visual review candidate

Status: provisional, owner visual approval OPEN. This is an interactive local
prototype, not the integrated application. Original directions and rejected
treatments remain available as history.

Open the [workbench](http://127.0.0.1:8765/prototype/refined/) and
[identity study](http://127.0.0.1:8765/prototype/refined/brand.html).

The structure retains adjacent product / source evidence / decision on desktop.
White and light-neutral surfaces replace the rejected blue-gray wash. Charcoal
defines controls; orange identifies the brand and primary action; amber marks
review conditions. The original SVG mark uses two offset label forms to suggest
a B and the evidence-matching mechanism. It remains a design proposal.

| Surface | Desktop | Phone |
| --- | --- | --- |
| Evidence workbench | [1440px](../ui/refined/workbench-desktop.jpg) | [390px](../ui/refined/workbench-phone.jpg) |
| Retail queue | [1440px](../ui/refined/retail-desktop.jpg) | [390px](../ui/refined/retail-phone.jpg) |
| Capture guidance | [Draft](../ui/refined/guidance-desktop.jpg) | [Confirmation](../ui/refined/guidance-phone.jpg) |
| Brand mark and small-size/monochrome study | [Identity](../ui/refined/brand-desktop.jpg) | Mark also present in each phone header |

## Impeccable execution and questions

Original pinned Impeccable 4.6.0 init/shape/new-work/Operate guidance and the
admitted 0.1.15 engine were used. The earlier replacement used only an adapted
subset; the complete workshop was run after that was rejected. The
[discovery map](M1-design-discovery.md#actual-impeccable-discovery-mapped-to-this-project)
shows the actual question categories and the answers already supplied. Impeccable
is guidance executed by the agent; it does not supply hidden independent opinions.

## Concrete usability evidence

`BATCHBEACON_TEST_BROWSER_CHANNEL=chrome .venv/bin/pytest tests/browser/test_refined.py -q`
passed **15 local browser tests**. These cover native keyboard example selection,
paired evidence selection and announcements, confirmation gating/Escape/focus return,
five widths (320/390/720/1280/1440) across views and long-name/error states,
identity-mismatch behavior, empty-queue recovery, reduced motion, guidance focus
and reset, and computed text contrast on the three default surfaces.

Selection has a checked control, full boundary and Selected text. Field selection
has an outline, pressed state and a live text description. Disabled controls have
nearby explanations. Phone pages offer direct Label/Evidence/Decision navigation.

The first inspection found excess vertical setup space; examples are now collapsed
with the active choice named. Static detection identified small label text; the
functional label/meta sizes were increased to at least 12px. Guidance confirmation
lost keyboard focus when disabling its trigger: reproduced as REQUIRED_CONTRACT,
failure retained privately, fixed by focusing the newly revealed consent checkbox,
and regression passed. No second static detector run or compliance claim.

A fresh Impeccable finish review inspected all seven captures and source evidence.
Its disposition was **ship for provisional owner presentation only**, with no
material finding at that scope. The focus correction was independently inspected
from source/test assertions; a separate independent reviewer subsequently reran
all 15 refined browser checks in actual Chrome and closed the focus correction.
Advisory: guidance lifecycle emphasis should distinguish the current step from
completed steps in integration. Screenshot extensions were corrected to match their
actual JPEG bytes. No pixel transformation was performed.

## Remaining product gates

No full screen-reader test or accessibility certification. The 720px layout is a
reflow proxy, not proof of actual browser 200% zoom. Real camera capture, upload,
extraction, source refresh, persistence, action authorization, actual guidance
evaluation and hosted availability are not established by this prototype.

Before product acceptance: test the integrated flows by keyboard and assistive
technology, actual 200% zoom and phone hardware; run cold/warm/error recovery and
fresh-session hosted journeys. First-time comprehension/adoption remains a design
hypothesis until observed with users. No claim of a hackathon outcome.

Owner approval here closes only the replacement visual-treatment gate in U02.
It does not close UK/remaining human source review, protected-case custody,
runtime acceptance or final submission.
