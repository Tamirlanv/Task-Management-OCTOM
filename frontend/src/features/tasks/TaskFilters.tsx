import { Search, SlidersHorizontal } from 'lucide-react';
import { useState } from 'react';
import type { Member, Project, Tag } from '../../api/types';
import { ResourceSelect } from '../../components/ResourceSelect';
import { priorities, statuses } from '../../lib/format';

import { initialFilters, type Filters } from './filters';
export function TaskFilters({
  workspace,
  value,
  onChange,
}: {
  workspace: string;
  value: Filters;
  onChange: (value: Filters) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const set = (field: keyof Filters, next: string | boolean) =>
    onChange({ ...value, [field]: next });
  const base = `/workspaces/${workspace}`;
  return (
    <div className="filter-panel">
      <div className="filter-main">
        <label className="search-field">
          <Search size={19} />
          <input
            aria-label="Поиск задач"
            value={value.q}
            maxLength={200}
            placeholder="Найти задачу…"
            onChange={(event) => set('q', event.target.value)}
          />
        </label>
        <label className="sr-only" htmlFor="status-filter">
          Статус задач
        </label>
        <select
          id="status-filter"
          value={value.status}
          onChange={(event) => set('status', event.target.value)}
        >
          <option value="">Все статусы</option>
          {Object.entries(statuses).map(([key, text]) => (
            <option key={key} value={key}>
              {text}
            </option>
          ))}
        </select>
        <button
          className={expanded ? 'secondary selected' : 'secondary'}
          aria-expanded={expanded}
          onClick={() => setExpanded(!expanded)}
        >
          <SlidersHorizontal size={17} />
          Фильтры
        </button>
      </div>
      {expanded && (
        <div className="filter-details">
          <ResourceSelect<Project>
            path={`${base}/projects`}
            label="Проект"
            value={value.project}
            onChange={(next) => set('project', next)}
            option={(item) => ({ value: item.id, label: item.name })}
            empty="Все проекты"
          />
          <label>
            Приоритет
            <select
              value={value.priority}
              onChange={(event) => set('priority', event.target.value)}
            >
              <option value="">Все приоритеты</option>
              {Object.entries(priorities).map(([key, text]) => (
                <option key={key} value={key}>
                  {text}
                </option>
              ))}
            </select>
          </label>
          <ResourceSelect<Member>
            path={`${base}/members`}
            label="Исполнитель"
            value={value.assignee}
            onChange={(next) => set('assignee', next)}
            option={(item) => ({ value: item.user_id, label: item.name })}
            empty="Все исполнители"
          />
          <ResourceSelect<Tag>
            path={`${base}/tags`}
            label="Тег"
            value={value.tag}
            onChange={(next) => set('tag', next)}
            option={(item) => ({ value: item.id, label: item.name })}
            empty="Все теги"
          />
          <label>
            Порядок
            <select value={value.sort} onChange={(event) => set('sort', event.target.value)}>
              <option value="created_at:desc">Сначала новые</option>
              <option value="updated_at:desc">Недавно обновлённые</option>
              <option value="due_at:asc">По ближайшему сроку</option>
              <option value="priority:desc">Сначала срочные</option>
            </select>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={value.overdue}
              onChange={(event) => set('overdue', event.target.checked)}
            />
            Только просроченные
          </label>
        </div>
      )}
      {JSON.stringify(value) !== JSON.stringify(initialFilters) && (
        <button className="text-button reset-filters" onClick={() => onChange(initialFilters)}>
          Сбросить фильтры
        </button>
      )}
    </div>
  );
}
