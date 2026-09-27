export interface Filters {
  q: string;
  status: string;
  priority: string;
  project: string;
  assignee: string;
  tag: string;
  overdue: boolean;
  sort: string;
}
export const initialFilters: Filters = {
  q: '',
  status: '',
  priority: '',
  project: '',
  assignee: '',
  tag: '',
  overdue: false,
  sort: 'created_at:desc',
};
