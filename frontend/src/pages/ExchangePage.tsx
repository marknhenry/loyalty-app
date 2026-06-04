import { useState } from 'react';
import { useAccount } from '../context/AccountContext';
import styles from './ExchangePage.module.css';

type ExchangeStep = 'select' | 'preview' | 'success';

export function ExchangePage() {
  const { account, exchangePoints } = useAccount();
  const [selectedPartnerId, setSelectedPartnerId] = useState<string>('');
  const [inputAmount, setInputAmount] = useState<string>('');
  const [step, setStep] = useState<ExchangeStep>('select');
  const [exchangedPlatformPoints, setExchangedPlatformPoints] = useState(0);

  const partner = account.partnerBalances.find(p => p.id === selectedPartnerId);
  const numericAmount = parseInt(inputAmount, 10) || 0;
  const platformPreview = partner
    ? Math.floor(numericAmount * partner.exchangeRate)
    : 0;

  const canPreview =
    partner !== undefined &&
    numericAmount > 0 &&
    numericAmount <= partner.points;

  function handlePreview() {
    if (canPreview) setStep('preview');
  }

  function handleConfirm() {
    if (!partner || numericAmount <= 0) return;
    exchangePoints(selectedPartnerId, numericAmount);
    setExchangedPlatformPoints(platformPreview);
    setStep('success');
  }

  function handleReset() {
    setSelectedPartnerId('');
    setInputAmount('');
    setStep('select');
    setExchangedPlatformPoints(0);
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Exchange Points</h1>
        <p className={styles.subtitle}>
          Convert partner points into platform points
        </p>
      </header>

      {step === 'success' ? (
        <div className={styles.successCard}>
          <div className={styles.successIcon}>✓</div>
          <h2 className={styles.successTitle}>Exchange Complete!</h2>
          <p className={styles.successDesc}>
            You received{' '}
            <strong>{exchangedPlatformPoints.toLocaleString()} platform points</strong>.
          </p>
          <p className={styles.newBalance}>
            New balance:{' '}
            <strong>{account.platformPoints.toLocaleString()} pts</strong>
          </p>
          <button className={styles.resetBtn} onClick={handleReset}>
            Make Another Exchange
          </button>
        </div>
      ) : (
        <div className={styles.formCard}>
          {/* Step indicator */}
          <div className={styles.steps}>
            <span className={`${styles.step} ${step === 'select' ? styles.stepActive : styles.stepDone}`}>
              1 Select
            </span>
            <span className={styles.stepConnector} />
            <span className={`${styles.step} ${step === 'preview' ? styles.stepActive : ''}`}>
              2 Preview
            </span>
          </div>

          {step === 'select' && (
            <div className={styles.stepContent}>
              <h3 className={styles.stepHeading}>Choose a partner</h3>
              <div className={styles.partnerList}>
                {account.partnerBalances.map(p => (
                  <button
                    key={p.id}
                    className={`${styles.partnerOption} ${
                      selectedPartnerId === p.id ? styles.partnerSelected : ''
                    }`}
                    onClick={() => {
                      setSelectedPartnerId(p.id);
                      setInputAmount('');
                    }}
                  >
                    <div
                      className={styles.partnerDot}
                      style={{ background: p.logoColor }}
                    />
                    <div className={styles.partnerDetails}>
                      <span className={styles.partnerName}>{p.name}</span>
                      <span className={styles.partnerBal}>
                        {p.points.toLocaleString()} pts available
                      </span>
                    </div>
                    <span className={styles.partnerRate}>×{p.exchangeRate} rate</span>
                  </button>
                ))}
              </div>

              {partner && (
                <div className={styles.amountSection}>
                  <label className={styles.label} htmlFor="amount">
                    Amount to exchange
                  </label>
                  <div className={styles.amountRow}>
                    <input
                      id="amount"
                      type="number"
                      min={1}
                      max={partner.points}
                      value={inputAmount}
                      onChange={e => setInputAmount(e.target.value)}
                      className={styles.input}
                      placeholder="0"
                    />
                    <button
                      className={styles.maxBtn}
                      onClick={() => setInputAmount(String(partner.points))}
                    >
                      Max
                    </button>
                  </div>
                  {numericAmount > partner.points && (
                    <p className={styles.errorMsg}>
                      Exceeds available balance of{' '}
                      {partner.points.toLocaleString()} pts
                    </p>
                  )}
                  {numericAmount > 0 && numericAmount <= partner.points && (
                    <div className={styles.ratePreview}>
                      <span>{numericAmount.toLocaleString()} {partner.name} pts</span>
                      <span className={styles.arrow}>→</span>
                      <span className={styles.platformPts}>
                        {platformPreview.toLocaleString()} platform pts
                      </span>
                    </div>
                  )}
                </div>
              )}

              <button
                className={styles.primaryBtn}
                disabled={!canPreview}
                onClick={handlePreview}
              >
                Preview Exchange
              </button>
            </div>
          )}

          {step === 'preview' && partner && (
            <div className={styles.stepContent}>
              <h3 className={styles.stepHeading}>Review your exchange</h3>
              <div className={styles.previewBox}>
                <div className={styles.previewRow}>
                  <span className={styles.previewLabel}>You give</span>
                  <span className={styles.previewValue}>
                    {numericAmount.toLocaleString()} {partner.name} pts
                  </span>
                </div>
                <div className={styles.previewDivider} />
                <div className={styles.previewRow}>
                  <span className={styles.previewLabel}>Exchange rate</span>
                  <span className={styles.previewValue}>×{partner.exchangeRate}</span>
                </div>
                <div className={styles.previewDivider} />
                <div className={styles.previewRow}>
                  <span className={styles.previewLabel}>You receive</span>
                  <span className={`${styles.previewValue} ${styles.highlight}`}>
                    {platformPreview.toLocaleString()} platform pts
                  </span>
                </div>
                <div className={styles.previewDivider} />
                <div className={styles.previewRow}>
                  <span className={styles.previewLabel}>New platform balance</span>
                  <span className={styles.previewValue}>
                    {(account.platformPoints + platformPreview).toLocaleString()} pts
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
                <button className={styles.primaryBtn} onClick={handleConfirm}>
                  Confirm Exchange
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
