import { API_ENDPOINTS } from '../config/api';
import {
  mapBackendSession,
  mapBackendSessionDetail,
} from '../mappers/sessionMapper';
import type {
  BackendSessionDto,
  SessionDetail,
  SessionListItem,
} from '../types/session';
import api from '../utils/api';

export const getSessions = async (): Promise<SessionListItem[]> => {
  const { data } = await api.get<BackendSessionDto[]>(
    API_ENDPOINTS.sessions.mine,
  );
  return data.map(mapBackendSession);
};

export const getSessionById = async (id: string): Promise<SessionDetail> => {
  const { data } = await api.get<BackendSessionDto>(
    API_ENDPOINTS.sessions.detail(id),
  );
  if (!data) throw new Error('Session not found');
  return mapBackendSessionDetail(data);
};
