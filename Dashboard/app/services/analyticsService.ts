import { API_ENDPOINTS } from '../config/api';
import { mapSessionReport } from '../mappers/sessionReportMapper';
import type { SessionAnalytics } from '../types/analytics';
import type { SessionReportDto } from '../types/report.dto';
import api from '../utils/api';
import { getSessions } from './sessionService';

export const getAnalyticsSessions = getSessions;

export const getSessionAnalytics = async (
  id: string,
): Promise<SessionAnalytics> => {
  const { data } = await api.get<SessionReportDto>(
    API_ENDPOINTS.sessions.report(id),
  );
  if (!data) throw new Error('Analytics not found');
  return mapSessionReport(data, id);
};
