# Learning

Tripwire should help the project owner become a better reviewer of AI-generated code.

The goal is not dependence. The goal is sharper judgment.

Meaningful findings should explain the underlying product, architecture, or economics principle when that explanation helps the user make better future calls. Tripwire should not add a tutorial to every finding.

Good learning notes are concise. They should help the user recognize the pattern next time without turning the review into a lecture.

Tripwire should accelerate both shipping and understanding. A useful review prevents avoidable rework while also making the reason visible.

A green check should not become blind trust. When Tripwire finds nothing, that means it found no high-confidence project-alignment issue from the available evidence. It does not mean the change is correct, complete, secure, performant, or production-ready.

When there are no findings, Tripwire should still make the alignment judgment visible. The useful answer is not only "nothing is wrong"; it is which priorities got better, worse, stayed flat, or remain unknown from the available evidence.

Tripwire should distinguish unchanged from unknown. Unchanged means it inspected enough to believe there was no meaningful movement. Unknown means it lacks enough evidence to make that claim.

Tripwire should reject ungrounded alignment output. If the model cannot tie project-understanding, alignment, findings, or emergent concerns back to evidence in the review packet, Tripwire should say confidence is limited instead of showing a polished hallucination.

When Tripwire is uncertain, it may ask calibration questions that improve future judgment. These questions should be clearly marked as calibration, not treated as blocking findings.

Tripwire should make the user better at evaluating AI output, not less responsible for it.

## Suppressed Findings

When Tripwire has no finding, it may show one suppressed finding if doing so improves judgment calibration.

A suppressed finding is not a finding. It should explain the strongest near-miss Tripwire considered, why it stayed below the bar, and what evidence would change that judgment.

Tripwire should not invent suppressed findings to prove it did work. Silence remains better than fake signal.
