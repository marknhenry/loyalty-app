import styles from './TransactionList.module.css';
import type { Transaction } from '../../types';

interface Props {
  transactions: Transaction[];
}

const typeConfig: Record<
  Transaction['type'],
  { label: string; sign: string; colorClass: string }
> = {
  earn: { label: 'Earned', sign: '+', colorClass: 'earn' },
  exchange: { label: 'Exchange', sign: '+', colorClass: 'exchange' },
  redeem: { label: 'Redeemed', sign: '', colorClass: 'redeem' },
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

export function TransactionList({ transactions }: Props) {
  if (transactions.length === 0) {
    return <p className={styles.empty}>No transactions yet.</p>;
  }

  return (
    <ul className={styles.list}>
      {transactions.map(tx => {
        const cfg = typeConfig[tx.type];
        const isNegative = tx.points < 0;
        return (
          <li key={tx.id} className={styles.item}>
            <div className={`${styles.typeBadge} ${styles[cfg.colorClass]}`}>
              {cfg.label}
            </div>
            <div className={styles.desc}>
              <span className={styles.descText}>{tx.description}</span>
              {tx.source && (
                <span className={styles.source}>{tx.source}</span>
              )}
            </div>
            <span className={styles.date}>{formatDate(tx.date)}</span>
            <span
              className={`${styles.points} ${isNegative ? styles.negative : styles.positive}`}
            >
              {isNegative ? '' : '+'}{tx.points.toLocaleString()} pts
            </span>
          </li>
        );
      })}
    </ul>
  );
}
