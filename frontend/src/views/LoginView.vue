<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const email = ref('')
const password = ref('')
const showPassword = ref(false) // toggles the password <input> between type="password" and type="text"
const isLoading = ref(false)    // true while the login request is in flight — swaps the button text for a spinner

const router = useRouter()
const authStore = useAuthStore()

// A fixed set of star positions, generated once (not reactive) so they don't
// jump to new random spots every time Vue re-renders the component.
// Increase `length` for a denser starfield; each star gets a random position,
// size, and animation timing so the twinkle doesn't look mechanical/synced.
const stars = Array.from({ length: 45 }, () => ({
    top: `${Math.random() * 60}%`,      // keeps stars in the top 60% of the screen (the "sky", above the mountains)
    left: `${Math.random() * 100}%`,    // full horizontal spread
    size: `${Math.random() * 2 + 1}px`, // between 1px and 3px — small dots, not big blobs
    delay: `${Math.random() * 4}s`,     // random start offset so stars don't all twinkle in unison
    duration: `${Math.random() * 3 + 2}s` // random speed (2s–5s) per star, for the same reason
}))

const handleLogin = async () => {
    isLoading.value = true // switches the submit button into its "spinner" state (see .spinner in <style>)
    console.log('Sending data to the backend via axios')

    try {
        const response = await axios.post('http://127.0.0.1:5000/login', {
            email: email.value,
            password: password.value
        })

        authStore.login(response.data.access_token, response.data.role)

        // Redirect the user based on their role

        if (authStore.role == 'admin') {
            router.push('/admin-dashboard')
        } else if (authStore.role == 'staff') {
            router.push('/staff-dashboard')
        } else {
            router.push('/trekker-dashboard')
        }
    } catch (error) {
        if (error.response) {
            alert(`Login Failed: ${error.response.data.msg}`)
        } else {
            console.log("Connection error: ", error)
            alert("Could not connect to the server. Is Flask Running ?")
        }
    } finally {
        isLoading.value = false // always turn the spinner off, whether login succeeded or failed
    }
}
</script>

