import { describe, expect, it } from 'vitest';
import {
  getPasswordChecks,
  getUsernameError,
  isStrongPassword,
} from './accountValidation';

describe('account validation', () => {
  it('accepts valid usernames and rejects unsafe formats', () => {
    expect(getUsernameError('valid.user_1')).toBeNull();
    expect(getUsernameError('_invalid')).toMatch(/start with/i);
    expect(getUsernameError('ab')).toMatch(/at least 3/i);
  });

  it('requires every password strength category', () => {
    expect(isStrongPassword('Strong1!')).toBe(true);
    expect(isStrongPassword('missing-number!')).toBe(false);
    expect(getPasswordChecks('Strong1!')).toEqual({
      minLength: true,
      uppercase: true,
      lowercase: true,
      number: true,
      specialCharacter: true,
    });
  });
});
