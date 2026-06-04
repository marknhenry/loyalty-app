import { NavLink } from 'react-router-dom';
import { useAccount } from '../../context/AccountContext';
import styles from './Nav.module.css';

export function Nav() {
  const { account } = useAccount();
  const initials = account.name
    .split(' ')
    .map(n => n[0])
    .join('');

  return (
    <nav className={styles.nav}>
      <div className={styles.brand}>
        <span className={styles.brandIcon}>✦</span>
        <span className={styles.brandName}>LoyaltyOS</span>
      </div>

      <div className={styles.userCard}>
        <div className={styles.avatar}>{initials}</div>
        <div className={styles.userInfo}>
          <p className={styles.userName}>{account.name}</p>
          <p className={styles.userEmail}>{account.email}</p>
        </div>
      </div>

      <ul className={styles.links}>
        <li>
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              isActive ? `${styles.link} ${styles.active}` : styles.link
            }
          >
            <span className={styles.linkIcon}>◈</span>
            <span className={styles.linkLabel}>Dashboard</span>
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/exchange"
            className={({ isActive }) =>
              isActive ? `${styles.link} ${styles.active}` : styles.link
            }
          >
            <span className={styles.linkIcon}>⇌</span>
            <span className={styles.linkLabel}>Exchange</span>
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/redeem"
            className={({ isActive }) =>
              isActive ? `${styles.link} ${styles.active}` : styles.link
            }
          >
            <span className={styles.linkIcon}>◉</span>
            <span className={styles.linkLabel}>Redeem</span>
          </NavLink>
        </li>
      </ul>

      <div className={styles.balanceBox}>
        <p className={styles.balanceLabel}>Platform Points</p>
        <p className={styles.balanceValue}>
          {account.platformPoints.toLocaleString()}
        </p>
        <p className={styles.balanceSub}>available to exchange or redeem</p>
      </div>
    </nav>
  );
}
