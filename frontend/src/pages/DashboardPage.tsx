import { useAccount } from '../context/AccountContext';
import { TransactionList } from '../components/TransactionList/TransactionList';
import styles from './DashboardPage.module.css';

export function DashboardPage() {
  const { account } = useAccount();
  const totalPartnerPoints = account.partnerBalances.reduce(
    (sum, p) => sum + p.points,
    0
  );

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Dashboard</h1>
        <p className={styles.subtitle}>Your loyalty overview at a glance</p>
      </header>

      {/* Hero balance */}
      <div className={styles.heroGrid}>
        <div className={`${styles.heroCard} ${styles.platform}`}>
          <p className={styles.heroLabel}>Platform Points</p>
          <p className={styles.heroValue}>
            {account.platformPoints.toLocaleString()}
          </p>
          <p className={styles.heroSub}>Ready to redeem</p>
        </div>
        <div className={`${styles.heroCard} ${styles.partner}`}>
          <p className={styles.heroLabel}>Partner Points</p>
          <p className={styles.heroValue}>
            {totalPartnerPoints.toLocaleString()}
          </p>
          <p className={styles.heroSub}>Across {account.partnerBalances.length} partners</p>
        </div>
      </div>

      {/* Partner balances */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Partner Balances</h2>
        <div className={styles.partnerGrid}>
          {account.partnerBalances.map(partner => (
            <div key={partner.id} className={styles.partnerCard}>
              <div
                className={styles.partnerLogo}
                style={{ background: partner.logoColor }}
              >
                {partner.name.slice(0, 2)}
              </div>
              <div className={styles.partnerInfo}>
                <p className={styles.partnerName}>{partner.name}</p>
                <p className={styles.partnerPoints}>
                  {partner.points.toLocaleString()} pts
                </p>
              </div>
              <div className={styles.partnerRate}>
                <span className={styles.rateValue}>×{partner.exchangeRate}</span>
                <span className={styles.rateLabel}>rate</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Transaction history */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Recent Activity</h2>
        <div className={styles.card}>
          <TransactionList transactions={account.transactions.slice(0, 6)} />
        </div>
      </section>
    </div>
  );
}
