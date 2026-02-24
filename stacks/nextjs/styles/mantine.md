# Mantine UI Style Guide

## Overview

Use Mantine v7+ components for all UI. Never use raw HTML when a Mantine component exists.

## Component Mapping

| Raw HTML | Use Instead |
|----------|-------------|
| `<button>` | `<Button>` |
| `<input>` | `<TextInput>`, `<NumberInput>`, etc. |
| `<textarea>` | `<Textarea>` |
| `<select>` | `<Select>` or `<NativeSelect>` |
| `<form>` | `<form>` with `@mantine/form` hooks |
| `<table>` | `<Table>` |
| `<div>` for layout | `<Stack>`, `<Group>`, `<Flex>`, `<Grid>` |
| `<div>` for card | `<Card>`, `<Paper>` |
| `<span>` for text | `<Text>` |
| `<h1>`-`<h6>` | `<Title order={n}>` |
| `<p>` | `<Text>` |
| `<a>` | `<Anchor>` or Next.js `<Link>` |
| `<ul>` / `<ol>` | `<List>` |
| `<dialog>` / `<div>` modal | `<Modal>` |
| Custom spinner | `<LoadingOverlay>` or `<Loader>` |
| Custom alert | `<Alert>` |
| Custom card | `<Card>` |

## Import Organization

Mantine imports go in the **Third-party** group (group 2):

```typescript
// 1. React / Next.js
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

// 2. Third-party (Mantine)
import { Button, TextInput, Stack, Group } from '@mantine/core';
import { useForm } from '@mantine/form';
import { showNotification } from '@mantine/notifications';

// 3. Internal
import { fetchProjectsApi } from '@/services/projects';
```

## Layout Components

```tsx
// Vertical stack with gap
<Stack gap="md">
  <Component1 />
  <Component2 />
</Stack>

// Horizontal group with gap
<Group gap="sm">
  <Button>Action 1</Button>
  <Button>Action 2</Button>
</Group>

// Responsive grid
<Grid>
  <Grid.Col span={{ base: 12, md: 6 }}>
    <Content />
  </Grid.Col>
</Grid>
```

## Layout Provider Setup

Set up MantineProvider in the root layout:

```tsx
// src/app/layout.tsx
import { MantineProvider, ColorSchemeScript } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { theme } from '@/styles/theme';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <ColorSchemeScript />
      </head>
      <body>
        <MantineProvider theme={theme}>
          <Notifications position="top-right" />
          {children}
        </MantineProvider>
      </body>
    </html>
  );
}
```

## Server vs Client Components

Mantine layout components (`Card`, `Stack`, `Text`, `Title`, `Badge`, `Group`) work in Server Components — no `'use client'` needed for display-only usage.

Interactive components requiring hooks or event handlers still need `'use client'`:

```tsx
// Server Component (no directive needed)
import { Card, Text, Badge, Group, Stack } from '@mantine/core';

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Card shadow="sm" padding="lg">
      <Group justify="space-between">
        <Text fw={500}>{project.name}</Text>
        <Badge color={project.status === 'active' ? 'green' : 'gray'}>
          {project.status}
        </Badge>
      </Group>
      <Text size="sm" c="dimmed" mt="xs">{project.description}</Text>
    </Card>
  );
}
```

## Form Handling

Use `@mantine/form` for all forms:

```tsx
'use client';

import { useForm } from '@mantine/form';
import { TextInput, PasswordInput, Button, Stack } from '@mantine/core';
import { showNotification } from '@mantine/notifications';

const form = useForm({
  initialValues: {
    email: '',
    password: '',
  },
  validate: {
    email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
    password: (value) => (value.length >= 8 ? null : 'Password too short'),
  },
});

const handleSubmit = form.onSubmit((values) => {
  (async () => {
    try {
      await submitApi(values);
      showNotification({ title: 'Success', message: 'Saved', color: 'green' });
      form.reset();
    } catch {
      showNotification({ title: 'Error', message: 'Failed', color: 'red' });
    }
  })();
});

<form onSubmit={handleSubmit}>
  <Stack gap="md">
    <TextInput {...form.getInputProps('email')} label="Email" />
    <PasswordInput {...form.getInputProps('password')} label="Password" />
    <Button type="submit">Submit</Button>
  </Stack>
</form>
```

## Notifications

Use `@mantine/notifications` for all user feedback:

```tsx
import { notifications } from '@mantine/notifications';

// Success
notifications.show({
  title: 'Success',
  message: 'Your changes have been saved',
  color: 'green',
});

// Error
notifications.show({
  title: 'Error',
  message: 'Something went wrong',
  color: 'red',
});
```

## Modals

Use `@mantine/modals` for confirmations and dialogs:

```tsx
import { modals } from '@mantine/modals';

modals.openConfirmModal({
  title: 'Delete item?',
  children: <Text>This action cannot be undone.</Text>,
  labels: { confirm: 'Delete', cancel: 'Cancel' },
  confirmProps: { color: 'red' },
  onConfirm: () => deleteItem(),
});
```

## Loading States

Use Mantine loading components:

```tsx
<LoadingOverlay visible={isLoading} />
<Skeleton height={50} visible={isLoading} />
<Button loading={isSubmitting}>Submit</Button>
```

## Error States

Use Mantine's `Alert` component:

```tsx
import { Alert } from '@mantine/core';

if (error) {
  return (
    <Alert color="red" title="Error">
      {error.message}
    </Alert>
  );
}
```

## Loading and Error Pages

```tsx
// loading.tsx
import { Center, Loader } from '@mantine/core';

export default function Loading() {
  return (
    <Center h="60vh">
      <Loader size="xl" />
    </Center>
  );
}

// error.tsx
'use client';

import { Alert, Button, Stack } from '@mantine/core';

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <Stack align="center" mt="xl">
      <Alert color="red" title="Something went wrong">
        {error.message}
      </Alert>
      <Button onClick={reset}>Try again</Button>
    </Stack>
  );
}
```

## Theming

Access theme values via hooks, never hardcode colors:

```tsx
import { useMantineTheme } from '@mantine/core';

const theme = useMantineTheme();
// Use theme.colors.blue[6] instead of '#228be6'
```
