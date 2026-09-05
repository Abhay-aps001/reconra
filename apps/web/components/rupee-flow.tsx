export function RupeeFlow() {
  return (
    <figure className="rupee-flow">
      <div className="currency-architecture" aria-hidden="true" />
      <div className="currency-edge" aria-hidden="true" />
      <svg viewBox="0 0 780 450" aria-hidden="true" focusable="false">
        <g className="art-wave-lines">
          {Array.from({ length: 18 }, (_, i) => <path key={i} opacity={0.55 + i % 3 * 0.15} d={`M-30 ${365 + i * 4}C110 ${440 + i * 3} 202 ${274 + i * 4} 350 ${337 + i * 3}S560 ${318 + i * 3} 650 ${265 + i * 4} 746 ${251 + i * 3} 810 ${269 + i * 3}`} />)}
        </g>
        <g className="art-microcopy"><text x="195" y="42">DATA</text><text x="195" y="58">TRUST</text><text x="195" y="74">CLARITY</text><path d="M195 87h34" /></g>
      </svg>
      <figcaption>Illustrative money trail · decorative currency image, not reconciliation results</figcaption>
    </figure>
  );
}
