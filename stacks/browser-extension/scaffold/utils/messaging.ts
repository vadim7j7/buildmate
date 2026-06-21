import { defineExtensionMessaging } from '@webext-core/messaging';

// One typed protocol for the whole extension. Add a method to ProtocolMap, implement it
// with onMessage() in the background, and call it with sendMessage() from any context.
// See patterns/messaging.md
interface ProtocolMap {
  ping(): string;
  getActiveTab(): { id?: number; url?: string; title?: string };
}

export const { sendMessage, onMessage } = defineExtensionMessaging<ProtocolMap>();
