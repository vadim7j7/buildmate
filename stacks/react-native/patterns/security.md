# React Native Security Patterns

Security patterns and best practices for React Native + Expo applications. All
agents must follow these patterns to protect mobile app data and users.

---

## 1. Secure Storage

Never store sensitive data in AsyncStorage. Use secure storage.

```typescript
// WRONG - AsyncStorage is not encrypted
import AsyncStorage from '@react-native-async-storage/async-storage';

await AsyncStorage.setItem('authToken', token);
await AsyncStorage.setItem('userPassword', password);

// CORRECT - use SecureStore for sensitive data
import * as SecureStore from 'expo-secure-store';

await SecureStore.setItemAsync('authToken', token);
const token = await SecureStore.getItemAsync('authToken');
await SecureStore.deleteItemAsync('authToken');

// AsyncStorage is OK for non-sensitive preferences
await AsyncStorage.setItem('theme', 'dark');
await AsyncStorage.setItem('language', 'en');
```

### What Goes Where

| Data Type | Storage | Example |
|-----------|---------|---------|
| Auth tokens | SecureStore | JWT, API keys |
| User credentials | SecureStore | Password, PIN |
| Encryption keys | SecureStore | Symmetric keys |
| User preferences | AsyncStorage | Theme, language |
| Cache data | AsyncStorage | Non-sensitive cache |
| Temporary data | Memory (state) | Form inputs |

---

## 2. API Communication

### HTTPS Only

```typescript
// WRONG - HTTP (unencrypted, can be intercepted)
const API_URL = 'http://api.example.com';

// CORRECT - HTTPS only
const API_URL = 'https://api.example.com';

// For development, use ngrok or similar for HTTPS
const API_URL = __DEV__
  ? 'https://abc123.ngrok.io'
  : 'https://api.example.com';
```

### Certificate Pinning (Optional, High Security)

```typescript
// For high-security apps, implement certificate pinning
// Using react-native-ssl-pinning
import { fetch as pinnedFetch } from 'react-native-ssl-pinning';

const response = await pinnedFetch('https://api.example.com/data', {
  method: 'GET',
  sslPinning: {
    certs: ['cert1', 'cert2'],  // Certificate names in assets
  },
});
```

### Token Management

```typescript
// services/auth.ts
import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export async function storeTokens(accessToken: string, refreshToken: string) {
  await SecureStore.setItemAsync(TOKEN_KEY, accessToken);
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken);
}

export async function getAccessToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export async function clearTokens() {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
}

// API client with automatic token refresh
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  let token = await getAccessToken();

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    // Token expired, try refresh
    token = await refreshAccessToken();
    if (token) {
      return fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${token}`,
        },
      });
    }
    // Refresh failed, log out user
    await clearTokens();
    throw new AuthenticationError('Session expired');
  }

  return response;
}
```

---

## 3. Input Validation

Validate all user input before sending to API or storing.

```typescript
// WRONG - trusting user input
const sendMessage = async (message: string) => {
  await api.post('/messages', { content: message });
};

// CORRECT - validate and sanitize
import { z } from 'zod';

const messageSchema = z.object({
  content: z.string()
    .min(1, 'Message cannot be empty')
    .max(5000, 'Message too long')
    .trim(),
});

const sendMessage = async (message: string) => {
  const result = messageSchema.safeParse({ content: message });
  if (!result.success) {
    throw new ValidationError(result.error.message);
  }
  await api.post('/messages', result.data);
};
```

### Form Validation

```typescript
// screens/ProfileForm.tsx
import { z } from 'zod';

const profileSchema = z.object({
  name: z.string().min(2).max(100).trim(),
  email: z.string().email(),
  phone: z.string().regex(/^\+?[1-9]\d{1,14}$/).optional(),
  bio: z.string().max(500).optional(),
});

type ProfileFormData = z.infer<typeof profileSchema>;

