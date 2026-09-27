export type Role = 'Admin' | 'Manager' | 'Member' | 'Viewer';
export type Status = 'todo' | 'in_progress' | 'done' | 'cancelled';
export type Priority = 'low' | 'medium' | 'high' | 'urgent';
export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
export interface User {
  id: string;
  name: string;
  email: string;
}
export interface Workspace {
  id: string;
  name: string;
  description: string;
}
export interface Project extends Workspace {
  workspace_id: string;
}
export interface Member {
  user_id: string;
  name: string;
  role: Role;
}
export interface Tag {
  id: string;
  name: string;
  color: string | null;
}
export interface Task {
  id: string;
  workspace_id: string;
  project_id: string;
  title: string;
  description: string;
  status: Status;
  priority: Priority;
  due_at: string | null;
  assignee_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  tag_ids: string[];
}
export interface TaskInput {
  title: string;
  description: string;
  status: Status;
  priority: Priority;
  due_at: string | null;
  assignee_id: string | null;
  tag_ids: string[];
}
export interface Overview {
  role: Role;
  statistics: {
    total: number;
    done: number;
    in_progress: number;
    overdue: number;
    projects: number;
    days: { date: string; count: number }[];
  };
}
export interface Tokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}
