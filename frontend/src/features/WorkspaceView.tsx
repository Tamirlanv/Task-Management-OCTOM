import { useState } from 'react';
import { useResource } from '../api/queries';
import type { Overview, User } from '../api/types';
import { ErrorNotice, Loading } from '../components/Feedback';
import type { Screen } from '../components/Sidebar';
import { Dashboard } from './dashboard/Dashboard';
import { TasksPage } from './tasks/TasksPage';
import { ProjectsPage } from './catalog/ProjectsPage';
import { TeamPage } from './catalog/TeamPage';
import { SettingsPage } from './catalog/SettingsPage';

export function WorkspaceView({
  workspace,
  user,
  screen,
  navigate,
  onUser,
  onDeleted,
}: {
  workspace: string;
  user: User;
  screen: Screen;
  navigate: (screen: Screen) => void;
  onUser: (user: User) => void;
  onDeleted: () => void;
}) {
  const overview = useResource<Overview>(`/workspaces/${workspace}/overview`);
  const [project, setProject] = useState('');
  if (overview.isPending) return <Loading />;
  if (overview.error)
    return <ErrorNotice error={overview.error} retry={() => void overview.refetch()} />;
  const props = { workspace, user, role: overview.data.role };
  return (
    <>
      {screen === 'dashboard' && (
        <Dashboard {...props} overview={overview.data} navigate={navigate} />
      )}
      {screen === 'tasks' && <TasksPage {...props} initialProject={project} />}
      {screen === 'projects' && (
        <ProjectsPage
          {...props}
          openProject={(id) => {
            setProject(id);
            navigate('tasks');
          }}
        />
      )}
      {screen === 'team' && <TeamPage {...props} />}
      {screen === 'settings' && <SettingsPage {...props} onUser={onUser} onDeleted={onDeleted} />}
    </>
  );
}
