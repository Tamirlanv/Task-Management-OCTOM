import type { Tag } from '../../api/types';
import { useOptions } from '../../api/queries';
import { ErrorNotice } from '../../components/Feedback';

export function TagPicker({
  workspace,
  selected,
  onChange,
}: {
  workspace: string;
  selected: string[];
  onChange: (ids: string[]) => void;
}) {
  const tags = useOptions<Tag>(`/workspaces/${workspace}/tags`);
  const missing = selected.filter((id) => !tags.items.some((tag) => tag.id === id));
  return (
    <div className="tag-picker">
      <span className="field-label">
        Теги <small>до 20</small>
      </span>
      <div className="tag-options">
        {tags.items.map((tag) => (
          <label className="tag-choice" key={tag.id}>
            <input
              type="checkbox"
              checked={selected.includes(tag.id)}
              disabled={!selected.includes(tag.id) && selected.length >= 20}
              onChange={(event) =>
                onChange(
                  event.target.checked
                    ? [...selected, tag.id]
                    : selected.filter((id) => id !== tag.id),
                )
              }
            />
            <i style={{ backgroundColor: tag.color ?? '#8271f5' }} />
            {tag.name}
          </label>
        ))}
        {missing.map((id) => (
          <label className="tag-choice" key={id}>
            <input
              type="checkbox"
              checked
              onChange={() => onChange(selected.filter((value) => value !== id))}
            />
            Тег · {id.slice(0, 8)}
          </label>
        ))}
      </div>
      {!tags.items.length && !tags.isPending && !tags.error && (
        <p className="muted small">Тегов пока нет. Менеджер может создать их в настройках.</p>
      )}
      {tags.isPending && <span className="muted small">Загружаем теги…</span>}
      {tags.hasNextPage && (
        <button
          type="button"
          className="text-button"
          disabled={tags.isFetchingNextPage}
          onClick={() => void tags.fetchNextPage()}
        >
          Ещё теги
        </button>
      )}
      {tags.error && <ErrorNotice error={tags.error} retry={() => void tags.refetch()} />}
    </div>
  );
}
