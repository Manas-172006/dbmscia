import { api } from './client';
import type {
  DatabaseOverview,
  DatabaseRelationship,
  SqlQueryMeta,
  SqlQueryResult,
  TableMeta,
  TableRowsData,
} from '../types';

export const adminApi = {
  getOverview: () =>
    api.get<DatabaseOverview>('/admin/database/overview'),

  getTables: () =>
    api.get<TableMeta[]>('/admin/database/tables'),

  getTableRows: (tableName: string, page: number = 1, pageSize: number = 15) =>
    api.get<TableRowsData>(`/admin/database/tables/${encodeURIComponent(tableName)}/rows`, {
      page,
      page_size: pageSize,
    }),

  getSqlQueries: () =>
    api.get<SqlQueryMeta[]>('/admin/sql/queries'),

  runSqlQuery: (queryId: string, params?: Record<string, number>) =>
    api.post<SqlQueryResult>(`/admin/sql/queries/${queryId}/run`, { params }),

  getRelationships: () =>
    api.get<DatabaseRelationship[]>('/admin/database/relationships'),
};
