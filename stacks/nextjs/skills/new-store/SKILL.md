---
name: new-store
description: Generate a state management store for the configured library
---

# /new-store

## What This Does

Generates a new state store using the project's configured state management library
(Zustand, Redux Toolkit, MobX, or Jotai). The store holds **UI state only** — never
server data or database records (use React Query / SWR for that).

## Usage

```
/new-store cart                     # stores/useCartStore.ts (Zustand)
/new-store cart                     # store/slices/cartSlice.ts (Redux)
/new-store cart                     # stores/CartStore.ts (MobX)
/new-store cart                     # atoms/cartAtoms.ts (Jotai)
```

## How It Works

1. **Detect the state library.** Check the project's dependencies:
   - `zustand` → Zustand store
   - `@reduxjs/toolkit` → Redux Toolkit slice
   - `mobx` + `mobx-react-lite` → MobX store
   - `jotai` → Jotai atoms

2. **Generate the store file.** Based on the detected library:

### Zustand

```typescript
// stores/useCartStore.ts
import { create } from 'zustand';

type CartState = {
  items: CartItem[];
  isOpen: boolean;
  addItem: (item: CartItem) => void;
  removeItem: (id: string) => void;
  toggleCart: () => void;
  reset: () => void;
};

const initialState = {
  items: [] as CartItem[],
  isOpen: false,
};

export const useCartStore = create<CartState>()((set) => ({
  ...initialState,
  addItem: (item) => set((s) => ({ items: [...s.items, item] })),
  removeItem: (id) => set((s) => ({ items: s.items.filter((i) => i.id !== id) })),
  toggleCart: () => set((s) => ({ isOpen: !s.isOpen })),
  reset: () => set(initialState),
}));
```

### Redux Toolkit

```typescript
// store/slices/cartSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type CartState = {
  items: CartItem[];
  isOpen: boolean;
};

const initialState: CartState = {
  items: [],
  isOpen: false,
};

export const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    addItem: (state, action: PayloadAction<CartItem>) => {
      state.items.push(action.payload);
    },
    removeItem: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter((i) => i.id !== action.payload);
    },
    toggleCart: (state) => {
      state.isOpen = !state.isOpen;
    },
    reset: () => initialState,
  },
});

export const { addItem, removeItem, toggleCart, reset } = cartSlice.actions;
export default cartSlice.reducer;
```

### MobX

```typescript
// stores/CartStore.ts
import { makeAutoObservable } from 'mobx';

class CartStore {
  items: CartItem[] = [];
  isOpen = false;

  constructor() {
    makeAutoObservable(this);
  }

  addItem(item: CartItem) {
    this.items.push(item);
  }

  removeItem(id: string) {
    this.items = this.items.filter((i) => i.id !== id);
  }

  toggleCart() {
    this.isOpen = !this.isOpen;
  }

  reset() {
    this.items = [];
    this.isOpen = false;
  }
}

export const cartStore = new CartStore();
```

### Jotai

```typescript
// atoms/cartAtoms.ts
import { atom } from 'jotai';

export const cartItemsAtom = atom<CartItem[]>([]);
export const cartIsOpenAtom = atom(false);

// Derived atoms
export const cartCountAtom = atom((get) => get(cartItemsAtom).length);
export const cartTotalAtom = atom((get) =>
  get(cartItemsAtom).reduce((sum, item) => sum + item.price, 0)
);

// Write atoms
export const addItemAtom = atom(null, (get, set, item: CartItem) => {
  set(cartItemsAtom, [...get(cartItemsAtom), item]);
});

export const removeItemAtom = atom(null, (get, set, id: string) => {
  set(cartItemsAtom, get(cartItemsAtom).filter((i) => i.id !== id));
});
```

3. **Generate the test file.** Create tests appropriate to the library:
   - Initial state values
   - Each action/setter
   - Reset to initial state

4. **Verify.**

   ```bash
   npx tsc --noEmit
   ```

## CRITICAL RULES

### UI State ONLY

A store MUST only contain transient UI state. If data comes from an API or
database, it belongs in React Query / SWR, not in a store.

**Acceptable state:**
- Filter selections, sort order, search query
- Modal visibility, sidebar state
- Form drafts (before submission)
- Selected items (multi-select UI)
- Tab index, accordion open/closed
- Theme preference, locale selection

**NEVER in a store:**
- User profile data (from API)
- List data (from database)
- Any cached server response

### Required Patterns

1. Always include a `reset()` action
2. Extract `initialState` for clean reset
3. Use TypeScript types for all state and actions
4. Export selector hooks (Zustand) or typed selectors (Redux)
5. Keep stores focused — one domain per store

## Generated Files

```
stores/use<Name>Store.ts          (Zustand)
store/slices/<name>Slice.ts       (Redux)
stores/<Name>Store.ts             (MobX)
atoms/<name>Atoms.ts              (Jotai)
__tests__/stores/<name>.test.ts   (test file)
```
