export const PLATFORM_TIME_ZONE = 'Africa/Cairo';

const EXPLICIT_TIME_ZONE_PATTERN = /(Z|[+-]\d{2}:?\d{2})$/i;

export function parseApiDateTime(value: string): Date {
  const normalized = EXPLICIT_TIME_ZONE_PATTERN.test(value)
    ? value
    : `${value}Z`;
  return new Date(normalized);
}

export function formatPlatformDate(
  value: string,
  options: Intl.DateTimeFormatOptions = {},
): string {
  return parseApiDateTime(value).toLocaleDateString('en-US', {
    timeZone: PLATFORM_TIME_ZONE,
    ...options,
  });
}

export function formatPlatformTime(
  value: string,
  options: Intl.DateTimeFormatOptions = {},
): string {
  return parseApiDateTime(value).toLocaleTimeString('en-US', {
    timeZone: PLATFORM_TIME_ZONE,
    ...options,
  });
}

export function platformTimestampMs(value: string): number {
  return parseApiDateTime(value).getTime();
}

export function formatPlatformCalendarDay(
  value: string,
  options: Intl.DateTimeFormatOptions,
): string {
  return formatPlatformDate(`${value}T12:00:00Z`, options);
}