<template>
    <!--
        Top-level wrapper. Everything on this page — the animated background
        AND the login card — lives inside this one <div>, because the
        background is positioned "absolute" relative to it (see .auth-page
        in <style> — it's the "position: relative" anchor).
    -->
    <div class="auth-page">

        <!-- ===== ANIMATED AURORA / DAWN-OVER-MOUNTAINS BACKGROUND ===== -->
        <!-- This whole block is purely decorative (position: absolute, sits BEHIND
             the login card via z-index). Everything inside is generated with CSS/SVG,
             no image files, so there's nothing to upload or link externally. -->
        <div class="aurora-bg">

            <!-- 3 soft, blurred, colored circles that slowly drift and pulse.
                 This is what creates the "aurora" / sunrise glow effect. -->
            <div class="orb orb-1"></div>
            <div class="orb orb-2"></div>
            <div class="orb orb-3"></div>

            <!-- One empty <span class="star"> per entry in the `stars` array above.
                 Each one gets its own inline `style` (position/size/timing) computed
                 in the script, while the shared look (white, round, twinkle animation)
                 comes from the `.star` class in <style>. -->
            <div class="stars">
                <span v-for="(star, i) in stars" :key="i" class="star" :style="{
                    top: star.top,
                    left: star.left,
                    width: star.size,
                    height: star.size,
                    animationDelay: star.delay,
                    animationDuration: star.duration
                }"></span>
            </div>

            <!-- 3 mountain "ridges" stacked back-to-front, each a flat div shaped
                 into a jagged mountain silhouette using CSS clip-path (see <style>).
                 Order in the DOM = stacking order: back is drawn first (furthest),
                 front is drawn last (closest / darkest / tallest on screen). -->
            <div class="mountains">
                <div class="ridge ridge-back"></div>
                <div class="ridge ridge-mid"></div>
                <div class="ridge ridge-front"></div>
            </div>

            <!-- A very faint noise texture layered on top of everything above,
                 so the smooth gradients don't look too flat/artificial. -->
            <div class="grain"></div>
        </div>

        <!-- ===== FOREGROUND CONTENT ===== -->
        <!-- Everything the user actually reads/clicks. Sits ON TOP of .aurora-bg
             because of z-index: 2 in .auth-content (<style>). Split into two
             columns by CSS Grid: brand-pane (left) and login-pane (right). -->
        <div class="auth-content">

            <!-- LEFT COLUMN: marketing/branding copy, no interactive elements -->
            <div class="brand-pane">
                <div class="brand-mark">
                    <!-- Small inline SVG mountain-peak logo. `fill="url(#peakGrad)"`
                         points at the <linearGradient> defined just below it — that's
                         what gives the peak its orange-to-purple gradient fill. -->
                    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 20L9 8L13 15L16 10L21 20H3Z" fill="url(#peakGrad)" stroke="white" stroke-width="0.5" stroke-linejoin="round"/>
                        <circle cx="18" cy="6" r="2" fill="#ffd27a"/>
                        <defs>
                            <linearGradient id="peakGrad" x1="3" y1="20" x2="21" y2="8" gradientUnits="userSpaceOnUse">
                                <stop stop-color="#ff8a5b"/>
                                <stop offset="1" stop-color="#8b5cf6"/>
                            </linearGradient>
                        </defs>
                    </svg>
                    <span>Trekker Basecamp</span>
                </div>

                <!-- The <span class="highlight"> wraps just the word "summit" so only
                     that word gets the gradient-text treatment (see .highlight below) -->
                <h1>Your next<br /><span class="highlight">summit</span> starts here.</h1>
                <p class="tagline">Discover curated expeditions across the Himalayas, book your slot, and track every trek from one basecamp.</p>

                <ul class="feature-list">
                    <li><span class="dot"></span>Live slot availability across every trek</li>
                    <li><span class="dot"></span>One ledger for all your bookings</li>
                    <li><span class="dot"></span>Exportable trip history, on demand</li>
                </ul>
            </div>

            <!-- RIGHT COLUMN: the actual login form, wrapped in the glass card -->
            <div class="login-pane">
                <div class="glass-card">
                    <h2>Welcome back, Explorer</h2>
                    <p class="subtitle">Sign in to plan your next expedition</p>

                    <form @submit.prevent="handleLogin">
                        <div class="field">
                            <label>Email</label>
                            <!-- .input-wrap is the pill-shaped container that holds the
                                 icon AND the <input> together, so they share one border/
                                 background/focus-ring instead of the icon floating separately -->
                            <div class="input-wrap">
                                <svg class="field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M3 6.5L12 13L21 6.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                                    <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" stroke-width="1.6"/>
                                </svg>
                                <input type="email" v-model="email" placeholder="you@example.com" required />
                            </div>
                        </div>

                        <div class="field">
                            <label>Password</label>
                            <div class="input-wrap">
                                <svg class="field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <rect x="5" y="10" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.6"/>
                                    <path d="M8 10V7a4 4 0 018 0v3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                </svg>
                                <!-- :type swaps between "password" (dots) and "text" (visible)
                                     based on showPassword, which the button below toggles -->
                                <input :type="showPassword ? 'text' : 'password'" v-model="password" placeholder="Enter your password" required />
                                <!-- v-if / v-else swaps between the "open eye" icon (password hidden,
                                     click to reveal) and the "crossed-out eye" icon (password shown,
                                     click to hide) — only one of the two <svg> exists in the DOM at a time -->
                                <button type="button" class="toggle-visibility" @click="showPassword = !showPassword" :aria-label="showPassword ? 'Hide password' : 'Show password'">
                                    <svg v-if="!showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M1 12S5 5 12 5s11 7 11 7-4 7-11 7-11-7-11-7z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                                        <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.6"/>
                                    </svg>
                                    <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M3 3L21 21" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                        <path d="M10.6 5.2C11 5.1 11.5 5 12 5c7 0 11 7 11 7-.6 1.1-1.5 2.4-2.7 3.6M6.6 6.6C4 8.3 1 12 1 12s4 7 11 7c1.3 0 2.5-.2 3.6-.6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                                        <path d="M9.9 9.9a3 3 0 004.2 4.2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                    </svg>
                                </button>
                            </div>
                        </div>

                        <!-- :disabled="isLoading" stops double-submits while a request is
                             already in flight. Inside, v-if/v-else swaps the label+arrow
                             for the spinner div depending on isLoading. -->
                        <button type="submit" class="submit-btn" :disabled="isLoading">
                            <span v-if="!isLoading">Continue Expedition</span>
                            <span v-if="!isLoading" class="arrow">→</span>
                            <span v-else class="spinner"></span>
                        </button>
                    </form>

                    <!-- RouterLink renders as a real <a href="/register"> under the hood
                         (so it behaves like a normal link, e.g. Ctrl+click opens a new
                         tab), but navigates client-side via Vue Router instead of doing
                         a full page reload. -->
                    <p class="footnote">New here? <RouterLink to="/register">Register here</RouterLink></p>
                </div>
            </div>

        </div>
    </div>
</template>

<style scoped>
/* ============================================================
   HOW TO READ THIS FILE (for viva prep)
   ------------------------------------------------------------
   1. .auth-page        -> the full-screen container everything sits in
   2. .aurora-bg + kids  -> the decorative animated background layer
   3. .auth-content      -> the 2-column grid (brand text | login card)
   4. .glass-card + kids -> the actual login form styling
   5. @media queries     -> how it re-flows on smaller screens

   General CSS ideas used throughout, so you don't have to look them
   up mid-viva:
   - `position: absolute` = "take this element out of normal page flow
     and place it relative to the nearest ancestor that has
     `position: relative` (or absolute/fixed)."
   - `rgba(255,255,255,0.07)` = white at 7% opacity — used a lot for the
     "glass" look, because a very transparent white lets the colorful
     background show through while still looking like a solid panel.
   - `filter: blur(90px)` = blurs the element itself (used on the orbs).
   - `backdrop-filter: blur(24px)` = blurs whatever is BEHIND the
     element (used on the glass card) — this is what makes it look like
     frosted glass rather than just a semi-transparent box.
   - `clip-path: polygon(...)` = cuts a shape out of a plain rectangular
     div using a list of (x%, y%) points — this is how the flat mountain
     divs become jagged silhouettes with no image file needed.
   ============================================================ */

/* ========================================
    PAGE SHELL
    Affects: the single outer <div class="auth-page"> wrapping the
    whole page.
======================================== */
.auth-page {
    position: relative;   /* REQUIRED: makes this the anchor for the .aurora-bg
                              layer below, which uses position:absolute + inset:0
                              to fill exactly this element. Without this line,
                              the background would try to fill the whole <body>
                              or an unrelated ancestor instead. */
    min-height: 100vh;    /* Forces the page to be at least the full height of
                              the browser viewport, so the background/gradient
                              never runs out before the bottom of the screen.
                              Change to a fixed value (e.g. 800px) and the page
                              would stop growing with the viewport. */
    overflow: hidden;     /* Clips anything that pokes outside this box — needed
                              because the orbs (.orb-1/2/3) are deliberately
                              positioned partly off-screen (negative top/left
                              values) so their blur fades out at the edges
                              instead of showing a hard circular edge. */
    background: #0e1024;  /* Fallback near-black indigo behind everything, in
                              case the gradient orbs haven't rendered yet or a
                              browser doesn't support backdrop-filter. Change
                              this and the "base night sky" tone shifts. */
    display: flex;             /* Turns this into a flex container so the two
                                   lines below can center its child (.auth-content). */
    align-items: center;       /* Vertically centers .auth-content in the viewport. */
    justify-content: center;   /* Horizontally centers .auth-content in the viewport. */
}

/* ========================================
   AURORA BACKGROUND
   Three large, blurred, animated color blobs drifting behind everything —
   this is the "dawn breaking over the range" effect.
   Affects: <div class="aurora-bg"> and everything inside it.
======================================== */
.aurora-bg {
    position: absolute;  /* Taken out of normal flow; positioned relative to
                             .auth-page (the nearest `position: relative`
                             ancestor) rather than sitting inline with the
                             rest of the content. */
    inset: 0;             /* Shorthand for top:0; right:0; bottom:0; left:0 —
                             stretches this div to exactly cover its parent
                             (.auth-page), corner to corner. */
    overflow: hidden;     /* Clips the orbs/ridges to this box's edges. */
}

/* Shared styling for ALL THREE orbs. The .orb-1/2/3 rules below only
   override position, size, color, and timing — everything else (shape,
   blur amount, base opacity, animation NAME) comes from here. */
.orb {
    position: absolute;
    border-radius: 50%;     /* Turns the square div into a perfect circle.
                                Lower this (e.g. 20%) for a rounded-square
                                "blob" instead of a circle. */
    filter: blur(90px);     /* THE key property for the "aurora glow" look —
                                blurs the circle itself so it has no hard
                                edge. Raise this number (e.g. 140px) for a
                                softer, more diffuse glow; lower it (e.g. 30px)
                                and you'd start to see a visible circular edge. */
    opacity: 0.65;           /* Overall transparency of each orb. Raise toward
                                1 for a much more saturated/intense background;
                                lower toward 0 to make the background subtler. */
    animation: drift 18s ease-in-out infinite;
    /* ^ Runs the `drift` keyframes (defined below) on a loop forever.
         18s here is a DEFAULT duration — each orb overrides it individually
         via `animation-duration` below so they don't all move in sync. */
}

.orb-1 {
    width: 520px;   /* Diameter of this specific orb before blurring. Bigger
                        number = a larger glow patch. */
    height: 520px;
    top: -120px;    /* Negative value = pushes the orb partly above the visible
                        area, so only its lower portion (already faded by the
                        blur) is visible — avoids a harsh circle appearing. */
    left: -100px;
    background: radial-gradient(circle at 30% 30%, #8b5cf6, transparent 70%);
    /* ^ A circular gradient FROM violet (#8b5cf6) at the point 30%,30% inside
         this element, FADING TO fully transparent by the time it reaches 70%
         of the element's radius. Change the hex code to change this orb's
         color; change "70%" to make it fade out sooner (smaller solid core)
         or later (larger solid core). */
    animation-duration: 22s;  /* This orb's personal loop speed — slightly
                                  different from the others so their movements
                                  don't repeat in a visible pattern. */
}

.orb-2 {
    width: 480px;
    height: 480px;
    top: 10%;
    right: -140px;      /* Positioned from the right edge instead of left,
                            so it sits in the top-right region. */
    background: radial-gradient(circle at 60% 40%, #ff6a5b, transparent 70%);
    animation-duration: 26s;
    animation-delay: -6s;  /* NEGATIVE delay = the animation starts as if it
                               had already been running for 6 seconds. Used
                               purely to de-synchronize this orb from orb-1,
                               so they don't pulse/drift in lockstep. */
}

.orb-3 {
    width: 420px;
    height: 420px;
    bottom: -160px;    /* Anchored to the bottom this time, so it glows up
                           from behind the mountains. */
    left: 30%;
    background: radial-gradient(circle at 50% 50%, #17c3b2, transparent 70%);
    animation-duration: 30s;
    animation-delay: -12s;
}

/* The actual motion path all three orbs share (each just runs it at a
   different speed/offset, set above). Percentages = points in time across
   ONE full loop of the `animation-duration`, not seconds. */
@keyframes drift {
    0%, 100% { transform: translate(0, 0) scale(1); }        /* start = end position, so the loop is seamless */
    33%      { transform: translate(40px, 30px) scale(1.08); } /* drifts down-right and grows slightly */
    66%      { transform: translate(-30px, -20px) scale(0.96); } /* drifts up-left and shrinks slightly */
}
/* To make the drift more dramatic, increase the px values (e.g. 40px -> 100px).
   To make the pulsing size-change more/less noticeable, adjust the scale()
   numbers (e.g. 1.08 -> 1.3 for a bigger "breathing" effect). */

/* Container that simply holds all the individual <span class="star"> dots
   and stretches to fill the background, same technique as .aurora-bg. */
.stars {
    position: absolute;
    inset: 0;
}

/* Shared look for every star dot. Actual position/size/timing per star
   comes from the inline `:style` binding set in the <template> (from the
   `stars` array in <script>) — this class only controls what they all
   have in COMMON. */
.star {
    position: absolute;
    background: #ffffff;      /* Star color. Change to a warm tint (e.g. #fff2d6)
                                  for a "candle-light" star field instead of
                                  pure white. */
    border-radius: 50%;       /* Makes each square span into a round dot. */
    opacity: 0.2;              /* Base/resting opacity BEFORE the twinkle
                                  animation kicks in (animation overrides
                                  this while running). */
    animation-name: twinkle;              /* Which @keyframes block to run (below). */
    animation-iteration-count: infinite;  /* Never stops looping. */
    animation-timing-function: ease-in-out; /* Smooth accelerate/decelerate,
                                                rather than a linear, robotic fade. */
    /* NOTE: animation-duration and animation-delay for each star are set
       INLINE per-star from the <script> `stars` array, which is why they
       don't appear here — that's what makes each star twinkle at its own
       random rate instead of all blinking together. */
}

@keyframes twinkle {
    0%, 100% { opacity: 0.15; }  /* dimmest point of the loop */
    50%      { opacity: 0.9; }   /* brightest point, halfway through */
}
/* Raise the 0.9 toward 1 for brighter twinkle peaks; raise 0.15 toward
   the 0.9 value to make stars twinkle less (always fairly bright). */

/* Container that positions the 3 mountain ridge layers along the very
   bottom of the background, spanning the full width. */
.mountains {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 45vh;   /* How tall the whole mountain "band" is, as a percentage
                        of the browser's viewport height. Raise this for
                        taller mountains that eat more of the screen; lower
                        it for a thinner strip along the bottom. Also
                        overridden to 35vh on small screens — see the
                        @media block near the end of this file. */
}

/* Shared positioning for all 3 ridge layers — each one stretches slightly
   WIDER than 100% (left/right: -5%) so its jagged edges never show a gap
   at the very left/right sides of the screen on unusual aspect ratios. */
.ridge {
    position: absolute;
    left: -5%;
    right: -5%;
    bottom: 0;
}

/* FURTHEST-BACK mountain layer: shortest peaks, most transparent, drawn
   first so the other two layers sit visually in front of it. */
.ridge-back {
    height: 70%;         /* % of the parent .mountains height this layer's
                             bounding box occupies — combined with clip-path
                             below, this controls how tall its tallest peaks
                             can reach. */
    background: #171a35; /* Flat fill color of this "layer of rock". Darker
                             layers (front) vs lighter layers (back) is what
                             sells the sense of depth/distance. */
    opacity: 0.75;        /* Slightly see-through, so the aurora glow behind
                             it still shows through faintly (mimics haze/
                             atmospheric distance). */
    clip-path: polygon(0% 60%, 10% 40%, 22% 55%, 34% 25%, 48% 50%, 60% 20%, 74% 48%, 88% 30%, 100% 55%, 100% 100%, 0% 100%);
    /* ^ This is the actual "mountain shape". Each pair is an (x%, y%) point
         inside this div's box, connected in order to form the visible
         silhouette; the last two points (100% 100% and 0% 100%) close the
         shape off along the bottom edge. Lower a y% value (e.g. 20% -> 5%)
         to make that specific peak taller/sharper; raise it (e.g. 20% -> 45%)
         to make that peak shorter/flatter. Add more (x%, y%) pairs for more
         individual peaks. */
}

/* MIDDLE mountain layer: slightly taller peaks, darker, more opaque —
   sits visually in front of ridge-back but behind ridge-front. */
.ridge-mid {
    height: 55%;
    background: #12142a;
    opacity: 0.85;
    clip-path: polygon(0% 70%, 14% 45%, 26% 65%, 40% 35%, 55% 68%, 68% 30%, 82% 60%, 94% 40%, 100% 65%, 100% 100%, 0% 100%);
}

/* CLOSEST/FRONT mountain layer: shortest "height" box but with the
   sharpest, tallest-LOOKING peaks (because it has no opacity applied —
   fully solid, reads as "closest to the camera"). */
.ridge-front {
    height: 38%;
    background: #0a0b1a;   /* No `opacity` line here on purpose — fully
                               solid/opaque, unlike the two layers behind it. */
    clip-path: polygon(0% 80%, 12% 55%, 24% 75%, 38% 50%, 50% 78%, 64% 48%, 78% 72%, 90% 55%, 100% 75%, 100% 100%, 0% 100%);
}

/* A single full-screen layer of "noise" laid on TOP of the aurora + stars +
   mountains, at very low opacity, purely to break up the smoothness of the
   CSS gradients so they read as slightly textured instead of digitally flat. */
.grain {
    position: absolute;
    inset: 0;
    opacity: 0.05;           /* Very subtle by design. Raise this (e.g. 0.15)
                                 to make the grainy/film texture much more
                                 obvious — useful to see what it's doing if
                                 you want to demo the effect in your viva. */
    mix-blend-mode: overlay; /* Blends the noise WITH the colors beneath it
                                 (darkening dark areas, lightening light areas)
                                 instead of just sitting on top as flat gray
                                 specks — this is what keeps it feeling like a
                                 texture rather than a visible layer. */
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    /* ^ This isn't a linked file — it's a tiny SVG written directly inside
         the CSS as a "data URI" (the svg markup itself, URL-encoded). The
         <feTurbulence> filter is what procedurally generates the random
         static/noise pattern, entirely in code, with nothing to download. */
}

/* ========================================
   FOREGROUND LAYOUT
   Affects: <div class="auth-content"> — the 2-column grid holding the
   brand text (left) and the login card (right).
======================================== */
.auth-content {
    position: relative;  /* Needed so `z-index` below actually has an effect
                             (z-index is ignored on statically-positioned
                             elements). */
    z-index: 2;           /* Stacks this ABOVE .aurora-bg (which has no
                             explicit z-index, so defaults to effectively 0/auto).
                             Without this, the background layer could end up
                             drawn on top of the readable content. */
    width: 100%;
    max-width: 1100px;    /* Caps how wide the whole layout gets on large
                             monitors, so the brand text and card don't stretch
                             uncomfortably far apart on an ultrawide screen. */
    margin: 0 auto;       /* Centers this block horizontally within .auth-page. */
    padding: 40px 32px;   /* Breathing room between the content and the edges
                             of the browser window. */
    display: grid;                    /* Switches on CSS Grid layout. */
    grid-template-columns: 1.1fr 0.9fr;
    /* ^ Two columns: left column gets 1.1 "shares" of the available space,
         right column gets 0.9 shares — i.e. left (brand text) is slightly
         wider than right (login card). Change to "1fr 1fr" for equal
         columns, or e.g. "2fr 1fr" to make the brand side much wider. */
    gap: 60px;             /* Horizontal space between the two columns. */
    align-items: center;   /* Vertically centers both columns' content
                               relative to each other. */
}

/* ---- Brand / marketing pane (LEFT column) ---- */
.brand-pane {
    color: #f4f2ff;   /* Base (near-white, slightly violet-tinted) text color
                          for everything in this column, unless overridden
                          by a more specific rule below. */
    animation: fadeSlideUp 0.8s ease both;
    /* ^ Runs the fadeSlideUp keyframes ONCE (no `infinite`) when the page
         loads, so the text gently rises + fades in rather than just
         appearing instantly. `both` keeps the animation's end state
         (fully visible) applied after it finishes, instead of snapping
         back to its "from" state. */
}

.brand-mark {
    display: flex;          /* Puts the logo <svg> and the "Trekker Basecamp"
                                <span> on the same line. */
    align-items: center;    /* Vertically aligns the icon with the text. */
    gap: 10px;               /* Space between icon and text. */
    font-weight: 700;
    letter-spacing: 0.02em; /* Slightly spreads the letters apart — a common
                                trick for small all-caps/brand-style text to
                                look more "designed" rather than just default. */
    margin-bottom: 32px;    /* Space below the logo row, before the big headline. */
    opacity: 0.9;
}

.brand-pane h1 {
    font-size: 2.75rem;   /* Main headline size. 1rem = the page's base font
                              size (usually 16px), so 2.75rem ≈ 44px. */
    font-weight: 800;      /* Extra-bold weight for maximum visual impact. */
    line-height: 1.15;    /* Tight line spacing so the 2-line headline
                              ("Your next / summit starts here.") reads as
                              one tight block instead of loose/airy. */
    margin-bottom: 18px;
}

.brand-pane h1 .highlight {
    /* This targets ONLY the <span class="highlight"> wrapping the word
       "summit" inside the <h1> — the rest of the heading is unaffected. */
    background: linear-gradient(120deg, #ff8a5b, #ff5b9c 60%, #8b5cf6);
    /* ^ A left-to-right-ish gradient (120deg) sweeping through orange ->
         pink (at 60% of the way across) -> violet. */
    -webkit-background-clip: text;  /* Safari/Chrome-specific: clips the
                                        gradient background so it only shows
                                        THROUGH the shape of the text. */
    background-clip: text;           /* Standard version of the line above. */
    color: transparent;              /* The text itself must be transparent,
                                        otherwise the solid text color would
                                        just paint over the gradient and hide it. */
    /* Together, these 3 lines are the standard "gradient text" trick. To
       change the highlight color, edit the gradient stops above. */
}

.tagline {
    font-size: 1.05rem;
    color: rgba(244, 242, 255, 0.7);  /* Same base tint as .brand-pane's text
                                          color, but at 70% opacity, so it
                                          reads as secondary/supporting text
                                          rather than competing with the h1. */
    line-height: 1.6;                  /* Looser line spacing than the h1 —
                                          easier to read for a full sentence. */
    max-width: 440px;                  /* Stops the paragraph from stretching
                                          edge-to-edge on wide screens, which
                                          would make it hard to read. */
    margin-bottom: 32px;
}

.feature-list {
    list-style: none;      /* Removes the default bullet points. */
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column; /* Stacks the <li> items vertically. */
    gap: 14px;               /* Space between each list item. */
}

.feature-list li {
    display: flex;          /* Puts the colored dot and the text side by side. */
    align-items: center;
    gap: 12px;
    color: rgba(244, 242, 255, 0.85);
    font-size: 0.95rem;
}

.feature-list .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;    /* Turns the small square span into a round dot —
                                the "custom bullet point" replacing list-style. */
    background: linear-gradient(135deg, #ff8a5b, #8b5cf6);
    /* ^ Same orange-to-violet gradient family as the logo/highlight text,
         so the accent color feels consistent across the page. */
    flex-shrink: 0;          /* Stops the dot from getting squashed/shrunk if
                                the text next to it wraps onto a second line. */
}

/* ---- Glass login card (RIGHT column) ---- */
.login-pane {
    display: flex;
    justify-content: center;  /* Centers the (max-width-capped) glass card
                                  within its grid column, rather than letting
                                  it stretch to the full column width. */
    animation: fadeSlideUp 0.8s ease 0.15s both;
    /* ^ Same fade/rise-in animation as .brand-pane, but with a 0.15s DELAY,
         so the card visibly follows just after the text — a small staggered
         entrance rather than everything popping in at once. */
}

@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(18px); } /* starting state: invisible, 18px lower than final position */
    to   { opacity: 1; transform: translateY(0); }     /* ending state: fully visible, in its normal position */
}
/* Increase 18px for a more dramatic "rise up" entrance; decrease toward 0
   for a subtler fade with barely any movement. */

.glass-card {
    width: 100%;
    max-width: 400px;        /* Caps the card's width so it doesn't become an
                                 uncomfortably wide form on large screens. */
    padding: 36px 32px;      /* Inner spacing between the card's edge and its content. */
    border-radius: 20px;     /* Rounded corners — raise for a softer/more
                                 "bubbly" card, lower toward 0 for sharp corners. */
    background: rgba(255, 255, 255, 0.07);
    /* ^ Barely-there white tint. This is intentionally very transparent so
         the colorful aurora background behind it still shows through,
         which combined with the blur below is what creates "frosted glass". */
    border: 1px solid rgba(255, 255, 255, 0.16);
    /* ^ A faint light border traces the card's edge — helps it read as a
         distinct panel even though its fill is almost fully transparent. */
    backdrop-filter: blur(24px);
    /* ^ THE key property for the glass effect: blurs whatever is BEHIND
         this element (the moving orbs/mountains), rather than blurring the
         card itself. Raise this for a foggier/frostier glass look; lower
         it and you'd start to see the background more sharply through the card. */
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
    /* ^ A large, soft, dark drop shadow beneath the card, which is what
         makes it feel like it's physically floating above the background
         rather than pasted flat onto it. */
}

.glass-card h2 {
    color: #ffffff;
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 4px;
}

.glass-card .subtitle {
    color: rgba(255, 255, 255, 0.55);  /* Dimmer than the heading, same
                                           "secondary text" idea as .tagline. */
    font-size: 0.9rem;
    margin-bottom: 28px;
}

.field {
    margin-bottom: 18px;   /* Vertical gap between each label+input group
                               (Email field, Password field, etc). */
}

.field label {
    display: block;                 /* Forces the label onto its own line,
                                        above the input, instead of inline. */
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;      /* "EMAIL" / "PASSWORD" instead of
                                        "Email" / "Password" — a common
                                        modern-form styling choice. */
    color: rgba(255, 255, 255, 0.5);
    margin-bottom: 8px;             /* Small gap between the label text and
                                        the input box below it. */
}

.input-wrap {
    position: relative;    /* Anchor point, in case any child needed
                               absolute positioning (not currently used, but
                               a safe default for input-with-icon patterns). */
    display: flex;          /* Lays the icon, the <input>, and (for the
                               password field) the show/hide button out
                               side-by-side in one row. */
    align-items: center;   /* Vertically centers the icon/input/button
                               against each other. */
    background: rgba(255, 255, 255, 0.06);  /* Very faint fill — same
                                                 "glass" family as the card
                                                 itself, just a touch more
                                                 opaque so the field reads
                                                 as a distinct control. */
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 12px;    /* Rounded pill-ish corners, matching the
                               overall soft/rounded look of the card. */
    padding: 0 14px;        /* Left/right inner padding so the icon and text
                               don't touch the edges of the box. */
    transition: 0.2s ease;  /* Makes the focus-state changes below (border
                               color, glow, background) animate smoothly
                               instead of snapping instantly. */
}

.input-wrap:focus-within {
    /* :focus-within applies these styles to the WRAPPER whenever the
       <input> INSIDE it has keyboard focus — this is how clicking into the
       input highlights the whole pill, not just the text cursor. */
    border-color: rgba(255, 138, 91, 0.7);   /* Switches the border to the
                                                 orange accent color while
                                                 the field is active. */
    box-shadow: 0 0 0 3px rgba(255, 138, 91, 0.15);
    /* ^ A soft "glow ring" around the field — a 0-offset, 0-blur, 3px-spread
         shadow, which effectively draws a soft colored halo around the
         entire pill shape. Increase "3px" for a thicker/more obvious glow. */
    background: rgba(255, 255, 255, 0.09);   /* Slightly brighter fill while
                                                 focused, for extra feedback. */
}

.field-icon {
    color: rgba(255, 255, 255, 0.45);
    /* ^ The little mail/lock SVGs use `stroke="currentColor"` in the
         template, meaning they inherit whatever `color` is set here in CSS
         — so changing this one value re-colors the icon without touching
         the SVG markup at all. */
    flex-shrink: 0;   /* Stops the icon from being squeezed narrower if the
                          input text is long. */
}

.input-wrap input {
    flex: 1;               /* Lets the actual <input> expand to fill all
                               remaining space in the row (after the icon,
                               and before the show/hide button on the
                               password field). */
    background: transparent;  /* No box of its own — it visually blends
                                  into the .input-wrap pill around it. */
    border: none;
    outline: none;          /* Removes the browser's default blue focus
                                outline — safe here because .input-wrap's
                                own :focus-within glow (above) replaces it. */
    color: #ffffff;         /* Text the user types appears white, readable
                                against the dark glass background. */
    padding: 13px 10px;     /* Controls the input's clickable height and the
                                gap between the icon and the typed text. */
    font-size: 0.95rem;
}

.input-wrap input::placeholder {
    color: rgba(255, 255, 255, 0.32);  /* Dim placeholder text ("you@example.com")
                                           so it's clearly distinguishable from
                                           text the user has actually typed. */
}

.toggle-visibility {
    background: none;      /* Strips all default <button> styling so it just
                               looks like a plain clickable icon. */
    border: none;
    color: rgba(255, 255, 255, 0.45);  /* Icon color, same `currentColor`
                                           trick as .field-icon. */
    cursor: pointer;        /* Shows a hand/pointer cursor on hover, signaling
                                it's clickable. */
    display: flex;
    align-items: center;
    padding: 4px;           /* Small hit-area padding so it's easier to click
                                than just the bare icon outline. */
}

.toggle-visibility:hover {
    color: rgba(255, 255, 255, 0.85);   /* Brightens on hover as a hint that
                                            it's interactive. */
}

.submit-btn {
    width: 100%;              /* Spans the full width of the card. */
    margin-top: 10px;
    padding: 14px;
    border: none;
    border-radius: 12px;
    background: linear-gradient(135deg, #ff8a5b, #ff5b9c);
    /* ^ The button's signature gradient (orange -> pink). Change these two
         hex values to re-theme the call-to-action color. */
    color: #ffffff;
    font-weight: 700;
    font-size: 0.98rem;
    display: flex;            /* Lets the label text, arrow, and spinner all
                                  sit centered in a row/stack inside the button. */
    align-items: center;
    justify-content: center;
    gap: 8px;                 /* Space between the label text and the arrow. */
    cursor: pointer;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    /* ^ Makes the hover "lift" effect below animate smoothly instead of jumping. */
    box-shadow: 0 8px 24px rgba(255, 91, 156, 0.35);
    /* ^ A pink-tinted glow beneath the button at rest, matching its gradient
         color — makes it look like it's already gently lit up. */
}

.submit-btn:hover:not(:disabled) {
    /* :not(:disabled) makes sure this hover effect ONLY applies when the
       button is clickable — it won't "lift" while a login request is
       already in progress and the button is disabled. */
    transform: translateY(-2px);  /* Nudges the button up 2px on hover, for
                                       a subtle "pressable" feel. */
    box-shadow: 0 12px 28px rgba(255, 91, 156, 0.45);
    /* ^ Bigger, slightly stronger glow on hover than the resting state,
         reinforcing the "lifted closer to you" illusion. */
}

.submit-btn:disabled {
    opacity: 0.7;             /* Visually fades the button while `isLoading`
                                  is true (see :disabled="isLoading" in the
                                  template), signaling it's temporarily inactive. */
    cursor: not-allowed;      /* Changes the mouse cursor to show clicking
                                  won't do anything right now. */
}

.submit-btn .arrow {
    transition: transform 0.15s ease;  /* Lets the arrow's own hover-nudge
                                           (below) animate smoothly. */
}

.submit-btn:hover:not(:disabled) .arrow {
    transform: translateX(3px);  /* Nudges JUST the arrow character 3px to
                                     the right on hover, like it's pointing
                                     "onward" — a small extra detail on top
                                     of the whole button's lift effect. */
}

.spinner {
    width: 18px;
    height: 18px;
    border: 2.5px solid rgba(255, 255, 255, 0.4);  /* The spinner's "track" —
                                                        a faint full circle. */
    border-top-color: #ffffff;   /* Only the TOP edge of that circle is fully
                                     opaque white — combined with the rotation
                                     animation below, this single bright edge
                                     is what visually "spins around" the circle. */
    border-radius: 50%;          /* Makes the bordered box into a circle/ring. */
    animation: spin 0.7s linear infinite;
    /* ^ `linear` (not ease-in-out) so the spin is a perfectly constant
         speed, which is what a loading spinner should look like. Lower
         0.7s for a faster spin, raise it for a slower one. */
}

@keyframes spin {
    to { transform: rotate(360deg); }  /* Rotates a full circle over the
                                            animation's duration; the "from"
                                            state is implicitly 0deg. */
}

.footnote {
    margin-top: 22px;
    text-align: center;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.4);   /* Dimmest text on the whole card —
                                           lowest-priority information. */
}

/* The "Register here" link inside .footnote. `:deep()` is needed because
   RouterLink renders its own <a> tag that Vue's `scoped` CSS wouldn't
   normally be able to reach — :deep() tells it to pierce through and
   style that inner element anyway. */
.footnote :deep(a) {
    color: #ff9d6e;       /* Warm accent color, matching the button gradient
                              family, so the link reads as "on-brand" rather
                              than a generic blue browser-default link. */
    font-weight: 600;
    text-decoration: none;
}

.footnote :deep(a:hover) {
    text-decoration: underline;   /* Underline only appears on hover, as a
                                      subtle interactive hint. */
}

/* ========================================
   RESPONSIVE
   These blocks OVERRIDE the rules above, but only when the browser
   window is narrower than the given width. Because plain CSS cascades
   top-to-bottom, and these appear AFTER the base rules, their values
   win on small screens without needing to touch the desktop rules at all.
======================================== */
@media (max-width: 900px) {
    /* Applies to tablets and phones — anything narrower than 900px. */
    .auth-content {
        grid-template-columns: 1fr;  /* Collapses the 2-column grid into a
                                         single column, stacking brand-pane
                                         above login-pane instead of side by
                                         side (there isn't room for both
                                         columns on a narrow screen). */
        gap: 36px;                    /* Smaller gap now that it's vertical
                                         spacing rather than a wide horizontal gap. */
        padding: 32px 24px;           /* Slightly tighter outer padding to
                                         save space on small screens. */
        text-align: center;           /* Centers the brand text, which reads
                                         better centered than left-aligned
                                         once it's stacked above the card. */
    }

    .brand-pane h1 {
        font-size: 2.1rem;   /* Smaller headline so it doesn't overflow or
                                 force awkward line-wraps on a narrow screen. */
    }

    .tagline {
        margin-left: auto;
        margin-right: auto;  /* Since text-align:center above only centers
                                 the TEXT within its box, these two lines
                                 also center the BOX itself (needed because
                                 .tagline has a max-width, so it doesn't
                                 naturally span full width to be centered). */
    }

    .feature-list {
        align-items: center;   /* Centers each dot+text row as a block,
                                   matching the rest of the centered layout. */
    }

    .mountains {
        height: 35vh;   /* Shorter mountain band on small screens, so it
                            doesn't dominate the limited vertical space. */
    }
}

@media (max-width: 480px) {
    /* Applies to typical phone-width screens only (narrower than 480px). */
    .glass-card {
        padding: 28px 22px;   /* Tighter inner padding so the card doesn't
                                  eat too much of a small phone screen. */
    }
}
</style>