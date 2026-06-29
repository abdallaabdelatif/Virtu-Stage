// app/components/UserTableRow.tsx
import { MoreVertical } from 'lucide-react';
import { styles } from '../utils/styles';
import type { ManagedUser } from '../types/admin';

interface UserTableRowProps {
  user: ManagedUser;
  openMenu: string | null;
  onToggleMenu: (id: string | null) => void;
  onDisable: (id: string) => void;
}

export function UserTableRow({
  user,
  openMenu,
  onToggleMenu,
  onDisable,
}: UserTableRowProps) {
  return (
    <tr className={styles.tableRow}>
      <td className="py-4 pr-4">
        <p className={`font-semibold ${user.disabled ? "text-[#5c6484] line-through" : "text-white"}`}>
          {user.name}
        </p>
        <p className={styles.textMuted}>{user.email}</p>
      </td>
      <td className="py-4 text-[#9aa1bc]">{user.sessions}</td>
      <td className="py-4 text-[#9aa1bc]">{user.joinedAt}</td>
      <td className="py-4">
        <span className={`px-2 py-1 rounded-lg text-xs font-bold ${
          user.role === "admin"
            ? "bg-[#5c7cff]/20 text-[#5c7cff]"
            : "bg-[#272b3a] text-[#9aa1bc]"
        }`}>
          {user.role}
        </span>
      </td>
      <td className="py-4 relative">
        <button
          onClick={() => onToggleMenu(openMenu === user.id ? null : user.id)}
          className="p-1 hover:bg-white/10 rounded-lg transition-colors"
        >
          <MoreVertical className="w-4 h-4 text-[#9aa1bc]" />
        </button>
        {openMenu === user.id && (
          <div className="absolute right-0 top-10 z-10 bg-[#1b1d28] border border-[#393f56] rounded-xl shadow-xl w-44 overflow-hidden">
            <button
              onClick={() => onDisable(user.id)}
              className={`w-full text-left px-4 py-2.5 text-sm hover:bg-white/5 ${
                user.disabled ? "text-[#0bda62]" : "text-red-400"
              }`}
            >
              {user.disabled ? "Enable User" : "Disable User"}
            </button>
          </div>
        )}
      </td>
    </tr>
  );
}
