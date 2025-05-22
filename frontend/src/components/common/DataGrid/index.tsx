import React, { useState } from 'react';
import styled from 'styled-components';
import { 
  useTable, 
  useSortBy, 
  useFilters, 
  usePagination 
} from 'react-table';

const Table = styled.table`
  width: 100%;
  border-spacing: 0;
  border: 1px solid ${props => props.theme.colors.border};
`;

const Th = styled.th`
  padding: ${props => props.theme.spacing.md};
  border-bottom: 2px solid ${props => props.theme.colors.border};
  background: ${props => props.theme.colors.background};
  
  &:hover {
    background: ${props => props.theme.colors.backgroundHover};
  }
`;

export const DataGrid: React.FC<{
  columns: any[];
  data: any[];
  onRowClick?: (row: any) => void;
}> = ({ columns, data, onRowClick }) => {
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    page,
    prepareRow,
    canPreviousPage,
    canNextPage,
    pageOptions,
    nextPage,
    previousPage,
    setPageSize,
    state: { pageIndex, pageSize }
  } = useTable(
    {
      columns,
      data,
      initialState: { pageSize: 10 }
    },
    useFilters,
    useSortBy,
    usePagination
  );

  return (
    <div>
      <Table {...getTableProps()}>
        <thead>
          {headerGroups.map(headerGroup => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map(column => (
                <Th {...column.getHeaderProps(column.getSortByToggleProps())}>
                  {column.render('Header')}
                  <span>
                    {column.isSorted
                      ? column.isSortedDesc
                        ? ' 🔽'
                        : ' 🔼'
                      : ''}
                  </span>
                </Th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
          {page.map(row => {
            prepareRow(row);
            return (
              <tr 
                {...row.getRowProps()}
                onClick={() => onRowClick?.(row.original)}
              >
                {row.cells.map(cell => (
                  <td {...cell.getCellProps()}>
                    {cell.render('Cell')}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </Table>
      
      <Pagination
        pageIndex={pageIndex}
        pageCount={pageOptions.length}
        onPrevious={previousPage}
        onNext={nextPage}
        canPrevious={canPreviousPage}
        canNext={canNextPage}
        pageSize={pageSize}
        onPageSizeChange={setPageSize}
      />
    </div>
  );
};