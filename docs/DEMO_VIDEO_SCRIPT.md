# SmartCart AI — 3-Minute Hackathon Demo Video Script

**Target Video Duration:** 2 minutes 45 seconds (Under 3:00)
**Presenter Tone:** Clear, energetic, technical yet consumer-centric
**Visual Style:** Screen recording of local web application (`http://localhost:5173`) with voiceover

---

### [0:00 - 0:25] Scene 1: The Shopping Problem
**Visual:**
- Open with a web search or browser tab showing a marketplace product listing with an advertised price, then clicking checkout where hidden delivery and handling fees appear.
- Transition camera to SmartCart AI homepage (`http://localhost:5173`).

**Voiceover (25s):**
> "Have you ever found a gadget online that looked like a steal, only to reach checkout and discover exorbitant shipping fees and restrictive return policies?
> Surface sticker prices are deceptive. Retailers game search engines by advertising low item prices while hiding delivery costs in the fine print.
> Welcome to **SmartCart AI** — an AI-powered e-commerce copilot that audits the **True Landed Cost** across competing retailers so you never overpay again."

---

### [0:25 - 0:50] Scene 2: SmartCart AI Homepage & Standard Comparison
**Visual:**
- Show the SmartCart AI hero section with the persistent "Simulated Demo Data" transparency banner.
- Scroll down to the catalogue table and search for `Sony WH-1000XM5`.
- Click **Compare** on the Sony headphones card.

**Voiceover (25s):**
> "Here on the SmartCart AI homepage, you immediately see our transparency disclosure — all catalog offers are simulated for this demonstration.
> When we inspect the Sony WH-1000XM5 headphones, our engine doesn't just show sticker prices. It compares competing retailers:
> SonicSound Store lists at ₹25,999 with ₹499 shipping, resulting in a ₹26,498 True Landed Cost. That actually beats ElectroMart at ₹26,990, even though ElectroMart claimed 'Free Delivery'.
> Every monetary amount is computed authoritatively on our backend in exact integer paise — zero floating-point rounding errors."

---

### [0:50 - 1:25] Scene 3: The AI Shopping Copilot in Action
**Visual:**
- Navigate back to the Copilot bar at the top of the Products page.
- Type in natural language: `"Sony WH-1000XM5 headphones under ₹28,000 with long battery life and noise cancellation"`.
- Click **Ask Copilot** (or click the suggestion chip).
- Watch the analysis spinner transition into the structured response view.

**Voiceover (35s):**
> "Now, let's test our flagship feature: the **AI Shopping Copilot**.
> Instead of wrestling with rigid filters, you describe what you need in plain English: 'Sony WH-1000XM5 headphones under ₹28,000 with noise cancellation'.
> Our backend connects to **Google's Gemini 3.8 Flash** via native REST with secure API key headers.
> And notice this engine badge: if the Gemini API key is unset, rate-limited, or offline, our zero-dependency **Deterministic Local Fallback Engine** seamlessly takes over.
> The Copilot instantly extracts the intent: Category: Audio, Brand: Sony, Budget Cap: ₹28,000, and key features like ANC."

---

### [1:25 - 1:55] Scene 4: AI Best Value Recommendation & Landed Cost Breakdown
**Visual:**
- Hover over the **AI Best Value Recommendation** card that popped up in the Copilot.
- Highlight the retailer name (`SonicSound Store`), seller rating (`4.8`), delivery days, and the Landed Cost Audit breakdown: `₹25,999.00 + ₹499.00 = ₹26,498.00`.
- Highlight the demo disclosure banner at the bottom of the Copilot.

**Voiceover (30s):**
> "The Copilot cross-references the extracted criteria against our verified database catalogue.
> It identifies the best overall deal, giving you an itemized Landed Cost Audit.
> Notice the transparency: if an offer has unknown or unconfirmed delivery costs, our engine quarantines it — it's never treated as free shipping, and checkout is guarded until shipping is verified.
> Furthermore, the demo-data notice explicitly reminds the user that these offers and prices are simulated for the hackathon."

---

### [1:55 - 2:25] Scene 5: PayPal Sandbox Integration Architecture
**Visual:**
- Click **Select for Checkout** from the Copilot card.
- Show the `/checkout` page with pre-filled delivery address.
- Click **Confirm Address & Proceed to Payment**.
- Show the official `@paypal/react-paypal-js` button rendering cleanly.
- Show a brief architectural diagram or slide explaining the server-side PayPal order and capture verification flow.

**Voiceover (30s):**
> "When the buyer selects an offer, checkout adheres strictly to PayPal's secure server-side architecture.
> The client never submits order totals. Instead, our FastAPI backend recalculates the exact price and shipping from database records before creating the PayPal order.
> When the buyer approves the sandbox payment, our server captures the transaction directly with PayPal, verifying the captured currency and paise amount before issuing the receipt.
> In our automated test suite, all PayPal order creations, captures, and failure recovery flows are verified with 100% test coverage."

---

### [2:25 - 2:45] Scene 6: Impact & Conclusion
**Visual:**
- Switch back to the clean web interface, showing the user profile, order history, and logout.
- Display final closing slide: SmartCart AI GitHub link and team credits.

**Voiceover (20s):**
> "SmartCart AI brings together conversational AI with mathematical pricing honesty.
> Powered by Gemini 3.8 Flash, an offline deterministic fallback, and PayPal Sandbox payments, we're building the future of transparent e-commerce.
> Thank you, judges, for watching SmartCart AI!"