function ProfileForm() {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (data: ProfileFormData) => {
    const result = profileSchema.safeParse(data);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.errors.forEach((err) => {
        if (err.path[0]) {
          fieldErrors[err.path[0] as string] = err.message;
        }
      });
      setErrors(fieldErrors);
      return;
    }

    await updateProfile(result.data);
  };
}
```

---

## 4. Deep Link Security

Validate all deep link parameters.

```typescript
// WRONG - trusting deep link parameters
// myapp://reset-password?token=abc123
export default function ResetPassword() {
  const { token } = useLocalSearchParams();
  // Directly using token without validation
  await resetPassword(token);
}

// CORRECT - validate deep link parameters
const tokenSchema = z.string().min(32).max(128).regex(/^[a-zA-Z0-9]+$/);

export default function ResetPassword() {
  const { token } = useLocalSearchParams<{ token?: string }>();

  useEffect(() => {
    if (!token) {
      Alert.alert('Error', 'Invalid reset link');
      router.replace('/login');
      return;
    }

    const result = tokenSchema.safeParse(token);
    if (!result.success) {
      Alert.alert('Error', 'Invalid reset token');
      router.replace('/login');
      return;
    }

    // Token is valid format, verify with server
    verifyResetToken(result.data);
  }, [token]);
}
```

### URL Scheme Protection

```typescript
// app.json
{
  "expo": {
    "scheme": "myapp",
    // Add URL intent filters for Android
    "android": {
      "intentFilters": [
        {
          "action": "VIEW",
          "autoVerify": true,  // Enable App Links verification
          "data": [
            {
              "scheme": "https",
              "host": "*.myapp.com",
              "pathPrefix": "/app"
            }
          ],
          "category": ["BROWSABLE", "DEFAULT"]
        }
      ]
    }
  }
}
```

---

## 5. Biometric Authentication

```typescript
// hooks/useBiometricAuth.ts
import * as LocalAuthentication from 'expo-local-authentication';

export function useBiometricAuth() {
  const [isAvailable, setIsAvailable] = useState(false);

  useEffect(() => {
    checkAvailability();
  }, []);

  const checkAvailability = async () => {
    const compatible = await LocalAuthentication.hasHardwareAsync();
    const enrolled = await LocalAuthentication.isEnrolledAsync();
    setIsAvailable(compatible && enrolled);
  };

  const authenticate = async (prompt: string): Promise<boolean> => {
    if (!isAvailable) return false;

    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: prompt,
      cancelLabel: 'Cancel',
      disableDeviceFallback: false,  // Allow PIN/password fallback
      fallbackLabel: 'Use passcode',
    });

    return result.success;
  };

  return { isAvailable, authenticate };
}

// Usage
function SensitiveAction() {
  const { isAvailable, authenticate } = useBiometricAuth();

  const handleSensitiveAction = async () => {
    if (isAvailable) {
      const authenticated = await authenticate('Confirm your identity');
      if (!authenticated) {
        Alert.alert('Authentication required');
        return;
      }
    }

    // Proceed with sensitive action
    await performSensitiveAction();
  };
}
```

---

## 6. Data in Transit

### Encryption for Sensitive Payloads

```typescript
// For extra-sensitive data, encrypt before sending
import * as Crypto from 'expo-crypto';

async function encryptSensitiveData(data: string, key: string): Promise<string> {
  // Use server-provided public key for asymmetric encryption
  // Or use symmetric encryption with a derived key
  const encrypted = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    data + key
  );
  return encrypted;
}
```

### Request Signing

```typescript
// Sign requests to prevent tampering
async function signRequest(body: object, timestamp: number): Promise<string> {
  const secret = await SecureStore.getItemAsync('apiSecret');
  const payload = JSON.stringify(body) + timestamp.toString();

  const signature = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    payload + secret
  );

  return signature;
}

async function secureApiCall(endpoint: string, body: object) {
  const timestamp = Date.now();
  const signature = await signRequest(body, timestamp);

  return fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Timestamp': timestamp.toString(),
      'X-Signature': signature,
    },
    body: JSON.stringify(body),
  });
}
```

---

## 7. Screenshot Prevention

Prevent screenshots of sensitive screens.

```typescript
// For sensitive screens, prevent screenshots
import { usePreventScreenCapture } from 'expo-screen-capture';

