import styles from './QRCode.module.css';

interface Props {
  value: string;
  size?: number;
}

// Deterministic pattern seeded from the value string
function buildPattern(value: string, size: number): boolean[][] {
  const seed = value
    .split('')
    .reduce((acc, c) => acc * 31 + c.charCodeAt(0), 17);

  const grid: boolean[][] = Array.from({ length: size }, (_, row) =>
    Array.from({ length: size }, (_, col) => {
      // Finder patterns (top-left, top-right, bottom-left corners)
      const inFinder =
        (row < 7 && col < 7) ||
        (row < 7 && col >= size - 7) ||
        (row >= size - 7 && col < 7);
      if (inFinder) {
        const r = row < 7 ? row : row - (size - 7);
        const c = col < 7 ? col : col - (size - 7);
        return (
          r === 0 || r === 6 || c === 0 || c === 6 ||
          (r >= 2 && r <= 4 && c >= 2 && c <= 4)
        );
      }
      // Timing patterns
      if (row === 6 || col === 6) return (row + col) % 2 === 0;
      // Data cells — pseudo-random from seed
      const n = ((seed * (row * size + col + 1)) >>> 0) % 100;
      return n < 48;
    })
  );
  return grid;
}

export function QRCode({ value, size = 21 }: Props) {
  const pattern = buildPattern(value, size);
  const cellSize = 8;
  const svgSize = size * cellSize;

  return (
    <div className={styles.wrapper}>
      <svg
        width={svgSize}
        height={svgSize}
        viewBox={`0 0 ${svgSize} ${svgSize}`}
        className={styles.svg}
        aria-label={`QR code for ${value}`}
      >
        <rect width={svgSize} height={svgSize} fill="#ffffff" />
        {pattern.map((row, r) =>
          row.map((cell, c) =>
            cell ? (
              <rect
                key={`${r}-${c}`}
                x={c * cellSize}
                y={r * cellSize}
                width={cellSize}
                height={cellSize}
                fill="#0f172a"
              />
            ) : null
          )
        )}
      </svg>
      <p className={styles.label}>{value}</p>
    </div>
  );
}
