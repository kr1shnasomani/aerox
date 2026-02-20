import axios from 'axios';
import type { BookingRequest, ProcessingResult, NegotiationResult, Scenario, Agency, DecisionConfig, Stats } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

// Booking
export async function processBooking(request: BookingRequest): Promise<ProcessingResult> {
  const { data } = await api.post('/booking/process', request);
  return data;
}

// Negotiation
export async function negotiate(
  userMessage: string,
  roundNumber: number,
  bookingRequest: Record<string, unknown>,
  mlScores: Record<string, unknown>,
  initialOptions: Record<string, unknown>[]
): Promise<NegotiationResult> {
  const { data } = await api.post('/negotiate', {
    user_message: userMessage,
    round_number: roundNumber,
    booking_request: bookingRequest,
    ml_scores: mlScores,
    initial_options: initialOptions,
  });
  return data;
}

export async function resetNegotiation(): Promise<void> {
  await api.post('/negotiate/reset');
}

// Scenarios
export async function getScenarios(): Promise<{ scenarios: Scenario[]; negotiation_messages: string[] }> {
  const { data } = await api.get('/scenarios');
  return data;
}

// Agencies
export async function getAgencies(params?: {
  page?: number;
  page_size?: number;
  segment?: string;
  region?: string;
  search?: string;
}): Promise<{ agencies: Agency[]; total: number; page: number; page_size: number; total_pages: number }> {
  const { data } = await api.get('/agencies', { params });
  return data;
}

export async function getAgency(companyId: string): Promise<{ agency: Agency }> {
  const { data } = await api.get(`/agencies/${companyId}`);
  return data;
}

// Config
export async function getConfig(): Promise<DecisionConfig> {
  const { data } = await api.get('/config');
  return data;
}

// Stats
export async function getStats(): Promise<Stats> {
  const { data } = await api.get('/stats');
  return data;
}
