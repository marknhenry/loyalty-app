import type { Account, MemberLocation } from '../types';

export const mockAccount: Account = {
  id: 'usr_001',
  name: 'Alex Rivera',
  email: 'alex@loyaltyos.app',
  platformPoints: 12_450,
  partnerBalances: [
    { id: 'p1', name: 'SkyMiles', logoColor: '#0ea5e9', points: 3_200, exchangeRate: 0.8 },
    { id: 'p2', name: 'ShopRewards', logoColor: '#f59e0b', points: 8_750, exchangeRate: 0.5 },
    { id: 'p3', name: 'FuelPlus', logoColor: '#10b981', points: 1_100, exchangeRate: 1.2 },
    { id: 'p4', name: 'DineClub', logoColor: '#8b5cf6', points: 560, exchangeRate: 0.9 },
  ],
  transactions: [
    { id: 't1', type: 'earn', description: 'SkyMiles Sync', points: 640, date: '2026-06-03', source: 'SkyMiles' },
    { id: 't2', type: 'exchange', description: 'ShopRewards → Platform', points: 1_250, date: '2026-06-02', source: 'ShopRewards' },
    { id: 't3', type: 'earn', description: 'ShopRewards Sync', points: 875, date: '2026-06-02', source: 'ShopRewards' },
    { id: 't4', type: 'redeem', description: 'Redeemed at Bean & Brew', points: -800, date: '2026-06-01' },
    { id: 't5', type: 'exchange', description: 'FuelPlus → Platform', points: 1_320, date: '2026-05-30', source: 'FuelPlus' },
    { id: 't6', type: 'earn', description: 'DineClub Sync', points: 300, date: '2026-05-29', source: 'DineClub' },
    { id: 't7', type: 'redeem', description: 'Redeemed at Metro Fitness', points: -1_000, date: '2026-05-28' },
    { id: 't8', type: 'earn', description: 'FuelPlus Sync', points: 480, date: '2026-05-27', source: 'FuelPlus' },
  ],
};

export const mockLocations: MemberLocation[] = [
  { id: 'l1', name: 'Bean & Brew Coffee', category: 'Café', icon: '☕', minPoints: 500 },
  { id: 'l2', name: 'Metro Fitness', category: 'Gym', icon: '🏋️', minPoints: 1_000 },
  { id: 'l3', name: 'The Book Nook', category: 'Retail', icon: '📚', minPoints: 750 },
  { id: 'l4', name: 'Urban Eats', category: 'Restaurant', icon: '🍽️', minPoints: 1_200 },
  { id: 'l5', name: 'Ride & Go', category: 'Transport', icon: '🚴', minPoints: 600 },
];
