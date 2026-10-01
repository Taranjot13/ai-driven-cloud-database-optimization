import { useMemo, useState } from 'react';

function formatCell(value) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  return String(value);
}

function DataTable({ title, columns, rows = [], emptyLabel = 'No records available.', onRowClick }) {
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState(columns[0]?.key || '');
  const [sortDirection, setSortDirection] = useState('asc');
  const [search, setSearch] = useState('');

  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    const items = rows.filter((row) => {
      if (!query) return true;
      return Object.values(row).some((value) => String(value).toLowerCase().includes(query));
    });

    if (!sortKey) return items;

    return [...items].sort((left, right) => {
      const leftValue = left[sortKey];
      const rightValue = right[sortKey];

      if (leftValue == null && rightValue == null) return 0;
      if (leftValue == null) return 1;
      if (rightValue == null) return -1;

      const compare = typeof leftValue === 'number' && typeof rightValue === 'number'
        ? leftValue - rightValue
        : String(leftValue).localeCompare(String(rightValue));

      return sortDirection === 'asc' ? compare : -compare;
    });
  }, [rows, search, sortDirection, sortKey]);

  const pageSize = 8;
  const pageCount = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const currentPage = Math.min(page, pageCount);
  const pageRows = filteredRows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDirection((current) => (current === 'asc' ? 'desc' : 'asc'));
      return;
    }

    setSortKey(key);
    setSortDirection('asc');
  };

  return (
    <div className="panel">
      <div className="panel-header inline-header">
        <h3>{title}</h3>
        {rows.length ? <span>{filteredRows.length} rows</span> : null}
      </div>

      {rows.length ? (
        <>
          <div className="toolbar-row">
            <input
              type="search"
              value={search}
              placeholder="Search table…"
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
            />
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column.key}>
                      <button className="sort-button" onClick={() => handleSort(column.key)}>
                        {column.label}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pageRows.map((row, index) => (
                  <tr key={row.id || `${title}-${index}`} onClick={() => onRowClick && onRowClick(row)}>
                    {columns.map((column) => (
                      <td key={`${row.id || index}-${column.key}`}>
                        {column.render ? column.render(row[column.key], row) : formatCell(row[column.key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button disabled={currentPage === 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>
              Prev
            </button>
            <span>
              Page {currentPage} of {pageCount}
            </span>
            <button disabled={currentPage >= pageCount} onClick={() => setPage((value) => Math.min(pageCount, value + 1))}>
              Next
            </button>
          </div>
        </>
      ) : (
        <div className="empty-state">{emptyLabel}</div>
      )}
    </div>
  );
}

export default DataTable;
