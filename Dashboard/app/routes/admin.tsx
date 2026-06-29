import { useState, useEffect, useCallback } from 'react';
import { Search, UsersRound } from 'lucide-react';
import { Card } from '../components/Card';
import {
  deleteManagedUser,
  getAdminUsers,
  updateManagedUser,
} from '../services/adminService';
import { styles } from '../utils/styles';
import { SectionHeader } from '../components/SectionHeader';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { UserTableRow } from '../components/UserTableRow';
import type { ManagedUser } from '../types/admin';
import { getApiErrorMessage } from '../utils/apiError';
import { EmptyState } from '../components/EmptyState';
import { confirmDeletion } from '../utils/confirmDeletion';

export default function UserManagement() {
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [pendingUserId, setPendingUserId] = useState<string | null>(null);

  const fetchAdminUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAdminUsers();
      setUsers(data);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load admin users.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchAdminUsers();
  }, [fetchAdminUsers]);

  const managedUsers = users.filter((user) => user.role === 'user');

  const filtered = managedUsers.filter(
    (user) =>
      user.name.toLowerCase().includes(search.toLowerCase()) ||
      user.email.toLowerCase().includes(search.toLowerCase()),
  );

  const toggleDisable = async (id: string) => {
    const target = users.find((user) => user.id === id);
    if (!target) return;
    setOpenMenu(null);
    setPendingUserId(id);
    try {
      await updateManagedUser(id, { disabled: !target.disabled });
      setUsers((prev) =>
        prev.map((user) =>
          user.id === id ? { ...user, disabled: !user.disabled } : user,
        ),
      );
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to update the user.'));
    } finally {
      setPendingUserId(null);
    }
  };

  const deleteUser = async (id: string) => {
    const target = users.find((user) => user.id === id);
    if (!target) return;

    setOpenMenu(null);
    const confirmed = await confirmDeletion({
      title: 'Delete this user?',
      text: `${target.name}'s account and all associated session data will be permanently deleted. This cannot be undone.`,
      confirmButtonText: 'Delete user',
    });
    if (!confirmed) return;

    setPendingUserId(id);
    try {
      await deleteManagedUser(id);
      setUsers((previous) => previous.filter((user) => user.id !== id));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to delete the user.'));
    } finally {
      setPendingUserId(null);
    }
  };

  return (
    <>
      <SectionHeader
        title="User Management"
        subtitle="Manage users and review platform membership"
      />

      {loading && <LoadingSpinner text="Loading admin users..." />}
      {error && <ErrorMessage message={error} onRetry={fetchAdminUsers} />}

      {!loading && !error && (
        <Card title="All Users">
          <div className="relative mb-4">
            <Search
              aria-hidden="true"
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#858dab]"
            />
            <label htmlFor="admin-user-search" className="sr-only">
              Search users
            </label>
            <input
              id="admin-user-search"
              type="search"
              placeholder="Search users..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={`${styles.inputBase} ${styles.inputWithIcon}`}
            />
          </div>

          {filtered.length === 0 ? (
            <EmptyState
              compact
              icon={UsersRound}
              title={search ? 'No matching users' : 'No users yet'}
              description={
                search
                  ? `No platform users match "${search}".`
                  : 'Registered platform users will appear here.'
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <caption className="sr-only">Registered platform users</caption>
                <thead>
                  <tr className={styles.tableHeaderGroup}>
                    <th className="text-left pb-3 font-bold">User</th>
                    <th className="text-left pb-3 font-bold">Sessions</th>
                    <th className="text-left pb-3 font-bold">Joined</th>
                    <th className="text-left pb-3 font-bold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#272b3a]">
                  {filtered.map((user) => (
                    <UserTableRow
                      key={user.id}
                      user={user}
                      openMenu={openMenu}
                      onToggleMenu={setOpenMenu}
                      onDisable={toggleDisable}
                      onDelete={deleteUser}
                      isBusy={pendingUserId === user.id}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="text-[#858dab] text-xs mt-4">
            Showing {filtered.length} of {managedUsers.length} users
          </p>
        </Card>
      )}
    </>
  );
}
