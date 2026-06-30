import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { LoaderCircle, MoreVertical } from 'lucide-react';
import { styles } from '../utils/styles';
import type { ManagedUser } from '../types/admin';

interface UserTableRowProps {
  user: ManagedUser;
  openMenu: string | null;
  onToggleMenu: (id: string | null) => void;
  onDisable: (id: string) => void;
  onDelete: (id: string) => void;
  isBusy: boolean;
}

export function UserTableRow({
  user,
  openMenu,
  onToggleMenu,
  onDisable,
  onDelete,
  isBusy,
}: UserTableRowProps) {
  const actionButtonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
  const isMenuOpen = openMenu === user.id;

  const toggleMenu = () => {
    if (isMenuOpen) {
      onToggleMenu(null);
      return;
    }

    const bounds = actionButtonRef.current?.getBoundingClientRect();
    if (bounds) {
      const menuWidth = 176;
      const menuHeight = 94;
      const gap = 6;
      const top =
        bounds.bottom + gap + menuHeight <= window.innerHeight
          ? bounds.bottom + gap
          : bounds.top - menuHeight - gap;
      setMenuPosition({
        top: Math.max(8, top),
        left: Math.max(
          8,
          Math.min(bounds.right - menuWidth, window.innerWidth - menuWidth - 8),
        ),
      });
    }
    onToggleMenu(user.id);
  };

  useEffect(() => {
    if (!isMenuOpen) return;

    const closeOnOutsideClick = (event: PointerEvent) => {
      const target = event.target as Node;
      if (
        !actionButtonRef.current?.contains(target) &&
        !menuRef.current?.contains(target)
      ) {
        onToggleMenu(null);
      }
    };
    const closeMenu = () => onToggleMenu(null);
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onToggleMenu(null);
        actionButtonRef.current?.focus();
      }
    };

    document.addEventListener('pointerdown', closeOnOutsideClick);
    document.addEventListener('keydown', handleKeyDown);
    window.addEventListener('resize', closeMenu);
    window.addEventListener('scroll', closeMenu, true);
    return () => {
      document.removeEventListener('pointerdown', closeOnOutsideClick);
      document.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('resize', closeMenu);
      window.removeEventListener('scroll', closeMenu, true);
    };
  }, [isMenuOpen, onToggleMenu]);

  return (
    <tr className={styles.tableRow}>
      <td className="py-4 pr-4">
        <p
          className={`font-semibold ${user.disabled ? 'text-[#aeb4a8] line-through' : 'text-white'}`}
        >
          {user.name}
        </p>
        <p className={styles.textMuted}>{user.email}</p>
      </td>
      <td className="py-4 text-[#d9d9d9]">{user.sessions}</td>
      <td className="py-4 text-[#d9d9d9]">{user.joinedAt}</td>
      <td className="py-4">
        <button
          ref={actionButtonRef}
          type="button"
          aria-label={`Actions for ${user.name}`}
          aria-haspopup="menu"
          aria-expanded={isMenuOpen}
          aria-controls={isMenuOpen ? `user-actions-${user.id}` : undefined}
          disabled={isBusy}
          onClick={toggleMenu}
          className="p-1 hover:bg-white/10 rounded-lg transition-colors disabled:cursor-wait disabled:opacity-60"
        >
          {isBusy ? (
            <LoaderCircle className="w-4 h-4 animate-spin text-brand-soft" />
          ) : (
            <MoreVertical className="w-4 h-4 text-[#d9d9d9]" />
          )}
        </button>
        {isMenuOpen &&
          typeof document !== 'undefined' &&
          createPortal(
            <div
              id={`user-actions-${user.id}`}
              ref={menuRef}
              role="menu"
              aria-label={`Actions for ${user.name}`}
              style={{ top: menuPosition.top, left: menuPosition.left }}
              className="fixed z-[100] w-44 overflow-hidden rounded-xl border border-[#46513c] bg-[#1a2117] shadow-xl"
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => onDisable(user.id)}
                className={`w-full text-left px-4 py-2.5 text-sm hover:bg-white/5 ${
                  user.disabled ? 'text-[#0bda62]' : 'text-red-400'
                }`}
              >
                {user.disabled ? 'Enable User' : 'Disable User'}
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => onDelete(user.id)}
                className="w-full border-t border-[#46513c] px-4 py-2.5 text-left text-sm text-red-400 hover:bg-red-500/10"
              >
                Delete User
              </button>
            </div>,
            document.body,
          )}
      </td>
    </tr>
  );
}