function SensitiveScreen() {
  usePreventScreenCapture();

  return (
    <View>
      <Text>Sensitive content here</Text>
    </View>
  );
}

// Or toggle based on state
function BankingScreen() {
  const [showBalance, setShowBalance] = useState(false);

  usePreventScreenCapture(showBalance);  // Prevent when balance visible

  return (
    <View>
      <Button onPress={() => setShowBalance(true)}>Show Balance</Button>
      {showBalance && <Text>$10,000.00</Text>}
    </View>
  );
}
```

---

## 8. Jailbreak/Root Detection

```typescript
// Detect compromised devices for high-security apps
import * as Device from 'expo-device';

async function checkDeviceSecurity(): Promise<{
  isSecure: boolean;
  warnings: string[];
}> {
  const warnings: string[] = [];

  // Check if running in emulator (might be risky in production)
  if (!Device.isDevice) {
    warnings.push('Running on emulator/simulator');
  }

  // For more robust detection, use a dedicated library
  // like 'jail-monkey' or 'react-native-device-info'

  return {
    isSecure: warnings.length === 0,
    warnings,
  };
}

// Usage on app start
useEffect(() => {
  const checkSecurity = async () => {
    const { isSecure, warnings } = await checkDeviceSecurity();
    if (!isSecure && !__DEV__) {
      Alert.alert(
        'Security Warning',
        'This device may be compromised. Some features may be restricted.',
        [{ text: 'OK' }]
      );
    }
  };

  checkSecurity();
}, []);
```

---

## 9. Logging and Analytics

Never log sensitive data.

```typescript
// WRONG - logging sensitive data
console.log('User logged in:', { email, password, token });

// CORRECT - redact sensitive fields
console.log('User logged in:', { email, password: '[REDACTED]' });

// Use a logging utility that auto-redacts
const logger = {
  info: (message: string, data?: object) => {
    if (__DEV__) {
      console.log(message, sanitizeForLogging(data));
    }
    // In production, send to crash reporting without sensitive data
  },
};

function sanitizeForLogging(data?: object): object | undefined {
  if (!data) return undefined;

  const sensitiveKeys = ['password', 'token', 'secret', 'key', 'auth'];
  const sanitized = { ...data };

  for (const key of Object.keys(sanitized)) {
    if (sensitiveKeys.some((k) => key.toLowerCase().includes(k))) {
      (sanitized as Record<string, unknown>)[key] = '[REDACTED]';
    }
  }

  return sanitized;
}
```

---

## 10. Clipboard Security

```typescript
// Be careful with clipboard - it's shared across apps
import * as Clipboard from 'expo-clipboard';

// WRONG - leaving sensitive data in clipboard indefinitely
await Clipboard.setStringAsync(authToken);

// CORRECT - clear clipboard after a short delay
async function copyToClipboard(text: string, clearAfterMs = 30000) {
  await Clipboard.setStringAsync(text);

  // Clear after delay
  setTimeout(async () => {
    const current = await Clipboard.getStringAsync();
    if (current === text) {
      await Clipboard.setStringAsync('');
    }
  }, clearAfterMs);
}

// Usage
copyToClipboard(recoveryCode, 60000);  // Clear after 1 minute
```

---

## Security Checklist

Before releasing any feature, verify:

- [ ] Sensitive data stored in SecureStore, not AsyncStorage
- [ ] All API calls use HTTPS
- [ ] Auth tokens managed securely with refresh logic
- [ ] All user input validated with Zod or similar
- [ ] Deep link parameters validated before use
- [ ] Biometric auth for sensitive actions
- [ ] Screenshots prevented on sensitive screens
- [ ] No sensitive data in logs
- [ ] Clipboard cleared after copying sensitive data
- [ ] Error messages don't expose internal details
