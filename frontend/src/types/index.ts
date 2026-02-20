export interface BookingRequest {
  company_id: string;
  company_name: string;
  booking_amount: number;
  current_outstanding: number;
  credit_limit: number;
  route: string;
  booking_date: string;
}

export interface MLScores {
  intent_score: number;
  capacity_score: number;
  pd_7d: number;
  pd_14d: number;
  pd_30d: number;
}

export interface CreditOption {
  option_id: string;
  type: string;
  settlement_days: number;
  upfront_amount: number;
  approved_amount: number;
  expected_loss: number;
  friction_score: number;
  description: string;
}

export interface ProcessingResult {
  decision: 'APPROVED' | 'BLOCKED' | 'NEGOTIATE';
  risk_category: 'green' | 'yellow' | 'red';
  ml_scores: MLScores;
  booking_request: BookingRequest;
  approved_amount?: number;
  settlement_days?: number;
  reason?: string;
  financial_analysis?: {
    total_exposure: number;
    baseline_el_30d: number;
    exceeds_risk_appetite: boolean;
    [key: string]: unknown;
  };
  risk_assessment?: {
    risk_summary: string;
    key_risk_factors: string[];
    mitigating_factors: string[];
    recommendation: string;
    [key: string]: unknown;
  };
  options?: CreditOption[];
  validation?: {
    compliant: boolean;
    violations: string[];
    options_count: number;
  };
  message?: {
    subject: string;
    body: string;
    cta_buttons: string[];
  } | string;
}

export interface NegotiationResult {
  response: string;
  offer: {
    upfront: number;
    settlement_days: number;
    approved_amount: number;
  } | null;
  expected_loss: number | null;
  escalate: boolean;
}

export interface Scenario {
  id: string;
  label: string;
  booking: BookingRequest;
  expected_scores: MLScores & { risk_category: string };
  description: string;
}

export interface Agency {
  company_id: string;
  segment?: string;
  region?: string;
  business_age_months?: number;
  credit_limit_inr?: number;
  current_outstanding_inr?: number;
  credit_utilization?: number;
  on_time_payment_rate?: number;
  avg_late_payment_days?: number;
  chargeback_rate?: number;
  fraud_flag?: number;
  default_flag?: number;
  risk_score?: number;
  annual_revenue_inr?: number;
  total_bookings_lifetime?: number;
  [key: string]: unknown;
}

export interface PipelineStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'active' | 'complete' | 'skipped';
  duration?: number;
  data?: unknown;
  icon: string;
}

export interface DecisionConfig {
  decision_matrix: {
    block_intent_threshold: number;
    approve_intent_threshold: number;
    approve_capacity_threshold: number;
    negotiate_capacity_min: number;
    negotiate_capacity_max: number;
  };
  risk_constraints: {
    max_expected_loss: number;
    lgd: number;
  };
}

export interface Stats {
  total_agencies: number;
  segments: Record<string, number>;
  regions: Record<string, number>;
  avg_credit_utilization: number;
  avg_on_time_payment_rate: number;
  fraud_rate: number;
  default_rate: number;
}
