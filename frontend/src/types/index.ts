export interface PartnerBalance {
  id: string;
  name: string;
  logoColor: string;
  points: number;
  exchangeRate: number; // 1 partner point = exchangeRate platform points
}

export type TransactionType = 'earn' | 'exchange' | 'redeem';

export interface Transaction {
  id: string;
  type: TransactionType;
  description: string;
  points: number;
  date: string;
  source?: string;
}

export interface Account {
  id: string;
  name: string;
  email: string;
  platformPoints: number;
  partnerBalances: PartnerBalance[];
  transactions: Transaction[];
}

export interface MemberLocation {
  id: string;
  name: string;
  category: string;
  icon: string;
  minPoints: number;
}

export interface RedemptionCode {
  code: string;
  locationId: string;
  locationName: string;
  points: number;
  expiresAt: string;
}
