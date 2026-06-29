export const UNAUTHORIZED_EVENT = 'virtustage:unauthorized';

export function notifyUnauthorized() {
  window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
}
