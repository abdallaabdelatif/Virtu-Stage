import { useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  Bell,
  CheckCircle,
  LogOut,
  Shield,
  User,
} from 'lucide-react';
import { PageLayout } from '../components/PageLayout';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { useAuth } from '../context/AuthContext';
import {
  deleteAccount,
  getSettings,
  saveSettings,
  updateUserProfile,
  uploadAvatar,
} from '../services/settingsService';
import { changePasswordCall } from '../services/authService';
import { isStrongPassword } from '../utils/accountValidation';
import { getApiErrorMessage } from '../utils/apiError';
import { confirmDeletion } from '../utils/confirmDeletion';

type SettingsTab = 'profile' | 'notifications' | 'account';

export default function Settings() {
  const { user, logout, updateUser } = useAuth();
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [toast, setToast] = useState<string | null>(null);
  const [toastType, setToastType] = useState<'success' | 'error'>('success');
  const [firstName, setFirstName] = useState(user?.firstName ?? '');
  const [lastName, setLastName] = useState(user?.lastName ?? '');
  const [sessionAnalysisNotifications, setSessionAnalysisNotifications] =
    useState(true);
  const [weeklyDigest, setWeeklyDigest] = useState(false);
  const [settingsLoadError, setSettingsLoadError] = useState<string | null>(
    null,
  );
  const [avatar, setAvatar] = useState<string | null>(user?.avatar ?? null);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const avatarInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setFirstName(user?.firstName ?? '');
    setLastName(user?.lastName ?? '');
    setAvatar(user?.avatar ?? null);
  }, [user?.id]);

  const loadNotificationSettings = async () => {
    try {
      setSettingsLoadError(null);
      const settings = await getSettings();
      setSessionAnalysisNotifications(
        settings.sessionAnalysisNotifications ?? true,
      );
      setWeeklyDigest(settings.weeklyDigest ?? false);
    } catch (error) {
      setSettingsLoadError(
        getApiErrorMessage(error, 'Failed to load notification settings'),
      );
    }
  };

  useEffect(() => {
    void loadNotificationSettings();
  }, []);

  const showToast = (
    message: string,
    type: 'success' | 'error' = 'success',
  ) => {
    setToastType(type);
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  };

  const handleAvatarChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (file.size > 1024 * 1024) {
      showToast('Avatar must be 1MB or smaller', 'error');
      return;
    }

    try {
      const avatarUrl = await uploadAvatar(file);
      setAvatar(avatarUrl);
      updateUser({ avatar: avatarUrl });
      showToast('Avatar updated successfully');
    } catch (error) {
      showToast(
        getApiErrorMessage(error, 'Failed to update avatar'),
        'error',
      );
    } finally {
      event.target.value = '';
    }
  };

  const handleSave = async (event: React.FormEvent) => {
    event.preventDefault();

    try {
      if (activeTab === 'profile') {
        const trimmedFirstName = firstName.trim();
        const trimmedLastName = lastName.trim();
        if (!trimmedFirstName || !trimmedLastName) {
          showToast('First name and last name are required', 'error');
          return;
        }

        await updateUserProfile(trimmedFirstName, trimmedLastName);
        updateUser({
          firstName: trimmedFirstName,
          lastName: trimmedLastName,
          name: `${trimmedFirstName} ${trimmedLastName}`,
        });
      } else if (activeTab === 'notifications') {
        await saveSettings({
          sessionAnalysisNotifications,
          weeklyDigest,
        });
      }

      showToast('Settings saved successfully');
    } catch (error) {
      showToast(
        getApiErrorMessage(error, 'Failed to save settings'),
        'error',
      );
    }
  };

  const handleDiscard = async () => {
    if (activeTab === 'profile') {
      setFirstName(user?.firstName ?? '');
      setLastName(user?.lastName ?? '');
      return;
    }

    try {
      await loadNotificationSettings();
    } catch (error) {
      showToast(
        getApiErrorMessage(error, 'Failed to reload settings'),
        'error',
      );
    }
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
      showToast(
        getApiErrorMessage(error, 'Failed to delete account'),
        'error',
      );
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
      setPasswordError(
        getApiErrorMessage(error, 'Failed to update password'),
      );
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <ProtectedRoute>
      <PageLayout>
        {toast && (
          <div className="fixed top-24 left-1/2 -translate-x-1/2 z-50 animate-in fade-in slide-in-from-top-5">
            <div
              className={`bg-[#1b1d28] border rounded-xl p-4 flex items-center gap-3 shadow-2xl ${
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
          <p className="text-[#9aa1bc] mt-1">
            Manage your profile, notifications, and account security.
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
              icon={<Bell size={18} />}
              label="Notifications"
              active={activeTab === 'notifications'}
              onClick={() => setActiveTab('notifications')}
            />
            <TabButton
              icon={<Shield size={18} />}
              label="Account"
              active={activeTab === 'account'}
              onClick={() => setActiveTab('account')}
            />

            <div className="h-px bg-[#272b3a] my-4 mx-2" />

            <button
              onClick={logout}
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-left text-red-400 hover:bg-red-400/10 transition-colors font-medium text-sm"
            >
              <LogOut size={18} />
              Sign Out Securely
            </button>
          </div>

          <div className="flex-1 bg-[#12141c] border border-[#272b3a] rounded-3xl p-6 md:p-8">
            <form onSubmit={handleSave}>
              {activeTab === 'profile' && (
                <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <h2 className="text-xl font-black text-white mb-6">
                    Profile Information
                  </h2>

                  <input
                    ref={avatarInputRef}
                    type="file"
                    accept="image/png, image/jpeg, image/gif"
                    className="hidden"
                    onChange={handleAvatarChange}
                  />

                  <div className="flex items-center gap-6 mb-8">
                    <div className="w-20 h-20 rounded-full bg-[#5c7cff]/20 border border-[#5c7cff]/30 flex items-center justify-center text-2xl font-black text-[#5c7cff] overflow-hidden shrink-0">
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
                        onClick={() => avatarInputRef.current?.click()}
                        className="bg-[#272b3a] hover:bg-[#393f56] text-white text-sm font-bold px-4 py-2 rounded-lg transition-colors mb-2"
                      >
                        Change Avatar
                      </button>
                      <p className="text-[#5c6484] text-xs">
                        JPG, GIF or PNG. 1MB max.
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

              {activeTab === 'notifications' && (
                <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <h2 className="text-xl font-black text-white mb-6">
                    Notification Preferences
                  </h2>
                  {settingsLoadError && (
                    <div className="mb-6 flex items-start justify-between gap-4 rounded-xl border border-red-500/30 bg-red-500/10 p-4">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
                        <div>
                          <p className="text-sm font-bold text-red-300">
                            Could not load notification settings
                          </p>
                          <p className="mt-1 text-xs text-red-200/80">
                            {settingsLoadError}
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => void loadNotificationSettings()}
                        className="shrink-0 text-sm font-bold text-red-300 hover:text-white"
                      >
                        Retry
                      </button>
                    </div>
                  )}
                  <div className="space-y-6">
                    <ToggleRow
                      title="Session Processing Analysis"
                      desc="Get notified when AI finishes analyzing your VR session."
                      checked={sessionAnalysisNotifications}
                      onChange={setSessionAnalysisNotifications}
                    />
                    <ToggleRow
                      title="Weekly Digest"
                      desc="Receive a weekly email summarizing your performance progression."
                      checked={weeklyDigest}
                      onChange={setWeeklyDigest}
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
                      <input
                        type="password"
                        placeholder="Current Password"
                        autoComplete="current-password"
                        value={currentPassword}
                        onChange={(event) => {
                          setCurrentPassword(event.target.value);
                          setPasswordError(null);
                        }}
                        className="w-full bg-[#1b1d28] border border-[#393f56] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[#5c7cff]"
                      />
                      <input
                        type="password"
                        placeholder="New Password"
                        autoComplete="new-password"
                        value={newPassword}
                        onChange={(event) => {
                          setNewPassword(event.target.value);
                          setPasswordError(null);
                        }}
                        className="w-full bg-[#1b1d28] border border-[#393f56] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[#5c7cff]"
                      />
                      <input
                        type="password"
                        placeholder="Confirm New Password"
                        autoComplete="new-password"
                        value={confirmNewPassword}
                        onChange={(event) => {
                          setConfirmNewPassword(event.target.value);
                          setPasswordError(null);
                        }}
                        className="w-full bg-[#1b1d28] border border-[#393f56] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[#5c7cff]"
                      />
                      <button
                        type="button"
                        onClick={() => void handleChangePassword()}
                        disabled={isChangingPassword}
                        className="bg-[#272b3a] hover:bg-[#393f56] disabled:cursor-not-allowed disabled:opacity-60 text-white text-sm font-bold px-5 py-2.5 rounded-xl transition-colors"
                      >
                        {isChangingPassword
                          ? 'Updating Password...'
                          : 'Update Password'}
                      </button>
                    </div>
                  </div>

                  <div className="border border-red-500/20 bg-red-500/5 rounded-2xl p-6">
                    <h3 className="text-red-400 font-black mb-2">
                      Danger Zone
                    </h3>
                    <p className="text-[#9aa1bc] text-sm mb-4">
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
                <div className="mt-8 pt-6 border-t border-[#272b3a] flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => void handleDiscard()}
                    className="text-[#9aa1bc] hover:text-white px-5 py-2.5 text-sm font-bold transition-colors"
                  >
                    Discard Changes
                  </button>
                  <button
                    type="submit"
                    className="bg-[#5c7cff] hover:bg-[#4a6aee] text-white px-6 py-2.5 rounded-xl text-sm font-bold transition-colors shadow-lg shadow-[#5c7cff]/20"
                  >
                    Save Preferences
                  </button>
                </div>
              )}
            </form>
          </div>
        </div>
      </PageLayout>
    </ProtectedRoute>
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
  return (
    <div>
      <label className="block text-[#9aa1bc] text-sm font-bold mb-2">
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required
        className="w-full bg-[#1b1d28] border border-[#393f56] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[#5c7cff]"
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
  return (
    <div>
      <label className="block text-[#9aa1bc] text-sm font-bold mb-2">
        {label}
      </label>
      <input
        type={type}
        value={value}
        readOnly
        className="w-full bg-[#1b1d28] border border-[#393f56] rounded-xl px-4 py-2.5 text-sm text-[#5c6484] cursor-not-allowed"
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
      className={`flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all text-sm font-bold ${active ? 'bg-[#5c7cff]/10 text-[#5c7cff] shadow-[inset_2px_0_0_#5c7cff]' : 'text-[#9aa1bc] hover:bg-[#272b3a] hover:text-white'}`}
    >
      <span className={active ? 'text-[#5c7cff]' : 'text-[#5c6484]'}>
        {icon}
      </span>
      {label}
    </button>
  );
}

function ToggleRow({
  title,
  desc,
  checked,
  onChange,
}: {
  title: string;
  desc: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-6 p-4 rounded-xl bg-[#1b1d28] border border-[#272b3a]">
      <div>
        <h4 className="text-white font-bold text-sm mb-1">{title}</h4>
        <p className="text-[#5c6484] text-xs">{desc}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative w-12 h-6 rounded-full transition-colors shrink-0 ${checked ? 'bg-[#5c7cff]' : 'bg-[#393f56]'}`}
      >
        <span
          className={`absolute left-0 top-1 w-4 h-4 rounded-full bg-white transition-transform ${checked ? 'translate-x-7' : 'translate-x-1'}`}
        />
      </button>
    </div>
  );
}
