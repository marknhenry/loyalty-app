import React, { createContext, useContext, useState } from 'react';
import type { Account, RedemptionCode } from '../types';
import { mockAccount } from '../data/mockData';

interface AccountContextValue {
  account: Account;
  exchangePoints: (partnerId: string, partnerPoints: number) => void;
  generateRedemption: (locationId: string, locationName: string, points: number) => RedemptionCode;
}

const AccountContext = createContext<AccountContextValue | null>(null);

export function AccountProvider({ children }: { children: React.ReactNode }) {
  const [account, setAccount] = useState<Account>(mockAccount);

  function exchangePoints(partnerId: string, partnerPoints: number) {
    const partner = account.partnerBalances.find(p => p.id === partnerId);
    if (!partner) return;
    const platformGain = Math.floor(partnerPoints * partner.exchangeRate);

    setAccount(prev => ({
      ...prev,
      platformPoints: prev.platformPoints + platformGain,
      partnerBalances: prev.partnerBalances.map(p =>
        p.id === partnerId ? { ...p, points: p.points - partnerPoints } : p
      ),
      transactions: [
        {
          id: `t${Date.now()}`,
          type: 'exchange',
          description: `${partner.name} → Platform`,
          points: platformGain,
          date: new Date().toISOString().slice(0, 10),
          source: partner.name,
        },
        ...prev.transactions,
      ],
    }));
  }

  function generateRedemption(
    locationId: string,
    locationName: string,
    points: number
  ): RedemptionCode {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    const code = Array.from({ length: 8 }, () =>
      chars[Math.floor(Math.random() * chars.length)]
    ).join('');

    setAccount(prev => ({
      ...prev,
      platformPoints: prev.platformPoints - points,
      transactions: [
        {
          id: `t${Date.now()}`,
          type: 'redeem',
          description: `Redeemed at ${locationName}`,
          points: -points,
          date: new Date().toISOString().slice(0, 10),
        },
        ...prev.transactions,
      ],
    }));

    return {
      code,
      locationId,
      locationName,
      points,
      expiresAt: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
    };
  }

  return (
    <AccountContext.Provider value={{ account, exchangePoints, generateRedemption }}>
      {children}
    </AccountContext.Provider>
  );
}

export function useAccount(): AccountContextValue {
  const ctx = useContext(AccountContext);
  if (!ctx) throw new Error('useAccount must be used within AccountProvider');
  return ctx;
}
