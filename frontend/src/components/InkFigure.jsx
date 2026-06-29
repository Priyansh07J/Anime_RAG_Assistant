// Original decorative side art — a silhouetted figure in a dynamic,
// crouched pose with sharp ink-stroke hair and scattered motion
// particles. Inspired by the energy of high-contrast manga action
// art as a *style*, not based on or copied from any existing
// character, show, or artist's work.

export default function InkFigure({ flip = false }) {
  return (
    <svg
      className={`ink-figure ${flip ? "ink-figure-flip" : ""}`}
      viewBox="0 0 320 640"
      width="100%"
      height="100%"
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g className="ink-particles">
        <path d="M40 80 L52 74 L46 90 Z" />
        <path d="M260 120 L270 110 L268 126 Z" />
        <path d="M30 220 L40 214 L36 228 Z" />
        <path d="M280 260 L292 256 L284 270 Z" />
        <path d="M20 360 L30 354 L26 368 Z" />
        <path d="M270 400 L282 396 L274 410 Z" />
        <path d="M50 480 L60 474 L56 488 Z" />
        <path d="M250 520 L260 514 L256 528 Z" />
      </g>

      <g className="ink-body">
        <path d="
          M150 60
          C 130 50, 100 55, 95 80
          C 80 75, 70 95, 85 110
          C 70 115, 65 140, 85 150
          C 75 160, 80 185, 105 185
          C 100 210, 120 230, 145 225
          L 150 280
          C 120 300, 95 320, 70 360
          C 55 385, 50 420, 60 450
          L 50 460
          C 40 470, 38 490, 48 495
          C 56 498, 64 488, 66 478
          L 78 450
          C 95 425, 115 405, 140 390
          L 160 380
          C 175 410, 185 445, 180 480
          C 178 500, 190 515, 205 510
          C 218 505, 218 485, 208 475
          C 212 450, 205 420, 190 395
          L 175 365
          C 195 345, 210 320, 215 295
          C 220 270, 210 245, 190 230
          C 200 210, 195 185, 175 175
          C 185 160, 180 135, 160 128
          C 168 110, 162 85, 150 60
          Z" />

        <path className="ink-hair" d="
          M95 80
          L 75 40 L 90 55
          L 80 15 L 100 45
          L 95 5 L 112 42
          L 118 0 L 125 45
          L 140 8 L 138 48
          L 158 18 L 148 55
          L 170 35 L 155 62
          L 130 60
          C 120 55, 105 60, 95 80
          Z" />
      </g>
    </svg>
  );
}
