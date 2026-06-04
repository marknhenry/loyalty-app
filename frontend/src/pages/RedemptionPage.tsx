import { useState } from 'react';
import { useAccount } from '../context/AccountContext';
import { mockLocations } from '../data/mockData';
import { QRCode } from '../components/QRCode/QRCode';
import type { RedemptionCode } from '../types';
import styles from './RedemptionPage.module.css';

type RedemptionStep = 'select' | 'confirm' | 'code';

export function RedemptionPage() {
  const { account, generateRedemption } = useAccount();
  const [selectedLocationId, setSelectedLocationId] = useState<string>('');
  const [step, setStep] = useState<RedemptionStep>('select');
  const [redemptionCode, setRedemptionCode] = useState<RedemptionCode | null>(null);

  const location = mockLocations.find(l => l.id === selectedLocationId);
  const canAfford = location
    ? account.platformPoints >= location.minPoints
    : false;

  function handleSelect(id: string) {
    setSelectedLocationId(id);
  }

  function handleConfirm() {
    if (location && canAfford) setStep('confirm');
  }

  function handleGenerate() {
    if (!location) return;
    const code = generateRedemption(
      location.id,
      location.name,
      location.minPoints
    );
    setRedemptionCode(code);
    setStep('code');
  }

  function handleReset() {
    setSelectedLocationId('');
    setStep('select');
    setRedemptionCode(null);
  }

  function formatExpiry(iso: string): string {
    return new Date(iso).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Redeem Points</h1>
        <p className={styles.subtitle}>
          Use your platform points at member locations
        </p>
      </header>

      <div className={styles.balancePill}>
        <span className={styles.balancePillLabel}>Available:</span>
        <span className={styles.balancePillValue}>
          {account.platformPoints.toLocaleString()} pts
        </span>
      </div>

      {step === 'code' && redemptionCode ? (
        <div className={styles.codeCard}>
          <div className={styles.codeHeader}>
            <p className={styles.codeLocation}>{redemptionCode.locationName}</p>
            <h2 className={styles.codeTitle}>Your Redemption Code</h2>
            <p className={styles.codePoints}>
              {redemptionCode.points.toLocaleString()} points redeemed
            </p>
          </div>

          <div className={styles.qrSection}>
            <QRCode value={redemptionCode.code} size={21} />
          </div>

          <div className={styles.codeDetails}>
            <div className={styles.codeDetailRow}>
              <span className={styles.codeDetailLabel}>Expires at</span>
              <span className={styles.codeDetailValue}>
                {formatExpiry(redemptionCode.expiresAt)}
              </span>
            </div>
            <div className={styles.codeDetailRow}>
              <span className={styles.codeDetailLabel}>Remaining balance</span>
              <span className={styles.codeDetailValue}>
                {account.platformPoints.toLocaleString()} pts
              </span>
            </div>
          </div>

          <p className={styles.codeInstruction}>
            Show this code at the counter or scan the QR code to complete
            your redemption.
          </p>

          <button className={styles.secondaryBtn} onClick={handleReset}>
            New Redemption
          </button>
        </div>
      ) : (
        <div className={styles.card}>
          {step === 'select' && (
            <div className={styles.stepContent}>
              <h3 className={styles.stepHeading}>Choose a member location</h3>
              <div className={styles.locationList}>
                {mockLocations.map(loc => {
                  const affordable = account.platformPoints >= loc.minPoints;
                  return (
                    <button
                      key={loc.id}
                      className={`${styles.locationOption} ${
                        selectedLocationId === loc.id
                          ? styles.locationSelected
                          : ''
                      } ${!affordable ? styles.locationDisabled : ''}`}
                      onClick={() => affordable && handleSelect(loc.id)}
                      disabled={!affordable}
                    >
                      <span className={styles.locationIcon}>{loc.icon}</span>
                      <div className={styles.locationInfo}>
                        <span className={styles.locationName}>{loc.name}</span>
                        <span className={styles.locationCategory}>
                          {loc.category}
                        </span>
                      </div>
                      <div className={styles.locationCost}>
                        <span className={styles.costValue}>
                          {loc.minPoints.toLocaleString()}
                        </span>
                        <span className={styles.costLabel}>pts</span>
                        {!affordable && (
                          <span className={styles.insufficientBadge}>
                            Insufficient
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
              <button
                className={styles.primaryBtn}
                disabled={!location || !canAfford}
                onClick={handleConfirm}
              >
                Continue to Confirm
              </button>
            </div>
          )}

          {step === 'confirm' && location && (
            <div className={styles.stepContent}>
              <h3 className={styles.stepHeading}>Confirm redemption</h3>
              <div className={styles.confirmBox}>
                <div className={styles.confirmLocation}>
                  <span className={styles.confirmIcon}>{location.icon}</span>
                  <div>
                    <p className={styles.confirmName}>{location.name}</p>
                    <p className={styles.confirmCategory}>{location.category}</p>
                  </div>
                </div>
                <div className={styles.confirmDivider} />
                <div className={styles.confirmRow}>
                  <span className={styles.confirmLabel}>Points to redeem</span>
                  <span className={`${styles.confirmValue} ${styles.deductValue}`}>
                    −{location.minPoints.toLocaleString()} pts
                  </span>
                </div>
                <div className={styles.confirmRow}>
                  <span className={styles.confirmLabel}>Current balance</span>
                  <span className={styles.confirmValue}>
                    {account.platformPoints.toLocaleString()} pts
                  </span>
                </div>
                <div className={styles.confirmDivider} />
                <div className={styles.confirmRow}>
                  <span className={styles.confirmLabel}>Balance after</span>
                  <span className={styles.confirmValue}>
                    {(account.platformPoints - location.minPoints).toLocaleString()} pts
                  </span>
                </div>
              </div>
              <div className={styles.buttonRow}>
                <button
                  className={styles.secondaryBtn}
                  onClick={() => setStep('select')}
                >
                  Back
                </button>
                <button className={styles.primaryBtn} onClick={handleGenerate}>
                  Generate Code
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
