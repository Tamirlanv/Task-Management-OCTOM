import { useOptions } from '../api/queries';
import { ErrorNotice } from './Feedback';
interface Option {
  value: string;
  label: string;
}
export function ResourceSelect<T>({
  path,
  label,
  value,
  onChange,
  option,
  empty = 'Не выбран',
  required = false,
}: {
  path: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  option: (item: T) => Option | null;
  empty?: string;
  required?: boolean;
}) {
  const query = useOptions<T>(path);
  const options = query.items.map(option).filter((item): item is Option => item !== null);
  return (
    <label>
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        disabled={query.isPending}
      >
        <option value="">{query.isPending ? 'Загрузка…' : empty}</option>
        {value && !options.some((item) => item.value === value) && (
          <option value={value}>Текущий выбор · {value.slice(0, 8)}</option>
        )}
        {options.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
      {query.hasNextPage && (
        <button
          className="text-button"
          type="button"
          disabled={query.isFetchingNextPage}
          onClick={() => void query.fetchNextPage()}
        >
          Загрузить ещё варианты
        </button>
      )}
      {query.error && <ErrorNotice error={query.error} retry={() => void query.refetch()} />}
    </label>
  );
}
