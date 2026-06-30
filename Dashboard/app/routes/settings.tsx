import { useEffect, useId, useRef, useState } from 'react';
import { AlertCircle, CheckCircle, LogOut, Shield, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
  deleteAccount,
  updateUserProfile,
  uploadAvatar,
} from '../services/settingsService';
import { changePasswordCall } from '../services/authService';
import { isStrongPassword } from '../utils/accountValidation';
import { getApiErrorMessage } from '../utils/apiError';
import { confirmDeletion } from '../utils/confirmDeletion';

type SettingsTab = 'profile' | 'account';

export default function Settings() {
  const { user, logout, updateUser } = useAuth();
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [toast, setToast] = useState<string | null>(null);
  const [toastType, setToastType] = useState<'success' | 'error'>('success');
  const [firstName, setFirstName] = useState(user?.firstName ?? '');
  const [lastName, setLastName] = useState(user?.lastName ?? '');
  const [avatar, setAvatar] = useState<string | null>(user?.avatar ?? null);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const avatarInputRef = useRef<HTMLInputElement>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setFirstName(user?.firstName ?? '');
    setLastName(user?.lastName ?? '');
    setAvatar(user?.avatar ?? null);
  }, [user?.avatar, user?.firstName, user?.id, user?.lastName]);

  useEffect(
    () => () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    },
    [],
  );

  const showToast = (
    message: string,
    type: 'success' | 'error' = 'success',
  ) => {
    setToastType(type);
    setToast(message);
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(() => setToast(null), 3000);
  };

  const handleAvatarChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      showToast('Avatar must be a JPG, PNG, or WebP image', 'error');
      event.target.value = '';
      return;
    }
    if (file.size > 1024 * 1024) {
      showToast('Avatar must be 1MB or smaller', 'error');
      event.target.value = '';
      return;
    }

    try {
      setIsUploadingAvatar(true);
      const avatarUrl = await uploadAvatar(file);
      setAvatar(avatarUrl);
      updateUser({ avatar: avatarUrl });
      showToast('Avatar updated successfully');
    } catch (error) {
      showToast(getApiErrorMessage(error, 'Failed to update avatar'), 'error');
    } finally {
      setIsUploadingAvatar(false);
      event.target.value = '';
    }
  };

  const handleSave = async (event: React.FormEvent) => {
    event.preventDefault();
    if (activeTab !== 'profile') return;

    try {
      const trimmedFirstName = firstName.trim();
      const trimmedLastName = lastName.trim();
      if (!trimmedFirstName || !trimmedLastName) {
        showToast('First name and last name are required', 'error');
        return;
      }

      setIsSavingProfile(true);
      await updateUserProfile(trimmedFirstName, trimmedLastName);
      updateUser({
        firstName: trimmedFirstName,
        lastName: trimmedLastName,
        name: `${trimmedFirstName} ${trimmedLastName}`,
      });

      showToast('Settings saved successfully');
    } catch (error) {
      showToast(getApiErrorMessage(error, 'Failed to save settings'), 'error');
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleDiscard = () => {
    setFirstName(user?.firstName ?? '');
    setLastName(user?.lastName ?? '');
  };

  const handleDeleteAccount = async () => {
    const confirmed = await confirmDeletion({
      title: 'Delete your account?',
      text: 'Your account and all associated session data will be permanently deleted. This cannot be undone.',
      confirmButtonText: 'Delete my account',
    });
    if (!confirmed) return;

    try {
      await deleteAccount();
      logout();
    } catch (error) {
      showToast(getApiErrorMessage(error, 'Failed to delete account'), 'error');
    }
  };

  const handleChangePassword = async () => {
    setPasswordError(null);
    if (!currentPassword || !newPassword || !confirmNewPassword) {
      setPasswordError('Complete all password fields');
      return;
    }
    if (!isStrongPassword(newPassword)) {
      setPasswordError(
        'New password must include at least 8 characters, uppercase, lowercase, number, and special character',
      );
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setPasswordError('New passwords do not match');
      return;
    }
    if (currentPassword === newPassword) {
      setPasswordError('New password must be different from current password');
      return;
    }

    try {
      setIsChangingPassword(true);
      const result = await changePasswordCall(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
      showToast(result.message);
    } catch (error) {
      setPasswordError(getApiErrorMessage(error, 'Failed to update password'));
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <>
      {toast && (
        <div className="fixed top-24 left-1/2 -translate-x-1/2 z-50 animate-in fade-in slide-in-from-top-5">
          <div
            role={toastType === 'error' ? 'alert' : 'status'}
            aria-live={toastType === 'error' ? 'assertive' : 'polite'}
            aria-atomic="true"
            className={`bg-[#1a2117] border rounded-xl p-4 flex items-center gap-3 shadow-2xl ${
              toastType === 'success'
                ? 'border-[#0bda62]/30 shadow-[#0bda62]/10'
                : 'border-red-500/30 shadow-red-500/10'
            }`}
          >
            {toastType === 'success' ? (
              <CheckCircle className="w-5 h-5 text-[#0bda62]" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-400" />
            )}
            <p className="text-white font-bold text-sm">{toast}</p>
          </div>
        </div>
      )}

      <div className="mb-8">
        <h1 className="text-3xl font-black tracking-tight">Settings</h1>
        <p className="text-[#d9d9d9] mt-1">
          Manage your profile and account security.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        <div className="w-full lg:w-64 shrink-0 flex flex-col gap-1">
          <TabButton
            icon={<User size={18} />}
            label="Profile Information"
            active={activeTab === 'profile'}
            onClick={() => setActiveTab('profile')}
          />
          <TabButton
            icon={<Shield size={18} />}
            label="Account"
            active={activeTab === 'account'}
            onClick={() => setActiveTab('account')}
          />

          <div className="h-px bg-[#2a3325] my-4 mx-2" />

          <button
            onClick={logout}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-left text-red-400 hover:bg-red-400/10 transition-colors font-medium text-sm"
          >
            <LogOut size={18} />
            Sign Out Securely
          </button>
        </div>

        <div className="flex-1 bg-[#121610] border border-[#2a3325] rounded-3xl p-6 md:p-8">
          <form onSubmit={handleSave}>
            {activeTab === 'profile' && (
              <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                <h2 className="text-xl font-black text-white mb-6">
                  Profile Information
                </h2>

                <input
                  ref={avatarInputRef}
                  aria-label="Choose a profile image"
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={handleAvatarChange}
                />

                <div className="flex items-center gap-6 mb-8">
                  <div className="w-20 h-20 rounded-full bg-brand/20 border border-brand/30 flex items-center justify-center text-2xl font-black text-brand-soft overflow-hidden shrink-0">
                    {avatar ? (
                      <img
                        src={avatar}
                        alt="User avatar"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      (firstName.charAt(0) || 'U').toUpperCase()
                    )}
                  </div>
                  <div>
                    <button
                      type="button"
                      disabled={isUploadingAvatar}
                      onClick={() => avatarInputRef.current?.click()}
                      className="bg-[#2a3325] hover:bg-[#46513c] disabled:opacity-60 disabled:cursor-not-allowed text-white text-sm font-bold px-4 py-2 rounded-lg transition-colors mb-2"
                    >
                      {isUploadingAvatar ? 'Uploading...' : 'Change Avatar'}
                    </button>
                    <p className="text-[#aeb4a8] text-xs">
                      JPG, PNG or WebP. 1MB max.
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <ProfileField
                    label="First Name"
                    value={firstName}
                    onChange={setFirstName}
                  />
                  <ProfileField
                    label="Last Name"
                    value={lastName}
                    onChange={setLastName}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <ReadOnlyField
                    label="Username"
                    value={user?.username ?? ''}
                  />
                  <ReadOnlyField
                    label="Email Address"
                    value={user?.email ?? ''}
                    type="email"
                  />
                </div>
              </div>
            )}

            {activeTab === 'account' && (
              <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                <h2 className="text-xl font-black text-white mb-6">
                  Account Security
                </h2>
                <div className="mb-8">
                  <h3 className="text-lg font-bold text-white mb-3">
                    Change Password
                  </h3>
                  <div className="space-y-4">
                    {passwordError && (
                      <p
                        role="alert"
                        className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400"
                      >
                        {passwordError}
                      </p>
                    )}
                    <label
                      htmlFor="current-password"
                      className="text-sm font-bold text-secondary"
                    >
                      Current password
                    </label>
                    <input
                      id="current-password"
                      type="password"
                      placeholder="Enter current password"
                      autoComplete="current-password"
                      value={currentPassword}
                      onChange={(event) => {
                        setCurrentPassword(event.target.value);
                        setPasswordError(null);
                      }}
                      className="w-full bg-[#1a2117] border border-[#46513c] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand"
                    />
                    <label
                      htmlFor="new-password"
                      className="text-sm font-bold text-secondary"
                    >
                      New password
                    </label>
                    <input
                      id="new-password"
                      type="password"
                      placeholder="Enter new password"
                      autoComplete="new-password"
                      value={newPassword}
                      onChange={(event) => {
                        setNewPassword(event.target.value);
                        setPasswordError(null);
                      }}
                      className="w-full bg-[#1a2117] border border-[#46513c] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand"
                    />
                    <label
                      htmlFor="confirm-new-password"
                      className="text-sm font-bold text-secondary"
                    >
                      Confirm new password
                    </label>
                    <input
                      id="confirm-new-password"
                      type="password"
                      placeholder="Confirm new password"
                      autoComplete="new-password"
                      value={confirmNewPassword}
                      onChange={(event) => {
                        setConfirmNewPassword(event.target.value);
                        setPasswordError(null);
                      }}
                      className="w-full bg-[#1a2117] border border-[#46513c] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand"
                    />
                    <button
                      type="button"
                      onClick={() => void handleChangePassword()}
                      disabled={isChangingPassword}
                      className="bg-[#2a3325] hover:bg-[#46513c] disabled:cursor-not-allowed disabled:opacity-60 text-white text-sm font-bold px-5 py-2.5 rounded-xl transition-colors"
                    >
                      {isChangingPassword
                        ? 'Updating Password...'
                        : 'Update Password'}
                    </button>
                  </div>
                </div>

                <div className="border border-red-500/20 bg-red-500/5 rounded-2xl p-6">
                  <h3 className="text-red-400 font-black mb-2">Danger Zone</h3>
                  <p className="text-[#d9d9d9] text-sm mb-4">
                    Permanently delete your account and all associated session
                    data. This cannot be undone.
                  </p>
                  <button
                    type="button"
                    onClick={() => void handleDeleteAccount()}
                    className="bg-red-500 hover:bg-red-600 text-white text-sm font-bold px-5 py-2.5 rounded-xl transition-colors shadow-lg shadow-red-500/20"
                  >
                    Delete Account
                  </button>
                </div>
              </div>
            )}

            {activeTab !== 'account' && (
              <div className="mt-8 pt-6 border-t border-[#2a3325] flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => void handleDiscard()}
                  className="text-[#d9d9d9] hover:text-white px-5 py-2.5 text-sm font-bold transition-colors"
                >
                  Discard Changes
                </button>
                <button
                  type="submit"
                  disabled={isSavingProfile}
                  className="bg-brand hover:bg-brand-hover text-brand-contrast px-6 py-2.5 rounded-xl text-sm font-bold transition-colors shadow-lg shadow-brand/20"
                >
                  {isSavingProfile ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            )}
          </form>
        </div>
      </div>
    </>
  );
}

function ProfileField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const id = useId();
  return (
    <div>
      <label
        htmlFor={id}
        className="block text-secondary text-sm font-bold mb-2"
      >
        {label}
      </label>
      <input
        id={id}
        type="text"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required
        className="w-full bg-[#1a2117] border border-[#46513c] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand"
      />
    </div>
  );
}

function ReadOnlyField({
  label,
  value,
  type = 'text',
}: {
  label: string;
  value: string;
  type?: 'text' | 'email';
}) {
  const id = useId();
  return (
    <div>
      <label
        htmlFor={id}
        className="block text-secondary text-sm font-bold mb-2"
      >
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        readOnly
        className="w-full bg-[#1a2117] border border-[#46513c] rounded-xl px-4 py-2.5 text-sm text-[#aeb4a8] cursor-not-allowed"
      />
    </div>
  );
}

function TabButton({
  icon,
  label,
  active,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all text-sm font-bold ${active ? 'bg-brand/10 text-brand-soft shadow-[inset_2px_0_0_#c1ff72]' : 'text-[#d9d9d9] hover:bg-[#2a3325] hover:text-white'}`}
    >
      <span className={active ? 'text-brand-soft' : 'text-[#aeb4a8]'}>
        {icon}
      </span>
      {label}
    </button>
  );
}
