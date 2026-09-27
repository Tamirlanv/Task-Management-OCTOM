import { ChevronLeft, ChevronRight } from 'lucide-react';
export function Pagination({
  offset,
  limit,
  total,
  onChange,
}: {
  offset: number;
  limit: number;
  total: number;
  onChange: (offset: number) => void;
}) {
  return (
    <div className="pagination">
      <span>
        {total === 0
          ? 'Нет записей'
          : `${Math.min(offset + 1, total)}–${Math.min(offset + limit, total)} из ${total}`}
      </span>
      <div>
        <button
          className="icon-button"
          aria-label="Предыдущая страница"
          disabled={!offset}
          onClick={() => onChange(Math.max(0, offset - limit))}
        >
          <ChevronLeft size={18} />
        </button>
        <button
          className="icon-button"
          aria-label="Следующая страница"
          disabled={offset + limit >= total}
          onClick={() => onChange(offset + limit)}
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  );
}
