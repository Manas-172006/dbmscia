import { useEffect, useMemo, useState } from 'react'
import { ChevronLeft, ChevronRight, Database, Play, Table2 } from 'lucide-react'
import { adminApi } from '../api/admin'
import type {
  DatabaseOverview,
  DatabaseRelationship,
  SqlQueryMeta,
  SqlQueryResult,
  TableMeta,
  TableRowsData,
} from '../types'
import './AdminDashboardPage.css'

type AdminSection = 'overview' | 'sql' | 'schema'

const overviewCards: { key: keyof DatabaseOverview; label: string }[] = [
  { key: 'total_items', label: 'Found-item reports' },
  { key: 'available_items', label: 'Currently available' },
  { key: 'returned_items', label: 'Returned to owners' },
  { key: 'total_contact_requests', label: 'Enquiries' },
  { key: 'total_users', label: 'Registered users' },
  { key: 'categories_count', label: 'Categories' },
  { key: 'locations_count', label: 'Campus locations' },
  { key: 'total_status_history', label: 'Status changes' },
]

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  return typeof value === 'string' ? value : String(value)
}

function AdminDashboardPage() {
  const [section, setSection] = useState<AdminSection>('overview')
  const [overview, setOverview] = useState<DatabaseOverview | null>(null)
  const [queries, setQueries] = useState<SqlQueryMeta[]>([])
  const [tables, setTables] = useState<TableMeta[]>([])
  const [relationships, setRelationships] = useState<DatabaseRelationship[]>([])
  const [queryId, setQueryId] = useState('')
  const [queryCategory, setQueryCategory] = useState('all')
  const [queryParams, setQueryParams] = useState<Record<string, number>>({})
  const [queryResult, setQueryResult] = useState<SqlQueryResult | null>(null)
  const [queryLoading, setQueryLoading] = useState(false)
  const [selectedTable, setSelectedTable] = useState('')
  const [tableData, setTableData] = useState<TableRowsData | null>(null)
  const [tableLoading, setTableLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([
      adminApi.getOverview(),
      adminApi.getSqlQueries(),
      adminApi.getTables(),
      adminApi.getRelationships(),
    ])
      .then(([overviewData, queryData, tableDataResponse, relationshipData]) => {
        if (!active) return
        setOverview(overviewData)
        setQueries(queryData)
        setTables(tableDataResponse)
        setRelationships(relationshipData)
        setQueryId(queryData[0]?.id ?? '')
        setQueryParams(queryData[0]?.params ?? {})
      })
      .catch((requestError: Error) => {
        if (active) setError(requestError.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  const selectedQuery = queries.find((query) => query.id === queryId)
  const queryCategories = useMemo(
    () => [...new Set(queries.map((query) => query.category))],
    [queries],
  )
  const visibleQueries = queryCategory === 'all'
    ? queries
    : queries.filter((query) => query.category === queryCategory)

  const runQuery = async () => {
    if (!selectedQuery) return
    setQueryLoading(true)
    setError('')
    setQueryResult(null)
    try {
      const result = await adminApi.runSqlQuery(selectedQuery.id, queryParams)
      setQueryResult(result)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'The query could not be completed.')
    } finally {
      setQueryLoading(false)
    }
  }

  const loadTable = async (tableName: string, page: number) => {
    setSelectedTable(tableName)
    setTableLoading(true)
    setError('')
    try {
      setTableData(await adminApi.getTableRows(tableName, page))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'The table could not be loaded.')
    } finally {
      setTableLoading(false)
    }
  }

  if (loading) {
    return <main className="admin-page"><div className="admin-loading" role="status">Loading database dashboard...</div></main>
  }

  return (
    <main className="admin-page">
      <header className="admin-page-heading">
        <div>
          <span className="admin-eyebrow"><Database size={15} /> MySQL 8 · administrator</span>
          <h1>Database dashboard</h1>
          <p>Live Found It data, schema and predefined read-only SQL examples.</p>
        </div>
        <span className="admin-connection-badge"><span /> Connected to MySQL</span>
      </header>

      {error && <div className="admin-error" role="alert">{error}</div>}

      <nav className="admin-tabs" aria-label="Database dashboard sections">
        <button className={section === 'overview' ? 'active' : ''} onClick={() => setSection('overview')} type="button">Overview</button>
        <button className={section === 'sql' ? 'active' : ''} onClick={() => setSection('sql')} type="button">SQL Explorer</button>
        <button className={section === 'schema' ? 'active' : ''} onClick={() => setSection('schema')} type="button">Schema &amp; tables</button>
      </nav>

      {section === 'overview' && overview && (
        <section className="admin-overview" aria-label="Database overview">
          <div className="admin-metric-grid">
            {overviewCards.map((card) => (
              <article className="admin-metric" key={card.key}>
                <span>{card.label}</span>
                <strong>{overview[card.key].toLocaleString()}</strong>
              </article>
            ))}
          </div>
          <div className="admin-note">
            <Database size={20} />
            <div><strong>MySQL is the source of truth</strong><p>Dashboard counts and query results are read live from the campus database.</p></div>
          </div>
        </section>
      )}

      {section === 'sql' && (
        <section className="admin-sql-layout" aria-label="SQL Explorer">
          <aside className="admin-query-list">
            <label htmlFor="query-category">Query examples</label>
            <select id="query-category" value={queryCategory} onChange={(event) => setQueryCategory(event.target.value)}>
              <option value="all">All concepts</option>
              {queryCategories.map((category) => <option key={category} value={category}>{category}</option>)}
            </select>
            <div className="admin-query-options">
              {visibleQueries.map((query) => (
                <button
                  className={query.id === queryId ? 'selected' : ''}
                  key={query.id}
                  onClick={() => {
                    setQueryId(query.id)
                    setQueryParams(query.params)
                    setQueryResult(null)
                  }}
                  type="button"
                >
                  <span>{query.category}</span>
                  <strong>{query.title}</strong>
                </button>
              ))}
            </div>
          </aside>

          <div className="admin-query-workspace">
            {selectedQuery ? (
              <>
                <div className="admin-query-heading">
                  <div><span className="admin-eyebrow">{selectedQuery.concept}</span><h2>{selectedQuery.title}</h2><p>{selectedQuery.description}</p></div>
                  <button className="admin-run-button" disabled={queryLoading} onClick={() => void runQuery()} type="button">
                    <Play size={16} /> {queryLoading ? 'Running…' : 'Run query'}
                  </button>
                </div>
                {Object.keys(selectedQuery.params).length > 0 && (
                  <div className="admin-parameters">
                    {Object.entries(selectedQuery.params).map(([name, defaultValue]) => (
                      <label key={name}>
                        <span>{name.replaceAll('_', ' ')}</span>
                        <input
                          max={name === 'limit' ? 100 : name === 'min_days' ? 3650 : 100000}
                          min={name === 'min_days' ? 0 : 1}
                          onChange={(event) => setQueryParams((current) => ({ ...current, [name]: Number(event.target.value) }))}
                          type="number"
                          value={queryParams[name] ?? defaultValue}
                        />
                      </label>
                    ))}
                  </div>
                )}
                <pre className="admin-sql-code"><code>{selectedQuery.sql_text}</code></pre>
                {queryResult && (
                  <div className="admin-result">
                    <div className="admin-result-heading">
                      <div><strong>Live results</strong><span>{queryResult.row_count} rows · {queryResult.execution_time_ms} ms</span></div>
                    </div>
                    <div className="admin-table-scroll">
                      <table>
                        <thead><tr>{queryResult.columns.map((column) => <th key={column}>{column.replaceAll('_', ' ')}</th>)}</tr></thead>
                        <tbody>
                          {queryResult.rows.map((row, index) => (
                            <tr key={`${queryResult.query_id}-${index}`}>
                              {queryResult.columns.map((column) => <td key={column}>{displayValue(row[column])}</td>)}
                            </tr>
                          ))}
                          {queryResult.rows.length === 0 && <tr><td colSpan={Math.max(queryResult.columns.length, 1)}>No rows matched this query.</td></tr>}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            ) : <div className="admin-empty">No predefined queries are available.</div>}
          </div>
        </section>
      )}

      {section === 'schema' && (
        <section className="admin-schema-layout" aria-label="Database schema">
          <div className="admin-table-directory">
            <div className="admin-section-heading"><div><Table2 size={18} /><h2>Tables and views</h2></div><span>{tables.length} objects</span></div>
            <div className="admin-object-list">
              {tables.map((table) => (
                <button className={selectedTable === table.name ? 'selected' : ''} key={table.name} onClick={() => void loadTable(table.name, 1)} type="button">
                  <span><strong>{table.name}</strong><small>{table.type === 'VIEW' ? 'View' : 'Table'} · {table.row_count.toLocaleString()} rows</small></span>
                  <ChevronRight size={16} />
                </button>
              ))}
            </div>
            <div className="admin-relationships">
              <h3>Relationships</h3>
              {relationships.map((relationship) => (
                <p key={`${relationship.from_table}.${relationship.from_column}`}>
                  <span>{relationship.from_table}.{relationship.from_column}</span> → {relationship.to_table}.{relationship.to_column}
                </p>
              ))}
              {relationships.length === 0 && <p>No foreign-key relationships found.</p>}
            </div>
          </div>

          <div className="admin-table-preview">
            {tableLoading ? <div className="admin-empty">Loading table rows…</div> : tableData ? (
              <>
                <div className="admin-section-heading">
                  <div><Table2 size={18} /><h2>{tableData.table_name}</h2></div>
                  <span>{tableData.total_rows.toLocaleString()} rows</span>
                </div>
                <div className="admin-column-list">
                  {tables.find((table) => table.name === selectedTable)?.columns.map((column) => (
                    <span key={column.name}>{column.name}{column.is_primary ? ' · PK' : ''}{column.nullable ? '' : ' · required'}</span>
                  ))}
                </div>
                <div className="admin-table-scroll">
                  <table>
                    <thead><tr>{tableData.columns.map((column) => <th key={column}>{column.replaceAll('_', ' ')}</th>)}</tr></thead>
                    <tbody>
                      {tableData.rows.map((row, index) => (
                        <tr key={`${tableData.table_name}-${index}`}>
                          {tableData.columns.map((column) => <td key={column}>{displayValue(row[column])}</td>)}
                        </tr>
                      ))}
                      {tableData.rows.length === 0 && <tr><td colSpan={Math.max(tableData.columns.length, 1)}>This table is empty.</td></tr>}
                    </tbody>
                  </table>
                </div>
                <div className="admin-pagination">
                  <span>Page {tableData.page} of {tableData.total_pages}</span>
                  <div>
                    <button aria-label="Previous page" disabled={tableData.page <= 1} onClick={() => void loadTable(selectedTable, tableData.page - 1)} type="button"><ChevronLeft size={17} /></button>
                    <button aria-label="Next page" disabled={tableData.page >= tableData.total_pages} onClick={() => void loadTable(selectedTable, tableData.page + 1)} type="button"><ChevronRight size={17} /></button>
                  </div>
                </div>
              </>
            ) : <div className="admin-empty">Choose a table to inspect its safe, paginated rows.</div>}
          </div>
        </section>
      )}
    </main>
  )
}

export default AdminDashboardPage
