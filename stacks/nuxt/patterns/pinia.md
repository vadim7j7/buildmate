# Pinia in Nuxt 4

State shared across pages and components lives in Pinia stores, installed with the
`@pinia/nuxt` module. Server data that a single page reads stays in `useFetch` /
`useAsyncData`; a store is for state several places read and change (the signed-in
user's preferences, a cart, a multi-step wizard).

## Setup

```bash
npx nuxi module add pinia      # installs pinia + @pinia/nuxt, adds it to modules
```

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@pinia/nuxt'],
});
```

Stores in `app/stores/` are auto-imported, as are `defineStore`, `storeToRefs`,
`acceptHMRUpdate`.

## Store (setup syntax)

```ts
// app/stores/cart.ts
export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([]);
  const total = computed(() => items.value.reduce((sum, i) => sum + i.price * i.qty, 0));

  async function load() {
    items.value = await $fetch('/api/cart');
  }

  async function add(productId: string) {
    const item = await $fetch('/api/cart', { method: 'POST', body: { productId } });
    items.value.push(item);
  }

  function $reset() {
    items.value = [];
  }

  return { items, total, load, add, $reset };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useCartStore, import.meta.hot));
}
```

Rules:

- One store per domain concept, id = file name, `use<Name>Store`.
- Return every piece of state from the setup function (unreturned refs are not
  serialized to the client and break SSR hydration).
- Actions call the API with `$fetch`, never `useFetch` (actions run after setup).
- Setup stores have no built-in `$reset`; define one if callers need it.

## Loading Data on the Server

Fill a store during SSR once, and let the client reuse the serialized state:

```vue
<!-- app/pages/cart.vue -->
<script setup lang="ts">
const cart = useCartStore();
await callOnce('cart', () => cart.load()); // runs on the server, not again on hydration

const { items, total } = storeToRefs(cart);  // keep reactivity when destructuring
</script>
```

- `callOnce` (or `useAsyncData('cart', () => cart.load().then(() => true))`) avoids
  the double fetch you get from calling `cart.load()` directly in setup.
- Destructure state with `storeToRefs`; actions can be destructured from the store.
- Never create a store or `ref` at module scope outside `defineStore`: on the server
  that state is shared by every request (one user's data leaks to another).

## Using a Store in Middleware and Plugins

```ts
// app/middleware/cart-not-empty.ts
export default defineNuxtRouteMiddleware(() => {
  const cart = useCartStore(); // inside the function, not at module scope
  if (cart.items.length === 0) return navigateTo('/products');
});
```

## Testing

```ts
// tests/nuxt/CartBadge.test.ts
import { mountSuspended } from '@nuxt/test-utils/runtime';
import { createTestingPinia } from '@pinia/testing';
import { it, expect, vi } from 'vitest';
import CartBadge from '~/components/CartBadge.vue';

it('shows the item count', async () => {
  const wrapper = await mountSuspended(CartBadge, {
    global: {
      plugins: [
        createTestingPinia({ createSpy: vi.fn, initialState: { cart: { items: [{ id: '1', price: 5, qty: 2 }] } } }),
      ],
    },
  });
  expect(wrapper.text()).toContain('2');
});
```

Unit-test a store's logic with `setActivePinia(createPinia())` in `beforeEach` and
`registerEndpoint` for the API it calls.
